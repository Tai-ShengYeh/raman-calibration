(function(){
'use strict';
var NS='http://www.w3.org/2000/svg';
function n(s){var v=parseFloat((s||'').replace(/,/g,''));return Number.isFinite(v)?v:null}
function txt(el){return (el.textContent||'').trim()}
function rootBox(el,svg){
  try{
    var b=el.getBBox(),m=el.getCTM();
    if(!m)return b;
    var pts=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(function(p){var q=svg.createSVGPoint();q.x=p[0];q.y=p[1];return q.matrixTransform(m)});
    var xs=pts.map(function(p){return p.x}),ys=pts.map(function(p){return p.y});
    var x0=Math.min.apply(null,xs),x1=Math.max.apply(null,xs),y0=Math.min.apply(null,ys),y1=Math.max.apply(null,ys);
    return {x:x0,y:y0,width:x1-x0,height:y1-y0};
  }catch(e){return null}
}
function semanticText(svg){var f=svg.closest('figure');var scope=f||svg.parentElement;return ((scope&&scope.textContent)||'')+' '+Array.from(svg.querySelectorAll('text')).map(txt).join(' ')}
function isRaman(svg){return /(Raman|拉曼|wavenumber|波數|cm\s*[⁻-]?\s*[¹1])/i.test(semanticText(svg))}
function make(tag,attrs){var e=document.createElementNS(NS,tag);Object.keys(attrs||{}).forEach(function(k){e.setAttribute(k,attrs[k])});return e}
function chooseXAxis(nums){
  var groups=[];
  nums.forEach(function(o){var cy=o.b.y+o.b.height/2,g=groups.find(function(a){return Math.abs(a.y-cy)<7});if(!g){g={y:cy,a:[]};groups.push(g)}g.a.push(o)});
  var cand=[];
  groups.forEach(function(g){
    var a=g.a.slice().sort(function(x,y){return (x.b.x+x.b.width/2)-(y.b.x+y.b.width/2)});
    if(a.length<2)return;
    var filtered=[];a.forEach(function(o){var cx=o.b.x+o.b.width/2;if(!filtered.length||Math.abs(cx-(filtered[filtered.length-1].b.x+filtered[filtered.length-1].b.width/2))>8)filtered.push(o)});
    if(filtered.length<2)return;
    var xs=filtered.map(function(o){return o.b.x+o.b.width/2}),vs=filtered.map(function(o){return o.v});
    var inc=true,dec=true;for(var i=1;i<vs.length;i++){if(vs[i]<=vs[i-1])inc=false;if(vs[i]>=vs[i-1])dec=false}
    var span=Math.max.apply(null,xs)-Math.min.apply(null,xs),vr=Math.max.apply(null,vs)-Math.min.apply(null,vs);
    if((inc||dec)&&span>120&&vr>100)cand.push({ticks:filtered,span:span,vr:vr,y:g.y});
  });
  if(!cand.length)return null;
  cand.sort(function(a,b){return (b.span*b.ticks.length)-(a.span*a.ticks.length)});
  return cand[0].ticks;
}
function fitLinear(ticks){
  var pts=ticks.map(function(t){return {x:t.b.x+t.b.width/2,v:t.v}}),mx=0,mv=0;
  pts.forEach(function(p){mx+=p.x;mv+=p.v});mx/=pts.length;mv/=pts.length;
  var num=0,den=0;pts.forEach(function(p){num+=(p.x-mx)*(p.v-mv);den+=(p.x-mx)*(p.x-mx)});if(!den)return null;
  var slope=num/den,intercept=mv-slope*mx;
  var err=Math.sqrt(pts.reduce(function(s,p){var d=p.v-(intercept+slope*p.x);return s+d*d},0)/pts.length);
  var range=Math.max.apply(null,pts.map(function(p){return p.v}))-Math.min.apply(null,pts.map(function(p){return p.v}));
  if(!Number.isFinite(slope)||!Number.isFinite(intercept)||err>Math.max(3,range*0.015))return null;
  return {slope:slope,intercept:intercept,err:err};
}
function enhance(svg){
 if(svg.dataset.spectraReady||!isRaman(svg))return;
 var texts=Array.from(svg.querySelectorAll('text')).map(function(e){return {e:e,b:rootBox(e,svg),v:n(txt(e))}}).filter(function(o){return o.b});
 var nums=texts.filter(function(o){return o.v!==null}); if(nums.length<2)return;
 var ticks=chooseXAxis(nums); if(!ticks||ticks.length<2)return;
 var fit=fitLinear(ticks); if(!fit)return;
 var xs=ticks.map(function(t){return t.b.x+t.b.width/2}),minX=Math.min.apply(null,xs),maxX=Math.max.apply(null,xs);
 var vals=ticks.map(function(t){return t.v}),lo=Math.min.apply(null,vals),hi=Math.max.apply(null,vals);
 var axisY=Math.min.apply(null,ticks.map(function(t){return t.b.y}));
 var plotTexts=texts.filter(function(o){return o.b.y<axisY-12});
 var topY=plotTexts.length?Math.max(8,Math.min.apply(null,plotTexts.map(function(o){return o.b.y}))):10;
 svg.dataset.spectraReady='1'; svg.classList.add('spectra-enhanced');
 ticks.forEach(function(t){t.e.dataset.spectraXTick='1'});
 Array.from(svg.querySelectorAll('text')).forEach(function(e){var q=txt(e);if(/Raman\s*(shift)?|拉曼位移|wavenumber|波數/i.test(q)&&/(cm|shift|位移|wavenumber|波數)/i.test(q)){var b=rootBox(e,svg);if(b&&b.y>=axisY-4&&!e.dataset.axisShift){var old=e.getAttribute('transform')||'';e.setAttribute('transform',(old+' translate(0 16)').trim());e.dataset.axisShift='1'}}});
 var grid=make('g',{'class':'spectra-grid-layer','aria-hidden':'true'}); svg.insertBefore(grid,svg.firstChild);
 function xFor(v){return (v-fit.intercept)/fit.slope}
 ticks.forEach(function(t){var x=t.b.x+t.b.width/2;grid.appendChild(make('line',{x1:x,y1:topY,x2:x,y2:axisY-2,'class':'spectra-grid-major'}))});
 if(hi-lo<=5000){var start=Math.ceil(lo/100)*100;for(var v=start;v<=hi;v+=100){var near=ticks.some(function(t){return Math.abs(t.v-v)<25});if(!near){var x=xFor(v);if(x>=minX&&x<=maxX)grid.appendChild(make('line',{x1:x,y1:topY,x2:x,y2:axisY-2,'class':'spectra-grid-minor'}))}}}
 var reader=make('g',{'class':'spectra-reader','aria-hidden':'true',visibility:'hidden'}),line=make('line',{y1:topY,y2:axisY-2,'class':'spectra-reader-line'}),dot=make('circle',{r:4,'class':'spectra-reader-dot'}),bg=make('rect',{width:124,height:26,'class':'spectra-reader-label-bg'}),label=make('text',{'class':'spectra-reader-label','text-anchor':'middle','dominant-baseline':'middle'}); reader.append(line,dot,bg,label); svg.appendChild(reader);
 function valFor(x){return fit.intercept+fit.slope*x}
 function localX(ev){var p=svg.createSVGPoint();p.x=ev.clientX;p.y=ev.clientY;var m=svg.getScreenCTM();if(!m)return null;return p.matrixTransform(m.inverse()).x}
 function show(x,pin){x=Math.max(minX,Math.min(maxX,x));var v=valFor(x);line.setAttribute('x1',x);line.setAttribute('x2',x);dot.setAttribute('cx',x);dot.setAttribute('cy',axisY-3);var lx=Math.max(minX+62,Math.min(maxX-62,x));bg.setAttribute('x',lx-62);bg.setAttribute('y',topY+5);label.setAttribute('x',lx);label.setAttribute('y',topY+18);label.textContent=v.toFixed(1)+' cm⁻¹';reader.setAttribute('visibility','visible');if(pin)svg.dataset.spectraPinned='1'}
 svg.addEventListener('pointermove',function(ev){if(svg.dataset.spectraPinned)return;var x=localX(ev);if(x!==null)show(x,false)});
 svg.addEventListener('pointerleave',function(){if(!svg.dataset.spectraPinned)reader.setAttribute('visibility','hidden')});
 svg.addEventListener('click',function(ev){var x=localX(ev);if(x===null)return;if(svg.dataset.spectraPinned){delete svg.dataset.spectraPinned;reader.setAttribute('visibility','hidden')}else show(x,true)});
 var fig=svg.closest('figure');if(fig&&!fig.querySelector('.spectra-help')){var h=document.createElement('div');h.className='spectra-help';h.innerHTML='🔎 <b>座標讀值器：</b>依圖上的 x 軸刻度重新校準後讀取 Raman shift；滑鼠／手指移動可讀值，點一下固定垂直線。這是座標讀值，不會自動判定峰頂。';fig.appendChild(h)}
}
function run(){document.querySelectorAll('svg').forEach(enhance)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
new MutationObserver(run).observe(document.documentElement,{childList:true,subtree:true});
})();