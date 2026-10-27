// Owned scene adapter. Rendering, video, depth and lens effects remain in Atlas.
export function registerAtlasScene({canvas, camera, target, refresh, host = window}) {
  host.__pinpinRenderScene = Object.freeze({
    id: 'pinpin.atlas',
    controls: Object.freeze({pointer:true, arrows:'cursor'}),
    async create() {
      let last = performance.now(), stopped = false;
      const streams = new Set();
      return {
        canvas,
        capture({fps = 30} = {}) {
          if (stopped) throw new Error('Atlas scene has stopped');
          if (typeof canvas.captureStream !== 'function') throw new Error('Canvas streaming is unavailable');
          const stream = canvas.captureStream(Math.max(1, Math.min(60, Number.isFinite(fps) ? fps : 30)));
          streams.add(stream);
          return stream;
        },
        applyInput(input) {
          if (stopped || !input || typeof input !== 'object') return;
          const now = performance.now(), dt = Math.max(0, Math.min(.1, (now - last) / 1000));
          last = now;
          const state = camera.snapshot;
          const keys = new Set(Array.isArray(input.keys) ? input.keys : []);
          const dx = Number(keys.has('KeyD')) - Number(keys.has('KeyA'));
          const dy = Number(keys.has('KeyS')) - Number(keys.has('KeyW'));
          if (dx || dy) {
            const speed = 240 * dt / state.scale / Math.max(1, Math.hypot(dx, dy));
            camera.focus([state.x + dx * speed, state.y + dy * speed]);
          }
          if (Number.isFinite(input.zoom) && input.zoom) {
            camera.zoomBy(Math.pow(1.12, Math.max(-3, Math.min(3, input.zoom))));
          }
          if (input.activate === true && Array.isArray(input.pointer)
              && input.pointer.length === 2 && input.pointer.every(Number.isFinite)) {
            const point = input.pointer.map(value => Math.max(0, Math.min(1, value)));
            target(camera.screenToWorld([point[0] * state.width, point[1] * state.height]));
          }
          refresh();
        },
        snapshot() { return camera.snapshot; },
        stop() {
          stopped = true;
          for (const stream of streams) for (const track of stream.getTracks()) track.stop();
          streams.clear();
        }
      };
    }
  });
  return host.__pinpinRenderScene;
}
