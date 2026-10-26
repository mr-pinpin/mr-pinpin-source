// World-pixel center, CSS-pixel viewport. The renderer owns the fixed canvas.
export function navigationBounds(worldWidth = 1536, worldHeight = 1024) {
  return {minX: -worldWidth / 4, minY: -worldHeight / 4,
    maxX: worldWidth * 1.25, maxY: worldHeight * 1.25,
    width: worldWidth * 1.5, height: worldHeight * 1.5};
}

export function createCamera(canvas, options = {}) {
  const {worldWidth = 1536, worldHeight = 1024} = options;
  const bounds = navigationBounds(worldWidth, worldHeight);
  const view = canvas.ownerDocument.defaultView;
  const reduced = view.matchMedia('(prefers-reduced-motion: reduce)');
  const pointers = new Map(), listeners = [];
  const oldTouchAction = canvas.style.touchAction;
  let state, overview = false, moving = false, dead = false, movementKind;
  let pinch, origin, dragged = false, cancelled = false;
  let velocity = [0, 0], lastMove = 0, frame = 0, wheelTimer = 0;
  const now = () => view.performance.now();
  const cover = () => Math.max(state.width / worldWidth, state.height / worldHeight);
  const contain = () => Math.min(state.width / worldWidth, state.height / worldHeight);
  const snapshot = () => ({...state});
  const screenToWorld = ([x, y]) => [state.x + (x - state.width / 2) / state.scale,
    state.y + (y - state.height / 2) / state.scale];
  const worldToScreen = ([x, y]) => [(x - state.x) * state.scale + state.width / 2,
    (y - state.y) * state.scale + state.height / 2];
  function clamp() {
    state.scale = Math.max(overview ? contain() : cover(), Math.min(cover() * 16, state.scale));
    for (const [axis, dimension, min, max] of [
      ['x', 'width', bounds.minX, bounds.maxX], ['y', 'height', bounds.minY, bounds.maxY]
    ]) {
      const half = state[dimension] / (2 * state.scale);
      state[axis] = half >= (max - min) / 2 ? (min + max) / 2 : Math.max(min + half, Math.min(max - half, state[axis]));
    }
  }
  function change(kind) { clamp(); options.onChange?.(snapshot(), kind); }
  function start(kind = 'pan') {
    if (!moving) {
      moving = true; movementKind = kind; options.onMoveStart?.(snapshot(), kind);
    } else if (movementKind !== kind) {
      movementKind = kind; options.onMoveKindChange?.(snapshot(), kind);
    }
  }
  function end() {
    if (moving) { moving = false; movementKind = undefined; options.onMoveEnd?.(snapshot()); }
  }
  function stop() {
    view.cancelAnimationFrame(frame); view.clearTimeout(wheelTimer);
    frame = wheelTimer = 0;
    end();
  }
  function local(event) {
    const rect = canvas.getBoundingClientRect();
    return [(event.clientX - rect.left) * state.width / Math.max(1, rect.width),
      (event.clientY - rect.top) * state.height / Math.max(1, rect.height)];
  }
  const point = (p, event) => options.onPoint?.(screenToWorld(p), event);
  function anchored(anchor, at, scale) {
    state.scale = Math.max(overview ? contain() : cover(), Math.min(cover() * 16, scale));
    if (state.scale >= cover()) overview = false;
    state.x = anchor[0] - (at[0] - state.width / 2) / state.scale;
    state.y = anchor[1] - (at[1] - state.height / 2) / state.scale;
    change();
  }
  function pair() {
    const [a, b] = [...pointers.values()];
    return {mid: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
      distance: Math.max(1, Math.hypot(a[0] - b[0], a[1] - b[1]))};
  }
  function baseline() {
    velocity = [0, 0]; lastMove = now();
    if (pointers.size >= 2) {
      const p = pair();
      pinch = {...p, anchor: screenToWorld(p.mid), scale: state.scale};
    } else { pinch = undefined; origin = [...pointers.values()][0]; }
  }
  function releaseCapture(id) {
    if (canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
  }
  function reset() {
    const ids = [...pointers.keys()]; pointers.clear();
    ids.forEach(releaseCapture); pinch = undefined; stop();
  }
  function down(event) {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    event.preventDefault();
    if (!pointers.size) { stop(); dragged = cancelled = false; }
    pointers.set(event.pointerId, local(event)); canvas.setPointerCapture(event.pointerId);
    if (pointers.size > 1) cancelled = true;
    baseline();
    if (pointers.size === 1) point(origin, event);
  }
  function move(event) {
    const p = local(event), previous = pointers.get(event.pointerId);
    if (!previous) {
      if (!pointers.size && event.pointerType === 'mouse') point(p, event);
      return;
    }
    event.preventDefault(); pointers.set(event.pointerId, p);
    if (pinch) {
      const next = pair(); start('zoom');
      anchored(pinch.anchor, next.mid, pinch.scale * next.distance / pinch.distance);
      return;
    }
    if (Math.hypot(p[0] - origin[0], p[1] - origin[1]) >= 3) dragged = true;
    const dx = p[0] - previous[0], dy = p[1] - previous[1];
    const time = now(), dt = time - lastMove; lastMove = time;
    velocity = dt > 0 && dt < 50 ? [velocity[0] * .7 + dx / dt * .3,
      velocity[1] * .7 + dy / dt * .3] : [0, 0];
    if (dx || dy) {
      start(); state.x -= dx / state.scale; state.y -= dy / state.scale; change();
    }
    point(p, event);
  }
  function coast() {
    const from = snapshot(), started = now();
    const offset = velocity.map(v => -v * 260 / 2 / state.scale);
    function tick(time) {
      const t = Math.max(0, Math.min(1, (time - started) / 260));
      const eased = 1 - (1 - t) ** 2;
      state.x = from.x + offset[0] * eased; state.y = from.y + offset[1] * eased;
      change();
      if (t < 1) frame = view.requestAnimationFrame(tick);
      else { frame = 0; end(); }
    }
    frame = view.requestAnimationFrame(tick);
  }
  function up(event) {
    if (!pointers.has(event.pointerId)) return;
    const p = local(event), aborted = event.type !== 'pointerup';
    if (aborted) cancelled = true;
    if (origin && Math.hypot(p[0] - origin[0], p[1] - origin[1]) >= 3) dragged = true;
    pointers.delete(event.pointerId); releaseCapture(event.pointerId);
    if (pointers.size) { baseline(); return; }
    pinch = undefined;
    if (!cancelled && !dragged) options.onTap?.(screenToWorld(p), event);
    if (!aborted && dragged && !reduced.matches && now() - lastMove < 80 && Math.hypot(...velocity) > .05) coast();
    else end();
  }
  function wheel(event) {
    event.preventDefault();
    if (pointers.size) return;
    view.cancelAnimationFrame(frame); frame = 0; view.clearTimeout(wheelTimer);
    const p = local(event), delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? state.height : 1);
    start('zoom'); anchored(screenToWorld(p), p, state.scale * 2 ** (-delta * (event.ctrlKey ? .01 : .0022)));
    wheelTimer = view.setTimeout(() => { wheelTimer = 0; end(); }, 120);
  }
  function listen(target, name, handler, settings) {
    target.addEventListener(name, handler, settings);
    listeners.push(() => target.removeEventListener(name, handler, settings));
  }
  function resize() {
    if (dead) return;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(1, rect.width), height = Math.max(1, rect.height);
    const ratio = state ? state.scale / cover() : 2;
    reset();
    if (!state) state = {x: worldWidth * (width < 600 ? .30 : .36), y: worldHeight * .5, scale: 1, width, height};
    else Object.assign(state, {width, height});
    state.scale = overview ? contain() : ratio * cover(); change();
  }
  const camera = {
    get snapshot() { return snapshot(); }, worldToScreen, screenToWorld,
    zoomBy(factor) {
      if (dead || !Number.isFinite(factor) || factor <= 0) return;
      reset(); start('zoom'); anchored([state.x, state.y], [state.width / 2, state.height / 2], state.scale * factor); end();
    },
    fit() {
      if (dead) return;
      reset(); start(); overview = true;
      state.x = worldWidth / 2; state.y = worldHeight / 2; state.scale = contain(); change(); end();
    },
    focus([x, y], scale = state.scale) {
      if (dead || ![x, y, scale].every(Number.isFinite) || scale <= 0) return;
      reset(); start(); overview = false; Object.assign(state, {x, y, scale}); change(); end();
    },
    track([x, y], blend = 1) {
      if (dead || ![x, y, blend].every(Number.isFinite)) return false;
      const previous = {x:state.x,y:state.y};
      Object.assign(state,{x,y}); clamp();
      x=state.x; y=state.y; Object.assign(state,previous);
      const amount = Math.max(0, Math.min(1, blend));
      if (Math.hypot(state.x-x, state.y-y) < .05) {
        if (state.x !== x || state.y !== y) { Object.assign(state,{x,y}); change('track'); }
        return false;
      }
      state.x += (x-state.x)*amount; state.y += (y-state.y)*amount; change('track');
      return Math.hypot(state.x-x,state.y-y) >= .05;
    },
    resize,
    destroy() {
      if (dead) return;
      dead = true; reset(); listeners.forEach(remove => remove());
      canvas.style.touchAction = oldTouchAction;
    }
  };
  canvas.style.touchAction = 'none';
  listen(canvas, 'pointerdown', down);
  listen(canvas, 'pointermove', move);
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) listen(canvas, name, up);
  listen(canvas, 'wheel', wheel, {passive: false});
  listen(reduced, 'change', () => { if (reduced.matches) stop(); });
  listen(view, 'blur', reset);
  resize();
  return camera;
}
