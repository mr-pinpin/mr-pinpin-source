(() => {
  'use strict';
  const languages = ['en', 'es', 'ru'];
  const entries = {
    lake:{chapter:'1', coverId:'chapter-01', route:'chapter=1'},
    elder:{story:'one-day-in-the-forest', coverId:'one-day-in-the-forest', route:'story=one-day-in-the-forest'},
    bridge:{story:'timber-tractor', coverId:'timber-tractor', route:'story=timber-tractor'},
    home:{story:'home-sweet-home', coverId:'home-sweet-home', route:'story=home-sweet-home', relatedStories:['bath-magic']}
  };
  const language = lang => languages.includes(lang) ? lang : 'en';
  function href(id, lang) {
    if (!Object.hasOwn(entries, id)) return null;
    const query = new URLSearchParams(entries[id].route);
    query.set('lang', language(lang));
    if (new URLSearchParams(location.search).get('coverPreview') === '1') query.set('coverPreview', '1');
    return 'index.html?' + query;
  }
  async function json(path) {
    const response = await fetch(path, {cache:'no-cache'});
    if (!response.ok) throw new Error(path);
    return response.json();
  }
  let main;
  function mainBook() {
    if (!main) main = Promise.all(['illustrations.json', 'translations.json', 'book.json'].map(json))
      .catch(error => { main = null; throw error; });
    return main;
  }
  const resolved = new Map();
  function resolve(id) {
    if (!Object.hasOwn(entries, id)) return Promise.resolve(null);
    if (!resolved.has(id)) resolved.set(id, loadStory(id).then(story => {
      if (!story) resolved.delete(id);
      return story;
    }, error => { resolved.delete(id); throw error; }));
    return resolved.get(id);
  }
  async function loadStory(id) {
    if (!Object.hasOwn(entries, id)) return null;
    const entry = entries[id];
    if (entry.story) {
      const story = await window.standaloneStories.load(entry.story);
      return story ? {title:story.title, covers:story.cover,
        first:{src:story.scenes[0].image, alt:story.scenes[0].alt}} : null;
    }
    const [art, translations, book] = await mainBook();
    const published = await window.chapterEditions.available(art, translations);
    if (!published.has(entry.chapter)) return null;
    const chapter = window.chapterEditions.editions[entry.chapter].id;
    const first = art.chapters[chapter]?.[0];
    if (!first) return null;
    return {first, title:Object.fromEntries(languages.map(lang =>
      [lang, translations[chapter]?.[lang]?.title || book.chapters.find(item => item.id === chapter)?.title]))};
  }
  async function available() {
    const ready = await Promise.all(Object.keys(entries).map(async id => {
      try { return await resolve(id) ? id : null; } catch { return null; }
    }));
    return new Set(ready.filter(Boolean));
  }
  async function preview(id, lang) {
    lang = language(lang);
    try {
      const story = await resolve(id);
      if (!story) return null;
      const title = story.title[lang];
      const covers = window.titleCovers;
      let selected;
      try {
        await covers?.load();
        selected = covers?.resolve(entries[id].coverId, lang);
      } catch { /* An optional cover registry cannot disable an existing edition. */ }
      const fallback = story.covers?.[lang] || story.first.src;
      for (const src of new Set([selected?.src, fallback, story.first.src].filter(Boolean))) {
        try {
          const image = new Image(); image.src = src; await image.decode();
          return {src, alt:src === selected?.src ? selected.alt[lang] : story.first.alt[lang], title, href:href(id, lang)};
        } catch { /* Missing or incomplete covers retain the first published illustration. */ }
      }
    } catch { /* Unreadable editions do not produce a preview link. */ }
    return null;
  }
  async function related(id, lang) {
    lang = language(lang);
    return (await Promise.all((entries[id]?.relatedStories || []).map(async storyId => {
      try {
        const story = await window.standaloneStories.load(storyId);
        if (!story) return null;
        const query = new URLSearchParams({story:storyId,lang});
        return {title:story.title[lang], src:story.miniature || story.cover[lang], href:'index.html?' + query};
      } catch { return null; }
    }))).filter(Boolean);
  }
  const bitmapLoads = new WeakMap();
  function loadMiniature(image, selected) {
    if (image.getAttribute?.('src') === selected.src && image.complete && image.naturalWidth) return Promise.resolve();
    const loading = bitmapLoads.get(image);
    if (loading?.src === selected.src) return loading.pending;
    const pending = (async () => {
      if (selected.srcset) {
        image.sizes ||= '160px';
        image.srcset = selected.srcset;
        // Also covers a later high-resolution candidate failing after a zoom.
        image.onerror = () => {
          image.onerror = null;
          image.removeAttribute('srcset');
        };
      }
      image.src = selected.src;
      try { await image.decode(); }
      catch {
        if (!selected.srcset) throw new Error('Missing miniature');
        image.removeAttribute('srcset');
        await image.decode();
      }
    })().finally(() => bitmapLoads.delete(image));
    bitmapLoads.set(image, {src:selected.src, pending});
    return pending;
  }
  async function miniature(id, lang, {image = new Image()} = {}) {
    lang = language(lang);
    try {
      const story = await resolve(id);
      if (!story) return null;
      const covers = window.titleCovers;
      await covers?.load();
      // Atlas preview is authorized to show proposed miniatures without approving them.
      const selected = covers?.resolveMiniature?.(entries[id].coverId, lang, {allowProposed:true});
      if (selected) {
        // Decode on the persistent banner node. Language changes reuse its bitmap.
        await loadMiniature(image, selected);
        return {src:selected.src, alt:selected.alt[lang], title:story.title[lang], href:href(id, lang)};
      }
    } catch { /* Missing miniatures cannot trigger full-title downloads on the map. */ }
    return null;
  }
  window.AtlasStories = {entries, available, href, preview, miniature, related};
})();
