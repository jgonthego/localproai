(function(){
  var root=document.documentElement;
  // theme toggle
  var tb=document.getElementById('theme');
  function cur(){var t=root.getAttribute('data-theme');if(t)return t;return window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}
  function label(){if(tb){var d=cur()==='dark';tb.setAttribute('aria-pressed',d?'true':'false');tb.setAttribute('aria-label',d?'Switch to light mode':'Switch to dark mode')}}
  if(tb){label();tb.addEventListener('click',function(){var n=cur()==='dark'?'light':'dark';root.setAttribute('data-theme',n);try{localStorage.setItem('theme',n)}catch(e){}label()})}
  // mobile menu
  var mb=document.getElementById('menu'),nav=document.getElementById('nav');
  if(mb&&nav)mb.addEventListener('click',function(){var o=nav.classList.toggle('open');mb.setAttribute('aria-expanded',o?'true':'false')});
  // directory filter (homepage)
  var q=document.getElementById('q');if(!q)return;
  var fv='',fu='',cards=[].slice.call(document.querySelectorAll('.grid .card')),cnt=document.getElementById('count'),empty=document.getElementById('empty');
  function f(){var s=q.value.toLowerCase().trim(),n=0;cards.forEach(function(c){var ok=(!s||c.dataset.n.indexOf(s)>-1)&&(!fv||c.dataset.v.split(' ').indexOf(fv)>-1)&&(!fu||c.dataset.u.split(' ').indexOf(fu)>-1);c.style.display=ok?'':'none';if(ok)n++});
    if(cnt)cnt.textContent='Showing '+n+' tool'+(n===1?'':'s');if(empty)empty.hidden=n>0}
  function chips(attr,set){[].forEach.call(document.querySelectorAll('[data-'+attr+']'),function(b){b.addEventListener('click',function(){[].forEach.call(document.querySelectorAll('[data-'+attr+']'),function(x){x.setAttribute('aria-pressed','false')});b.setAttribute('aria-pressed','true');set(b.getAttribute('data-'+attr));f()})})}
  chips('fv',function(v){fv=v});chips('fu',function(v){fu=v});
  q.addEventListener('input',f);
  var r=document.getElementById('reset');if(r)r.addEventListener('click',function(){q.value='';fv='';fu='';[].forEach.call(document.querySelectorAll('[data-fv],[data-fu]'),function(x){x.setAttribute('aria-pressed',x.getAttribute('data-fv')===''||x.getAttribute('data-fu')===''?'true':'false')});f();q.focus()});
  document.addEventListener('keydown',function(e){if(e.key==='/'&&document.activeElement!==q&&!/input|textarea|select/i.test(document.activeElement.tagName)){e.preventDefault();q.focus()}});
})();
