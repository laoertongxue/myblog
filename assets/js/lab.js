(() => {
  const menuDialog = document.querySelector('#mobile-navigation');
  const menuToggle = document.querySelector('.mobile-menu-toggle');
  if (menuDialog && menuToggle) {
    const mobile = matchMedia('(max-width: 760px)');
    const close = () => menuDialog.close();
    menuToggle.addEventListener('click', () => {
      if (!mobile.matches) return;
      menuDialog.showModal();
      menuToggle.setAttribute('aria-expanded', 'true');
      document.documentElement.classList.add('navigation-open');
    });
    menuDialog.querySelector('.mobile-menu-close').addEventListener('click', close);
    menuDialog.addEventListener('click', event => {
      if (event.target === menuDialog || event.target.closest('a')) close();
    });
    menuDialog.addEventListener('close', () => {
      menuToggle.setAttribute('aria-expanded', 'false');
      document.documentElement.classList.remove('navigation-open');
      if (mobile.matches) menuToggle.focus();
    });
    mobile.addEventListener('change', () => { if (!mobile.matches && menuDialog.open) close(); });
  }

  const toc = document.querySelector('.floating-toc');
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    if (toc?.open) { toc.open = false; toc.querySelector('summary').focus(); }
  });
  document.addEventListener('click', event => { if (toc?.open && !toc.contains(event.target)) toc.open = false; });
  if (toc) {
    const links = [...toc.querySelectorAll('a')];
    const entries = links.map(link => ({ link, heading: document.getElementById(decodeURIComponent(link.hash.slice(1))) })).filter(entry => entry.heading);
    const update = () => {
      const atBottom = window.scrollY > 0 && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
      const active = atBottom ? entries.at(-1) : (entries.filter(entry => entry.heading.getBoundingClientRect().top <= 150).at(-1) || entries[0]);
      entries.forEach(entry => entry === active ? entry.link.setAttribute('aria-current', 'location') : entry.link.removeAttribute('aria-current'));
    };
    let pending = false;
    window.addEventListener('scroll', () => { if (!pending) { pending = true; requestAnimationFrame(() => { update(); pending = false; }); } }, { passive: true });
    links.forEach(link => link.addEventListener('click', () => { toc.open = false; }));
    update();
  }
})();
