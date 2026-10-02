(() => {
  // PDF routes are handled before reader initialization or story asset fetches.
  if (window.pinpinPDFRoute?.active) return;
  const $ = id => document.getElementById(id);
  let artwork, translations, book, published, edition, story, language = 'ru', printing = false;
  let loadedKey, navigation = 0;
  const navigationLabels = {
    en:{map:'Map', back:'Back to map', language:'Language', navigation:'Book navigation', loading:'Loading the book…'},
    es:{map:'Mapa', back:'Volver al mapa', language:'Idioma', navigation:'Navegación del libro', loading:'Cargando el libro…'},
    ru:{map:'Карта', back:'Вернуться к карте', language:'Язык', navigation:'Навигация по книге', loading:'Загрузка книги…'}
  };
  const languageNames = {en:'English', es:'Español', ru:'Русский'};

  function syncNavigation() {
    const requested = new URL(location.href).searchParams.get('lang');
    language = Object.hasOwn(navigationLabels, requested) ? requested : 'ru';
    const labels = navigationLabels[language];
    document.documentElement.lang = language;
    const destination = new URL(location.href).searchParams.get('returnTo');
    const map = new URL(['atlas-webgpu.html', 'atlas.html'].includes(destination) ? destination : 'atlas-webgpu.html', location.href);
    map.searchParams.set('lang', language);
    const returnPlace = new URL(location.href).searchParams.get('returnPlace');
    if (['home', 'lake', 'elder', 'bridge'].includes(returnPlace)) map.searchParams.set('returnPlace', returnPlace);
    ['reader-map', 'reader-map-end'].forEach(id => {
      const link = $(id);
      const label = id === 'reader-map' ? labels.map : labels.back;
      link.href = map.href;
      link.querySelector('span').textContent = label;
      link.title = label;
      link.setAttribute('aria-label', label);
    });
    $('reader-controls').setAttribute('aria-label', labels.navigation);
    document.querySelector('.reader-footer').setAttribute('aria-label', labels.navigation);
    $('reader-languages').setAttribute('aria-label', labels.language);
    $('language-toggle').dataset.lang = language;
    $('language-toggle').title = labels.language + ': ' + languageNames[language];
    $('language-toggle').setAttribute('aria-label', $('language-toggle').title);
    document.querySelectorAll('#reader-languages [data-lang]').forEach(button =>
      button.setAttribute('aria-pressed', String(button.dataset.lang === language)));
  }

  function route(lang) {
    const url = new URL(location.href);
    if (story) {
      url.searchParams.set('story', story.id);
      url.searchParams.delete('chapter');
    } else {
      url.searchParams.delete('story');
      url.searchParams.set('chapter', String(edition.number));
    }
    url.searchParams.set('lang', lang);
    url.hash = '';
    return url;
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function render(readingPosition = 0) {
    closeControls();
    edition = story || window.chapterEditions.resolve(new URL(location.href).searchParams.get('chapter'), published);
    const { id:chapterId, number:chapterNumber, spreads } = edition;
    syncNavigation();
    history.replaceState(null, '', route(language));
    const ui = window.readerLabels[language];
    const preview = new URL(location.href).searchParams.get('view') === 'print';
    document.documentElement.classList.toggle('print-preview', preview);
    $('paper-styles').media = preview ? 'all' : 'print';
    $('preview').setAttribute('aria-pressed', String(preview));
    $('preview').title = preview ? ui.reading : ui.preview;
    $('preview').setAttribute('aria-label', ui.preview);
    $('preview').disabled = false;
    const translated = story ? window.standaloneStories.edition(story, language) : translations[chapterId]?.[language];
    const scenes = translated?.scenes || artwork.scenes[chapterId];
    const images = story ? translated.images : artwork.chapters[chapterId];
    const titleCover = window.titleCovers.resolve(chapterId, language);
    document.documentElement.lang = language;
    document.title = story ? translated.title : ui.book + ' - ' + ui.chapter + ' ' + chapterNumber;
    $('print').title = ui.print;
    $('print').setAttribute('aria-label', ui.print);
    $('print').disabled = false;
    $('export-status').textContent = '';
    const article = element('article');
    if (story) {
      article.dataset.story = story.id;
      article.setAttribute('aria-label', translated.title);
    } else article.dataset.chapter = chapterId;
    article.lang = language;
    const header = element('header', 'chapter-heading');
    if (!story) header.append(element('p', 'eyebrow', ui.chapter + ' ' + chapterNumber));
    header.append(element('h1', '', translated?.title || (chapterNumber === 1 ? ui.title :
      book.chapters.find(chapter => chapter.id === chapterId).title.replace(/^Глава\s*\d*\s*:\s*/, ''))));
    if (titleCover?.placement === 'prepend') {
      const slot = element('div', 'page-slot title-cover-slot');
      slot.dataset.paper = 'portrait';
      const frame = element('div', 'page-frame');
      const sheet = element('section', 'spread spread-cover paper-portrait');
      sheet.id = 'title-cover';
      sheet.setAttribute('aria-label', titleCover.title[language]);
      const figure = element('figure', 'scene-art');
      const image = element('img');
      image.loading = 'eager'; image.decoding = 'async'; image.fetchPriority = 'high';
      window.titleCovers.apply(image, titleCover, language, null, () => slot.remove());
      figure.append(image); sheet.append(figure); frame.append(sheet); slot.append(frame); article.append(slot);
    }
    if (Array.isArray(story?.chapterNav) && story.chapterNav.length) {
      const navigation = element('nav', 'story-chapter-nav');
      navigation.setAttribute('aria-label', ui.contents);
      navigation.append(element('h1', '', translated.title));
      const list = element('div', 'story-chapter-links');
      story.chapterNav.forEach((part, index) => {
        const link = element('a');
        const destination = new URL(location.href);
        destination.searchParams.set('story', part.storyId);
        destination.searchParams.set('lang', language);
        destination.searchParams.delete('chapter');
        destination.hash = '';
        link.href = destination;
        if (part.storyId === story.id) link.setAttribute('aria-current', 'page');
        const image = element('img');
        image.src = `images/published/elder-cycle/${part.id}-miniature.webp`;
        image.alt = ''; image.width = 1024; image.height = 1536;
        link.append(image, element('span', '', `${part.number || index + 1}. ${part.title[language]}`));
        list.append(link);
      });
      navigation.append(list);
      if (story.id !== 'one-day-in-the-forest') {
        const all = element('a', 'story-read-all', {ru:'Читать все пять глав',en:'Read all five chapters',es:'Leer los cinco capítulos'}[language]);
        const full = new URL(location.href);
        full.searchParams.set('story', 'one-day-in-the-forest');
        full.searchParams.set('lang', language);
        full.searchParams.delete('chapter'); full.hash = '';
        all.href = full;
        navigation.append(all);
      }
      article.append(navigation);
    }
    if (Array.isArray(story?.sectionNav) && story.sectionNav.length) {
      const navigation = element('nav', 'story-section-nav');
      navigation.setAttribute('aria-label', ui.contents);
      for (const section of story.sectionNav) {
        const spreadIndex = spreads.findIndex(spread => spread.scenes.includes(section.startScene));
        if (spreadIndex < 0) continue;
        const link = element('a', '', section.title[language] || section.title.en);
        link.href = '#spread-' + (spreadIndex + 1);
        navigation.append(link);
      }
      article.append(navigation);
    }
    spreads.forEach((spread, spreadIndex) => {
      const sheet = element('section', 'spread spread-' + spread.style + ' paper-' + spread.paper);
      sheet.id = 'spread-' + (spreadIndex + 1);
      spread.scenes.forEach(index => {
        const scene = scenes[index];
        const section = element('section', 'scene');
        section.id = 'scene-' + (index + 1);
        if (story) section.dataset.sceneId = story.scenes[index].id;
        section.setAttribute('aria-label', ui.scene + ' ' + (index + 1));
        const asset = images.find(image => image.scene === index + 1);
        const figure = element('figure', 'scene-art');
        const image = element('img');
        image.src = asset.src;
        image.alt = asset.alt[language] || asset.alt.en;
        image.width = asset.width;
        image.height = asset.height;
        if (index === 0 && titleCover?.placement === 'replace') {
          window.titleCovers.apply(image, titleCover, language, asset);
        }
        image.loading = index === 0 || preview ? 'eager' : 'lazy';
        image.decoding = 'async';
        if (index === 0) image.fetchPriority = 'high';
        figure.append(image);
        section.append(figure);
        if (scene.paragraphs.length) {
          const prose = element('div', 'prose');
          if (index === 0) prose.append(header);
          scene.paragraphs.forEach((paragraph, paragraphIndex) => {
            const p = element('p');
            if (!story && index === 0 && chapterNumber === 2 && paragraphIndex === 0) {
              p.append(element('span', 'opening-lead', paragraph));
            } else if (index === 0 && chapterNumber === 1 && typeof Intl.Segmenter === 'function') {
              const first = new Intl.Segmenter(language, { granularity:'sentence' }).segment(paragraph)[Symbol.iterator]().next().value.segment;
              p.append(element('span', 'opening-lead', first), document.createTextNode(paragraph.slice(first.length)));
            } else p.textContent = paragraph;
            prose.append(p);
          });
          section.append(prose);
        }
        sheet.append(section);
      });
      const folio = element('div', 'folio');
      const ornament = element('span', 'asterism', '* * *');
      ornament.setAttribute('aria-hidden', 'true');
      folio.append(ornament, element('span', 'page-number', String(spreadIndex + 1).padStart(2, '0')));
      sheet.append(folio);
      const slot = element('div', 'page-slot');
      slot.dataset.paper = spread.paper;
      const frame = element('div', 'page-frame');
      frame.append(sheet);
      slot.append(frame);
      article.append(slot);
    });
    $('reader').replaceChildren(article);
    $('reader').setAttribute('aria-busy', 'false');
    requestAnimationFrame(() => {
      if (!article.isConnected) return;
      resizePreview();
      restorePosition(readingPosition);
      updateProgress();
    });
  }

  function readingPosition() {
    const scenes = [...document.querySelectorAll('#reader #title-cover, #reader .scene')];
    const scene = scenes.find(node => node.getBoundingClientRect().bottom > 16) || scenes.at(-1);
    if (!scene) return position();
    const rect = scene.getBoundingClientRect();
    return {id:scene.id, relative:(16 - rect.top) / rect.height, fraction:position()};
  }

  function restorePosition(saved) {
    const scene = typeof saved === 'object' && $(saved.id);
    if (scene) {
      const rect = scene.getBoundingClientRect();
      window.scrollTo(0, scrollY + rect.top + rect.height * saved.relative - 16);
    } else {
      const fraction = typeof saved === 'number' ? saved : saved.fraction;
      window.scrollTo(0, Math.max(0, document.documentElement.scrollHeight - innerHeight) * fraction);
    }
  }

  function position() {
    const range = document.documentElement.scrollHeight - innerHeight;
    return range > 0 ? scrollY / range : 0;
  }
  function closeControls() {
    $('reader-languages').hidden = true;
    $('language-toggle').setAttribute('aria-expanded', 'false');
  }
  $('language-toggle').onclick = () => {
    const open = $('reader-languages').hidden;
    $('reader-languages').hidden = !open;
    $('language-toggle').setAttribute('aria-expanded', String(open));
    if (open) $('reader-languages').querySelector('[aria-pressed="true"]').focus({preventScroll:true});
  };
  addEventListener('keydown', event => {
    if (event.key === 'Escape' && !$('reader-languages').hidden) {
      closeControls();
      $('language-toggle').focus({preventScroll:true});
    }
  });
  addEventListener('click', event => {
    if (!event.target.closest('#reader-controls')) closeControls();
  });
  $('reader-controls').addEventListener('focusout', event => {
    if (!$('reader-controls').contains(event.relatedTarget)) closeControls();
  });
  function updateProgress() {
    $('progress').style.height = Math.min(100, Math.max(0, position() * 100)) + '%';
  }

  function resizePreview() {
    if (!document.documentElement.classList.contains('print-preview')) return;
    document.querySelectorAll('.page-slot').forEach(slot => {
      const paperWidth = (slot.dataset.paper === 'landscape' ? 297 : 210) * 96 / 25.4;
      slot.style.setProperty('--page-scale', slot.clientWidth / paperWidth);
    });
  }

  $('preview').onclick = () => {
    if (!artwork || printing) return;
    const fraction = position();
    const url = route(language);
    if (url.searchParams.get('view') === 'print') url.searchParams.delete('view');
    else url.searchParams.set('view', 'print');
    history.pushState(null, '', url);
    render(fraction);
  };

  // Decode every illustration before opening the print dialog, including lazy images.
  async function preparePrint() {
    const images = [...document.querySelectorAll('.scene-art img')];
    images.forEach(image => { image.loading = 'eager'; });
    await Promise.all(images.map(image => image.decode()));
    await document.fonts.ready;
  }
  window.prepareChapterPrint = preparePrint;

  $('print').onclick = async () => {
    if (printing || !artwork) return;
    printing = true;
    const ui = window.readerLabels[language];
    const controls = [...document.querySelectorAll('.toolbar button')];
    controls.forEach(button => { button.disabled = true; });
    $('export-status').textContent = ui.preparing;
    $('print').setAttribute('aria-busy', 'true');
    try {
      await preparePrint();
      $('export-status').textContent = '';
      window.print();
    } catch {
      $('export-status').textContent = ui.printError;
    } finally {
      controls.forEach(button => { button.disabled = false; });
      $('print').removeAttribute('aria-busy');
      printing = false;
    }
  };
  addEventListener('beforeprint', () =>
    document.querySelectorAll('.scene-art img').forEach(image => { image.loading = 'eager'; }));
  document.querySelectorAll('#reader-languages [data-lang]').forEach(button => {
    button.onclick = () => {
      if (printing) return;
      const saved = readingPosition();
      closeControls();
      $('language-toggle').focus({preventScroll:true});
      if (button.dataset.lang === language) return;
      const url = new URL(location.href);
      url.searchParams.set('lang', button.dataset.lang);
      history.pushState(null, '', url);
      if (artwork) render(saved);
      else openRoute();
    };
  });
  addEventListener('popstate', () => { if (!printing) openRoute(); });
  addEventListener('scroll', updateProgress, { passive: true });
  $('reader').addEventListener('scroll', updateProgress, { passive: true });
  addEventListener('resize', () => { resizePreview(); updateProgress(); });
  new ResizeObserver(() => { resizePreview(); updateProgress(); }).observe($('reader'));

  async function initialize(url) {
    await window.titleCovers.load();
    const requestedStory = url.searchParams.get('story');
    if (requestedStory !== null) {
      const selected = await window.standaloneStories.load(requestedStory, url.searchParams.get('chapter'));
      if (!selected) throw new Error('Story is not available');
      return {story:selected, artwork:{}, published:new Set()};
    }
    const [art, text, original] = await Promise.all(['illustrations.json', 'translations.json', 'book.json'].map(async path => {
      const response = await fetch(path, { cache: 'no-cache' });
      if (!response.ok) throw new Error(path + ': ' + response.status);
      return response.json();
    }));
    return {published:await window.chapterEditions.available(art, text), artwork:art,
      translations:text, book:original, story:null};
  }
  function showError() {
    artwork = null;
    loadedKey = null;
    $('print').disabled = true;
    $('preview').disabled = true;
    $('reader').setAttribute('aria-busy', 'false');
    syncNavigation();
    const lang = language;
    const ui = window.readerLabels[lang];
    document.documentElement.lang = lang;
    const unavailable = {en:'This story is not available yet.', es:'Esta historia todavía no está disponible.', ru:'Эта история пока недоступна.'};
    const message = element('p', 'error', (new URL(location.href).searchParams.has('story') ? unavailable[lang] || unavailable.en : ui.loadError) + ' ');
    const retry = element('a', '', ui.retry);
    retry.href = location.href;
    message.append(retry);
    $('reader').replaceChildren(message);
    window.lucide?.createIcons();
  }

  async function openRoute() {
    const current = ++navigation;
    closeControls();
    syncNavigation();
    window.lucide?.createIcons();
    const url = new URL(location.href);
    const key = JSON.stringify([url.searchParams.get('story'), url.searchParams.get('chapter')]);
    if (loadedKey === key && artwork) { render(); return; }
    $('reader').setAttribute('aria-busy', 'true');
    const loading = element('p', 'loading', navigationLabels[language].loading);
    loading.setAttribute('role', 'status');
    $('reader').replaceChildren(loading);
    $('print').disabled = true;
    $('preview').disabled = true;
    artwork = null;
    try {
      const data = await initialize(url);
      if (current !== navigation) return;
      ({artwork, translations, book, published, story} = data);
      render();
      const rendered = new URL(location.href);
      loadedKey = JSON.stringify([rendered.searchParams.get('story'), rendered.searchParams.get('chapter')]);
      window.lucide?.createIcons();
    } catch {
      if (current === navigation) showError();
    }
  }
  openRoute();
})();
