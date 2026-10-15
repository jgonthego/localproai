const q=document.getElementById('q'),fv=document.getElementById('fv'),fu=document.getElementById('fu');
function f(){const s=q.value.toLowerCase();document.querySelectorAll('.card').forEach(c=>{c.style.display=(!s||c.dataset.n.includes(s))&&(!fv.value||c.dataset.v.split(' ').includes(fv.value))&&(!fu.value||c.dataset.u.split(' ').includes(fu.value))?'':'none'})}
[q,fv,fu].forEach(el=>el.addEventListener('input',f));
