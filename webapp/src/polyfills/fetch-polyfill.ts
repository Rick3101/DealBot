/**
 * Fetch API Polyfill - Import this FIRST in main.tsx
 *
 * This polyfill runs in module scope, ensuring Request/Response/Headers
 * are available before any other ES modules import them.
 */

// Polyfill Request
if (typeof globalThis.Request === 'undefined') {
  (globalThis as any).Request = function(this: any, input: any, init?: any) {
    if (input && typeof input === 'object' && input.url) {
      this.url = input.url;
      this.method = input.method || 'GET';
      this.headers = input.headers || {};
      this.body = input.body || null;
      this.mode = input.mode || 'cors';
      this.credentials = input.credentials || 'same-origin';
    } else {
      this.url = typeof input === 'string' ? input : '';
      init = init || {};
      this.method = init.method || 'GET';
      this.headers = init.headers || {};
      this.body = init.body || null;
      this.mode = init.mode || 'cors';
      this.credentials = init.credentials || 'same-origin';
    }
  };
  console.log('[TS Polyfill] Request API installed in module scope');
}

// Polyfill Response
if (typeof globalThis.Response === 'undefined') {
  (globalThis as any).Response = function(this: any, body?: any, init?: any) {
    init = init || {};
    this.body = body || null;
    this.status = init.status !== undefined ? init.status : 200;
    this.statusText = init.statusText || 'OK';
    this.headers = init.headers || {};
    this.ok = this.status >= 200 && this.status < 300;
    this.redirected = init.redirected || false;
    this.type = init.type || 'basic';
    this.url = init.url || '';
  };

  (globalThis.Response as any).prototype.json = function() {
    try {
      const parsed = typeof this.body === 'string' ? JSON.parse(this.body) : this.body;
      return Promise.resolve(parsed);
    } catch (e) {
      return Promise.reject(e);
    }
  };

  (globalThis.Response as any).prototype.text = function() {
    return Promise.resolve(String(this.body || ''));
  };

  console.log('[TS Polyfill] Response API installed in module scope');
}

// Polyfill Headers
if (typeof globalThis.Headers === 'undefined') {
  (globalThis as any).Headers = function(this: any, init?: any) {
    this._headers = {};
    if (init) {
      if (typeof init === 'object' && !Array.isArray(init)) {
        for (const key in init) {
          if (init.hasOwnProperty(key)) {
            this._headers[key.toLowerCase()] = String(init[key]);
          }
        }
      }
    }
  };

  (globalThis.Headers as any).prototype.get = function(name: string) {
    return this._headers[String(name).toLowerCase()] || null;
  };

  (globalThis.Headers as any).prototype.set = function(name: string, value: string) {
    this._headers[String(name).toLowerCase()] = String(value);
  };

  (globalThis.Headers as any).prototype.has = function(name: string) {
    return this._headers.hasOwnProperty(String(name).toLowerCase());
  };

  console.log('[TS Polyfill] Headers API installed in module scope');
}

// Also ensure they're on window for older code
if (typeof window !== 'undefined') {
  (window as any).Request = (window as any).Request || globalThis.Request;
  (window as any).Response = (window as any).Response || globalThis.Response;
  (window as any).Headers = (window as any).Headers || globalThis.Headers;
}

console.log('[TS Polyfill] Fetch API polyfills ready');

// Export empty object to make this a valid module
export {};
