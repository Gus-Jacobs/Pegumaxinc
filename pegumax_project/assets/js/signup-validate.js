/* Live signup validation — reused by the dedicated signup page and the nav modal.
   Highlights inputs red/green, shows per-field hints, ticks the rule list, and
   blocks submission until the client-side rules pass. Server-side validation
   (common/similar passwords, uniqueness) remains the source of truth. */
(function () {
  var USERNAME_RE = /^[\w.@+\-]+$/;          // letters, digits, @ . + - _  (no spaces)
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setState(input, hintEl, ok, msg) {
    if (!input) return ok;
    input.classList.toggle('valid', ok === true);
    input.classList.toggle('invalid', ok === false);
    if (hintEl) {
      hintEl.textContent = msg || '';
      hintEl.classList.toggle('ok', ok === true && !!msg);
      hintEl.classList.toggle('bad', ok === false);
    }
    return ok;
  }

  window.initSignupValidation = function (formId) {
    var form = document.getElementById(formId);
    if (!form) return;
    var u = form.querySelector('[name=username]');
    var em = form.querySelector('[name=email]');
    var p1 = form.querySelector('[name=password1]');
    var p2 = form.querySelector('[name=password2]');
    var submit = form.querySelector('button[type=submit]');

    function hint(name) { return form.querySelector('[data-for="' + name + '"]'); }
    function rule(key, met) {
      var li = document.querySelector('[data-rule="' + key + '"]');
      if (li) li.classList.toggle('met', !!met);
    }

    function vUser() {
      var val = (u && u.value) || '';
      if (!val) return setState(u, hint('username'), null, '');
      var lenOk = val.length >= 3, charOk = USERNAME_RE.test(val);
      rule('u-len', lenOk); rule('u-chars', charOk);
      if (!charOk) return setState(u, hint('username'), false, 'No spaces; letters, digits and @ . + - _ only.');
      if (!lenOk) return setState(u, hint('username'), false, 'At least 3 characters.');
      return setState(u, hint('username'), true, 'Looks good.');
    }
    function vEmail() {
      var val = (em && em.value) || '';
      if (!val) return setState(em, hint('email'), null, '');
      var ok = EMAIL_RE.test(val);
      return setState(em, hint('email'), ok, ok ? '' : 'Enter a valid email address.');
    }
    function vPass() {
      var val = (p1 && p1.value) || '';
      if (!val) { rule('p-len', false); rule('p-notnum', false); return setState(p1, hint('password1'), null, ''); }
      var lenOk = val.length >= 8, notNum = !/^\d+$/.test(val);
      rule('p-len', lenOk); rule('p-notnum', notNum);
      if (!lenOk) return setState(p1, hint('password1'), false, 'At least 8 characters.');
      if (!notNum) return setState(p1, hint('password1'), false, "Can't be all numbers.");
      return setState(p1, hint('password1'), true, 'Strong enough.');
    }
    function vMatch() {
      var a = (p1 && p1.value) || '', b = (p2 && p2.value) || '';
      if (!b) { rule('p-match', false); return setState(p2, hint('password2'), null, ''); }
      var ok = a === b;
      rule('p-match', ok);
      return setState(p2, hint('password2'), ok, ok ? 'Passwords match.' : "Passwords don't match.");
    }

    function validateAll() {
      var a = vUser(), b = vEmail(), c = vPass(), d = vMatch();
      var allOk = a && b && c && d;
      if (submit) submit.disabled = !allOk;
      return allOk;
    }

    [[u, vUser], [em, vEmail], [p1, function () { vPass(); vMatch(); }], [p2, vMatch]].forEach(function (pair) {
      if (pair[0]) {
        pair[0].addEventListener('input', function () { pair[1](); if (submit) submit.disabled = !validateAll(); });
        pair[0].addEventListener('blur', pair[1]);
      }
    });

    form.addEventListener('submit', function (e) {
      if (!validateAll()) { e.preventDefault(); }
    });

    validateAll(); // sets initial state + disables submit until the form is valid
  };
})();
