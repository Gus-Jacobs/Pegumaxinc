/* ============================================================= */
/*  PEGUMAX — shared front-end behaviour (every page)            */
/*  Exposes window.Pegumax = { observe, reset } for the SPA.     */
/* ============================================================= */
(function(){
  "use strict";
  var fine = window.matchMedia('(hover:hover) and (pointer:fine)').matches;
  var reduce = window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  var CFG = {};
  try { CFG = JSON.parse((document.getElementById('site-config')||{}).textContent || '{}'); } catch(e){ CFG = {}; }
  var STRIPE_PUBLISHABLE_KEY = CFG.stripePk || '';
  var API = { message:'/api/message/', donateSession:'/donate/create-session/' };

  function $(id){ return document.getElementById(id); }
  function anyModalOpen(){ return document.querySelector('.modal.open') !== null; }

  /* ---- year ---- */
  var yr = $('year'); if(yr) yr.textContent = new Date().getFullYear();

  /* ---- nav scroll / progress / back-to-top ---- */
  var nav=$('nav'), progress=$('progress'), totop=$('totop');
  function onScroll(){
    var y=window.scrollY||document.documentElement.scrollTop;
    if(nav) nav.classList.toggle('scrolled', y>30);
    if(progress){ var h=document.documentElement.scrollHeight-window.innerHeight; progress.style.width=(h>0?(y/h*100):0)+'%'; }
    if(totop) totop.classList.toggle('show', y>500);
  }
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  if(totop) totop.addEventListener('click', function(){ window.scrollTo({top:0,behavior:'smooth'}); });

  /* ---- mobile menu ---- */
  var hamb=$('hamb');
  if(hamb && nav){ hamb.addEventListener('click', function(){ nav.classList.toggle('open'); document.body.classList.toggle('locked', nav.classList.contains('open')); }); }
  function closeMenu(){ if(nav) nav.classList.remove('open'); if(!anyModalOpen()) document.body.classList.remove('locked'); }

  /* ---- spotlight ---- */
  var sp=$('spotlight');
  if(sp && fine && !reduce){
    window.addEventListener('mousemove', function(e){ sp.style.opacity='1'; sp.style.left=e.clientX+'px'; sp.style.top=e.clientY+'px'; });
    window.addEventListener('mouseleave', function(){ sp.style.opacity='0'; });
  }

  /* ---- reveal + counters ---- */
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        en.target.classList.add('in');
        if(en.target.querySelector && en.target.querySelector('[data-count]')) animateCounters(en.target);
        io.unobserve(en.target);
      }
    });
  }, {threshold:0.14, rootMargin:'0px 0px -8% 0px'});

  function animateCounters(scope){
    scope.querySelectorAll('[data-count]').forEach(function(n){
      if(n.dataset.done) return; n.dataset.done='1';
      var target=parseInt(n.getAttribute('data-count'),10)||0, dur=1300, t0=null;
      function step(ts){ if(!t0)t0=ts; var p=Math.min((ts-t0)/dur,1); var e=1-Math.pow(1-p,3);
        n.textContent=Math.round(target*e); if(p<1) requestAnimationFrame(step); }
      requestAnimationFrame(step);
    });
  }

  function bindInteractions(scope){
    if(!fine || reduce) return;
    (scope||document).querySelectorAll('.tilt:not([data-bound])').forEach(function(el){
      el.setAttribute('data-bound','1'); el.style.transition='transform .15s var(--ease)';
      el.addEventListener('mousemove', function(e){
        var r=el.getBoundingClientRect(); var px=(e.clientX-r.left)/r.width-0.5, py=(e.clientY-r.top)/r.height-0.5;
        el.style.transform='perspective(900px) rotateY('+(px*7)+'deg) rotateX('+(-py*7)+'deg) translateY(-4px)';
      });
      el.addEventListener('mouseleave', function(){ el.style.transform=''; });
    });
    (scope||document).querySelectorAll('.magnetic:not([data-bound])').forEach(function(el){
      el.setAttribute('data-bound','1');
      el.addEventListener('mousemove', function(e){
        var r=el.getBoundingClientRect();
        el.style.transform='translate('+(e.clientX-r.left-r.width/2)*0.25+'px,'+(e.clientY-r.top-r.height/2)*0.35+'px)';
      });
      el.addEventListener('mouseleave', function(){ el.style.transform=''; });
    });
  }

  function observe(scope){
    scope = scope || document;
    scope.querySelectorAll('.reveal,.reveal-x,.reveal-s').forEach(function(el){ if(!el.classList.contains('in')) io.observe(el); });
    bindInteractions(scope);
  }
  function reset(scope){
    (scope||document).querySelectorAll('.in').forEach(function(el){ el.classList.remove('in'); io.unobserve(el); });
  }
  observe(document);

  /* ---- modal plumbing ---- */
  function openModalEl(el){ if(!el) return; el.classList.add('open'); document.body.classList.add('locked'); }
  function closeModalEl(el){ if(!el) return; el.classList.remove('open'); if(!anyModalOpen()) document.body.classList.remove('locked'); }

  /* auth */
  var authModal=$('authModal');
  function openAuth(type){
    var lf=$('loginForm'), sf=$('signupForm');
    if(lf) lf.style.display=(type==='signup')?'none':'';
    if(sf) sf.style.display=(type==='signup')?'':'none';
    openModalEl(authModal);
  }
  if(authModal){
    authModal.addEventListener('click', function(e){
      if(e.target.hasAttribute('data-close')) closeModalEl(authModal);
      var sw=e.target.closest('[data-swap]'); if(sw){ openAuth(sw.getAttribute('data-swap')); }
    });
  }

  /* feedback */
  var msgModal=$('msgModal');
  function openFeedback(type){
    if(msgModal && type){ var seg=msgModal.querySelector('[data-typeseg]');
      if(seg) seg.querySelectorAll('button').forEach(function(b){ b.classList.toggle('active', b.getAttribute('data-t')===type); }); }
    openModalEl(msgModal);
  }
  if(msgModal){ msgModal.addEventListener('click', function(e){ if(e.target.hasAttribute('data-close-msg')) closeModalEl(msgModal); }); }

  /* type segmented controls (feedback modal + any page form) */
  document.querySelectorAll('[data-typeseg]').forEach(function(seg){
    seg.addEventListener('click', function(e){
      var b=e.target.closest('button[data-t]'); if(!b) return;
      seg.querySelectorAll('button').forEach(function(x){x.classList.remove('active');});
      b.classList.add('active');
    });
  });

  function setNote(el,msg,kind){ if(!el)return; el.textContent=msg; el.className='form-note '+(kind||''); }
  function sendJSON(url,data){
    return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
      .then(function(res){ return res.json().catch(function(){return {success:res.ok};}); });
  }

  document.querySelectorAll('[data-msgform]').forEach(function(form){
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var note=form.querySelector('[data-note]');
      var seg=form.querySelector('[data-typeseg] button.active');
      var type=seg?seg.getAttribute('data-t'):(form.getAttribute('data-msgtype')||'message');
      var fd={ type:type,
        name:(form.querySelector('[name=name]')||{}).value||'Anonymous',
        email:(form.querySelector('[name=email]')||{}).value||'',
        message:(form.querySelector('[name=message]')||{}).value||'' };
      if(!fd.message.trim()){ setNote(note,'Please write a message first.','err'); return; }
      var btn=form.querySelector('button[type=submit]'); var orig=btn?btn.innerHTML:''; if(btn) btn.innerHTML='Sending…';
      sendJSON(API.message, fd).then(function(r){
        if(btn) btn.innerHTML=orig;
        if(r && r.success){ setNote(note, r.message||'Thanks! Your message is on its way.', 'ok'); form.reset();
          form.querySelectorAll('[data-typeseg] button').forEach(function(x,i){x.classList.toggle('active',i===0);}); }
        else setNote(note, (r&&r.message)||'Could not send right now.', 'err');
      }).catch(function(){ if(btn) btn.innerHTML=orig; setNote(note, 'Could not reach the server. Please try again.', 'err'); });
    });
  });

  document.querySelectorAll('[data-notify]').forEach(function(form){
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var note=form.querySelector('[data-note]');
      sendJSON(API.message, {type:'store-notify', name:'Store waitlist', email:(form.querySelector('[name=email]')||{}).value||'', message:'Notify me when the Store opens.'});
      setNote(note,'Thanks — we\'ll email you when the Store opens!','ok'); form.reset();
    });
  });

  /* ---- donations (Stripe embedded checkout) ---- */
  var donateModal=$('donateModal');
  var stripe = (window.Stripe && STRIPE_PUBLISHABLE_KEY.indexOf('pk_')===0) ? Stripe(STRIPE_PUBLISHABLE_KEY) : null;
  var checkout=null, donateAmount=5;
  function resetDonate(){
    var s1=$('donateStep1'), s2=$('donateStep2'), m=$('donate-checkout');
    if(s1) s1.style.display=''; if(s2) s2.style.display='none'; if(m) m.innerHTML='';
    if(checkout){ try{checkout.destroy();}catch(e){} checkout=null; }
  }
  function openDonate(){ if(!donateModal) return; resetDonate(); openModalEl(donateModal); }
  if(donateModal){
    donateModal.addEventListener('click', function(e){ if(e.target.hasAttribute('data-close-donate')){ closeModalEl(donateModal); resetDonate(); } });
    var amtGrid=$('amtGrid'), customAmt=$('customAmt');
    if(amtGrid){
      amtGrid.addEventListener('click', function(e){
        var b=e.target.closest('button[data-amt]'); if(!b) return;
        amtGrid.querySelectorAll('button').forEach(function(x){x.classList.remove('active');});
        b.classList.add('active');
        if(b.getAttribute('data-amt')==='custom'){ if(customAmt){customAmt.style.display='block';customAmt.focus();donateAmount=parseFloat(customAmt.value)||0;} }
        else { if(customAmt) customAmt.style.display='none'; donateAmount=parseFloat(b.getAttribute('data-amt')); }
      });
    }
    if(customAmt) customAmt.addEventListener('input', function(){ donateAmount=parseFloat(customAmt.value)||0; });
    var cont=$('donateContinue');
    if(cont) cont.addEventListener('click', function(){
      if(!donateAmount || donateAmount<1){ alert('Please choose an amount of at least $1.'); return; }
      var lbl=$('donateAmtLabel'); if(lbl) lbl.textContent='$'+donateAmount;
      $('donateStep1').style.display='none'; $('donateStep2').style.display='';
      var mount=$('donate-checkout'); mount.innerHTML='<div class="demo-msg">Starting secure checkout…</div>';
      if(!stripe){ mount.innerHTML='<div class="demo-msg"><b>Payments aren\'t configured.</b><br>Add your Stripe publishable key to enable donations.</div>'; return; }
      sendJSON(API.donateSession, {amount:donateAmount}).then(function(data){
        if(!data || !data.clientSecret){ throw new Error((data&&data.error)||'No client secret'); }
        mount.innerHTML='';
        return stripe.initEmbeddedCheckout({clientSecret:data.clientSecret}).then(function(c){ checkout=c; c.mount('#donate-checkout'); });
      }).catch(function(err){
        mount.innerHTML='<div class="demo-msg"><b>Couldn\'t start checkout.</b><br>'+(err&&err.message||'Please try again later.')+'</div>';
      });
    });
  }

  /* ---- notify / wishlist ---- */
  var notifyModal=$('notifyModal'), notifyApp='', notifyKind='notify';
  function openNotify(app, kind){
    notifyApp = app || 'Pegumax'; notifyKind = (kind==='wishlist') ? 'wishlist' : 'notify';
    var t=$('notifyTitle'), s=$('notifySub'), b=$('notifyBtnLabel'), note=notifyModal?notifyModal.querySelector('[data-note]'):null;
    if(note) setNote(note,'','');
    if(notifyKind==='wishlist'){
      if(t) t.textContent='Wishlist '+notifyApp;
      if(s) s.textContent='We\'ll email you the moment '+notifyApp+' enters beta.';
      if(b) b.textContent='Add me to the wishlist';
    } else {
      if(t) t.textContent='Get notified about '+notifyApp;
      if(s) s.textContent='Leave your email and we\'ll tell you the moment '+notifyApp+' is ready.';
      if(b) b.textContent='Add me to the list';
    }
    openModalEl(notifyModal);
  }
  if(notifyModal){
    notifyModal.addEventListener('click', function(e){ if(e.target.hasAttribute('data-close-notify')) closeModalEl(notifyModal); });
    var nf=$('notifyForm');
    if(nf) nf.addEventListener('submit', function(e){
      e.preventDefault();
      var note=nf.querySelector('[data-note]');
      var email=(nf.querySelector('[name=email]')||{}).value||'';
      var extra=(nf.querySelector('[name=note]')||{}).value||'';
      var btn=nf.querySelector('button[type=submit]'); var orig=btn?btn.innerHTML:''; if(btn) btn.innerHTML='Adding…';
      var msg=(notifyKind==='wishlist'?'WISHLIST request for ':'NOTIFY request for ')+notifyApp+'.'+(extra?(' Note: '+extra):'');
      sendJSON(API.message, {type:notifyKind, name:notifyKind+' list', email:email, message:msg}).then(function(r){
        if(btn) btn.innerHTML=orig;
        if(r && r.success){ setNote(note,'You\'re on the list — thank you!','ok'); nf.reset(); setTimeout(function(){ closeModalEl(notifyModal); },1200); }
        else setNote(note,(r&&r.message)||'Could not add you right now.','err');
      }).catch(function(){ if(btn) btn.innerHTML=orig; setNote(note,'Could not reach the server. Please try again.','err'); });
    });
  }
  window.Pegumax = window.Pegumax || {};

  /* ---- global delegated clicks (modals / feedback / donate / dropdowns) ---- */
  document.addEventListener('click', function(e){
    var md=e.target.closest('[data-modal]'); if(md){ e.preventDefault(); openAuth(md.getAttribute('data-modal')); return; }
    var fb=e.target.closest('[data-feedback]'); if(fb){ e.preventDefault(); openFeedback(fb.getAttribute('data-feedback')); return; }
    var dn=e.target.closest('[data-donate]'); if(dn){ e.preventDefault(); openDonate(); return; }
    var nt=e.target.closest('[data-notify-app]'); if(nt){ e.preventDefault(); openNotify(nt.getAttribute('data-notify-app'), nt.getAttribute('data-notify-kind')); return; }
    var dd=e.target.closest('[data-dropdown]');
    var drop=dd?dd.closest('.dl-drop'):null;
    document.querySelectorAll('.dl-drop.open').forEach(function(x){ if(x!==drop) x.classList.remove('open'); });
    if(dd && drop){ e.preventDefault(); drop.classList.toggle('open'); }
  });

  document.addEventListener('keydown', function(e){
    if(e.key==='Escape'){
      document.querySelectorAll('.modal.open').forEach(function(m){ m.classList.remove('open'); if(m===donateModal) resetDonate(); });
      if(!anyModalOpen()) document.body.classList.remove('locked');
      closeMenu();
    }
  });

  window.Pegumax = { observe:observe, reset:reset, closeMenu:closeMenu, openDonate:openDonate, openFeedback:openFeedback, openAuth:openAuth, openNotify:openNotify };
})();
