#!/usr/bin/env node
// Runs every browser regression check against a build of this repository.
//
// The check files in scripts/ are *closures* (`async (page, ctx) => {...}`),
// not programs: `node scripts/check-design-browser.js` exits 0 and asserts
// nothing. Before this runner existed they could only be executed by hand,
// through playwright-cli run-code, against a manually started static server on
// port 1316 - so nothing in CI ever ran them.
//
// This runner provides the missing pieces:
//   * a dependency-free static file server (mirrors the production Caddy
//     behaviour: directory index, and 404.html served with status 404),
//   * one isolated browser context per check,
//   * a shared failure net (pageerror + non-aborted requestfailed) for checks
//     that forgot to attach their own listener,
//   * a per-check watchdog, and a non-zero exit code when anything fails.
//
// Usage: npm run check:browser [-- --dir public] [--only design] [--list]
//
// Exit codes: 0 all passed, 1 a check failed, 3 playwright/browser missing.

import { createServer } from 'node:http';
import { mkdir, readFile, stat } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

// fileURLToPath instead of import.meta.dirname: keeps this runnable on whatever
// Node the CI image ships (>=18) instead of requiring 20.11+.
const ROOT = fileURLToPath(new URL('..', import.meta.url));

// Keep this list explicit: `--list` is the record of what actually runs.
const CHECKS = [
  { name: 'design', file: 'check-design-browser.js', description: 'layout, all blog images and originals, pagination, TOC, search, no-JS pagination' },
  { name: 'mobile-navigation', file: 'check-mobile-navigation.js', description: 'mobile dialog open/close/focus, footer, reading stats' },
  { name: 'adversarial-ui', file: 'check-adversarial-ui.js', description: 'long-content overflow, aria-current, contrast, image priority' },
  { name: 'agent-series', file: 'check-agent-series-browser.js', description: 'Agent/Harness series structure end to end' },
  { name: 'thumbnail-fit', file: 'check-thumbnail-fit-browser.js', description: '900:383 thumbnail frames, complete images and responsive widths' },
  { name: 'resource-loading', file: 'check-resource-loading.js', description: 'chosen image candidates, lazy search index, no hidden avatar' },
];

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

function parseArgs(argv) {
  const options = { dir: '.hugo-check', port: 1316, only: null, list: false, timeout: 600 };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--dir') options.dir = argv[++i];
    else if (arg === '--port') options.port = Number(argv[++i]);
    else if (arg === '--only') options.only = argv[++i].split(',').map(value => value.trim());
    else if (arg === '--timeout') options.timeout = Number(argv[++i]);
    else if (arg === '--list') options.list = true;
    else if (arg === '--help' || arg === '-h') options.help = true;
    else throw new Error(`unknown argument: ${arg}`);
  }
  return options;
}

// hugo.toml owns the page size; passing it in keeps the checks from carrying a
// second copy of the number.
function readPagerSize() {
  const config = readFileSync(path.join(ROOT, 'hugo.toml'), 'utf8');
  const match = config.match(/pagerSize\s*=\s*(\d+)/);
  if (!match) throw new Error('hugo.toml: pagination.pagerSize not found');
  return Number(match[1]);
}

// The production security headers live in scripts/Caddyfile. They are applied
// to the local static server too, so the browser checks exercise the real
// policy: a blocked script, stylesheet or picture fails this run instead of
// silently breaking the deployed site.
function readCaddyHeaders() {
  const config = readFileSync(path.join(ROOT, 'scripts/Caddyfile'), 'utf8');
  const headers = {};
  const wanted = {
    'Content-Security-Policy': 'content-security-policy',
    'X-Content-Type-Options': 'x-content-type-options',
    'X-Frame-Options': 'x-frame-options',
    'Referrer-Policy': 'referrer-policy',
  };
  for (const [directive, header] of Object.entries(wanted)) {
    const match = config.match(new RegExp(`${directive}\\s+"([^"]+)"`));
    if (!match) throw new Error(`scripts/Caddyfile: ${directive} not found (update this reader)`);
    headers[header] = match[1];
  }
  return headers;
}

