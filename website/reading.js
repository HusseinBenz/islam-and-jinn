/* Jinn in Islam — gentle reading helpers. The pages work fully without it.
   · a thin progress thread under the header
   · the section you are reading is highlighted in "In this chapter"
   · your place is kept in this browser, and read chapters get a tick */
(function () {
  'use strict';
  var KEY = 'jinn-reading';
  var store = {};
  try { store = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { store = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* private mode */ } }
  store.read = store.read || {};

  // Mark chapters already read, everywhere they are listed
  Array.prototype.forEach.call(document.querySelectorAll('[data-slug]'), function (el) {
    if (el.tagName === 'A' && store.read[el.getAttribute('data-slug')]) el.classList.add('is-read');
  });

  var article = document.querySelector('.article[data-slug]');
  if (!article) {
    // Portal: offer to pick up where the reader left off
    var resume = document.getElementById('resume');
    if (resume && store.last && store.last.href && store.last.progress < 97) {
      resume.href = store.last.href;
      resume.querySelector('strong').textContent = store.last.title + ' · ' + store.last.progress + '%';
      resume.hidden = false;
    }
    return;
  }

  var prose = article.querySelector('.prose');
  var bar = document.querySelector('.reading-progress span');
  var card = document.querySelector('.progress-card');
  var ring = card && card.querySelector('.progress-ring');
  var label = card && card.querySelector('.progress-ring span');
  var left = card && card.querySelector('.progress-card__text strong');
  var minutes = parseInt(article.getAttribute('data-minutes'), 10) || 1;
  var slug = article.getAttribute('data-slug');
  var href = 'articles/' + slug + '/';
  if (card) card.hidden = false;

  var ticking = false;
  function measure() {
    ticking = false;
    var rect = prose.getBoundingClientRect();
    var total = rect.height - window.innerHeight * 0.6;
    var p = total > 0 ? Math.min(100, Math.max(0, Math.round((-rect.top + window.innerHeight * 0.3) / total * 100))) : 100;
    if (bar) bar.style.width = p + '%';
    if (ring) { ring.style.setProperty('--p', p); label.textContent = p + '%'; }
    if (left) {
      var m = Math.max(0, Math.round(minutes * (100 - p) / 100));
      left.textContent = p >= 97 ? 'Chapter finished' : m <= 1 ? 'About a minute left' : 'About ' + m + ' min left';
    }
    store.last = { slug: slug, href: href, title: article.getAttribute('data-title'), progress: p };
    if (p >= 97) store.read[slug] = true;
    save();
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(measure); } }, { passive: true });
  window.addEventListener('resize', measure, { passive: true });
  measure();

  // Highlight the current section in the table of contents
  var links = document.querySelectorAll('.reading-sidebar .toc a[href^="#"]');
  if (!links.length || !('IntersectionObserver' in window)) return;
  var byId = {};
  Array.prototype.forEach.call(links, function (a) { byId[decodeURIComponent(a.getAttribute('href').slice(1))] = a; });
  var heads = Array.prototype.filter.call(prose.querySelectorAll('h2[id], h3[id]'), function (h) { return byId[h.id]; });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      Array.prototype.forEach.call(links, function (a) { a.classList.remove('is-active'); });
      byId[e.target.id].classList.add('is-active');
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  heads.forEach(function (h) { io.observe(h); });
})();
