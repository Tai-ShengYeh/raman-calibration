(function(){
'use strict';
var NS='http://www.w3.org/2000/svg';
function n(s){var v=parseFloat((s||'').replace(/,/g,''));return Number.isFinite(v)?v:null}
function box(el){try{return el.getBBox()}catch(e){return null}}
function txt(el){return (el.textContent||'').trim()}
function semanticText(svg){var f=svg.closest('figure');var scope=f||svg.parentElement;return ((scope&&scope.textContent)||'')+' '+Array.from(svg.querySelectorAll('text')).map(txt).join(' ')}
function isRaman(svg){return /(Raman|拉曼|wavenumber|波數|cm\s*[⁻-]?\s*[¹1])/i.test(semanticText(svg))}
function svgSize(svg){var vb=svg.viewBox&&svg.viewBox.baseVal;return {w:(vb&&vb.width)||svg.clientWidth||800,h:(vb&&vb.height)||svg.clientHeight||450}}
function make(tag,attrs){var e=document.createElementNS(NS,tag);Object.keys(attrs||{}).forEach(function(k){e.setAttribute(k,attrs[k])});return e}
function enhance(svg){
 if(svg.dataset.spectraReady||!isRaman(svg))return;
 var s=svgSize(svg), texts=Array.from(svg.querySelectorAll('text')).map(function(e){return {e:e,b:box(e),v:n(txt(e))}}).filter(function(o){return o.b});
 var nums=texts.filter(function(o){return o.v!==null}); if(nums.length<2)return;
 var maxY=Math.max.apply(null,nums.map(function(o){return o.b.y+o.b.height}));
 var bottom=nums.filter(function(o){return (o.b.y+o.b.height)>maxY-12}).sort(function(a,b){return a.b.x-b.b.x});
 if(bottom.length<2)return;
 var ticks=[]; bottom.forEach(function(o){var cx=o.b.x+o.b.width/2;if(!ticks.length||Math.abs(cx-ticks[ticks.length-1].x)>8)ticks.push({x:cx,v:o.v,e:o.e,b:o.b})});
 if(ticks.length<2)return;
 var first=ticks[0],last=ticks[ticks.length-1], dv=last.v-first.v, dx=last.x-first.x;
 if(!dx||!dv||Math.abs(dv)<100)return;
 svg.dataset.spectraReady='1'; svg.classList.add('spectra-enhanced');
 ticks.forEach(function(t){t.e.dataset.spectraXTick='1'});
 var axisY=Math.min.apply(null,ticks.map(function(t){return t.b.y}));
 var plotTexts=texts.filter(function(o){return o.b.y<axisY-12});
 var topY=plotTexts.length?Math.max(8,Math.min.apply(null,plotTexts.map(function(o){return o.b.y}))):10;
 Array.from(svg.querySelectorAll('text')).forEach(function(e){var q=txt(e);if(/Raman\s*(shift)?|拉曼位移|wavenumber|波數/i.test(q)&&/(cm|shift|位移|wavenumber|波數)/i.test(q)){var b=box(e);if(b&&b.y>=axisY-4&&!e.dataset.axisShift){var old=e.getAttribute('transform')||'';e.setAttribute('transform',(old+' translate(0 16)').trim());e.dataset.axisShift='1'}}});
 var grid=make('g',{'class':'spectra-grid-layer','aria-hidden':'true'}); svg.insertBefore(grid,svg.firstChild);
 function xFor(v){return first.x+(v-first.v)*dx/dv}
 ticks.forEach(function(t){grid.appendChild(make('line',{x1:t.x,y1:topY,x2:t.x,y2:axisY-2,'class':'spectra-grid-major'}))});
 var lo=Math.min(first.v,last.v),hi=Math.max(first.v,last.v); if(hi-lo<=5000){var start=Math.ceil(lo/100)*100;for(var v=start;v<=hi;v+=100){var near=ticks.some(function(t){return Math.abs(t.v-v)<25});if(!near){var x=xFor(v);if(x>=Math.min(first.x,last.x)&&x<=Math.max(first.x,last.x))grid.appendChild(make('line',{x1:x,y1:topY,x2:x,y2:axisY-2,'class':'spectra-grid-minor'}))}}}
 var reader=make('g',{'class':'spectra-reader','aria-hidden':'true',visibility:'hidden'}),line=make('line',{y1:topY,y2:axisY-2,'class':'spectra-reader-line'}),dot=make('circle',{r:4,'class':'spectra-reader-dot'}),bg=make('rect',{width:112,height:26,'class':'spectra-reader-label-bg'}),label=make('text',{'class':'spectra-reader-label','text-anchor':'middle','dominant-baseline':'middle'}); reader.append(line,dot,bg,label); svg.appendChild(reader);
 function valFor(x){return first.v+(x-first.x)*dv/dx}
 function localX(ev){var p=svg.createSVGPoint();p.x=ev.clientX;p.y=ev.clientY;var m=svg.getScreenCTM();if(!m)return null;return p.matrixTransform(m.inverse()).x}
 function show(x,pin){var minX=Math.min(first.x,last.x),maxX=Math.max(first.x,last.x);x=Math.max(minX,Math.min(maxX,x));var v=valFor(x);line.setAttribute('x1',x);line.setAttribute('x2',x);dot.setAttribute('cx',x);dot.setAttribute('cy',axisY-3);var lx=Math.max(minX+56,Math.min(maxX-56,x));bg.setAttribute('x',lx-56);bg.setAttribute('y',topY+5);label.setAttribute('x',lx);label.setAttribute('y',topY+18);label.textContent=v.toFixed(Math.abs(v)<100?1:0)+' cm⁻¹';reader.setAttribute('visibility','visible');if(pin)svg.dataset.spectraPinned='1'}
 svg.addEventListener('pointermove',function(ev){if(svg.dataset.spectraPinned)return;var x=localX(ev);if(x!==null)show(x,false)});
 svg.addEventListener('pointerleave',function(){if(!svg.dataset.spectraPinned)reader.setAttribute('visibility','hidden')});
 svg.addEventListener('click',function(ev){var x=localX(ev);if(x===null)return;if(svg.dataset.spectraPinned){delete svg.dataset.spectraPinned;reader.setAttribute('visibility','hidden')}else show(x,true)});
 var fig=svg.closest('figure');if(fig&&!fig.querySelector('.spectra-help')){var h=document.createElement('div');h.className='spectra-help';h.innerHTML='🔎 <b>Peak reader：</b>滑鼠／手指移動可直接讀取 Raman shift；點一下固定垂直線，再點一次解除。淡色格線每 100 cm⁻¹，方便比對峰位。';fig.appendChild(h)}
}
function run(){document.querySelectorAll('svg').forEach(enhance)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
new MutationObserver(run).observe(document.documentElement,{childList:true,subtree:true});
})();