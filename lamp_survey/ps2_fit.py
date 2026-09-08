"""Avantes NIR (1003186U2)：用聚苯乙烯的 1143 與 1680 帶檢查波長軸。
兩種厚度 × 三次重覆 × 多組基線窗，用散布量化系統不確定度。"""
import numpy as np, json
def rd(f):
    r=[]
    for l in open(f,encoding='utf-8',errors='replace'):
        p=l.strip().split(',')
        if len(p)<2: continue
        try: r.append((float(p[0]),float(p[1])))
        except ValueError: pass
    return np.array(r)
d='/mnt/user-data/uploads/imai_0825_2026/'
dk=rd(d+'avantes_dark_check_1.csv'); x=dk[:,0]; yd=dk[:,1]
R=rd(d+'avantes_reference_check_1.csv')[:,1]-yd
FILES={'PS（薄）':['PS_check_1','PS_check_2','PS_check_3'],
       'PS2（厚）':['PS2_check_1','PS2_check_2','PS2_check_3']}
BANDS={'1143':dict(true=1143.0, peak=(1125,1178), bl=[(1085,1122),(1180,1215)]),
       '1680':dict(true=1680.0, peak=(1666,1697), bl=[(1640,1664),(1699,1730)])}
def locate(A,B,npts,shift):
    lo1,hi1=B['bl'][0]; lo2,hi2=B['bl'][1]
    b=((x>lo1+shift)&(x<hi1+shift))|((x>lo2+shift)&(x<hi2+shift))
    c=np.polyfit(x[b],A[b],1); Ac=A-np.polyval(c,x)
    w=(x>B['peak'][0])&(x<B['peak'][1]); xs,As=x[w],Ac[w]
    j=int(np.argmax(As)); k=npts//2
    l2,h2=max(0,j-k),min(len(xs),j+k+1)
    if h2-l2<3: return None,None
    a2,b2,_=np.polyfit(xs[l2:h2],As[l2:h2],2)
    return float(-b2/(2*a2)), float(As[j])
out={}
print(f'{"樣品":10s} {"帶":6s} {"頂點平均":>9s} {"重覆SD":>7s} {"基線/點數散布":>12s} {"峰高":>7s} {"報告−真實":>10s}')
for lab,names in FILES.items():
    for bk,B in BANDS.items():
        v=[];h=[]
        for n in names:
            S=rd(d+f'avantes_{n}.csv')[:,1]-yd
            A=-np.log10(np.clip(S,1,None)/np.clip(R,1,None))
            for npts in (3,5):
                for sh in (-6,0,6):
                    p,ht=locate(A,B,npts,sh)
                    if p: v.append(p); h.append(ht)
        v=np.array(v)
        # 重覆散布（同設定不同檔）
        rep=[]
        for npts in (3,5):
            for sh in (-6,0,6):
                q=[locate(-np.log10(np.clip(rd(d+f'avantes_{n}.csv')[:,1]-yd,1,None)/np.clip(R,1,None)),B,npts,sh)[0] for n in names]
                rep.append(np.std([z for z in q if z]))
        print(f'{lab:10s} {bk:6s} {v.mean():9.2f} {np.mean(rep)*1000:6.0f}pm {v.std()*1000:11.0f}pm {np.mean(h):7.3f} {v.mean()-B["true"]:+10.2f}')
        out.setdefault(bk,[]).extend(v.tolist())
print()
dev={}
for bk,v in out.items():
    v=np.array(v); dev[bk]=(v.mean(),v.std()); 
    print(f'{bk} 帶（兩種厚度全部合併，n={len(v)}）：{v.mean():.2f} ± {v.std():.2f} nm ⇒ 偏差 {v.mean()-BANDS[bk]["true"]:+.2f} nm')
d1,s1=dev['1143']; d2,s2=dev['1680']
off=((d1-1143)+(d2-1680))/2
slope=((d2-1680)-(d1-1143))/(1680-1143)
su=np.hypot(s1,s2)/(1680-1143)
print(f'\n平均偏移 = {off:+.2f} nm')
print(f'斜率 = {slope*1e6:+.0f} ± {su*1e6:.0f} ppm  ⇒ {"不顯著，視為純平移" if abs(slope)<2*su else "顯著"}')
json.dump(dict(serial='1003186U2',bands={k:dict(true=BANDS[k]["true"],obs=float(np.mean(out[k])),sd=float(np.std(out[k])),n=len(out[k])) for k in out},
               offset_nm=float(off),slope_ppm=float(slope*1e6),slope_unc_ppm=float(su*1e6)),
          open('avantes_nir_ps_fit.json','w'),indent=1)
