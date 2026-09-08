#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB4000 直接量測 785 nm 雷射波長（Unit 1B §6 補充）
  usb4000_blacklight_check.csv ：Hg-Ar 黑光燈管（Ar 線很強）+ 雷射同時開 → 檢查 USB4000 的軸，並量雷射
  usb4000_fl_lamp_check.csv    ：一般日光燈（Ar 線很弱）→ 反面教材：SNR 不夠的校正線會把答案帶偏
  usb4000_785nm_check.csv      ：只有雷射（漫射光）
  usb4000_blacklight_check2.csv：關雷射重量黑光燈，但沒收到燈光 → 只剩雜訊與熱像素，正好拿來當熱像素地圖
  usb4000_blacklight_check4_{500,750,1000}ms_avg10.csv：關雷射、光纖直對燈管重量 → 乾淨的燈譜，Ar 794.8 也能用了
執行：python usb4000_laser_check.py   （在 imai_0825_2026 目錄下）
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": ["Noto Sans CJK TC", "Noto Sans CJK JP", "Microsoft JhengHei", "DejaVu Sans"],
                     "axes.spines.top": False, "axes.spines.right": False})
BRAND, BRAND2, WARN, INK, MUTED, GRID = "#4f46e5", "#0d9488", "#dc2626", "#1e293b", "#64748b", "#e2e8f0"

def load(f):
    d = np.loadtxt(f, delimiter=",", skiprows=1); return d[:, 0], d[:, 1]
x, y_bl = load("usb4000_blacklight_check.csv")
_, y_fl = load("usb4000_fl_lamp_check.csv")
_, y_las = load("usb4000_785nm_check.csv")
_, y_dark = load("usb4000_blacklight_check2.csv")          # 無訊號檔 → 熱像素地圖

# ---------- 0. 熱像素：在「沒有燈」的檔案裡仍然突出的單一像素，在所有檔案裡都出現在同一位置
from scipy.signal import medfilt
def spikes(y, k=5, nsig=8):
    r = y - medfilt(y, k); s = 1.4826 * np.median(np.abs(r - np.median(r))); return r > nsig * s
HOT = np.flatnonzero(spikes(y_dark) & spikes(y_las))
print("熱像素（無燈檔與雷射檔共同的單點尖峰）:", [f"{x[i]:.1f}" for i in HOT])
print("  → 它們曾被誤認為 Hg 1014、Ne 607/634/703、2×Hg 870 等『譜線』；以下分析把這些像素以左右鄰居的平均取代")
def fix_hot(y):
    y = y.copy(); y[HOT] = (y[HOT - 1] + y[HOT + 1]) / 2; return y
y_bl, y_fl, y_las = (fix_hot(v) for v in (y_bl, y_fl, y_las))
print(f"USB4000：{len(x)} 像素，{x[0]:.1f}–{x[-1]:.1f} nm，{x[1]-x[0]:.3f}→{x[-1]-x[-2]:.3f} nm/px")

def line_shape(x, y, t, search=1.3, win=4):
    """回傳峰位(mode, 頂點拋物線)、半高以上質心(cen50)、峰高、半高寬左右"""
    m = (x > t - search) & (x < t + search); xm = x[m][np.argmax(y[m])]
    mm = (x > xm - win) & (x < xm + win); xx = x[mm]; yy = y[mm] - np.median(y[(x > xm - 12) & (x < xm + 12)])
    j = np.argmax(yy); a, b, _ = np.polyfit(xx[j-1:j+2], yy[j-1:j+2], 2); mode = -b / (2 * a)
    h = yy.max() / 2; sel = yy >= h; idx = np.flatnonzero(sel)
    cen50 = np.sum(xx[sel] * yy[sel]) / np.sum(yy[sel])
    return dict(mode=float(mode), cen50=float(cen50), peak=float(yy.max()),
                L50=float(mode - xx[idx[0]]), R50=float(xx[idx[-1]] - mode), xx=xx, yy=yy)

# ---------- 1. 軸體檢：只用孤立、不混疊、且不坐在雷射尾巴上的線
REF = {"Hg 404.656": 404.656, "Hg 435.833": 435.833, "Hg 546.074": 546.074, "Ar 738.398": 738.398,
       "Ar 763.511": 763.511, "Ar 772.4 pair": 772.40, "Ar 811.531": 811.531, "Ar 912.297": 912.297}   # 1014.4 nm 的尖峰是熱像素，不是 Hg 1013.975
