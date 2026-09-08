(function () {
  'use strict';

  var root = document.documentElement;
  var glossary = Array.isArray(window.RAMAN_GLOSSARY) ? window.RAMAN_GLOSSARY : [];
  var originalAttributes = new WeakMap();
  var popover;
  var activeTerm;
  var languageListeners = [];

  function languageFrom(value) {
    return value === 'en' ? 'en' : 'zh';
  }

  function currentLanguage() {
    return root.lang === 'en' ? 'en' : 'zh';
  }

  function dispatchLanguageChange(language) {
    languageListeners.slice().forEach(function (listener) {
      listener(language);
    });
    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: language } }));
  }

  window.I18N = {
    t: function (translations) {
      return translations[currentLanguage()];
    },
    on: function (listener) {
      if (typeof listener === 'function') languageListeners.push(listener);
    },
    set: function (value) {
      setLanguage(value, true);
    }
  };
  Object.defineProperty(window.I18N, 'lang', {
    enumerable: true,
    get: currentLanguage
  });

  function rememberAttribute(element, name) {
    var saved = originalAttributes.get(element);
    if (!saved) {
      saved = {};
      originalAttributes.set(element, saved);
    }
    if (!Object.prototype.hasOwnProperty.call(saved, name)) {
      saved[name] = element.getAttribute(name);
    }
  }

  function swapAttributes(language) {
    var attrMap = {
      content: 'data-en-content',
      placeholder: 'data-en-placeholder',
      title: 'data-en-title',
      alt: 'data-en-alt',
      'aria-label': 'data-en-aria-label',
      value: 'data-en-value'
    };

    Object.keys(attrMap).forEach(function (attribute) {
      var dataName = attrMap[attribute];
      document.querySelectorAll('[' + dataName + ']').forEach(function (element) {
        rememberAttribute(element, attribute);
        if (language === 'en') {
          element.setAttribute(attribute, element.getAttribute(dataName));
        } else {
          var saved = originalAttributes.get(element) || {};
          if (saved[attribute] === null || typeof saved[attribute] === 'undefined') {
            element.removeAttribute(attribute);
          } else {
            element.setAttribute(attribute, saved[attribute]);
          }
        }
      });
    });

    document.querySelectorAll('[data-en]').forEach(function (element) {
      if (element.tagName === 'TITLE') {
        if (!Object.prototype.hasOwnProperty.call(element.dataset, 'zhText')) {
          element.dataset.zhText = element.textContent;
        }
        element.textContent = language === 'en' ? element.getAttribute('data-en') : element.dataset.zhText;
      } else if (element.tagName === 'OPTION') {
        if (!element.hasAttribute('data-zh')) element.setAttribute('data-zh', element.textContent);
        element.textContent = language === 'en' ? element.getAttribute('data-en') : element.getAttribute('data-zh');
      }
    });
  }

  function updatePageLanguageUrl(language) {
    try {
      var url = new URL(window.location.href);
      url.searchParams.set('lang', language);
      window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash);
    } catch (error) { /* URL/history are optional in non-browser test environments */ }
  }

  function updateRelativeLinkLanguages(language) {
    document.querySelectorAll('a[href]').forEach(function (link) {
      var href = link.getAttribute('href');
      if (!href || href.charAt(0) === '#' || /^([a-z][a-z\d+.-]*:|\/\/)/i.test(href) || !/\.html(?:$|[?#])/i.test(href)) return;
      var hashIndex = href.indexOf('#');
      var hash = hashIndex >= 0 ? href.slice(hashIndex) : '';
      var withoutHash = hashIndex >= 0 ? href.slice(0, hashIndex) : href;
      var queryIndex = withoutHash.indexOf('?');
      var path = queryIndex >= 0 ? withoutHash.slice(0, queryIndex) : withoutHash;
      var query = queryIndex >= 0 ? withoutHash.slice(queryIndex + 1) : '';
      var params = new URLSearchParams(query);
      params.set('lang', language);
      link.setAttribute('href', path + '?' + params.toString() + hash);
    });
  }

  function updateToggle(language) {
    document.querySelectorAll('.i18n-toggle button[data-lang]').forEach(function (button) {
      var active = languageFrom(button.getAttribute('data-lang')) === language;
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function setLanguage(value, persist, initialLoad) {
    var language = languageFrom(value);
    var changed = currentLanguage() !== language;
    root.lang = language === 'en' ? 'en' : 'zh-Hant';
    swapAttributes(language);
    updateToggle(language);
    updatePageLanguageUrl(language);
    updateRelativeLinkLanguages(language);
    if (persist) {
      try { window.localStorage.setItem('raman_lang', language); } catch (error) { /* storage is optional */ }
    }
    if (activeTerm) showPopover(activeTerm);
    if (changed || initialLoad) dispatchLanguageChange(language);
  }

  function createToggle() {
    var toggle = document.createElement('div');
    toggle.className = 'i18n-toggle';
    toggle.setAttribute('role', 'group');
    toggle.setAttribute('aria-label', 'Language');

    var zh = document.createElement('button');
    zh.type = 'button';
    zh.setAttribute('data-lang', 'zh');
    zh.setAttribute('lang', 'zh-Hant');
    zh.textContent = '中文';

    var en = document.createElement('button');
    en.type = 'button';
    en.setAttribute('data-lang', 'en');
    en.setAttribute('lang', 'en');
    en.textContent = 'EN';

    toggle.appendChild(zh);
    toggle.appendChild(en);
    toggle.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-lang]');
      if (button) setLanguage(button.getAttribute('data-lang'), true);
    });

    var slot = document.getElementById('i18n-slot');
    if (slot) slot.appendChild(toggle);
    else if (document.body) document.body.appendChild(toggle);
    updateToggle(currentLanguage());
  }

  function textHasExcludedAncestor(node) {
    var excluded = 'script,style,pre,code,kbd,svg,textarea,input,button,label,select,option,a,h1,h2,h3,h4,h5,h6,nav,header,.hero,.tag,.tags,.chip,.chips,.badge,.pill,.btn,.button,.i18n-popover';
    var element = node.parentElement;
    while (element) {
      if (element.matches(excluded) || element.classList.contains('term') ||
          element.classList.contains('i18n-toggle') || element.classList.contains('i18n-glossary') ||
          element.classList.contains('toc') || element.hasAttribute('data-no-term')) return true;
      element = element.parentElement;
    }
    return false;
  }

  function languageContext(node) {
    var element = node.parentElement;
    while (element) {
      if (element.hasAttribute('lang')) return element.getAttribute('lang');
      element = element.parentElement;
    }
    return root.lang;
  }

  var patternCache = {};

  function wholeWordPattern(term) {
    if (patternCache[term]) return patternCache[term];
    return patternCache[term] = new RegExp('(^|[^\\p{L}\\p{N}_])(' + term.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&') + ')(?=$|[^\\p{L}\\p{N}_])', 'iu');
  }

  function findMatch(text, terms, language) {
    var best = null;
    terms.forEach(function (term) {
      if (!term) return;
      var match;
      if (language === 'zh') {
        var index = text.indexOf(term);
        if (index >= 0) match = { index: index, length: term.length, text: term };
      } else {
        var pattern = wholeWordPattern(term);
        var found = pattern.exec(text);
        if (found) match = { index: found.index + found[1].length, length: found[2].length, text: found[2] };
      }
      if (match && (!best || match.index < best.index)) best = match;
    });
    return best;
  }

  var altShown = { zh: {}, en: {} };

  function wrapMatch(textNode, match, entry, language) {
    var text = textNode.nodeValue;
    var before = text.slice(0, match.index);
    var after = text.slice(match.index + match.length);
    var term = document.createElement('span');
    term.className = 'term';
    term.tabIndex = 0;
    term.setAttribute('data-term', entry.key);
    term.appendChild(document.createTextNode(match.text));
    if (!altShown[language][entry.key]) {
      altShown[language][entry.key] = true;
      var alternate = document.createElement('small');
      alternate.className = 'term-alt';
      alternate.textContent = language === 'zh' ? '（' + entry.en + '）' : ' (' + entry.zh + ')';
      term.appendChild(alternate);
    }

    var fragment = document.createDocumentFragment();
    if (before) fragment.appendChild(document.createTextNode(before));
    fragment.appendChild(term);
    if (after) fragment.appendChild(document.createTextNode(after));
    textNode.parentNode.replaceChild(fragment, textNode);
  }

  function annotateRegion(region, language) {
    var used = {};
    var ordered = glossary.slice().sort(function (a, b) {
      var la = String(language === 'zh' ? a.zh : a.en).length, lb = String(language === 'zh' ? b.zh : b.en).length;
      return lb - la;
    });
    ordered.forEach(function (entry) {
      var key = String(entry.key || '');
      if (!key || used[key]) return;
      var terms = language === 'zh' ? [entry.zh].concat(entry.aliasesZh || []) : [entry.en].concat(entry.aliasesEn || []);
      var walker = document.createTreeWalker(region, NodeFilter.SHOW_TEXT);
      var node;
      while ((node = walker.nextNode())) {
        if (textHasExcludedAncestor(node) || languageContext(node) !== (language === 'zh' ? 'zh-Hant' : 'en')) continue;
        var match = findMatch(node.nodeValue, terms, language);
        if (match) {
          wrapMatch(node, match, entry, language);
          used[key] = true;
          break;
        }
      }
    });
  }

  function annotateGlossaryTerms() {
    if (!glossary.length) return;
    var regions = Array.prototype.slice.call(document.querySelectorAll('body > section'));
    if (!regions.length) regions = [document.querySelector('main') || document.body].filter(Boolean);
    regions.forEach(function (region) {
      annotateRegion(region, 'zh');
      annotateRegion(region, 'en');
    });
  }

  function ensurePopover() {
    if (popover) return popover;
    popover = document.createElement('div');
    popover.className = 'i18n-popover';
    popover.hidden = true;
    popover.setAttribute('role', 'status');
    popover.innerHTML = '<div class="i18n-popover-title"></div><div class="i18n-popover-main"></div><div class="i18n-popover-secondary"></div>';
    document.body.appendChild(popover);
    popover.addEventListener('pointerdown', function (event) { event.stopPropagation(); });
    return popover;
  }

  function showPopover(term) {
    var entry = glossary.find(function (item) { return String(item.key) === term.getAttribute('data-term'); });
    if (!entry) return;
    var card = ensurePopover();
    var language = currentLanguage();
    card.querySelector('.i18n-popover-title').textContent = entry.zh + ' / ' + entry.en;
    card.querySelector('.i18n-popover-main').textContent = language === 'en' ? entry.defEn : entry.defZh;
    card.querySelector('.i18n-popover-secondary').textContent = language === 'en' ? entry.defZh : entry.defEn;
    card.hidden = false;
    activeTerm = term;

    var termBox = term.getBoundingClientRect();
    var cardBox = card.getBoundingClientRect();
    var left = termBox.left + (termBox.width / 2) - (cardBox.width / 2);
    var top = termBox.bottom + 9;
    var margin = 12;
    left = Math.max(margin, Math.min(left, window.innerWidth - cardBox.width - margin));
    if (top + cardBox.height > window.innerHeight - margin) top = termBox.top - cardBox.height - 9;
    top = Math.max(margin, Math.min(top, window.innerHeight - cardBox.height - margin));
    card.style.left = left + 'px';
    card.style.top = top + 'px';
  }

  function closePopover() {
    if (popover) popover.hidden = true;
    activeTerm = null;
  }

  function wirePopover() {
    document.addEventListener('pointerover', function (event) {
      var term = event.target.closest && event.target.closest('.term');
      if (term) showPopover(term);
    });
    document.addEventListener('focusin', function (event) {
      var term = event.target.closest && event.target.closest('.term');
      if (term) showPopover(term);
    });
    document.addEventListener('click', function (event) {
      var term = event.target.closest && event.target.closest('.term');
      if (term) { showPopover(term); event.stopPropagation(); }
      else if (!event.target.closest('.i18n-popover')) closePopover();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closePopover();
    });
    document.addEventListener('pointerout', function (event) {
      var term = event.target.closest && event.target.closest('.term');
      if (!term || event.pointerType === 'touch') return;
      var to = event.relatedTarget;
      if (to && to.closest && to.closest('.term, .i18n-popover')) return;
      if (document.activeElement === term) return;
      closePopover();
    });
    document.addEventListener('focusout', function (event) {
      if (!event.relatedTarget || !event.relatedTarget.closest || !event.relatedTarget.closest('.term, .i18n-popover')) closePopover();
    });
    window.addEventListener('resize', closePopover);
  }

  function appendPair(parent, tag, zhText, enText, className) {
    var zh = document.createElement(tag);
    zh.setAttribute('lang', 'zh-Hant');
    zh.textContent = zhText;
    var en = document.createElement(tag);
    en.setAttribute('lang', 'en');
    en.textContent = enText;
    if (className) { zh.className = className; en.className = className; }
    parent.appendChild(zh);
    parent.appendChild(en);
  }

  function renderGlossary() {
    if (!glossary.length || document.getElementById('glossary')) return;
    var section = document.createElement('section');
    section.id = 'glossary';
    section.className = 'i18n-glossary';
    var heading = document.createElement('h2');
    appendPair(heading, 'span', '專有名詞', 'Glossary of Terms');
    section.appendChild(heading);
    var intro = document.createElement('p');
    intro.className = 'i18n-glossary-intro';
    appendPair(intro, 'span', '中文與英文術語並列顯示；正文中的點線底線術語可用滑鼠停留或點選查看相同說明。', 'Chinese and English terms are shown side by side; dotted-underlined terms in the body reveal the same explanation on hover or tap.');
    section.appendChild(intro);
    var filter = document.createElement('input');
    filter.type = 'search';
    filter.className = 'i18n-glossary-filter';
    filter.setAttribute('aria-label', 'Glossary filter');
    filter.setAttribute('placeholder', '搜尋專有名詞');
    filter.setAttribute('data-en-placeholder', 'Search glossary terms');
    section.appendChild(filter);

    var wrap = document.createElement('div');
    wrap.className = 'i18n-glossary-table-wrap';
    var table = document.createElement('table');
    var thead = document.createElement('thead');
    var headerRow = document.createElement('tr');
    [['中文術語', 'Chinese term'], ['英文術語', 'English term'], ['說明', 'Explanation']].forEach(function (labels) {
      var th = document.createElement('th');
      appendPair(th, 'span', labels[0], labels[1]);
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    var tbody = document.createElement('tbody');
    glossary.slice().sort(function (a, b) { return String(a.en).localeCompare(String(b.en)); }).forEach(function (entry) {
      var row = document.createElement('tr');
      row.setAttribute('data-glossary-row', '');
      var zhCell = document.createElement('td');
      zhCell.textContent = entry.zh;
      var enCell = document.createElement('td');
      enCell.textContent = entry.en;
      var defCell = document.createElement('td');
      appendPair(defCell, 'span', entry.defZh, entry.defEn);
      row.appendChild(zhCell);
      row.appendChild(enCell);
      row.appendChild(defCell);
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    section.appendChild(wrap);

    filter.addEventListener('input', function () {
      var query = filter.value.trim().toLocaleLowerCase();
      tbody.querySelectorAll('tr').forEach(function (row) {
        var terms = (row.children[0].textContent + ' ' + row.children[1].textContent).toLocaleLowerCase();
        row.hidden = Boolean(query && !terms.includes(query));
      });
    });
    var slot = document.getElementById('glossary-slot');
    if (slot) slot.appendChild(section);
    else {
      var footer = document.querySelector('footer');
      if (footer && footer.parentNode) footer.parentNode.insertBefore(section, footer);
      else if (document.body) document.body.appendChild(section);
    }
  }

  function initialLanguage() {
    var query = new URLSearchParams(window.location.search).get('lang');
    if (query === 'en' || query === 'zh' || query === 'zh-Hant') return languageFrom(query);
    try {
      var saved = window.localStorage.getItem('raman_lang');
      if (saved === 'en' || saved === 'zh') return saved;
    } catch (error) { /* storage is optional */ }
    var browserLanguage = typeof navigator.language === 'string' ? navigator.language.toLowerCase() : '';
    if (browserLanguage.indexOf('zh') === 0) return 'zh';
    if (browserLanguage) return 'en';
    return 'zh';
  }

  document.addEventListener('DOMContentLoaded', function () {
    createToggle();
    renderGlossary();
    setLanguage(initialLanguage(), false, true);
    annotateGlossaryTerms();
    wirePopover();
  });
}());
