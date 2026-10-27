// The website uses ordinary mouse events; no LG privileged APIs are required.
// A native display already supplies its own local pointer. Require an explicit
// streaming session as well as the opt-out; ordinary TV pages keep their circle.
export function usesNativeCursor(url) {
  const params = new URL(url).searchParams;
  return params.get('renderSession') === '1' && params.get('nativeCursor') === '1';
}

export function createTVControls({canvas, viewport, camera, activate, blocked = () => false, showPointer = true}) {
  const doc = canvas.ownerDocument;
  const cursor = showPointer ? doc.createElement('div') : null;
  if (cursor) {
    cursor.className = 'atlas-tv-cursor'; cursor.setAttribute('aria-hidden', 'true');
    viewport.append(cursor);
  }
  let point = null;
  function paint() {
    const rect = canvas.getBoundingClientRect();
    point ||= [rect.width / 2, rect.height / 2];
    point = [Math.max(0, Math.min(rect.width, point[0])), Math.max(0, Math.min(rect.height, point[1]))];
    if (cursor) {
      cursor.style.left = `${point[0]}px`; cursor.style.top = `${point[1]}px`;
      cursor.hidden = blocked();
    }
  }
  function key(event) {
    if (blocked() || event.target?.closest?.('button,a,input,textarea,select,[role="dialog"]')) return;
    const key = (['ArrowLeft','ArrowUp','ArrowRight','ArrowDown','Enter'].includes(event.key) ? event.key : null) || ({13:'Enter',37:'ArrowLeft',38:'ArrowUp',39:'ArrowRight',40:'ArrowDown'})[event.keyCode];
    if (!['ArrowLeft','ArrowUp','ArrowRight','ArrowDown','Enter'].includes(key)) return;
    event.preventDefault(); event.stopImmediatePropagation();
    canvas.focus({preventScroll:true}); paint();
    if (key === 'Enter') activate(camera.screenToWorld(point));
    else {
      const step = event.repeat ? 24 : 36;
      point[0] += key === 'ArrowLeft' ? -step : key === 'ArrowRight' ? step : 0;
      point[1] += key === 'ArrowUp' ? -step : key === 'ArrowDown' ? step : 0;
      paint();
    }
  }
  function mouse(event) {
    const rect = canvas.getBoundingClientRect();
    point = [event.clientX - rect.left, event.clientY - rect.top]; paint();
  }
  // Mouse click also works on older TV browsers that do not dispatch PointerEvent.
  function click(event) { if (!blocked() && !doc.defaultView.PointerEvent) { mouse(event); activate(camera.screenToWorld(point)); } }
  doc.addEventListener('keydown', key, true);
  canvas.addEventListener('mousemove', mouse);
  canvas.addEventListener('click', click);
  doc.defaultView.addEventListener('resize', paint);
  paint(); canvas.focus({preventScroll:true});
  return {get point() { return [...point]; }, refresh:paint, destroy() {
    doc.removeEventListener('keydown',key,true); canvas.removeEventListener('mousemove',mouse);
    canvas.removeEventListener('click',click); doc.defaultView.removeEventListener('resize',paint); cursor?.remove();
  }};
}