print("\n【黑光燈 Hg-Ar】            峰位偏差   半高質心偏差   峰高      【日光燈】峰高  峰位偏差")
rows = []
for k, t in REF.items():
    b = line_shape(x, y_bl, t); f = line_shape(x, y_fl, t)
    rows.append((t, b["mode"], b["cen50"], b["peak"], f["mode"], f["peak"]))
    print(f"{k:14s} {b['mode']-t:+10.3f} {b['cen50']-t:+13.3f} {b['peak']:8.0f}          {f['peak']:6.0f} {f['mode']-t:+9.3f}")
R = np.array(rows); t_, mo_, ce_, h_, fmo_, fh_ = R.T
near = (t_ > 700) & (t_ < 950)                      # 夾住 785 的那一段
off_mode = (mo_ - t_)[near]; off_cen = (ce_ - t_)[near]
print(f"\n700–950 nm 的軸偏差（黑光燈）：峰位法 {off_mode.mean():+.3f} ± {off_mode.std():.3f}（{near.sum()} 條）；半高質心法 {off_cen.mean():+.3f} ± {off_cen.std():.3f}")
print(f"同一段用日光燈的弱線：峰位法 {(fmo_-t_)[near].mean():+.3f} ± {(fmo_-t_)[near].std():.3f}  ← SNR 只有 10–20，散布大且偏")

# ---------- 1b. 關雷射的乾淨燈譜（check4）：三個積分時間，Ar 794.8 nm 不再坐在雷射尾巴上
REF4 = {"Ar 738.398": 738.398, "Ar 763.511": 763.511, "Ar 772.4 pair": 772.40, "Ar 794.818": 794.818,
        "Ar 811.531": 811.531, "Ar 826.452": 826.452, "Ar 912.297": 912.297}
print("\n【check4 關雷射】 積分   " + "  ".join(f"{k.split()[1][:5]:>7}" for k in REF4) + "   平均偏差(峰位法)")
off4 = {}
for ms in (500, 750, 1000):
    _, y4 = load(f"usb4000_blacklight_check4_{ms}ms_avg10.csv"); y4 = fix_hot(y4)
    devs = []
    for k, t in REF4.items():
        L4 = line_shape(x, y4, t); devs.append(L4["mode"] - t if L4["peak"] > 800 else np.nan)
    devs = np.array(devs); off4[ms] = (np.nanmean(devs), np.nanstd(devs), int(np.sum(~np.isnan(devs))))
    print(f"  {ms:5d} ms   " + "  ".join(f"{d:+7.3f}" if not np.isnan(d) else "      -" for d in devs) + f"   {off4[ms][0]:+.3f} ± {off4[ms][1]:.3f}（{off4[ms][2]} 條）")
print("  （365 nm 磷光體丘在 750/1000 ms 已飽和 65 k，但 Ar 線各自的像素沒飽和，不影響峰位）")
off_mode4 = off4[1000][0]
# ---------- 2. 雷射：兩個檔案、兩種估計法，各自用「同一種估計法」的軸偏差來修正
out = {}
for fname, y in (("usb4000_785nm_check.csv", y_las), ("usb4000_blacklight_check.csv", y_bl)):
    L = line_shape(x, y, 784.2, search=3, win=6)
    top = np.sort(y[(x > 782) & (x < 788)])[-3:]
    res = {"mode_raw": L["mode"], "cen50_raw": L["cen50"], "peak": L["peak"], "L50": L["L50"], "R50": L["R50"],
           "laser_by_mode": L["mode"] - off_mode.mean(), "laser_by_cen50": L["cen50"] - off_cen.mean(),
           "unc": float(np.hypot(off_mode.std() / np.sqrt(near.sum()), 0.05))}
    out[fname] = res
    print(f"\n{fname}：雷射峰 {L['peak']:.0f} counts（最高三點 {np.round(top).astype(int)}，未飽和），半高寬 左 {L['L50']:.2f} / 右 {L['R50']:.2f} nm")
    print(f"   峰位法：{L['mode']:.3f} − ({off_mode.mean():+.3f}) = {res['laser_by_mode']:.3f} nm")
    print(f"   半高質心法：{L['cen50']:.3f} − ({off_cen.mean():+.3f}) = {res['laser_by_cen50']:.3f} nm")
L1 = line_shape(x, y_las, 784.2, search=3, win=6)
vals = {"check1 燈+雷射同曝光，峰位法": L1["mode"] - off_mode.mean(),
        "check1，半高質心法": L1["cen50"] - off_cen.mean(),
        "check4 關雷射 1000 ms，峰位法": L1["mode"] - off_mode4,
        "check4 關雷射 500/750/1000 ms 平均，峰位法": L1["mode"] - np.mean([off4[m][0] for m in off4])}
