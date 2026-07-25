/*! Kathat Estate — mouse & touch interaction layer. Plain JS, no dependencies. */
(function () {
  'use strict';

  var hasFinePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  // ---- Property card tilt (mouse only — skipped entirely on touch) ------------
  function initCardTilt() {
    if (!hasFinePointer) return;
    var cards = document.querySelectorAll('.property-card');
    cards.forEach(function (card) {
      var frame = null;
      card.addEventListener('pointermove', function (e) {
        if (frame) return;
        frame = requestAnimationFrame(function () {
          var rect = card.getBoundingClientRect();
          var x = (e.clientX - rect.left) / rect.width - 0.5;
          var y = (e.clientY - rect.top) / rect.height - 0.5;
          card.style.transform = 'perspective(800px) rotateY(' + (x * 8) + 'deg) rotateX(' + (y * -8) + 'deg) translateY(-4px)';
          frame = null;
        });
      });
      card.addEventListener('pointerleave', function () {
        card.style.transform = '';
      });
    });
  }

  // ---- Button ripple (works for both mouse click and touch tap) --------------
  function initRipple() {
    document.querySelectorAll('.btn').forEach(function (btn) {
      btn.addEventListener('pointerdown', function (e) {
        var rect = btn.getBoundingClientRect();
        var size = Math.max(rect.width, rect.height);
        var ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
        btn.appendChild(ripple);
        setTimeout(function () { ripple.remove(); }, 600);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initCardTilt();
    initRipple();
  });
})();
