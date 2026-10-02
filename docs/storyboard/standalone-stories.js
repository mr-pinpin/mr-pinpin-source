(() => {
  const languages = ['en', 'es', 'ru'];
  const prefix = 'images/standalone/timber-tractor/';
  const sceneIds = [
    'scene-01', 'scene-02', 'scene-03', 'scene-04', 'scene-05', 'scene-06', 'scene-07',
    'scene-08', 'scene-09', 'scene-10', 'scene-11', 'scene-12', 'scene-13', 'scene-14',
    'scene-19', 'scene-21', 'scene-22', 'scene-20', 'scene-23', 'scene-24',
    'scene-15', 'scene-16', 'scene-17', 'scene-18'
  ];
  const localized = value => languages.every(lang => typeof value?.[lang] === 'string' && value[lang].trim());

  const elderParts = ['papa-home', 'family-morning', 'forest-path', 'elder-house', 'beneath-roots'];
  const elderCounts = [27, 20, 22, 35, 69];
  const elderIds = ['one-day-in-the-forest', ...elderParts.map(part => 'elder-' + part)];
  const elderPrefix = 'images/published/elder-cycle/';
  // Explicit approved arrival sequence and revisions; unrelated assets stay rejected.
  const papaFamilyIds = numbers => numbers.map(n => 'elder-r6-family-' + String(n).padStart(3, '0'));
  const papaArrivalIds = numbers => numbers.map(n => 'arrival-' + String(n).padStart(2, '0'));
  const papaSequence = ['elder-papa-home-title', ...papaFamilyIds([1, 2]),
    ...papaArrivalIds([1, 2, 3, 4]), ...papaFamilyIds([3, 4]),
    ...papaArrivalIds([5, 6, 7, 8, 9, 10, 11, 12]), ...papaFamilyIds([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])];
  const papaArrivalImages = Object.fromEntries([
    ['elder-r6-family-002', 'family-002-window-v2'],
    ...['arrival-01-v4', 'arrival-02-v4', 'arrival-03-v5', 'arrival-04',
      'arrival-05', 'arrival-06', 'arrival-07', 'arrival-08', 'arrival-09-v2',
      'arrival-10-v3', 'arrival-11-v2', 'arrival-12-v2'].map(name => [name.slice(0, 10), name])
  ].map(([id, name]) => [id, elderPrefix + 'papa-arrival-20260922-' + name + '.webp']));
  const elderPath = value => typeof value === 'string' &&
    /^images\/published\/elder-cycle\/[a-z0-9-]+\.webp$/.test(value);

  function completeElder(story) {
    if (!elderIds.includes(story?.id) || story.editionVersion !== (['one-day-in-the-forest', 'elder-papa-home'].includes(story.id) ? 2 : 1) ||
        story.sourceChapter !== 'chapter-02' || !localized(story.title) || !localized(story.cover)) return false;
    const parts = story.id === elderIds[0] ? elderParts : [story.id.slice(6)];
    const expected = parts.reduce((sum, part) => sum + elderCounts[elderParts.indexOf(part)] + 1, 0);
    if (!Array.isArray(story.scenes) || story.scenes.length !== expected ||
        !Array.isArray(story.spreads) || story.spreads.length !== expected ||
        !Array.isArray(story.chapterNav) || story.chapterNav.length !== parts.length ||
        !languages.every(lang => story.cover[lang] === elderPrefix + parts[0] + '-title-' + lang + '.webp') ||
        story.miniature !== elderPrefix + parts[0] + '-miniature.webp') return false;
    let offset = 0;
    const seen = new Set();
    for (const [partIndex, part] of parts.entries()) {
      const count = elderCounts[elderParts.indexOf(part)];
      const nav = story.chapterNav[partIndex];
      if (nav?.id !== part || nav.number !== elderParts.indexOf(part) + 1 || nav.storyId !== 'elder-' + part || nav.startScene !== offset || !localized(nav.title)) return false;
      for (let local = 0; local <= count; local++) {
        const index = offset + local, scene = story.scenes[index], spread = story.spreads[index];
        if (!scene || seen.has(scene.id) || scene.part !== part || !elderPath(scene.image) || !localized(scene.alt) ||
            !languages.every(lang => Array.isArray(scene.paragraphs?.[lang]) &&
              scene.paragraphs[lang].every(p => typeof p === 'string' && p.trim())) ||
            !spread || !Array.isArray(spread.scenes) || spread.scenes.length !== 1 || spread.scenes[0] !== index) return false;
        if (part === 'papa-home' && scene.id !== papaSequence[local]) return false;
        seen.add(scene.id);
        if (local === 0) {
          if (scene.id !== 'elder-' + part + '-title' || scene.role !== 'title' ||
              scene.width !== 1024 || scene.height !== 1536 || spread.style !== 'cover' || spread.paper !== 'portrait' ||
              !localized(scene.images) || !languages.every(lang =>
                scene.images[lang] === elderPrefix + part + '-title-' + lang + '.webp' && scene.paragraphs[lang].length === 0) ||
              scene.image !== scene.images.en) return false;
        } else if (!(part === 'papa-home' && papaArrivalImages[scene.id]
            ? scene.image === papaArrivalImages[scene.id]
            : /^elder-r6-(family|forest|mentor)-[0-9]{3}$/.test(scene.id) && scene.image === elderPrefix + scene.id + '.webp') ||
            scene.role !== undefined || scene.images !== undefined ||
            scene.width !== 1536 || scene.height !== 1024 || spread.style !== 'elder' || spread.paper !== 'landscape' ||
            !languages.every(lang => scene.paragraphs[lang].length > 0)) return false;
      }
      offset += count + 1;
    }
    return true;
  }

  function chapterNumber(value) {
    if (value === undefined || value === null) return 1;
    return value === 1 || value === '1' ? 1 : value === 2 || value === '2' ? 2 : null;
  }

  function complete(story, chapter = story?.number ?? 1) {
    if (story?.id === 'bath-magic') return completeBath(story);
    if (elderIds.includes(story?.id)) return completeElder(story);
    if (story?.id === 'home-sweet-home') return completeBedtime(story);
    const number = chapterNumber(chapter);
    if (!number || story?.id !== 'timber-tractor' ||
        (number === 1 ? story.number !== undefined && story.number !== 1 : story.number !== 2) ||
        !localized(story.title) || !localized(story.cover)) return false;
    if (number === 2) return completeHome(story);
    if (!Array.isArray(story.scenes) || story.scenes.length !== sceneIds.length ||
        !Array.isArray(story.spreads) || story.spreads.length !== 18) return false;
    if (!languages.every(lang => story.cover[lang] === prefix + (lang === 'en' ? 'title-v1.png' : `title-${lang}-v1.png`))) return false;
    if (!story.scenes.every((scene, index) => scene?.id === sceneIds[index] && typeof scene.image === 'string' &&
        (index === 0 ? scene.image === prefix + 'title-v1.png' :
          new RegExp(`^${prefix}${sceneIds[index]}(?:-v[1-9][0-9]*)?\\.png$`).exec(scene.image)?.[0] === scene.image) &&
        scene.width === (index === 0 ? 1024 : 1536) && scene.height === (index === 0 ? 1536 : 1024) &&
        localized(scene.alt) && languages.every(lang => Array.isArray(scene.paragraphs?.[lang]) &&
          scene.paragraphs[lang].every(p => typeof p === 'string' && p.trim()) &&
          (index === 0 ? scene.paragraphs[lang].length === 0 : scene.paragraphs[lang].length > 0)))) return false;
    if (!story.spreads.every(spread => spread && typeof spread.style === 'string' &&
        /^[a-z][a-z-]*$/.exec(spread.style)?.[0] === spread.style &&
        ['portrait', 'landscape'].includes(spread.paper) && Array.isArray(spread.scenes) && spread.scenes.length > 0 &&
        spread.scenes.every(Number.isInteger))) return false;
    if (story.spreads.flatMap(spread => spread.scenes).join(',') !== sceneIds.map((_, i) => i).join(',')) return false;
    if (story.spreads[0].style !== 'cover' || story.spreads[0].paper !== 'portrait' || story.spreads[0].scenes.length !== 1) return false;
    if (!['scene-14', 'scene-19', 'scene-21', 'scene-22', 'scene-20', 'scene-23', 'scene-24', 'scene-15'].every(id => story.spreads.some(spread =>
        spread.paper === 'landscape' && spread.scenes.length === 1 && spread.scenes[0] === sceneIds.indexOf(id)))) return false;
    // Keep the willow-twig answer behind a page turn after both setup shots.
    return story.spreads.at(-1).scenes.length === 1 && story.spreads.at(-1).scenes[0] === sceneIds.indexOf('scene-18');
  }

  function completeHome(story) {
    const homePrefix = prefix + 'chapter-02/';
    const groups = [[0,1],[2,3],[4],[5],[6],[7],[8],[9]];
    if (!languages.every(lang => story.cover[lang] === homePrefix + 'scene-05.png') ||
        !Array.isArray(story.scenes) || story.scenes.length !== 10 ||
        !Array.isArray(story.spreads) || story.spreads.length !== groups.length) return false;
    if (!story.scenes.every((scene, index) => {
      const id = 'scene-' + String(index + 1).padStart(2, '0');
      return scene?.id === id && typeof scene.image === 'string' &&
        new RegExp(`^${homePrefix}${id}(?:-v[1-9][0-9]*)?\\.png$`).exec(scene.image)?.[0] === scene.image &&
        scene.width === 1536 && scene.height === 1024 && localized(scene.alt) &&
        languages.every(lang => Array.isArray(scene.paragraphs?.[lang]) && scene.paragraphs[lang].length > 0 &&
          scene.paragraphs[lang].every(p => typeof p === 'string' && p.trim()));
    })) return false;
    return story.spreads.every((spread, index) => spread && typeof spread.style === 'string' &&
      /^[a-z][a-z-]*$/.exec(spread.style)?.[0] === spread.style && spread.style !== 'cover' &&
      spread.paper === (index < 2 ? 'portrait' : 'landscape') && Array.isArray(spread.scenes) &&
      spread.scenes.every(Number.isInteger) && spread.scenes.join(',') === groups[index].join(','));
  }

  // Source parts retain their production IDs; the reader receives one continuous edition.
  function compose(opening, home) {
    if (!complete(opening, 1) || !complete(home, 2)) return null;
    const offset = opening.scenes.length;
    const {number, ...story} = opening;
    return {...story, continuationTitles:home.title,
      scenes:[...opening.scenes, ...home.scenes.map(scene => ({...scene, id:'home-' + scene.id}))],
      spreads:[...opening.spreads, ...home.spreads.map(spread =>
        ({...spread, scenes:spread.scenes.map(index => index + offset)}))]};
  }

  function completeBedtime(story) {
    const homePrefix = 'images/standalone/home-sweet-home/';
    if (story?.id !== 'home-sweet-home' || story.number !== 3 || !localized(story.title) || !localized(story.cover) ||
        !languages.every(lang => story.cover[lang] === homePrefix + `title-${lang}-v1.png`) ||
        !Array.isArray(story.scenes) || story.scenes.length !== 21 ||
        !Array.isArray(story.spreads) || story.spreads.length !== 21) return false;
    return story.scenes.every((scene, index) => {
      const id = index === 0 ? 'bedtime-cover' : 'bedtime-' + String(index).padStart(2, '0');
      return scene?.id === id && typeof scene.image === 'string' &&
        (index === 0 ? scene.image === story.cover.en :
          [1, 2].some(version => scene.image === homePrefix + id + '-v' + version + '.png')) &&
        scene.width === (index === 0 ? 1024 : 1536) && scene.height === (index === 0 ? 1536 : 1024) &&
        localized(scene.alt) && languages.every(lang => Array.isArray(scene.paragraphs?.[lang]) &&
          (index === 0 ? scene.paragraphs[lang].length === 0 : scene.paragraphs[lang].length > 0) &&
          scene.paragraphs[lang].every(p => typeof p === 'string' && p.trim()));
    }) && story.spreads.every((spread, index) => spread?.style === (index === 0 ? 'cover' : 'bedtime') &&
      spread.paper === (index === 0 ? 'portrait' : 'landscape') &&
      Array.isArray(spread.scenes) && spread.scenes.length === 1 && spread.scenes[0] === index);
  }

  function completeBath(story) {
    const prefix = 'images/published/bath-magic/';
    const count = story?.editionVersion === 1 ? 139 : story?.editionVersion === 2 ? 172 : null;
    if (story?.id !== 'bath-magic' || !count || !localized(story.title) ||
        !localized(story.cover) || !languages.every(lang => [prefix + 'title-' + lang + '.webp', prefix + 'title-' + lang + '-v2.webp'].includes(story.cover[lang])) ||
        story.miniature !== prefix + 'miniature.webp' || story.scenes?.length !== count || story.spreads?.length !== count) return false;
    const seen = new Set();
    return story.scenes.every((scene, index) => {
      if (!scene || seen.has(scene.id) || !localized(scene.alt)) return false;
      seen.add(scene.id);
      if (!languages.every(lang => Array.isArray(scene.paragraphs?.[lang]) &&
          (index === 0 ? scene.paragraphs[lang].length === 0 : scene.paragraphs[lang].length > 0) &&
          scene.paragraphs[lang].every(p => typeof p === 'string' && p.trim()))) return false;
      const spread = story.spreads[index];
      if (!spread || spread.scenes?.length !== 1 || spread.scenes[0] !== index ||
          spread.style !== (index === 0 ? 'cover' : 'elder') || spread.paper !== (index === 0 ? 'portrait' : 'landscape')) return false;
      return index === 0
        ? scene.id === 'bath-magic-title' && scene.role === 'title' && localized(scene.images) &&
          languages.every(lang => scene.images[lang] === story.cover[lang]) && scene.image === story.cover.en &&
          scene.width === 1024 && scene.height === 1536
        : /^scene-[0-9]{2,3}(?:[a-z][0-9]?)?$/.test(scene.id) &&
          (scene.image === prefix + scene.id + '.webp' ||
            (story.editionVersion === 2 && scene.image === prefix + 'r17/' + scene.id + '.webp')) &&
          scene.width === 1536 && scene.height === 1024;
    });
  }

  async function load(id, legacyChapter) {
    if (id === 'bath-magic') {
      try {
        const response = await fetch('stories/bath-magic.json', {cache:'no-cache'});
        if (!response.ok) return null;
        const story = await response.json();
        return completeBath(story) ? story : null;
      } catch { return null; }
    }
    if (elderIds.includes(id)) {
      try {
        const response = await fetch(`stories/${id}.json`, {cache:'no-cache'});
        if (!response.ok) return null;
        const story = await response.json();
        return story.id === id && completeElder(story) ? story : null;
      } catch { return null; }
    }
    if (id === 'home-sweet-home') {
      try {
        const response = await fetch('stories/home-sweet-home.json', {cache:'no-cache'});
        if (!response.ok) return null;
        const story = await response.json();
        if (story.id !== id || !complete(story)) return null;
        // A draft manifest alone must not unlock Home while its artwork is still arriving.
        const assets = [...new Set([...Object.values(story.cover), ...story.scenes.map(scene => scene.image)])];
        const ready = await Promise.all(assets.map(async src => (await fetch(src, {method:'HEAD'})).ok));
        return ready.every(Boolean) ? story : null;
      } catch { return null; }
    }
    if (id !== 'timber-tractor' || !chapterNumber(legacyChapter)) return null;
    try {
      const parts = await Promise.all(['', '-chapter-02'].map(async suffix => {
        const response = await fetch(`stories/${id}${suffix}.json`, {cache:'no-cache'});
        if (!response.ok) throw new Error('Story part is not available');
        return response.json();
      }));
      return compose(...parts);
    } catch { return null; }
  }

  function edition(story, lang) {
    return {
      title:story.title[lang], scenes:story.scenes.map(scene => ({paragraphs:scene.paragraphs[lang]})),
      images:story.scenes.map((scene, index) => ({...scene, scene:index + 1,
        src:scene.images?.[lang] || (index === 0 && story.spreads[0]?.style === 'cover' ? story.cover[lang] : scene.image)}))
    };
  }
  window.standaloneStories = {complete, completeElder, compose, load, edition,
    available:async () => (await Promise.all(['timber-tractor', 'home-sweet-home', 'one-day-in-the-forest', 'bath-magic'].map(id => load(id)))).filter(Boolean)};
})();
