(function(){
  const A=window.A247.a, tb=document.querySelector('#t tbody');
  let key='p', asc=false;
  const lang=()=>document.documentElement.dataset.lang||'fr';
  const nf=()=>new Intl.NumberFormat(lang()==='en'?'en-US':'fr-FR',{style:'currency',currency:'USD',maximumFractionDigits:2});
  const na=()=>`<span class="unk">${lang()==='en'?'n/a':'n.d.'}</span>`;
  const pct=v=>{if(v==null)return na();const s=(v>=0?'+':'')+v.toFixed(2);return `<span class="${v>=0?'pos':'neg'}">${lang()==='en'?s+'%':s.replace('.',',')+' %'}</span>`};
  document.querySelector('#fam option[value=""]').dataset.en='All issuers';
  document.querySelector('#plat option[value=""]').dataset.en='All platforms';
  function val(a,k){if(k==='p')return a.p.length*1e6+(a.tp?1e3:0)+(a.pr!=null?1:0);if(k==='c')return a.c.length;if(k==='pr')return a.pr==null?null:a.pr;return a[k]}
  window.renderTable=function(){
    const q=document.getElementById('q').value.trim().toLowerCase(), fam=document.getElementById('fam').value,
      plat=document.getElementById('plat').value, onlyp=document.getElementById('onlyp').checked;
    let r=A.filter(a=>(!q||(a.s+' '+(a.u||'')+' '+(a.n||'')).toLowerCase().includes(q))&&(!fam||a.f===fam)&&(!plat||a.p.includes(plat))&&(!onlyp||a.tp!=null));
    r.sort((x,y)=>{let a=val(x,key),b=val(y,key);if(a==null&&b==null)return 0;if(a==null)return 1;if(b==null)return -1;
      if(typeof a==='string')return asc?a.localeCompare(b):b.localeCompare(a);return asc?a-b:b-a});
    const f=nf();
    tb.innerHTML=r.slice(0,600).map(a=>`<tr>
<td><a href="actif/${a.id}.html"><b>${a.u||''}</b></a></td><td class="hide-m">${(a.n||'').slice(0,34)}</td>
<td><a href="actif/${a.id}.html">${a.s}</a></td><td><span class="tag ${a.f==='xStocks'?'x':'o'}">${a.f==='xStocks'?'xStocks':'Ondo GM'}</span></td>
<td class="hide-m small">${a.c.slice(0,3).join(', ')}${a.c.length>3?' +'+(a.c.length-3):''}</td>
<td class="num">${a.tp!=null?f.format(a.tp):na()}<div class="small">${a.ts||''}${a.ll?' ⚠':''}</div></td>
<td class="num">${a.sp!=null?f.format(a.sp):na()}</td>
<td class="num">${pct(a.pr)}${a.sg?' <span class="warn" title="&gt;5 %">⚠</span>':''}</td>
<td>${a.p.map(p=>`<span class="pl ${p}">${p}</span>`).join('')||`<span class="small">${lang()==='en'?'not verified':'non vérifié'}</span>`}</td></tr>`).join('');
    document.getElementById('cnt').textContent=r.length+(lang()==='en'?' tokens':' tokens');
    document.querySelectorAll('th').forEach(t=>{t.classList.toggle('sorted',t.dataset.k===key);t.classList.toggle('asc',t.dataset.k===key&&asc)});
  };
  document.querySelectorAll('th').forEach(t=>t.onclick=()=>{if(key===t.dataset.k)asc=!asc;else{key=t.dataset.k;asc=['u','n','s','f'].includes(key)}renderTable()});
  ['q','fam','plat','onlyp'].forEach(id=>document.getElementById(id).addEventListener('input',renderTable));
  renderTable();
})();
