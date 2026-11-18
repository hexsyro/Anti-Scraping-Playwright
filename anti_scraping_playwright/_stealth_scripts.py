"""Shared, idempotent stealth/anti-fingerprinting init scripts."""

from __future__ import annotations

import weakref
from typing import Iterable, Tuple

STEALTH_SCRIPT = r"""
(() => {
  const define = (obj, prop, value) => {
    try {
      Object.defineProperty(obj, prop, {
        get: () => value,
        configurable: true,
      });
    } catch (e) {}
  };

  define(navigator, 'webdriver', false);
  try { delete Object.getPrototypeOf(navigator).webdriver; } catch (e) {}
  define(navigator, 'languages', ['en-US', 'en']);
  define(navigator, 'plugins', [1, 2, 3, 4, 5]);

  // Preserve any real chrome object supplied by the browser.
  try {
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) window.chrome.runtime = {};
  } catch (e) {}

  try {
    const originalQuery = navigator.permissions.query;
    navigator.permissions.query = (parameters) =>
      parameters && parameters.name === 'notifications' &&
      typeof Notification !== 'undefined'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters);
  } catch (e) {}
})();
"""

ANTI_FINGERPRINT_SCRIPT = r"""
(() => {
  // Canvas: only touch 2D canvases, and never let a patch break page scripts
  // (tainted canvases and WebGL canvases must pass through unchanged).
  try {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function (...args) {
      try {
        const context = this.getContext('2d');
        if (context && this.width > 0 && this.height > 0) {
          const image = context.getImageData(0, 0, this.width, this.height);
          for (let i = 0; i < image.data.length; i += 4) {
            image.data[i] = (image.data[i] + ((Math.random() * 10) | 0) - 5 + 256) % 256;
          }
          context.putImageData(image, 0, 0);
        }
      } catch (e) {
        // Cross-origin/tainted or non-2D canvas: leave it untouched.
      }
      return originalToDataURL.apply(this, args);
    };
  } catch (e) {}

  // Audio fingerprint jitter.
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx && AudioCtx.prototype.createAnalyser) {
      const originalCreateAnalyser = AudioCtx.prototype.createAnalyser;
      AudioCtx.prototype.createAnalyser = function () {
        const analyser = originalCreateAnalyser.call(this);
        const originalGetData = analyser.getFloatFrequencyData;
        analyser.getFloatFrequencyData = function (array) {
          originalGetData.call(this, array);
          for (let i = 0; i < array.length; i++) {
            array[i] += Math.random() * 0.1 - 0.05;
          }
          return array;
        };
        return analyser;
      };
    }
  } catch (e) {}

  // WebGL: patch both WebGL 1 and WebGL 2 so the renderer string cannot leak.
  try {
    const patch = (ctor) => {
      if (!ctor || !ctor.prototype || !ctor.prototype.getParameter) return;
      const original = ctor.prototype.getParameter;
      ctor.prototype.getParameter = function (parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return original.call(this, parameter);
      };
    };
    patch(window.WebGLRenderingContext);
    patch(window.WebGL2RenderingContext);
  } catch (e) {}
})();
"""

ALL_SCRIPTS: Tuple[Tuple[str, str], ...] = (
    ("stealth", STEALTH_SCRIPT),
    ("anti_fingerprinting", ANTI_FINGERPRINT_SCRIPT),
)


class StealthScriptInstaller:
    """Install init scripts once per browser context.

    ``add_init_script`` accumulates with every call; installing per navigation
    produced duplicate scripts and inconsistent fingerprints.
    """

    def __init__(self) -> None:
        self._installed = weakref.WeakKeyDictionary()

    def install(self, context, scripts: Iterable[Tuple[str, str]] = ALL_SCRIPTS) -> None:
        try:
            installed = self._installed.setdefault(context, set())
        except TypeError:  # pragma: no cover - non-weakrefable mock contexts
            installed = set()
        for name, script in scripts:
            if name in installed:
                continue
            context.add_init_script(script)
            installed.add(name)
