(function(){
  // Language is fixed per URL (/ = FR, /en/ = EN); this only localises a few dynamic bits.
  var l=document.documentElement.dataset.lang||'fr';
  document.querySelectorAll('[data-ph-en]').forEach(function(i){if(l==='en')i.placeholder=i.dataset.phEn;});
  document.querySelectorAll('select option[data-en]').forEach(function(o){if(l==='en')o.textContent=o.dataset.en;});
  if(window.renderTable)window.renderTable();
})();
