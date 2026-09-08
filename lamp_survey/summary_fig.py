import numpy as np, json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams['font.family']=['Noto Sans CJK JP','DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False
C={'q532':'#4f46e5','q785':'#0d9488','im':'#b45309','pg':'#dc2626','ham':'#7c3aed','usb':'#0891b2','av':'#65a30d'}
def lines(path,key='lines'):
    J=json.load(open(path)); L=J[key] if key in J else J
    return np.array([float(k) for k,v in L.items() if v.get('used',True)]), np.array([v['dev'] for v in L.items().__iter__().__next__() and [v for k,v in L.items() if v.get('used',True)]])
def get(path,sub=None):
    J=json.load(open(path))
    if sub: J=J[sub]
    L=J['lines']
    t=[];d=[]
    for k,v in L.items():
        if not v.get('used',True): continue
        t.append(float(k) if not k.replace('.','').isdigit() or True else float(k)); d.append(v['dev'])
    return np.array(t),np.array(d)
S=[]
t,d=get('/home/claude/r532/qepro532_ne_fit.json'); S.append(('QEPro-532',t,d,C['q532'],'o'))
t,d=get('/home/claude/ne785/ne785_fit.json','qepro785'); S.append(('QEPro-785',t,d,C['q785'],'s'))
t,d=get('/home/claude/ne785/ne785_fit.json','im2000');  S.append(('Im2000 Pro',t,d,C['im'],'^'))
t,d=get('/home/claude/pg2000/pg2000_ne_fit.json');      S.append(('PG2000-Pro',t,d,C['pg'],'v'))
t,d=get('/home/claude/two/two_fit.json','hamamatsu');   S.append(('Hamamatsu C10082CAH',t,d,C['ham'],'D'))
t,d=get('/home/claude/two/two_fit.json','usb2000');     S.append(('USB2000',t,d,C['usb'],'P'))
t,d=get('/home/claude/av/avantes_uvvis_fit.json');      S.append(('Avantes UV-Vis',t,d,C['av'],'X'))
fig,ax=plt.subplots(1,2,figsize=(15.5,5.6))
for a in ax:
    for lab,t,d,col,m in S:
        o=np.argsort(t)
        a.plot(t[o],d[o],m+'-',color=col,ms=5,lw=1.1,alpha=0.9,label=f'{lab}  ({len(t)} 線)')
    a.axhline(0,color='k',lw=0.8); a.grid(alpha=0.25); a.set_xlabel('真實波長 (nm)',fontsize=10.5)
ax[0].set_ylabel('報告 − 真實 (nm)',fontsize=10.5)
ax[0].legend(fontsize=8.5,loc='center right',framealpha=0.95)
ax[0].set_title('(a) 七台全貌：QEPro-532 偏 +8.3 nm，其餘在 ±3 nm 內',fontsize=11)
ax[0].annotate('C0 被填成標稱 532.000',xy=(640,8.3),xytext=(720,6.3),fontsize=9,color=C['q532'],
               arrowprops=dict(arrowstyle='->',color=C['q532']))
ax[1].set_ylim(-3.2,1.6); ax[1].set_ylabel('報告 − 真實 (nm)',fontsize=10.5)
ax[1].set_title('(b) 放大：只有 USB2000 的偏差隨波長變陡（色散誤差）',fontsize=11)
ax[1].annotate('USB2000\n−0.29 → −0.74 nm\n(+1749 ppm)',xy=(830,-0.70),xytext=(900,-1.9),
               fontsize=9,color=C['usb'],arrowprops=dict(arrowstyle='->',color=C['usb']))
ax[1].text(1020,0.55,'其餘六台都是水平線 ⇒ 純平移',fontsize=9.5,color='#374151')
fig.suptitle('一顆延長線氖燈，七台光譜儀的波長軸體檢（2026-09-07）',fontsize=13,y=0.99)
plt.tight_layout(rect=[0,0,1,0.96]); plt.savefig('all_instruments_summary.png',dpi=150)
