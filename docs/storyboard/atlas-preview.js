(() => {
  'use strict';
  const backToMap={en:'Back to map',es:'Volver al mapa',ru:'\u041d\u0430\u0437\u0430\u0434 \u043a \u043a\u0430\u0440\u0442\u0435'};
  window.AtlasPreview = {create({canOpen,onOpen,onClose}) {
    const dialog=document.getElementById('story-preview'), image=document.getElementById('preview-image');
    const link=document.getElementById('preview-open'), close=document.getElementById('preview-close');
    const related=document.createElement('section');
    related.className='preview-related'; related.hidden=true; dialog.append(related);
    let ticket=0, current=null, closing=false, pointerStarted=false;
    dialog.addEventListener('pointerdown',() => { pointerStarted=true; });
    dialog.addEventListener('click',event => {
      // A cover's pointerup can open this dialog before its compatibility click.
      if (event.detail>0 && !pointerStarted) { event.preventDefault(); event.stopImmediatePropagation(); }
      pointerStarted=false;
    },true);
    function dismiss(fromHistory=false) {
      const wasOpen=dialog.open;
      ticket++; current=null;
      if (dialog.open) dialog.close();
      // Closing can resume map events before the asynchronous history traversal finishes.
      if (!fromHistory && wasOpen && !closing && history.state?.atlasPreview) { closing=true; history.back(); }
      if (wasOpen) onClose();
    }
    close.onclick=() => dismiss();
    dialog.addEventListener('cancel',event => { event.preventDefault(); dismiss(); });
    dialog.addEventListener('click',event => {
      const rect=dialog.getBoundingClientRect();
      if (event.target===dialog && (event.clientX<rect.left || event.clientX>rect.right || event.clientY<rect.top || event.clientY>rect.bottom)) dismiss();
    });
    addEventListener('popstate',() => {
      closing=false;
      dismiss(true);
      if (history.state?.atlasPreview) history.replaceState(null,'');
    });
    link.addEventListener('click',event => {
      if (!current || !canOpen(current.id)) { event.preventDefault(); dismiss(); return; }
      onOpen(current.id);
      if (!event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && (!link.target || link.target==='_self')) {
        event.preventDefault();
        const href=link.href, replace=Boolean(history.state?.atlasPreview);
        dismiss(true);
        if (replace) location.replace(href); else location.assign(href);
      }
    });
    link.addEventListener('auxclick',event => {
      if (event.button!==1) return;
      if (!current || !canOpen(current.id)) event.preventDefault();
      else onOpen(current.id);
    });
    return {
      get open() { return dialog.open; },
      dismiss,
      async show(id,lang,ui,href) {
        if (closing || !canOpen(id)) return;
        const request=++ticket;
        try {
          const asset=await window.AtlasStories.preview(id,lang);
          if (!asset) throw new Error('Story unavailable');
          if (request!==ticket || !canOpen(id)) return;
          current={id}; image.src=asset.src; image.alt=asset.alt;
          related.replaceChildren(); related.hidden=true; dialog.classList.remove('has-related-stories');
          const destination=new URL(asset.href,location.href);
          if (href) {
            const supplied=new URL(href,location.href);
            for (const key of ['returnTo','returnPlace']) {
              if (supplied.searchParams.has(key)) destination.searchParams.set(key,supplied.searchParams.get(key));
            }
          }
          const relatedAssets=await window.AtlasStories.related?.(id,lang).catch(()=>[]) || [];
          if (request!==ticket || !canOpen(id)) return;
          if (relatedAssets.length) {
            const heading=document.createElement('h3');
            heading.textContent={en:'More stories at home',ru:'Ещё истории дома',es:'Más historias en casa'}[lang] || 'More stories at home';
            related.append(heading);
            for (const item of relatedAssets) {
              const card=document.createElement('a'), thumbnail=document.createElement('img'), label=document.createElement('span');
              const url=new URL(item.href,location.href);
              for (const key of ['returnTo','returnPlace']) if (destination.searchParams.has(key)) url.searchParams.set(key,destination.searchParams.get(key));
              card.href=url.href; card.className='preview-related-story';
              thumbnail.src=item.src; thumbnail.alt=''; thumbnail.width=1024; thumbnail.height=1536;
              label.textContent=item.title; card.append(thumbnail,label);
              card.addEventListener('click',event=>{
                if (!current || !canOpen(current.id)) {event.preventDefault();dismiss();return;}
                onOpen(current.id);
                if (!event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
                  event.preventDefault();const href=card.href, replace=Boolean(history.state?.atlasPreview);dismiss(true);
                  if (replace) location.replace(href);else location.assign(href);
                }
              });
              card.addEventListener('auxclick',event=>{if(event.button===1 && current && canOpen(current.id))onOpen(current.id);});
              related.append(card);
            }
            related.hidden=false; dialog.classList.add('has-related-stories');
          }
          link.href=destination.href; link.setAttribute('aria-label',ui.available+': '+asset.title);
          document.getElementById('preview-title').textContent=asset.title;
          close.textContent=backToMap[lang] || backToMap.en;
          close.title=close.textContent; close.setAttribute('aria-label',close.textContent);
          if (!history.state?.atlasPreview) history.pushState({atlasPreview:id},'');
          pointerStarted=false;
          dialog.showModal(); link.focus();
        } catch {
          if (request===ticket) document.getElementById('map-status').textContent=ui.unavailable;
        }
      }
    };
  },createLanguage() {
    const toggle=document.getElementById('atlas-language-toggle'), popup=document.getElementById('atlas-languages');
    let currentLanguage;
    function close(focus=false) {
      popup.hidden=true; toggle.setAttribute('aria-expanded','false');
      if (focus) toggle.focus({preventScroll:true});
    }
    toggle.addEventListener('click',() => {
      if (!popup.hidden) { close(); return; }
      popup.hidden=false; toggle.setAttribute('aria-expanded','true');
    });
    popup.addEventListener('click',event => { if (event.target.closest('[data-lang]')) close(true); });
    document.addEventListener('pointerdown',event => {
      if (!popup.hidden && !popup.contains(event.target) && !toggle.contains(event.target)) close();
    });
    document.addEventListener('keydown',event => {
      if (event.key==='Escape' && !popup.hidden) { event.preventDefault(); close(true); }
    });
    return {update(lang,label) {
      const selected=popup.querySelector('[data-lang="'+lang+'"]');
      toggle.style.backgroundImage=getComputedStyle(selected).backgroundImage;
      toggle.title=label+': '+selected.title; toggle.setAttribute('aria-label',toggle.title);
      if (lang!==currentLanguage) close();
      currentLanguage=lang;
    }};
  }};
})();