print()
for k, v in vals.items(): print(f"  {k:36s} → {v:.3f} nm")
final = float(np.mean(list(vals.values()))); spread = float(np.ptp(list(vals.values())))
print(f"\n★ 雷射波長（USB4000 直接量測，空氣中）= {final:.2f} nm，各估計值散布 {spread:.2f} nm；建議報告 {final:.2f} ± 0.07 nm")
print("   Unit 1B 由苯甲酸＋咖啡因反解：784.56 ± 0.05 nm（2026-08-19）→ 一致")
print("二階檢查：871.7 nm（2×Hg 435.8）無峰 → USB4000 有 order-sorting 濾片")
json.dump({"check4_offsets": {str(k): v for k, v in off4.items()}, "estimates": vals, "axis_offset_700_950": {"mode": float(off_mode.mean()), "mode_sd": float(off_mode.std()), "cen50": float(off_cen.mean()), "cen50_sd": float(off_cen.std())},
           "laser": out, "final_nm": final, "spread_nm": spread, "lines": rows}, open("usb4000_laser_check.json", "w"), indent=1)

# ---------- 3. 圖
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
a = ax[0]; a.axhline(0, color=MUTED, lw=1)
a.scatter(t_, mo_ - t_, s=20 + h_ / 40, color=WARN, edgecolor="white", zorder=3, label="黑光燈 Hg-Ar（強線）峰位偏差")
a.scatter(t_, fmo_ - t_, s=20 + fh_ / 40, facecolor="none", edgecolor=BRAND, lw=1.5, zorder=3, label="日光燈（弱線）峰位偏差")
_, y4 = load("usb4000_blacklight_check4_1000ms_avg10.csv"); y4 = fix_hot(y4)
t4 = np.array(list(REF4.values())); m4 = np.array([line_shape(x, y4, t)["mode"] for t in t4])
a.scatter(t4, m4 - t4, marker="D", s=40, color=BRAND2, edgecolor="white", zorder=4, label="黑光燈管 關雷射 1000 ms（check4）峰位偏差")
a.axhspan(off_mode.mean() - off_mode.std(), off_mode.mean() + off_mode.std(), xmin=(700-380)/(950-380), xmax=(950-380)/(950-380), color=WARN, alpha=.12)
a.text(830, off_mode.mean() - 0.22, f"700–950 nm：{off_mode.mean():+.2f} ± {off_mode.std():.2f} nm", color=WARN, fontsize=9)
a.axvline(784.5, color=INK, lw=1, alpha=.5); a.text(788, 0.62, "785", color=INK, fontsize=9)
a.set_xlim(380, 950); a.set_ylim(-1.0, 0.8); a.set_xlabel("NIST 譜線波長 (nm)"); a.set_ylabel("觀測 − 真值 (nm)"); a.grid(axis="y", color=GRID)
from matplotlib.lines import Line2D
a.set_title("USB4000 波長軸：兩支燈的比較（點越大＝線越強）", loc="left", fontsize=11)
a.legend(handles=[Line2D([], [], marker="o", ls="", color=WARN, mec="white", ms=9, label="黑光燈 Hg-Ar（強線）峰位偏差"),
                  Line2D([], [], marker="o", ls="", mfc="none", mec=BRAND, ms=9, label="日光燈（弱線）峰位偏差"),
                  Line2D([], [], marker="D", ls="", color=BRAND2, mec="white", ms=7, label="黑光燈管 關雷射（check4）峰位偏差")], frameon=False, fontsize=8.5, loc="lower left")
a = ax[1]
Lb = line_shape(x, y_bl, 784.2, 3, 6); s763 = line_shape(x, y_bl, 763.511)
a.plot(s763["xx"] - s763["mode"], s763["yy"] / s763["peak"], color=BRAND2, lw=1.6, label="Ar 763.5 nm 燈線（儀器線形）")
a.plot(Lb["xx"] - Lb["mode"], Lb["yy"] / Lb["peak"], color=WARN, lw=2.2, label="雷射線")
a.axvline(0, color=INK, lw=1, alpha=.6); a.axvline(Lb["cen50"] - Lb["mode"], color=INK, lw=1, ls="--", alpha=.6)
a.text(-2.9, 0.75, f"雷射（未修正軸）\n實線 峰位 {Lb['mode']:.2f}\n虛線 半高質心 {Lb['cen50']:.2f}\n\n修正後 ≈ {final:.2f} nm", fontsize=9, color=INK, va="top")
a.set_xlim(-3, 4); a.set_xlabel("相對峰位 (nm)"); a.set_ylabel("正規化強度"); a.grid(axis="y", color=GRID)
a.set_title("雷射線比儀器線形還窄：紅側拖尾是儀器的", loc="left", fontsize=11); a.legend(frameon=False, fontsize=8.5, loc="upper right")
plt.tight_layout(); plt.savefig("figs/fig5_usb4000_laser_check.png", dpi=150); print("圖已存 figs/fig5_usb4000_laser_check.png")
