'use strict';
document.body.classList.add('js');
const chinese = document.documentElement.lang === 'zh-CN';
const ui = chinese ? {
  openMenu: '打开导航', closeMenu: '关闭导航',
  play: '播放相册', pause: '暂停相册',
  paperCount: (visible, total) => `显示 ${visible} 篇，共 ${total} 篇论文`,
} : {
  openMenu: 'Open navigation', closeMenu: 'Close navigation',
  play: 'Play slideshow', pause: 'Pause slideshow',
  paperCount: (visible, total) => `${visible} of ${total} publications`,
};

// The static link works without JS; enhance it with the current page state.
const languageSwitch = document.querySelector('[data-language-switch]');
const languageTarget = languageSwitch ? new URL(languageSwitch.href) : null;
function syncLanguageSwitch() {
  if (!languageTarget) return;
  const target = new URL(languageTarget);
  target.search = location.search;
  target.hash = location.hash;
  const search = document.querySelector('#paper-search');
  if (search) {
    const filters = {
      q: search.value,
      year: document.querySelector('#paper-year').value,
      type: document.querySelector('[data-status][aria-pressed="true"]')?.dataset.status || 'All',
    };
    for (const [key, value] of Object.entries(filters)) {
      if (value && (key === 'q' || value !== 'All')) target.searchParams.set(key, value);
      else target.searchParams.delete(key);
    }
  }
  languageSwitch.href = target.href;
}
languageSwitch?.addEventListener('click', syncLanguageSwitch);
window.addEventListener('hashchange', syncLanguageSwitch);

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.site-nav');
function closeMenu() {
  navigation.classList.remove('open');
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', ui.openMenu);
}
menuButton?.addEventListener('click', () => {
  const open = navigation.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? ui.closeMenu : ui.openMenu);
});
navigation?.addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && navigation.classList.contains('open')) { closeMenu(); menuButton.focus(); } });
document.addEventListener('click', e => { if (!e.target.closest('.site-header')) closeMenu(); });

// The full bibliography is rendered in HTML; filtering only changes visibility.
const searchInput = document.querySelector('#paper-search');
if (searchInput) {
  const year = document.querySelector('#paper-year');
  const typeButtons = [...document.querySelectorAll('[data-status]')];
  const papers = [...document.querySelectorAll('.pub-item')];
  let status = 'All';
  const params = new URLSearchParams(location.search);
  searchInput.value = params.get('q') || '';
  if ([...year.options].some(o => o.value === params.get('year'))) year.value = params.get('year');
  if (typeButtons.some(button => button.dataset.status === params.get('type'))) status = params.get('type');
  function filterPapers() {
    const terms = searchInput.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;
    papers.forEach(paper => {
      const haystack = paper.dataset.search;
      const matches = terms.every(term => haystack.includes(term)) && (year.value === 'All' || paper.dataset.year === year.value) && (status === 'All' || paper.dataset.type === status);
      paper.hidden = !matches;
      visible += Number(matches);
    });
    document.querySelectorAll('.pub-year').forEach(section => { section.hidden = ![...section.querySelectorAll('.pub-item')].some(p => !p.hidden); });
    document.querySelector('#paper-count').textContent = ui.paperCount(visible, papers.length);
    document.querySelector('#no-results').hidden = visible !== 0;
    typeButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.status === status)));
    syncLanguageSwitch();
  }
  searchInput.addEventListener('input', filterPapers);
  year.addEventListener('change', filterPapers);
  typeButtons.forEach(button => button.addEventListener('click', () => { status = button.dataset.status; filterPapers(); }));
  document.querySelectorAll('[data-reset-filters]').forEach(button => button.addEventListener('click', () => { searchInput.value = ''; year.value = 'All'; status = 'All'; filterPapers(); searchInput.focus(); }));
  filterPapers();
}

const gallery = document.querySelector('[data-gallery]');
if (gallery) {
  const slides = [...gallery.querySelectorAll('.gallery-stage figure')];
  const thumbs = [...gallery.querySelectorAll('.gallery-thumb')];
  const thumbRail = gallery.querySelector('.gallery-thumbs');
  const play = gallery.querySelector('[data-gallery-play]');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let index = 0, playing = false, timer;
  function show(next) {
    index = (next + slides.length) % slides.length;
    slides.forEach((slide, i) => { slide.hidden = i !== index; });
    thumbs.forEach((thumb, i) => thumb.setAttribute('aria-pressed', String(i === index)));
    gallery.querySelector('.gallery-counter').textContent = `${String(index + 1).padStart(2, '0')} / ${String(slides.length).padStart(2, '0')}`;
    const selected = thumbs[index];
    const left = selected.offsetLeft;
    const right = left + selected.offsetWidth;
    if (left < thumbRail.scrollLeft || right > thumbRail.scrollLeft + thumbRail.clientWidth) {
      // Scroll only the thumbnail strip; keep the page and main photo in place.
      thumbRail.scrollTo({ left: left - (thumbRail.clientWidth - selected.offsetWidth) / 2, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
    }
  }
  function updatePlayback() {
    clearInterval(timer);
    play.setAttribute('aria-label', playing ? ui.pause : ui.play);
    play.title = playing ? ui.pause : ui.play;
    play.querySelector('[data-play-icon]').hidden = playing;
    play.querySelector('[data-pause-icon]').hidden = !playing;
    gallery.querySelector('.gallery-stage').setAttribute('aria-live', playing ? 'off' : 'polite');
    if (playing && !document.hidden) timer = setInterval(() => show(index + 1), 7000);
  }
  function manual(next) { playing = false; updatePlayback(); show(next); }
  thumbs.forEach((thumb, i) => thumb.addEventListener('click', () => manual(i)));
  gallery.querySelector('[data-gallery-prev]').addEventListener('click', () => manual(index - 1));
  gallery.querySelector('[data-gallery-next]').addEventListener('click', () => manual(index + 1));
  play.addEventListener('click', () => { playing = !playing; updatePlayback(); });
  gallery.addEventListener('keydown', e => { if (e.key === 'ArrowRight') { e.preventDefault(); manual(index + 1); } if (e.key === 'ArrowLeft') { e.preventDefault(); manual(index - 1); } });
  document.addEventListener('visibilitychange', updatePlayback);
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) { playing = false; updatePlayback(); } });
  show(0); updatePlayback();
}
syncLanguageSwitch();
