(() => {
  'use strict';
  if (window.pinpinChapterHosting?.redirect) return;
  const active = new URL(location.href).searchParams.get('download') === 'pdf';
  window.pinpinPDFRoute = {active};
  if (!active) return;
  document.documentElement.classList.add('pdf-download-route');
  const labels = {
    ru:{preparing:'Готовим вашу книжку',intro:'Скачивание PDF начнётся автоматически.',downloading:'Скачиваем',checking:'Проверяем книжку…',done:'Книжка готова. Скачивание началось.',failed:'Не удалось скачать книжку. Попробуйте ещё раз.',unavailable:'Этой книжки пока нет в библиотеке PDF.',retry:'Скачать PDF',library:'В библиотеку',cancel:'Отменить',cancelled:'Скачивание отменено.'},
    en:{preparing:'Getting your book ready',intro:'Your PDF download will start automatically.',downloading:'Downloading',checking:'Checking your book…',done:'Your book is ready. The download has started.',failed:'The book could not be downloaded. Please try again.',unavailable:'This book is not available in the PDF library yet.',retry:'Download PDF',library:'Back to the library',cancel:'Cancel',cancelled:'Download cancelled.'},
    es:{preparing:'Preparando tu libro',intro:'La descarga del PDF comenzará automáticamente.',downloading:'Descargando',checking:'Comprobando tu libro…',done:'Tu libro está listo. La descarga ha comenzado.',failed:'No se pudo descargar el libro. Inténtalo de nuevo.',unavailable:'Este libro aún no está disponible en la biblioteca PDF.',retry:'Descargar PDF',library:'Volver a la biblioteca',cancel:'Cancelar',cancelled:'Descarga cancelada.'}
  };
  const requested = new URL(location.href).searchParams.get('lang');
  const lang = Object.hasOwn(labels, requested) ? requested : 'ru';
  const ui = labels[lang];
  function node(tag, text) { const value=document.createElement(tag); if(text)value.textContent=text; return value; }
  async function start() {
    document.documentElement.lang=lang; document.title=`Mr. PinPin · PDF`;
    const panel=node('div'); panel.className='pdf-route'; panel.setAttribute('role','main');
    const eyebrow=node('p','Mr. PinPin · PDF'); eyebrow.className='pdf-eyebrow';
    const title=node('h1',ui.preparing), description=node('p',ui.intro), status=node('p',ui.preparing);
    status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.id='pdf-route-status';
    const progress=node('progress');progress.max=100;progress.value=0;progress.setAttribute('aria-label',ui.downloading);
    const controls=node('div');controls.className='pdf-actions';
    const retry=node('button',ui.retry);retry.type='button';retry.hidden=true;retry.id='pdf-route-retry';
    const cancel=node('button',ui.cancel);cancel.type='button';cancel.id='pdf-route-cancel';
    const library=node('a',ui.library);library.href=new URL(`library.html?lang=${lang}`,window.pinpinChapterHosting?.central||location.href).href;
    controls.append(retry,cancel,library);panel.append(eyebrow,title,description,status,progress,controls);
    document.body.replaceChildren(panel);
    let controller=null, running=false;
    cancel.addEventListener('click',()=>controller?.abort());
    async function run() {
      if(running)return;running=true;controller=new AbortController();retry.hidden=true;cancel.hidden=false;progress.hidden=false;progress.value=0;status.textContent=ui.preparing;
      try {
        const response=await fetch('library-pdfs.json',{cache:'no-cache',signal:controller.signal});
        if(!response.ok)throw new Error('Catalog unavailable');
        const catalog=await response.json();
        if(catalog.schemaVersion!==1||!Array.isArray(catalog.chapters))throw new Error('Invalid PDF catalog');
        const params=new URL(location.href).searchParams, story=params.get('story'), chapter=params.get('chapter');
        const matches=catalog.chapters.filter(item=>story!==null ? chapter===null&&item.route?.story===story : chapter!==null&&/^\d+$/.test(chapter)&&String(item.route?.chapter)===String(Number(chapter)));
        const selected=matches.length===1?matches[0]:null, pdf=selected?.pdf?.[lang];
        if(!selected||!window.libraryDownload.validPDF(pdf)){status.textContent=ui.unavailable;description.hidden=true;progress.hidden=true;return;}
        title.textContent=selected.title?.[lang]||selected.title?.en||ui.preparing;document.title=`${title.textContent} · PDF`;
        await window.libraryDownload.download(pdf,{signal:controller.signal,filename:`${selected.id}-${lang}.pdf`,onProgress:({received,total,phase})=>{const percent=Math.min(100,Math.floor(received/total*100));progress.value=percent;status.textContent=phase==='checking'?ui.checking:`${ui.downloading} · ${percent}%`;}});
        status.textContent=ui.done;progress.value=100;retry.hidden=false;
      }catch(error){status.textContent=error.name==='AbortError'?ui.cancelled:ui.failed;progress.hidden=true;retry.hidden=false;}
      finally{running=false;cancel.hidden=true;}
    }
    retry.addEventListener('click',run);
    await run();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
