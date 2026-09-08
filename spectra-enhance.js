(function(){
'use strict';

function txt(el){return (el.textContent||'').trim()}
function semanticText(svg){
  var f=svg.closest('figure');
  var scope=f||svg.parentElement;
  return ((scope&&scope.textContent)||'')+' '+Array.from(svg.querySelectorAll('text')).map(txt).join(' ');
}
function isRaman(svg){
  return /(Raman|拉曼|wavenumber|波數|cm\s*[⁻-]?\s*[¹1])/i.test(semanticText(svg));
}

function enhance(svg){
  if(svg.dataset.spectraReady||!isRaman(svg))return;
  svg.dataset.spectraReady='1';
  svg.classList.add('spectra-enhanced');

  /*
   * Important: do NOT rebuild the x-axis and do NOT calculate a synthetic
   * cursor value from the visual positions of the tick-label text.  In these
   * teaching SVGs the tick text is manually offset for readability, so using
   * its bounding-box centre as a calibration point shifts the inferred Raman
   * value (for example, a labelled 1380 cm⁻¹ peak could be read as ~1328).
   * Keep the author-supplied peak labels and x-axis unchanged.
   */

  var axisTitle=null;
  Array.from(svg.querySelectorAll('text')).forEach(function(e){
    var q=txt(e);
    if(!axisTitle && /Raman\s*(shift)?|拉曼位移|wavenumber|波數/i.test(q) && /(cm|shift|位移|wavenumber|波數)/i.test(q)){
      axisTitle=e;
    }
  });

  /* Only solve the real layout issue: axis title overlapping tick numbers. */
  if(axisTitle){
    var vb=svg.viewBox && svg.viewBox.baseVal;
    var oldH=vb && vb.height ? vb.height : null;
    var y=parseFloat(axisTitle.getAttribute('y'));
    if(oldH && Number.isFinite(y) && y>oldH-24){
      svg.setAttribute('viewBox', [vb.x,vb.y,vb.width,oldH+28].join(' '));
      axisTitle.setAttribute('y', String(oldH+18));
    }
  }

  var fig=svg.closest('figure');
  if(fig && !fig.querySelector('.spectra-help')){
    var h=document.createElement('div');
    h.className='spectra-help';
    h.innerHTML='📌 <b>讀圖方式：</b>紅色數字是教材已標示的實測 peak Raman shift；保留原始 x 軸，不再用游標重新推算數值，避免因 SVG 文字位置偏移造成讀值錯誤。';
    fig.appendChild(h);
  }
}

function run(){document.querySelectorAll('svg').forEach(enhance)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
new MutationObserver(run).observe(document.documentElement,{childList:true,subtree:true});
})();
