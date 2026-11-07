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
  // software cost worksheet (guide page). Sums only monthly figures already written in vendor pricing text.
  var calcRoot=document.getElementById('cost-calc');
  if(calcRoot){
    var raw=document.getElementById('calc-data');
    if(raw){
      var calcData=JSON.parse(raw.textContent);
      var vertSel=document.getElementById('calc-vert');
      var calcOut=document.getElementById('calc-out');
      function showVert(){
        var v=vertSel.value;
        [].forEach.call(calcRoot.querySelectorAll('.calc-vert'),function(el){el.hidden=el.getAttribute('data-vertical')!==v});
      }
      function toCents(s){
        var parts=String(s).split('.');
        var w=parseInt(parts[0],10)||0;
        var frac=(parts[1]||'');
        if(frac.length>2)frac=frac.slice(0,2);
        while(frac.length<2)frac+='0';
        return w*100+parseInt(frac,10);
      }
      function formatCents(c){
        var neg=c<0;if(neg)c=-c;
        var w=Math.floor(c/100),d=c%100,s='$'+w;
        if(d)s+='.'+(d<10?'0':'')+d;
        return (neg?'-':'')+s;
      }
      function addRow(tb,name,pricing,note){
        var tr=document.createElement('tr');
        var th=document.createElement('th');th.scope='row';th.textContent=name;
        var td1=document.createElement('td');td1.setAttribute('data-l','Pricing');td1.textContent=pricing;
        var td2=document.createElement('td');td2.setAttribute('data-l','Counted');td2.textContent=note;
        tr.appendChild(th);tr.appendChild(td1);tr.appendChild(td2);tb.appendChild(tr);
      }
      function estimate(){
        calcOut.textContent='';
        var counted=[],skipped=[],total=0;
        [].forEach.call(calcRoot.querySelectorAll('.calc-vert:not([hidden]) select'),function(sel){
          if(!sel.value)return;
          var t=calcData[sel.value];if(!t)return;
          if(t.basis==='none')skipped.push(t);
          else{total+=toCents(t.monthly||'0');counted.push(t)}
        });
        if(!counted.length&&!skipped.length){
          var p=document.createElement('p');p.className='prose';p.textContent='Choose a tool to add its stated monthly figure.';calcOut.appendChild(p);return;
        }
        var table=document.createElement('table');table.className='compare';
        var tb=document.createElement('tbody');
        counted.forEach(function(t){
          var note=t.basis==='free'
            ?'Counted as $0 because the sentence marks a free plan and does not state a monthly dollar amount.'
            :'First monthly dollar amount written in that sentence: '+formatCents(toCents(t.monthly));
          addRow(tb,t.name,t.pricing+' (checked '+t.checked+')',note);
        });
        skipped.forEach(function(t){addRow(tb,t.name,t.pricing+' (checked '+t.checked+')','Not added. The sentence does not state a monthly dollar amount.')});
        table.appendChild(tb);
        var wrap=document.createElement('div');wrap.className='tbl-wrap';wrap.appendChild(table);calcOut.appendChild(wrap);
        var sum=document.createElement('p');sum.className='prose';
        sum.textContent=counted.length?('Sum of those stated monthly figures: '+formatCents(total)+'. This is not a quote.'):'None of the selected sentences state a monthly dollar amount, so there is no total.';
        calcOut.appendChild(sum);
      }
      if(vertSel)vertSel.addEventListener('change',function(){showVert();estimate()});
      calcRoot.addEventListener('change',function(ev){if(ev.target!==vertSel&&ev.target.tagName==='SELECT')estimate()});
      var go=document.getElementById('calc-go');if(go)go.addEventListener('click',estimate);
      showVert();
    }
  }
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
