/*! Kathat Estate — admin dashboard. Requires login; not part of the public site. */
(function () {
  'use strict';

  var API_BASE = window.KATHAT_API_BASE || '';
  var loginView = document.getElementById('dash-login');
  var mainView = document.getElementById('dash-main');
  var loginForm = document.getElementById('dash-login-form');
  var loginError = document.getElementById('dash-login-error');
  var signOutBtn = document.getElementById('dash-signout');
  var statusDot = document.getElementById('dash-status-dot');
  var statusText = document.getElementById('dash-status-text');

  function token() { return localStorage.getItem('kathat_token'); }
  function authHeaders() { return { Authorization: 'Bearer ' + token() }; }

  function showLoggedOut() {
    loginView.hidden = false;
    mainView.hidden = true;
  }
  function showLoggedIn() {
    loginView.hidden = true;
    mainView.hidden = false;
  }

  function pillClass(temp) {
    if (temp === 'hot') return 'pill pill--hot';
    if (temp === 'warm') return 'pill pill--warm';
    return 'pill pill--cold';
  }

  function renderStats(stats) {
    document.getElementById('stat-live').textContent = stats.live_visitors;
    document.getElementById('stat-qualified').textContent = stats.qualified_leads;
    document.getElementById('stat-total').textContent = stats.total_leads;
    document.getElementById('stat-stages').textContent = stats.conversion_funnel.length;
  }

  function renderLeads(leads) {
    var tbody = document.getElementById('leads-tbody');
    tbody.innerHTML = '';
    if (!leads.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="padding:24px;text-align:center;color:rgba(23,20,15,.4);">No leads yet — activity will appear here as visitors browse the site.</td></tr>';
      return;
    }
    leads.forEach(function (l) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + escapeHtml(l.name || l.phone || l.email || 'Anonymous') + '</td>' +
        '<td>' + escapeHtml(l.source_page || '\u2014') + '</td>' +
        '<td>' + l.score + '</td>' +
        '<td><span class="' + pillClass(l.temperature) + '">' + l.temperature + '</span></td>';
      tbody.appendChild(tr);
    });
  }

  function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function loadData() {
    Promise.all([
      fetch(API_BASE + '/api/v1/leads', { headers: authHeaders() }),
      fetch(API_BASE + '/api/v1/leads/stats', { headers: authHeaders() })
    ]).then(function (responses) {
      if (responses.some(function (r) { return !r.ok; })) throw new Error('unauthorized');
      return Promise.all(responses.map(function (r) { return r.json(); }));
    }).then(function (results) {
      renderLeads(results[0]);
      renderStats(results[1]);
    }).catch(function () {
      localStorage.removeItem('kathat_token');
      showLoggedOut();
    });
  }

  function connectLiveFeed() {
    var wsBase = (API_BASE || window.location.origin).replace(/^http/, 'ws');
    var ws;
    try {
      ws = new WebSocket(wsBase + '/api/v1/ws/dashboard');
    } catch (e) {
      statusText.textContent = 'Offline';
      return;
    }
    ws.onopen = function () {
      statusDot.classList.add('live');
      statusText.textContent = 'Live';
    };
    ws.onclose = function () {
      statusDot.classList.remove('live');
      statusText.textContent = 'Reconnecting\u2026';
    };
    ws.onerror = function () {
      statusDot.classList.remove('live');
      statusText.textContent = 'Offline';
    };
    ws.onmessage = function (event) {
      try {
        var data = JSON.parse(event.data);
        if (data.type === 'lead_activity') addLiveRow(data);
      } catch (e) {}
    };
  }

  function addLiveRow(data) {
    var feed = document.getElementById('live-feed');
    var empty = feed.querySelector('.empty');
    if (empty) empty.remove();
    var row = document.createElement('div');
    row.className = 'row';
    row.innerHTML =
      '<span>' + escapeHtml(data.page || '\u2014') + '</span>' +
      '<span class="' + pillClass(data.temperature) + '">' + data.temperature + '</span>';
    feed.prepend(row);
    while (feed.children.length > 8) feed.removeChild(feed.lastChild);
  }

  loginForm.addEventListener('submit', function (e) {
    e.preventDefault();
    loginError.hidden = true;
    var email = document.getElementById('dash-email').value;
    var password = document.getElementById('dash-password').value;

    fetch(API_BASE + '/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password })
    })
      .then(function (res) { if (!res.ok) throw new Error('bad login'); return res.json(); })
      .then(function (data) {
        localStorage.setItem('kathat_token', data.access_token);
        showLoggedIn();
        loadData();
        connectLiveFeed();
      })
      .catch(function () {
        loginError.hidden = false;
      });
  });

  signOutBtn.addEventListener('click', function () {
    localStorage.removeItem('kathat_token');
    showLoggedOut();
  });

  if (token()) {
    showLoggedIn();
    loadData();
    connectLiveFeed();
  } else {
    showLoggedOut();
  }
})();
