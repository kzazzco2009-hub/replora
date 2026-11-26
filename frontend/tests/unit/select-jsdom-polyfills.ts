// jsdom gaps in Radix Select's popup/pointer-capture handling (not needed by
// any other component yet, so kept local rather than in tests/setup.ts).
export function installSelectJsdomPolyfills() {
  const originals = {
    scrollIntoView: HTMLElement.prototype.scrollIntoView,
    hasPointerCapture: HTMLElement.prototype.hasPointerCapture,
    releasePointerCapture: HTMLElement.prototype.releasePointerCapture,
    ResizeObserver: globalThis.ResizeObserver,
  };

  HTMLElement.prototype.scrollIntoView = () => {};
  HTMLElement.prototype.hasPointerCapture = () => false;
  HTMLElement.prototype.releasePointerCapture = () => {};
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;

  return function restoreSelectJsdomPolyfills() {
    HTMLElement.prototype.scrollIntoView = originals.scrollIntoView;
    HTMLElement.prototype.hasPointerCapture = originals.hasPointerCapture;
    HTMLElement.prototype.releasePointerCapture =
      originals.releasePointerCapture;
    globalThis.ResizeObserver = originals.ResizeObserver;
  };
}
