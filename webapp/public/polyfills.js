/**
 * Critical polyfills for Telegram Mini App on Render
 *
 * This file MUST be loaded before any JavaScript modules.
 * Telegram's WebView in production (Render) may lack full Fetch API support.
 *
 * Without these polyfills, bundled libraries (like socket.io-client) that
 * destructure Request/Response will throw errors.
 */

(function() {
  'use strict';

  console.log('[Polyfills] Initializing for Telegram Mini App on Render...');

  /**
   * Request API Polyfill
   * Minimal but functional implementation
   */
  function RequestPolyfill(input, init) {
    if (input && typeof input === 'object' && input.url) {
      // Clone from existing Request
      this.url = input.url;
      this.method = input.method || 'GET';
      this.headers = input.headers || {};
      this.body = input.body || null;
      this.mode = input.mode || 'cors';
      this.credentials = input.credentials || 'same-origin';
      this.cache = input.cache || 'default';
      this.redirect = input.redirect || 'follow';
      this.referrer = input.referrer || 'about:client';
      this.integrity = input.integrity || '';
    } else {
      // Create from URL string
      this.url = typeof input === 'string' ? input : '';
      init = init || {};
      this.method = init.method || 'GET';
      this.headers = init.headers || {};
      this.body = init.body || null;
      this.mode = init.mode || 'cors';
      this.credentials = init.credentials || 'same-origin';
      this.cache = init.cache || 'default';
      this.redirect = init.redirect || 'follow';
      this.referrer = init.referrer || 'about:client';
      this.integrity = init.integrity || '';
    }
  }

  RequestPolyfill.prototype.clone = function() {
    return new RequestPolyfill(this.url, {
      method: this.method,
      headers: this.headers,
      body: this.body,
      mode: this.mode,
      credentials: this.credentials,
      cache: this.cache,
      redirect: this.redirect,
      referrer: this.referrer,
      integrity: this.integrity
    });
  };

  /**
   * Response API Polyfill
   * Minimal but functional implementation
   */
  function ResponsePolyfill(body, init) {
    init = init || {};
    this.body = body || null;
    this.status = init.status !== undefined ? init.status : 200;
    this.statusText = init.statusText || 'OK';
    this.headers = init.headers || {};
    this.ok = this.status >= 200 && this.status < 300;
    this.redirected = init.redirected || false;
    this.type = init.type || 'basic';
    this.url = init.url || '';
  }

  ResponsePolyfill.prototype.clone = function() {
    return new ResponsePolyfill(this.body, {
      status: this.status,
      statusText: this.statusText,
      headers: this.headers,
      redirected: this.redirected,
      type: this.type,
      url: this.url
    });
  };

  ResponsePolyfill.prototype.json = function() {
    try {
      var parsed = typeof this.body === 'string' ? JSON.parse(this.body) : this.body;
      return Promise.resolve(parsed);
    } catch (e) {
      return Promise.reject(e);
    }
  };

  ResponsePolyfill.prototype.text = function() {
    return Promise.resolve(String(this.body || ''));
  };

  ResponsePolyfill.prototype.blob = function() {
    return Promise.resolve(new Blob([this.body || '']));
  };

  ResponsePolyfill.prototype.arrayBuffer = function() {
    var text = String(this.body || '');
    var buf = new ArrayBuffer(text.length);
    var bufView = new Uint8Array(buf);
    for (var i = 0; i < text.length; i++) {
      bufView[i] = text.charCodeAt(i);
    }
    return Promise.resolve(buf);
  };

  /**
   * Headers API Polyfill
   * Full implementation with iteration support
   */
  function HeadersPolyfill(init) {
    this._headers = {};

    if (init) {
      if (init instanceof HeadersPolyfill) {
        this._headers = Object.assign({}, init._headers);
      } else if (typeof init === 'object' && !Array.isArray(init)) {
        for (var key in init) {
          if (init.hasOwnProperty(key)) {
            this._headers[key.toLowerCase()] = String(init[key]);
          }
        }
      } else if (Array.isArray(init)) {
        for (var i = 0; i < init.length; i++) {
          var header = init[i];
          if (Array.isArray(header) && header.length === 2) {
            this._headers[String(header[0]).toLowerCase()] = String(header[1]);
          }
        }
      }
    }
  }

  HeadersPolyfill.prototype.get = function(name) {
    return this._headers[String(name).toLowerCase()] || null;
  };

  HeadersPolyfill.prototype.set = function(name, value) {
    this._headers[String(name).toLowerCase()] = String(value);
  };

  HeadersPolyfill.prototype.has = function(name) {
    return this._headers.hasOwnProperty(String(name).toLowerCase());
  };

  HeadersPolyfill.prototype.delete = function(name) {
    delete this._headers[String(name).toLowerCase()];
  };

  HeadersPolyfill.prototype.append = function(name, value) {
    var existing = this.get(name);
    if (existing) {
      this.set(name, existing + ', ' + value);
    } else {
      this.set(name, value);
    }
  };

  HeadersPolyfill.prototype.forEach = function(callback, thisArg) {
    for (var name in this._headers) {
      if (this._headers.hasOwnProperty(name)) {
        callback.call(thisArg, this._headers[name], name, this);
      }
    }
  };

  // Install polyfills globally
  // This is critical for Render deployment where Telegram WebView may be limited
  if (typeof window.Request === 'undefined') {
    window.Request = RequestPolyfill;
    console.log('[Polyfills] Request API installed');
  }

  if (typeof window.Response === 'undefined') {
    window.Response = ResponsePolyfill;
    console.log('[Polyfills] Response API installed');
  }

  if (typeof window.Headers === 'undefined') {
    window.Headers = HeadersPolyfill;
    console.log('[Polyfills] Headers API installed');
  }

  // Ensure polyfills are available in all JavaScript contexts
  // This prevents "Cannot destructure 'Request' of undefined" errors
  if (typeof self !== 'undefined') {
    self.Request = self.Request || window.Request;
    self.Response = self.Response || window.Response;
    self.Headers = self.Headers || window.Headers;
  }

  if (typeof globalThis !== 'undefined') {
    globalThis.Request = globalThis.Request || window.Request;
    globalThis.Response = globalThis.Response || window.Response;
    globalThis.Headers = globalThis.Headers || window.Headers;
  }

  // Log final status for debugging on Render
  console.log('[Polyfills] Status check:', {
    window: {
      Request: typeof window.Request,
      Response: typeof window.Response,
      Headers: typeof window.Headers,
      fetch: typeof window.fetch
    },
    globalThis: {
      Request: typeof globalThis.Request,
      Response: typeof globalThis.Response,
      Headers: typeof globalThis.Headers
    }
  });

  console.log('[Polyfills] Initialization complete for Telegram Mini App');

})();
