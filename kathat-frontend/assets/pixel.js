/*!
 * pixel.js — Kathat Estate tracking pixel.
 * Zero dependencies, adds ~0ms to page load. Reads window.KATHAT_API_BASE
 * from config.js (load config.js BEFORE this file).
 */
(function (window, document) {
  'use strict';

  var CONFIG = {
    endpoint: (window.KATHAT_API_BASE || '') + '/api/v1/track',
    flushInterval: 5000,
    maxQueueSize: 20,
    hoverThreshold: 1200,
    scrollMilestones: [25, 50, 75, 100]
  };

  function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function getVisitorId() {
    try {
      var id = localStorage.getItem('_kathat_vid');
      if (!id) { id = uuid(); localStorage.setItem('_kathat_vid', id); }
      return id;
    } catch (e) { return 'no-storage-' + Date.now(); }
  }

  function getSessionId() {
    try {
      var id = sessionStorage.getItem('_kathat_sid');
      if (!id) { id = uuid(); sessionStorage.setItem('_kathat_sid', id); }
      return id;
    } catch (e) { return 'no-session-' + Date.now(); }
  }

  var visitorId = getVisitorId();
  var sessionId = getSessionId();
  var leadEmail = null;
  var leadPhone = null;
  window.KATHAT_VISITOR_ID = visitorId;

  var queue = [];
  var flushTimer = null;

  function scheduleFlush() {
    if (flushTimer) return;
    flushTimer = setTimeout(flush, CONFIG.flushInterval);
  }

  function flush() {
    if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
    if (!queue.length) return;

    var payload = JSON.stringify({
      visitor_id: visitorId,
      session_id: sessionId,
      email: leadEmail,
      phone: leadPhone,
      current_page: location.pathname,
      referrer: document.referrer,
      events: queue.splice(0, queue.length)
    });

    if (navigator.sendBeacon) {
      var blob = new Blob([payload], { type: 'application/json' });
      var ok = navigator.sendBeacon(CONFIG.endpoint, blob);
      if (ok) return;
    }
    fetch(CONFIG.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true
    }).catch(function () {});
  }

  function push(type, data) {
    queue.push({ type: type, data: data || {}, t: Date.now(), page: location.pathname });
    if (queue.length >= CONFIG.maxQueueSize) { flush(); } else { scheduleFlush(); }
  }

  function trackPageView() {
    push('page_view', { title: document.title, path: location.pathname });
  }

  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-track], a, button, input[type="submit"]');
    if (!el) return;
    push('click', {
      label: el.getAttribute('data-track') || (el.innerText || '').slice(0, 60) || el.name || el.id,
      tag: el.tagName.toLowerCase(),
      href: el.href || null
    });
  }, { passive: true });

  var hoverTimers = new WeakMap();
  document.addEventListener('mouseover', function (e) {
    var el = e.target.closest && e.target.closest('[data-track-hover]');
    if (!el || hoverTimers.has(el)) return;
    var timer = setTimeout(function () {
      push('hover_interest', { label: el.getAttribute('data-track-hover') });
    }, CONFIG.hoverThreshold);
    hoverTimers.set(el, timer);
  }, { passive: true });

  document.addEventListener('mouseout', function (e) {
    var el = e.target.closest && e.target.closest('[data-track-hover]');
    if (!el) return;
    var timer = hoverTimers.get(el);
    if (timer) { clearTimeout(timer); hoverTimers.delete(el); }
  }, { passive: true });

  document.addEventListener('focusin', function (e) {
    var el = e.target;
    if (!el.matches || !el.matches('input, textarea, select')) return;
    push('form_field_focus', { field: el.name || el.id || el.type });
  }, { passive: true });

  document.addEventListener('submit', function (e) {
    var form = e.target;
    var emailField = form.querySelector && form.querySelector('input[type="email"], input[name*="email" i]');
    var phoneField = form.querySelector && form.querySelector('input[type="tel"], input[name*="phone" i]');
    if ((emailField && emailField.value) || (phoneField && phoneField.value)) {
      identify({ email: emailField && emailField.value, phone: phoneField && phoneField.value });
    }
  }, { passive: true });

  function initScrollDepth() {
    if (!('IntersectionObserver' in window)) return;
    var seen = {};
    var docHeight = document.documentElement.scrollHeight;
    CONFIG.scrollMilestones.forEach(function (pct) {
      var marker = document.createElement('div');
      marker.style.cssText = 'position:absolute;left:0;width:1px;height:1px;visibility:hidden;top:' +
        Math.min(docHeight * (pct / 100), docHeight - 1) + 'px;';
      document.body.appendChild(marker);
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !seen[pct]) {
            seen[pct] = true;
            push('scroll_depth', { percent: pct });
            observer.disconnect();
          }
        });
      });
      observer.observe(marker);
    });
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') flush();
  });
  window.addEventListener('pagehide', flush);

  function identify(info) {
    if (!info) return;
    var payload = typeof info === 'string' ? { email: info } : info;
    var changed = false;
    if (payload.email && payload.email !== leadEmail) { leadEmail = payload.email; changed = true; }
    if (payload.phone && payload.phone !== leadPhone) { leadPhone = payload.phone; changed = true; }
    if (!changed) return;
    push('identify', { email: leadEmail, phone: leadPhone });
    flush();
  }

  window.LeadPixel = {
    identify: identify,
    track: function (name, data) { push(name, data); flush(); }
  };

  function boot() {
    trackPageView();
    initScrollDepth();
  }
  if ('requestIdleCallback' in window) {
    requestIdleCallback(boot, { timeout: 2000 });
  } else {
    setTimeout(boot, 0);
  }
})(window, document);
