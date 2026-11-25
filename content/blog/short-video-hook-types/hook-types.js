(() => {
  'use strict';
  const root = document.querySelector('.hook-types-study');
  if (!root) return;
  const byId = id => root.querySelector('#' + id);
  const filterBar = byId('filters');
  const search = byId('q');
  const count = byId('countNote');
  const buttons = Array.from(filterBar.querySelectorAll('button[data-fam]'));
  const cards = Array.from(byId('typeList').querySelectorAll('.type-card'));
  const empty = document.createElement('p');
  empty.textContent = '没有匹配的钩子类型，换个关键词试试。';
  empty.hidden = true;
  byId('typeList').append(empty);
  const searchable = cards.map(card => ['name', 'def', 'mech', 'good', 'bad'].map(key =>
    card.querySelector('[data-field="' + key + '"]').textContent
  ).join(' ').toLocaleLowerCase());
  let family = 'all';
  function render() {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    cards.forEach((card, i) => {
      const matches = (family === 'all' || family === card.dataset.fam) && (!query || searchable[i].includes(query));
      card.hidden = !matches;
      if (matches) visible++;
    });
    count.textContent = '当前显示 ' + visible + ' 种（共 ' + cards.length + ' 种）';
    empty.hidden = visible !== 0;
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    family = button.dataset.fam;
    buttons.forEach(el => {
      const selected = el === button;
      el.classList.toggle('on', selected);
      el.setAttribute('aria-pressed', String(selected));
    });
    render();
  }));
  search.addEventListener('input', render);
  render();
  const copy = byId('copyBtn');
  const message = byId('copyMsg');
  let timeout;
  copy.addEventListener('click', async () => {
    const pre = byId('skillText');
    const text = pre.textContent;
    let copied = false;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        copied = true;
      }
    } catch {
      // Older browsers or denied permission: try the local selection fallback.
    }
    if (!copied) {
      const buffer = document.createElement('textarea');
      buffer.value = text;
      buffer.style.position = 'fixed';
      buffer.style.insetInlineStart = '-9999px';
      buffer.setAttribute('readonly', '');
      document.body.append(buffer);
      buffer.select();
      try { copied = document.execCommand('copy'); } catch { /* remain false */ }
      buffer.remove();
      copy.focus();
    }
    clearTimeout(timeout);
    message.textContent = copied ? '已复制，可直接粘贴进 Skill。' : '复制失败，请手动选中文本复制。';
    if (copied) timeout = setTimeout(() => { message.textContent = ''; }, 3000);
  });
})();
