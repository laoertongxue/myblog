(() => {
  const search = document.querySelector('.search-page');
  if (!search) return;
  const input = document.querySelector('#search-query');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  const labels = { blog: '博客', weekly: 'Weekly', topics: '专题' };
  let filter = 'all';
  let indexPromise;
  let revision = 0;
  const getIndex = () => indexPromise ||= fetch(search.dataset.index).then(response => {
    if (!response.ok) throw new Error('Search index unavailable');
    return response.json();
  }).catch(error => { indexPromise = undefined; throw error; });
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const render = async () => {
    const current = ++revision;
    const query = input.value.trim();
    const url = new URL(location.href);
    if (query) url.searchParams.set('q', query); else url.searchParams.delete('q');
    if (filter !== 'all') url.searchParams.set('type', filter); else url.searchParams.delete('type');
    history.replaceState(null, '', url);
    results.replaceChildren();
    document.querySelectorAll('[data-count]').forEach(node => { node.textContent = '0'; });
    if (!query) { status.textContent = '输入关键词，查找博客、Weekly 和专题文章。'; return; }
    status.textContent = '正在搜索…';
    try {
      const index = await getIndex();
      if (current !== revision) return;
      const words = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
      const matches = index.filter(item => {
        const haystack = [item.title, item.description, item.text, ...item.tags].join(' ').toLocaleLowerCase();
        return words.every(word => haystack.includes(word));
      });
      document.querySelectorAll('[data-count]').forEach(node => { node.textContent = String(node.dataset.count === 'all' ? matches.length : matches.filter(item => item.section === node.dataset.count).length); });
      const visible = matches.filter(item => filter === 'all' || item.section === filter);
      status.textContent = visible.length ? `“${query}” 共找到 ${visible.length} 条结果` : `没有找到与“${query}”相关的${filter === 'all' ? '内容' : labels[filter]}，试试其他关键词或筛选。`;
      visible.forEach(item => {
        const row = element('article', '', 'search-result');
        const title = element('h2', '');
        const link = element('a', item.title);
        link.href = item.url;
        title.append(link);
        row.append(element('span', labels[item.section], 'result-kind'), title, element('p', item.description));
        if (item.date) row.append(element('time', item.date));
        results.append(row);
      });
    } catch {
      if (current === revision) status.textContent = '搜索暂时无法加载，请点击“搜索”重试。';
    }
  };
  const restore = () => {
    const params = new URLSearchParams(location.search);
    input.value = params.get('q') || '';
    filter = Object.hasOwn(labels, params.get('type')) ? params.get('type') : 'all';
    document.querySelectorAll('[data-filter]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
    render();
  };
  search.querySelector('form').addEventListener('submit', event => { event.preventDefault(); render(); });
  input.addEventListener('search', () => { if (!input.value) render(); });
  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    render();
  }));
  window.addEventListener('popstate', restore);
  restore();
})();
