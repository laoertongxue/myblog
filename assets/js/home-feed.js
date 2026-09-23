// Enhance the static ten-article pages only on mobile; links remain the no-JS fallback.
(() => {
  const feed = document.querySelector('.home-feed');
  if (!feed || !('IntersectionObserver' in window)) return;
  const loader = document.querySelector('.feed-loader');
  const status = loader.querySelector('[role="status"]');
  const retry = loader.querySelector('button');
  const mobile = matchMedia('(max-width: 760px)');
  const initialContent = feed.innerHTML;
  const initialNext = feed.dataset.next;
  let next = initialNext;
  let request = null;
  let failed = false;

  const observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) loadNext();
  }, { rootMargin: '200px 0px' });

  async function loadNext() {
    if (!mobile.matches || !next || request || failed) return;
    const controller = new AbortController();
    request = controller;
    observer.disconnect();
    feed.setAttribute('aria-busy', 'true');
    status.textContent = '正在加载更多文章…';
    retry.hidden = true;
    try {
      const response = await fetch(next, { signal: controller.signal });
      if (!response.ok) throw new Error('Page unavailable');
      const documentNext = new DOMParser().parseFromString(await response.text(), 'text/html');
      const nextFeed = documentNext.querySelector('.home-feed');
      if (!nextFeed || !nextFeed.querySelector('.post-row')) throw new Error('Invalid article page');
      if (request !== controller || !mobile.matches) return;
      const existing = new Set([...feed.querySelectorAll('h2 a')].map(link => link.getAttribute('href')));
      for (const row of nextFeed.querySelectorAll('.post-row')) {
        const href = row.querySelector('h2 a')?.getAttribute('href');
        if (href && !existing.has(href)) { feed.append(row); existing.add(href); }
      }
      next = nextFeed.dataset.next || '';
      status.textContent = next ? '继续滑动，加载更多文章' : '已加载全部文章';
    } catch (error) {
      if (error.name === 'AbortError' || request !== controller) return;
      failed = true;
      status.textContent = '暂时无法加载更多文章';
      retry.hidden = false;
    } finally {
      if (request === controller) {
        request = null;
        feed.removeAttribute('aria-busy');
        if (mobile.matches && next && !failed) observer.observe(loader);
      }
    }
  }

  function syncMode() {
    request?.abort();
    request = null;
    observer.disconnect();
    // Return to the server-rendered page when switching to desktop pagination.
    feed.innerHTML = initialContent;
    feed.removeAttribute('aria-busy');
    next = initialNext;
    failed = false;
    retry.hidden = true;
    document.documentElement.classList.toggle('mobile-feed', mobile.matches);
    loader.hidden = !mobile.matches;
    status.textContent = next ? '继续滑动，加载更多文章' : '已加载全部文章';
    if (mobile.matches && next) observer.observe(loader);
  }
  retry.addEventListener('click', () => { failed = false; loadNext(); });
  mobile.addEventListener('change', syncMode);
  syncMode();
})();
