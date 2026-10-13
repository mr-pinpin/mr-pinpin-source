(() => {
  const id = document.querySelector('meta[name="pinpin-chapter"]')?.content;
  if (!id || !/^[a-z0-9-]+$/.test(id)) return;
  const central = 'https://mr-pinpin.github.io/storyboard/';
  const current = new URL(location.href);
  const requested = current.searchParams.get('story');
  const redirect = (requested !== null && requested !== id) || current.searchParams.has('chapter');
  window.pinpinChapterHosting = {id, central, redirect};
  if (redirect) {
    const target = new URL(central);
    target.search = current.search;
    target.hash = current.hash;
    location.replace(target.href);
  } else if (requested === null) {
    current.searchParams.set('story', id);
    history.replaceState(null, '', current);
  }
})();
