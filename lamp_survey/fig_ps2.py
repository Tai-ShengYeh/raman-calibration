import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams['font.family']=['Noto Sans CJK JP','DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False
IND,TEAL,RED,GREY='#4f46e5','#0d9488','#dc2626','#6b7280'
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
def A_of(n):
    S=rd(d+f'avantes_{n}.csv')[:,1]-yd
    return -np.log10(np.clip(S,1,None)/np.clip(R,1,None))
fig,ax=plt.subplots(1,3,figsize=(15.5,4.4))
for n,col,lab in (('PS_check_2',TEAL,'PS 薄（1 層）'),('PS2_check_2',IND,'PS2 厚（≈1.4×）')):
    A=A_of(n); b=((x>1085)&(x<1122))|((x>1180)&(x<1215))
    c=np.polyfit(x[b],A[b],1)
    ax[0].plot(x,A-np.polyval(c,x),'o-',color=col,ms=3.5,lw=1.0,label=lab)
ax[0].axvline(1143.0,color=GREY,ls='--',lw=1.2); ax[0].text(1143,0.093,'認證 1143.0',fontsize=8,color=GREY,ha='center')
ax[0].set_xlim(1090,1215); ax[0].set_ylim(-0.035,0.10); ax[0].set_xlabel('波長 (nm)'); ax[0].set_ylabel('吸收度（局部基線已扣）')
ax[0].legend(fontsize=8.5); ax[0].set_title('(a) 1143 帶：加厚後終於出得來（0.054 → 0.069 A）',fontsize=10)
for n,col,lab in (('PS_check_2',TEAL,'PS 薄'),('PS2_check_2',IND,'PS2 厚')):
    A=A_of(n); b=((x>1640)&(x<1664))|((x>1699)&(x<1730))
    c=np.polyfit(x[b],A[b],1)
    ax[1].plot(x,A-np.polyval(c,x),'o-',color=col,ms=3.5,lw=1.0,label=lab)
ax[1].axvline(1680.0,color=GREY,ls='--',lw=1.2); ax[1].text(1680,0.52,'認證 1680.0',fontsize=8,color=GREY,ha='center')
ax[1].set_xlim(1640,1730); ax[1].set_ylim(-0.10,0.56); ax[1].set_xlabel('波長 (nm)'); ax[1].set_ylabel('吸收度')
ax[1].legend(fontsize=8.5); ax[1].set_title('(b) 1680 帶：0.294 → 0.414 A，峰位不隨厚度改變',fontsize=10)
tr=np.array([1143.0,1680.0]); dv=np.array([1.19,1.23]); sd=np.array([1.13,0.59])
ax[2].errorbar(tr,dv,yerr=sd,fmt='o',color=RED,ms=9,capsize=6,lw=1.6,label='PS 帶（6 檔 × 6 種基線設定）')
ax[2].axhline(1.21,color=RED,lw=1.4,ls='-',label='平均偏移 +1.21 nm')
ax[2].axhline(0,color='k',lw=0.8)
ax[2].fill_between([1100,1720],1.21-0.9,1.21+0.9,color=RED,alpha=0.10)
ax[2].set_xlim(1100,1720); ax[2].set_ylim(-0.6,2.9)
ax[2].set_xlabel('真實波長 (nm)'); ax[2].set_ylabel('報告 − 真實 (nm)')
ax[2].legend(fontsize=8.5,loc='lower right')
ax[2].text(1150,2.55,'斜率 +74 ± 2378 ppm ⇒ 不顯著\n此法無法判斷有無色散誤差',fontsize=9,color=GREY)
ax[2].set_title('(c) 兩帶偏差一致 ⇒ 純平移 +1.2 nm（約 0.4 像素）',fontsize=10)
plt.tight_layout(); plt.savefig('avantes_nir_ps2.png',dpi=150)