function serve(directory, port, headers) {
  const root = path.resolve(directory);
  const server = createServer(async (request, response) => {
    const url = new URL(request.url, `http://127.0.0.1:${port}`);
    let target;
    try {
      target = path.join(root, decodeURIComponent(url.pathname));
    } catch {
      response.writeHead(400, headers).end('bad request');
      return;
    }
    if (target !== root && !target.startsWith(root + path.sep)) {
      response.writeHead(403, headers).end('forbidden');
      return;
    }
    if (existsSync(target) && !target.endsWith(path.sep)) {
      const stats = await stat(target);
      if (stats.isDirectory()) target = path.join(target, 'index.html');
    } else {
      target = path.join(target, 'index.html');
    }
    const send = async (file, status) => {
      try {
        const body = await readFile(file);
        response.writeHead(status, { ...headers, 'content-type': MIME[path.extname(file)] ?? 'application/octet-stream' });
        response.end(body);
      } catch {
        response.writeHead(404, { ...headers, 'content-type': 'text/plain; charset=utf-8' }).end('not found');
      }
    };
    if (existsSync(target)) return send(target, 200);
    // Same contract as the Caddyfile: the custom page keeps the 404 status.
    const notFound = path.join(root, '404.html');
    return send(existsSync(notFound) ? notFound : target, 404);
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

async function loadChecks(names) {
  const checks = [];
  for (const check of CHECKS) {
    if (names && !names.includes(check.name)) continue;
    const source = await readFile(path.join(ROOT, 'scripts', check.file), 'utf8');
    checks.push({ ...check, run: new Function(`return (${source});`)() });
  }
  return checks;
}

function makeContext({ base, directory, pagerSize }) {
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  return {
    base,
    dir: directory,
    root: ROOT,
    pagerSize,
    assert,
    // Crawl a listing's pagination and return every article link in order.
    // Page size comes from hugo.toml, never from a literal in the checks.
    async walkPagination(page, { path: listing = '/', rowSelector = '.post-row', linkSelector = 'h2 a' } = {}) {
      await page.goto(base + listing);
      const advertised = (await page.locator('.feed-pagination a, .feed-pagination [aria-current=page]').allTextContents())
        .map(Number).filter(Number.isFinite);
      const lastPage = advertised.length ? Math.max(...advertised) : 1;
      const links = [];
      let pages = 0;
      for (;;) {
        pages++;
        assert(pages <= 200, `${listing}: pagination did not terminate`);
        const current = await page.locator(`${rowSelector} ${linkSelector}`)
          .evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
        const next = page.locator('.feed-pagination [rel=next]');
        const hasNext = await next.count() > 0;
        assert(current.length <= pagerSize, `${listing}: page ${pages} lists ${current.length} rows, above pagerSize ${pagerSize}`);
        if (hasNext) {
          assert(current.length === pagerSize, `${listing}: non-final page ${pages} lists ${current.length} rows, expected ${pagerSize}`);
        }
        links.push(...current);
        if (lastPage > 1) {
          const active = (await page.locator('.feed-pagination [aria-current=page]').textContent()).trim();
          assert(active === String(pages), `${listing}: page ${pages} marks "${active}" as current`);
        } else {
          assert(await page.locator('.feed-pagination').count() === 0, `${listing}: single-page listing should not render pagination`);
        }
        if (!hasNext) break;
        await next.click();
        await page.waitForFunction(expected => document.querySelector('.feed-pagination [aria-current=page]')?.textContent.trim() === String(expected), pages + 1);
      }
      assert(pages === lastPage, `${listing}: walked ${pages} page(s) but the pager advertises ${lastPage}`);
      assert(new Set(links).size === links.length, `${listing}: duplicate articles across pages`);
      return { pages, links, lastPage };
    },
    // Number of published items a section feed advertises (used instead of a
    // hardcoded "this topic has N chapters").
    async rssCount(feedPath) {
      const response = await fetch(base + feedPath);
      assert(response.ok, `${feedPath}: HTTP ${response.status}`);
      const xml = await response.text();
      return (xml.match(/<item>/g) ?? []).length;
    },
  };
}

function withTimeout(promise, seconds, label) {
  let timer;
  const guard = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label}: timed out after ${seconds}s`)), seconds * 1000);
  });
  return Promise.race([promise, guard]).finally(() => clearTimeout(timer));
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log('usage: node scripts/run-browser-checks.mjs [--dir .hugo-check] [--port 1316] [--only name,name] [--timeout 600] [--list]');
    return 0;
  }
  if (options.list) {
    for (const check of CHECKS) console.log(`${check.name.padEnd(20)} ${check.file}  ${check.description}`);
    return 0;
  }
  const directory = path.resolve(ROOT, options.dir);
  if (!existsSync(directory)) {
    console.error(`browser checks: build directory not found: ${directory}`);
    console.error('browser checks: run `make check` first, or pass --dir <build output>');
    return 1;
  }

  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch (error) {
    console.error('browser checks: playwright is not installed');
    console.error('browser checks: npm ci && npx playwright install chromium');
    return 3;
  }

  const pagerSize = readPagerSize();
  const headers = readCaddyHeaders();
  await mkdir(path.join(ROOT, 'output/playwright'), { recursive: true });
  const server = await serve(directory, options.port, headers);
  const base = `http://127.0.0.1:${options.port}`;
  const context = makeContext({ base, directory, pagerSize });
  const checks = await loadChecks(options.only);
  if (!checks.length) throw new Error('no checks selected');

  let browser;
  try {
    browser = await chromium.launch();
  } catch (error) {
    console.error(`browser checks: chromium is not available - ${String(error.message).split('\n')[0]}`);
    console.error('browser checks: npx playwright install chromium');
    server.close();
    return 3;
  }

  const results = [];
  try {
    for (const check of checks) {
      const pageContext = await browser.newContext({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1 });
      const page = await pageContext.newPage();
      const problems = [];
      page.on('pageerror', error => problems.push(`pageerror: ${error.message}`));
      page.on('console', message => {
        // A blocked inline block (e.g. the JSON-LD data block) only shows up here.
        if (/content security policy/i.test(message.text())) problems.push(`csp: ${message.text()}`);
      });
      page.on('requestfailed', request => {
        const text = request.failure()?.errorText ?? '';
        // Navigation cancels in-flight subresources; that is not a broken link.
        if (!text.includes('ERR_ABORTED')) problems.push(`requestfailed: ${request.url()} (${text})`);
      });
      try {
        const report = await withTimeout(check.run(page, context), options.timeout, check.name);
        const lines = Array.isArray(report) ? report : [String(report)];
        if (problems.length) throw new Error(problems.join('\n'));
        console.log(`ok    browser/${check.name}: ${lines.length} assertion group(s), ${lines.at(-1)}`);
      } catch (error) {
        results.push({ name: check.name, error });
        console.error(`FAIL  browser/${check.name}: ${error.message}`);
        if (problems.length && !String(error.message).includes(problems[0])) {
          console.error(`      also saw: ${problems.join('; ')}`);
        }
      } finally {
        await pageContext.close().catch(() => {});
      }
    }
  } finally {
    await browser.close().catch(() => {});
    server.close();
  }

  if (results.length) {
    console.error(`\n${results.length}/${checks.length} browser check(s) failed: ${results.map(result => result.name).join(', ')}`);
    return 1;
  }
  console.log(`\nAll ${checks.length} browser checks passed (${directory} served on ${base}).`);
  return 0;
}

main()
  .then(code => process.exit(code))
  .catch(error => {
    console.error(`browser checks: ${error.stack ?? error.message}`);
    process.exit(1);
  });
