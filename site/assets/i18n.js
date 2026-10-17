(function(){
  function set(l){document.documentElement.dataset.lang=l;document.documentElement.lang=l;localStorage.setItem('a247lang',l);
    document.querySelectorAll('.lang button').forEach(b=>b.classList.toggle('on',b.dataset.l===l));
    document.querySelectorAll('[data-ph-en]').forEach(i=>{if(!i.dataset.phFr)i.dataset.phFr=i.placeholder;i.placeholder=l==='en'?i.dataset.phEn:i.dataset.phFr;});
    document.querySelectorAll('select option[data-en]').forEach(o=>{if(!o.dataset.fr)o.dataset.fr=o.textContent;o.textContent=l==='en'?o.dataset.en:o.dataset.fr;});
    if(window.renderTable)window.renderTable();}
  document.querySelectorAll('.lang button').forEach(b=>b.onclick=()=>set(b.dataset.l));
  set(document.documentElement.dataset.lang||'fr');
})();
