#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit 1B — 兩台 785 nm 拉曼光譜儀的體檢：波長軸、雷射波長與二階繞射
=====================================================================
執行方式：  python unit1b_calibration.py
需要套件：  numpy  pandas  scipy  matplotlib
輸入資料：  ./unit1b_data/*.csv  （見 README_unit1b_data.md）
輸出：      ./figs/*.png  與  ./unit1b_results.json

流程（對應教材章節）
  §3  用日光燈（Ar/Hg 放電）的原子譜線檢查 QEPro 的「像素→波長」軸
  §4  同一支燈檢查 Im2000 Pro：nm 軸與波數軸各自對不對？二階繞射在哪？
  §5  把 QEPro 的波數偏差拆成兩個來源：波長軸偏移 + 雷射波長設定
  §6  用苯甲酸與咖啡因兩個獨立樣品反解雷射實際波長 λ_L
  §7  校正後才做未知樣品辨識

所有「文獻峰位」都是常見文獻值，不是認證值；請保留原始檔，修正版另存。
"""
import json
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import minimize_scalar
from scipy import sparse
from scipy.sparse.linalg import spsolve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = "unit1b_data/"
FIG = "figs/"
LASER_NOMINAL = 785.000          # OceanView 與 IMSpectralSuite 都用這個標稱值算波數
INK, MUTED, GRID, SURF = "#1e293b", "#64748b", "#e2e8f0", "#ffffff"
BRAND, BRAND2, WARN = "#4f46e5", "#0d9488", "#dc2626"
plt.rcParams.update({"font.family": ["Noto Sans CJK TC", "Noto Sans CJK JP", "Microsoft JhengHei", "DejaVu Sans"],
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})
results = {}

# ---------------------------------------------------------------- 工具函式
def shift_from_wavelength(lam_nm, laser_nm):
    """波長 (nm) → 拉曼位移 (cm⁻¹)"""
    return 1e7 * (1.0 / laser_nm - 1.0 / lam_nm)

def wavelength_from_shift(shift, laser_nm):
    """拉曼位移 (cm⁻¹) → 波長 (nm)；是上式的反函數"""
    return 1.0 / (1.0 / laser_nm - shift * 1e-7)

def locate_lines(x, y, ref_lines, search_nm=2.5, half_nm=0.9):
    """
    兩段式找線：
      第 1 段：每條 NIST 線在 ±search_nm 內找最大值，取「偏移量的中位數」當粗略偏移
              （中位數對緊鄰雙線很穩：就算其中一條抓錯，也不會拉偏整體）
      第 2 段：以『真值 + 粗略偏移』為中心，用 ±half_nm 的強度加權質心精修每一條線
    回傳 [(觀測波長, 真值, 物種, 峰高), ...]
    """
    ts = ref_lines["wavelength_air_nm"].to_numpy()
    rough = []
    for t in ts:
        m = (x > t - search_nm) & (x < t + search_nm)
        if m.sum() >= 5:
            rough.append(x[m][np.argmax(y[m])] - t)
    rough = float(np.median(rough))
    out = []
    for t, sp in zip(ts, ref_lines["species"]):
        w = (x > t + rough - half_nm) & (x < t + rough + half_nm)
        if w.sum() < 3:
            continue
        yy = y[w] - y[w].min()
        out.append((float(np.sum(x[w] * yy) / np.sum(yy)), float(t), sp, float(y[w].max())))
    return out

def als_baseline(y, lam=1e5, p=0.01, n_iter=15):
    """非對稱最小平方基線（Eilers & Boelens）"""
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2), dtype=float)
    D = lam * D.dot(D.T)
    w = np.ones(L)
    for _ in range(n_iter):
        W = sparse.spdiags(w, 0, L, L)
        z = spsolve((W + D).tocsc(), w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return z

# ================================================================ §3 QEPro 波長軸體檢
print("=" * 70)
print("§3  QEPro：用 Ar/Hg 燈的原子譜線檢查『像素 → 波長』軸")
ref = pd.read_csv(DATA + "reference_lines_ArHg_NIST_air.csv")
ref_first = ref[~ref["species"].str.contains("2nd")]           # 一階線
lamp1 = pd.read_csv(DATA + "qepro_light1_ArHg_lamp.csv")
lamp2 = pd.read_csv(DATA + "qepro_light2_ArHg_lamp.csv")
lam_q = lamp1["wavelength_nm_reported"].to_numpy()
y_q = lamp1["counts"].to_numpy()

# 質心找峰 → 只配一階 Ar/Hg 線；light1 與 light2 用的是不同光纖
# 只用孤立、夠強、不與鄰線混疊的 12 條線（800.6/801.5 是一對緊鄰雙線，先不用）
USE_Q = [794.8176, 801.4786, 810.3693, 811.5311, 826.4522, 840.8210, 842.4648, 852.1442, 866.7944, 912.2967, 922.4499, 1013.975]
ref_q = ref_first[ref_first["wavelength_air_nm"].isin(USE_Q)]
# 檔案裡的峰大約比真值低 1 nm，所以搜尋窗要夠寬（±2.5 nm）
pairs_q = locate_lines(lam_q, y_q, ref_q, search_nm=2.5, half_nm=0.9)
obs_q = np.array([p[0] for p in pairs_q]); tru_q = np.array([p[1] for p in pairs_q])
dev_q = obs_q - tru_q
A_q, B_q = np.polyfit(obs_q, tru_q, 1)                            # λ_true = A·λ_reported + B
resid_q = tru_q - (A_q * obs_q + B_q)
print(f"  可用譜線 {len(pairs_q)} 條；平均偏差 {dev_q.mean():+.3f} nm（SD {dev_q.std():.3f}）")
print(f"  線性修正：λ_true = {A_q:.8f} × λ_reported + {B_q:.5f}   殘差 rms {resid_q.std()*1000:.0f} pm")
# 換光纖有沒有差？
pairs_q2 = locate_lines(lamp2["wavelength_nm_reported"].to_numpy(), lamp2["counts"].to_numpy(), ref_q, 2.5, 0.9)
fiber_diff = [o1 - o2 for (o1, *_), (o2, *_) in zip(pairs_q, pairs_q2)]
print(f"  light1 vs light2（不同光纖）峰位差：最大 {max(abs(v) for v in fiber_diff):.3f} nm → 光纖不影響波長軸")
results["qepro_lamp"] = {"n_lines": len(pairs_q), "mean_dev_nm": float(dev_q.mean()), "sd_dev_nm": float(dev_q.std()),
                         "A": float(A_q), "B": float(B_q), "resid_rms_pm": float(resid_q.std() * 1000),
                         "lines": [{"obs": float(o), "true": float(t), "species": s} for o, t, s, _ in pairs_q],
                         "fiber_max_diff_nm": float(max(abs(v) for v in fiber_diff))}

# ================================================================ §4 Im2000 Pro：nm 軸 vs 波數軸
print("=" * 70)
print("§4  Im2000 Pro：同一支燈，nm 軸與波數軸各自體檢")
im = pd.read_csv(DATA + "im2000_light_ArHg_lamp_axes.csv")
lam_i = im["wavelength_nm_reported"].to_numpy()
wn_i = im["raman_shift_reported_cm-1"].to_numpy()
y_i = im["counts_pixel_file"].to_numpy()
# Im2000 的檔案峰位比真值高約 1.4 nm；810.4 nm 一階 Ar 與 2×Hg 404.7 nm 重疊，不用；
# 兩條乾淨的二階 Hg 線（407.8×2、435.8×2）反而是很好的錨點
USE_I = [811.5311, 815.566, 826.4522, 840.8210, 842.4648, 852.1442, 871.666, 912.2967, 922.4499, 1013.975]
ref_i = ref[ref["wavelength_air_nm"].isin(USE_I)]
pairs_i = locate_lines(lam_i, y_i, ref_i, search_nm=2.6, half_nm=0.9)
obs_i = np.array([p[0] for p in pairs_i]); tru_i = np.array([p[1] for p in pairs_i])
dev_i = obs_i - tru_i
print(f"  nm 軸：{len(pairs_i)} 條線，偏差 {dev_i.mean():+.3f} nm（SD {dev_i.std():.3f}）→ nm 軸偏高")
# 波數軸：在同一像素位置取波數值，反推它隱含的雷射波長
wn_at_lines = np.interp(obs_i, lam_i, wn_i)
laser_implied = 1.0 / (wn_at_lines * 1e-7 + 1.0 / tru_i)
laser_im = laser_implied.mean()
lam_from_wn = wavelength_from_shift(np.interp(obs_i, lam_i, wn_i), laser_im)
resid_wn = lam_from_wn - tru_i
print(f"  波數軸隱含的雷射波長：{laser_im:.4f} ± {laser_implied.std():.4f} nm")
print(f"  用它反算波長，殘差 rms {resid_wn.std():.3f} nm ≈ {1e7*resid_wn.std()/880**2:.1f} cm⁻¹ → 波數軸是好的")
second = [(o, t, s) for o, t, s, _ in pairs_i if "2nd" in s]
print(f"  二階繞射線：{[(round(o,1), s) for o, t, s in second]}")
results["im2000"] = {"n_lines": len(pairs_i), "mean_dev_nm": float(dev_i.mean()), "sd_dev_nm": float(dev_i.std()),
                     "laser_implied_nm": float(laser_im), "laser_implied_sd": float(laser_implied.std()),
                     "wn_axis_resid_rms_nm": float(resid_wn.std()),
                     "lines": [{"obs": float(o), "true": float(t), "species": s, "resid_nm_axis": float(o - t),
                                "resid_wn_axis": float(r)} for (o, t, s, _), r in zip(pairs_i, resid_wn)]}

# ================================================================ §5–6 QEPro 拉曼樣品：拆解偏差、反解雷射波長
print("=" * 70)
print("§5–6  苯甲酸與咖啡因：把 −20 cm⁻¹ 拆成『波長軸』+『雷射波長』兩個來源")
lit = pd.read_csv(DATA + "reference_raman_peaks_literature.csv")
LIT = {c: g["raman_shift_literature_cm-1"].to_numpy() for c, g in lit.groupby("compound")}
ba = pd.read_csv(DATA + "qepro_benzoic_acid_3reps.csv")
un = pd.read_csv(DATA + "qepro_unknown_sample.csv")
x_rep = ba["raman_shift_reported_cm-1"].to_numpy()             # OceanView 報告的位移（用 785.000 算的）
lam_rep = wavelength_from_shift(x_rep, LASER_NOMINAL)          # 還原成 OceanView 的波長軸
lam_true = A_q * lam_rep + B_q                                 # 套用 §3 的燈校正

def peaks_of(y, prom=0.02):
    c = savgol_filter(y - als_baseline(y), 7, 3)
    out = []
    for i in find_peaks(c, prominence=prom * c.max(), distance=2)[0]:
        sl = slice(max(0, i - 2), i + 3); w = c[sl] - c[sl].min()
        out.append((float(np.sum(x_rep[sl] * w) / np.sum(w)), float(np.sum(lam_true[sl] * w) / np.sum(w)), 100 * c[i] / c.max()))
    return out, c

pk_ba, corr_ba = peaks_of(ba[["rep1", "rep2", "rep3"]].mean(axis=1).to_numpy())
pk_un, corr_un = peaks_of(un["counts"].to_numpy())

def assign(pk, ref_vals, laser, tol=16):
    """在指定雷射波長下，把觀測峰配到文獻峰"""
    out = []
    for rep, lt, I in pk:
        cs = shift_from_wavelength(lt, laser)
        d = np.abs(ref_vals - cs); j = int(d.argmin())
        if d[j] < tol:
            out.append({"reported": rep, "lambda_true": lt, "corrected": float(cs), "lit": float(ref_vals[j]), "I": I})
    return out

def fit_laser(pairs, reject_cm=5.0):
    """
    找一個雷射波長，使『燈校正後的波長』換算出的位移最貼近文獻峰。
    做兩輪：第一輪全部峰擬合；把殘差 > reject_cm 的峰（弱峰、肩峰、文獻值不確定者）剔除後再擬合一次。
    回傳 (λ_L, rms, 使用峰數, 被剔除的峰)
    """
    lt = np.array([p["lambda_true"] for p in pairs]); li = np.array([p["lit"] for p in pairs])
    cost = lambda L, m: np.sqrt(np.mean((shift_from_wavelength(lt[m], L) - li[m]) ** 2))
    keep = np.ones(len(pairs), bool)
    L1 = minimize_scalar(lambda L: cost(L, keep), bounds=(783.5, 786.0), method="bounded").x
    resid = shift_from_wavelength(lt, L1) - li
    keep = np.abs(resid) <= reject_cm
    L2 = minimize_scalar(lambda L: cost(L, keep), bounds=(783.5, 786.0), method="bounded").x
    dropped = [(round(float(li[i]), 0), round(float(resid[i]), 1)) for i in np.flatnonzero(~keep)]
    return float(L2), float(cost(L2, keep)), int(keep.sum()), dropped

pairs_ba = assign(pk_ba, LIT["benzoic acid"], 784.65)
pairs_caf = assign(pk_un, LIT["caffeine"], 784.65)
L_ba, rms_ba, n_ba, drop_ba = fit_laser(pairs_ba)
L_caf, rms_caf, n_caf, drop_caf = fit_laser(pairs_caf)
print(f"  苯甲酸 → λ_L = {L_ba:.3f} nm（{n_ba} 峰，rms {rms_ba:.2f} cm⁻¹；剔除 {drop_ba}）")
print(f"  咖啡因 → λ_L = {L_caf:.3f} nm（{n_caf} 峰，rms {rms_caf:.2f} cm⁻¹；剔除 {drop_caf}）")
# 合併擬合（兩個化學上無關的樣品共用同一個 λ_L）
LASER_FIT, rms_all, n_all, drop_all = fit_laser(pairs_ba + pairs_caf)
lt_all = np.array([p["lambda_true"] for p in pairs_ba + pairs_caf]); li_all = np.array([p["lit"] for p in pairs_ba + pairs_caf])
rms_785 = float(np.sqrt(np.mean((shift_from_wavelength(lt_all, 785.0) - li_all) ** 2)))
cost_all = lambda L: float(np.sqrt(np.mean((shift_from_wavelength(lt_all, L) - li_all) ** 2)))
print(f"  合併 → λ_L = {LASER_FIT:.3f} nm（{n_all} 峰，rms {rms_all:.2f} cm⁻¹；若硬用 785.000：rms {rms_785:.2f}）")

# 未校正的原始誤差（苯甲酸）
raw_err = [(p["reported"], p["lit"], p["reported"] - p["lit"]) for p in assign(pk_ba, LIT["benzoic acid"], LASER_FIT)]
print("  苯甲酸原始誤差（OceanView − 文獻）：", [round(e, 1) for _, _, e in raw_err])

# 兩個來源各貢獻多少？（在 1001 cm⁻¹ 這條峰上算）
lam_1001 = wavelength_from_shift(1001, LASER_FIT)
only_axis = shift_from_wavelength((lam_1001 - B_q) / A_q, LASER_FIT) - 1001     # 只有波長軸偏移
only_laser = shift_from_wavelength(lam_1001, LASER_NOMINAL) - 1001              # 只有雷射波長設錯
print(f"  在 1001 cm⁻¹：波長軸貢獻 {only_axis:+.1f}，雷射波長貢獻 {only_laser:+.1f}，合計 {only_axis+only_laser:+.1f} cm⁻¹")

results["laser"] = {"benzoic": float(L_ba), "caffeine": float(L_caf), "combined": float(LASER_FIT),
                    "rms_combined": rms_all, "rms_if_785": rms_785, "n_pairs": n_all,
                    "rms_benzoic": rms_ba, "rms_caffeine": rms_caf, "n_benzoic": n_ba, "n_caffeine": n_caf,
                    "dropped": drop_all, "contrib_axis_at_1001": float(only_axis), "contrib_laser_at_1001": float(only_laser)}
results["benzoic_table"] = assign(pk_ba, LIT["benzoic acid"], LASER_FIT)
results["caffeine_table"] = assign(pk_un, LIT["caffeine"], LASER_FIT)

# ================================================================ §7 未知樣品辨識
print("=" * 70)
print("§7  未知樣品是什麼？校正後才比對")
cands = {"caffeine": LIT["caffeine"],
         "acetaminophen": np.array([213, 329, 391, 465, 504, 651, 710, 798, 834, 858, 1105, 1169, 1236, 1278, 1323, 1371, 1516, 1561, 1611, 1648, 2931]),
         "benzoic acid": LIT["benzoic acid"]}
id_table = {}
for name, vals in cands.items():
    m = assign(pk_un, vals, LASER_FIT, tol=10)
    id_table[name] = {"matched": len(m), "of": len(pk_un), "mean_abs_err": float(np.mean([abs(p["corrected"] - p["lit"]) for p in m])) if m else None}
    print(f"  vs {name:14s}: {len(m)}/{len(pk_un)} 峰對上，平均 |誤差| {id_table[name]['mean_abs_err']}")
results["unknown_id"] = id_table

# ================================================================ 修正處方 & 存檔
results["recipe"] = {"lambda_true = A*lambda_reported + B": {"A": float(A_q), "B": float(B_q)},
                     "laser_nm": float(LASER_FIT), "note": "λ 皆為空氣中波長；套用時 OceanView 的雷射設定應為 785.000"}
un_out = un.copy()
un_out["wavelength_true_nm"] = A_q * wavelength_from_shift(un["raman_shift_reported_cm-1"], LASER_NOMINAL) + B_q
un_out["raman_shift_corrected_cm-1"] = shift_from_wavelength(un_out["wavelength_true_nm"], LASER_FIT)
un_out.to_csv("qepro_unknown_sample_CORRECTED.csv", index=False)      # 另存，不覆寫原始檔
with open("unit1b_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("=" * 70)
print(f"修正處方：λ_true = {A_q:.8f}·λ_reported + {B_q:.5f}；  ν̃ = 1e7·(1/{LASER_FIT:.3f} − 1/λ_true)")

# ================================================================ 圖
# 圖 1：QEPro 燈譜 + 譜線指認 + 偏差
fig, ax = plt.subplots(2, 1, figsize=(10, 6.6), height_ratios=[1.3, 1])
ax[0].plot(lam_q, y_q, lw=1, color=INK)
for o, t, s, h in pairs_q:
    ax[0].axvline(t, color=BRAND2, lw=.8, alpha=.5); ax[0].axvline(o, color=WARN, lw=.8, alpha=.5)
ax[0].set_yscale("log"); ax[0].set_ylim(80, 6e4); ax[0].set_xlim(783, 1032)
ax[0].set_ylabel("counts (log)"); ax[0].set_title("QEPro：日光燈（Ar/Hg）譜　綠＝NIST 譜線真值　紅＝檔案裡的峰位", loc="left", fontsize=11)
ax[1].axhline(0, color=MUTED, lw=1)
ax[1].plot(tru_q, dev_q, "o", color=WARN, ms=8, mec=SURF, label="檔案波長 − 真值")
ax[1].plot(tru_q, resid_q, "s", color=BRAND2, ms=7, mec=SURF, label="線性修正後殘差")
ax[1].set_xlim(783, 1032); ax[1].set_ylim(-1.4, 0.4)
ax[1].set_xlabel("NIST 譜線波長 (nm, 空氣)"); ax[1].set_ylabel("偏差 (nm)")
ax[1].legend(frameon=False, loc="lower right"); ax[1].grid(axis="y", color=GRID)
ax[1].text(785, -1.3, f"平均 {dev_q.mean():+.2f} nm ≈ {1e7*abs(dev_q.mean())/850**2:.0f} cm⁻¹", color=WARN)
plt.tight_layout(); plt.savefig(FIG + "fig1_qepro_lamp_check.png", dpi=150); plt.close()

# 圖 2：Im2000 Pro nm 軸 vs 波數軸
fig, ax = plt.subplots(2, 1, figsize=(10, 6.8), height_ratios=[1.3, 1])
ax[0].plot(lam_i, y_i, lw=1, color=INK); ax[0].set_yscale("log"); ax[0].set_ylim(80, 6e4); ax[0].set_xlim(789, 1120)
for o, t, s, h in pairs_i: ax[0].axvline(o, color=WARN if "2nd" in s else BRAND, lw=.8, alpha=.45)
ax[0].text(873, 2.6e4, "873 nm＝Hg 435.8 nm 的二階繞射", color=WARN, ha="center", fontsize=9.5)
ax[0].text(1093, 9e3, "綠色磷光體\n二階繞射", color=WARN, ha="center", fontsize=9.5)
ax[0].set_ylabel("counts (log)"); ax[0].set_title("Im2000 Pro：同一支燈　藍＝一階 Ar/Hg　紅＝二階", loc="left", fontsize=11)
ax[1].axhline(0, color=MUTED, lw=1)
ax[1].plot(tru_i, dev_i, "o-", color=BRAND, ms=7, mec=SURF, lw=1.8, label="nm 軸：檔案 − 真值")
ax[1].plot(tru_i, resid_wn, "s-", color=BRAND2, ms=7, mec=SURF, lw=1.8, label=f"波數軸→nm（λ_L={laser_im:.2f}）− 真值")
ax[1].set_xlim(789, 1120); ax[1].set_ylim(-0.5, 2.0); ax[1].grid(axis="y", color=GRID)
ax[1].set_xlabel("NIST 譜線波長 (nm, 空氣)"); ax[1].set_ylabel("偏差 (nm)"); ax[1].legend(frameon=False, loc="upper right")
plt.tight_layout(); plt.savefig(FIG + "fig2_im2000_axes_check.png", dpi=150); plt.close()

# 圖 3：雙誤差分解——三條理論曲線 + 實測點
v = np.linspace(300, 3000, 300)
lam_v = wavelength_from_shift(v, LASER_FIT)
err_axis = shift_from_wavelength((lam_v - B_q) / A_q, LASER_FIT) - v          # 只有波長軸偏移會造成的報告誤差
err_laser = shift_from_wavelength(lam_v, LASER_NOMINAL) - v                    # 只有雷射波長設錯
err_both = shift_from_wavelength((lam_v - B_q) / A_q, LASER_NOMINAL) - v
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.axhline(0, color=MUTED, lw=1)
ax.plot(v, err_axis, "--", color=BRAND2, lw=2, label=f"只有波長軸偏 {dev_q.mean():+.2f} nm")
ax.plot(v, err_laser, ":", color=BRAND, lw=2.4, label=f"只有雷射設 785.000 而非 {LASER_FIT:.2f} nm")
ax.plot(v, err_both, "-", color=INK, lw=2.2, label="兩者相加（物理模型）")
ob = [(p["lit"], p["reported"] - p["lit"]) for p in results["benzoic_table"]]
oc = [(p["lit"], p["reported"] - p["lit"]) for p in results["caffeine_table"]]
ax.plot(*zip(*ob), "o", color=WARN, ms=8, mec=SURF, label="苯甲酸實測誤差")
ax.plot(*zip(*oc), "^", color="#b45309", ms=8, mec=SURF, label="咖啡因實測誤差")
ax.set_xlabel("文獻拉曼位移 (cm⁻¹)"); ax.set_ylabel("OceanView 報告值 − 真值 (cm⁻¹)")
ax.set_title("一個偏差，兩個來源：波長軸偏移的貢獻隨波數變小，雷射波長的貢獻是常數", loc="left", fontsize=11)
ax.legend(frameon=False, loc="lower right", ncol=2, fontsize=9.5); ax.grid(axis="y", color=GRID)
plt.tight_layout(); plt.savefig(FIG + "fig3_two_error_sources.png", dpi=150); plt.close()

# 圖 4：苯甲酸 / 咖啡因 修正前後
xc = shift_from_wavelength(lam_true, LASER_FIT)
fig, ax = plt.subplots(2, 1, figsize=(10, 6.8))
for a, (c, refv, ttl) in zip(ax, [(corr_ba, LIT["benzoic acid"], "苯甲酸（3 次平均）"), (corr_un, LIT["caffeine"], "未知樣品 → 咖啡因")]):
    yn = c / c[(x_rep > 300) & (x_rep < 1800)].max()
    for r in refv: a.axvline(r, color=MUTED, lw=.8, alpha=.35)
    a.plot(x_rep, yn, color=BRAND, lw=1.5, label="OceanView 原始軸")
    a.plot(xc, yn, color=WARN, lw=1.5, label=f"修正後（λ_L={LASER_FIT:.2f}）")
    a.set_xlim(350, 1800); a.set_ylim(-0.05, 1.2); a.set_yticks([]); a.set_title(ttl + "　灰線＝文獻峰位", loc="left", fontsize=11)
ax[0].legend(frameon=False, ncol=2, loc="upper left"); ax[1].set_xlabel("拉曼位移 (cm⁻¹)")
plt.tight_layout(); plt.savefig(FIG + "fig4_benzoic_caffeine_before_after.png", dpi=150); plt.close()
print("圖檔已輸出到", FIG)
