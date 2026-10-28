// Mouse hover changes the lens, never the character's destination. Retain client
// coordinates so pan/zoom recomputes the world point under a stationary cursor.
export function createPointerFocus() {
  let client = null;
  return {
    update(event) {
      if (event?.pointerType !== 'mouse' || !Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)) return false;
      client = [event.clientX, event.clientY];
      return true;
    },
    clear() { client = null; },
    world(camera, canvas) {
      if (!client) return null;
      const r = canvas.getBoundingClientRect();
      const point = [client[0] - r.left, client[1] - r.top];
      if (point[0] < 0 || point[1] < 0 || point[0] > r.width || point[1] > r.height) return null;
      return camera.screenToWorld(point);
    }
  };
}
