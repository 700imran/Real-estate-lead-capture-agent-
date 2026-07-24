/*! Kathat Estate — shared site behavior. Plain JS, no build step, no dependencies. */
(function () {
  'use strict';

  // ---- Language toggle (EN/HI) ----------------------------------------------
  function initLangToggle() {
    var stored = null;
    try { stored = localStorage.getItem('kathat_lang'); } catch (e) {}
    var lang = stored === 'hi' ? 'hi' : 'en';
    document.documentElement.classList.remove('lang-en', 'lang-hi');
    document.documentElement.classList.add('lang-' + lang);
    document.documentElement.setAttribute('lang', lang);

    document.querySelectorAll('[data-lang-btn]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', btn.getAttribute('data-lang-btn') === lang ? 'true' : 'false');
      btn.addEventListener('click', function () {
        var next = btn.getAttribute('data-lang-btn');
        document.documentElement.classList.remove('lang-en', 'lang-hi');
        document.documentElement.classList.add('lang-' + next);
        document.documentElement.setAttribute('lang', next);
        try { localStorage.setItem('kathat_lang', next); } catch (e) {}
        document.querySelectorAll('[data-lang-btn]').forEach(function (b) {
          b.setAttribute('aria-pressed', b.getAttribute('data-lang-btn') === next ? 'true' : 'false');
        });
      });
    });
  }

  // ---- Reveal on scroll -------------------------------------------------------
  function initReveal() {
    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('in-view'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    els.forEach(function (el) { io.observe(el); });
  }

  // ---- Portfolio city filter ---------------------------------------------------
  function initCityFilter() {
    var chips = document.querySelectorAll('[data-city-chip]');
    var cards = document.querySelectorAll('[data-city-card]');
    if (!chips.length) return;
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        var city = chip.getAttribute('data-city-chip');
        chips.forEach(function (c) { c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
        cards.forEach(function (card) {
          var show = city === 'all' || card.getAttribute('data-city-card') === city;
          card.style.display = show ? '' : 'none';
        });
      });
    });
  }

  // ---- Enquiry form -------------------------------------------------------------
  function initEnquiryForm() {
    var form = document.querySelector('.enquiry-form');
    if (!form) return;
    var success = document.querySelector('.enquiry-success');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = form.querySelector('[name="name"]');
      var phone = form.querySelector('[name="phone"]');
      var unit = form.querySelector('[name="unit"]');
      var property = form.getAttribute('data-property') || null;

      if (window.LeadPixel) {
        window.LeadPixel.identify({ phone: phone ? phone.value : '' });
        window.LeadPixel.track('form_submit', {
          name: name ? name.value : '',
          unit: unit ? unit.value : '',
          property: property
        });
      }

      form.hidden = true;
      if (success) success.hidden = false;
    });
  }

  // ---- AI chat widget -------------------------------------------------------------
  function initChat() {
    var launcher = document.querySelector('.chat-launcher');
    var panel = document.querySelector('.chat-panel');
    if (!launcher || !panel) return;

    var body = panel.querySelector('.chat-panel__body');
    var form = panel.querySelector('.chat-panel__form');
    var input = form.querySelector('input');
    var propertyName = panel.getAttribute('data-property-name') || null;
    var conversationId = null;
    var greeted = false;

    function isHindi() { return document.documentElement.classList.contains('lang-hi'); }

    function addMessage(role, text) {
      var div = document.createElement('div');
      div.className = 'chat-msg chat-msg--' + role;
      div.textContent = text;
      body.appendChild(div);
      body.scrollTop = body.scrollHeight;
    }

    function greeting() {
      if (propertyName) {
        return isHindi()
          ? ('नमस्ते — मैं ' + propertyName + ' के बारे में मदद कर सकता हूं। आप क्या जानना चाहेंगे?')
          : ('Hi — I can help with ' + propertyName + '. What would you like to know?');
      }
      return isHindi()
        ? 'नमस्ते — मैं पोर्टफोलियो, कीमत, या विज़िट बुक करने में मदद कर सकता हूं। आप क्या जानना चाहेंगे?'
        : 'Hi — I can help with any development in the portfolio, pricing, or booking a visit. What would you like to know?';
    }

    launcher.addEventListener('click', function () {
      panel.hidden = !panel.hidden;
      if (!panel.hidden && !greeted) {
        addMessage('assistant', greeting());
        greeted = true;
      }
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var text = input.value.trim();
      if (!text) return;
      addMessage('user', text);
      input.value = '';

      var visitorId = window.KATHAT_VISITOR_ID;
      if (!visitorId) return;

      var base = window.KATHAT_API_BASE || '';
      fetch(base + '/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          visitor_id: visitorId,
          message: text,
          language: isHindi() ? 'hi' : 'en',
          conversation_id: conversationId,
          property_name: propertyName
        })
      })
        .then(function (res) { if (!res.ok) throw new Error('bad response'); return res.json(); })
        .then(function (data) {
          conversationId = data.conversation_id;
          addMessage('assistant', data.reply);
        })
        .catch(function () {
          addMessage('assistant', isHindi()
            ? 'अभी जवाब देने में दिक्कत हो रही है।'
            : 'Having trouble responding right now.');
        });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initLangToggle();
    initReveal();
    initCityFilter();
    initEnquiryForm();
    initChat();
  });
})();
