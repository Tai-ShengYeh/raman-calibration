#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建置 Unit 1B 單檔 HTML：raman_calibration_unit1b.html
  - 數字全部從 unit1b_results.json 注入（先跑 unit1b_calibration.py）
  - 圖片由 figs_web/ 以 base64 內嵌；CSS 與 Unit 1（raman_calibration_tutorial.html）同一套
執行：python build_unit1b.py
"""
import json, base64, os, re, datetime

R = json.load(open("unit1b_results.json", encoding="utf-8"))
CSS = open("unit1_style.css", encoding="utf-8").read()
CSS += """
/* ---- Unit 1B 追加 ---- */
.lab{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px 22px;margin:18px 0}
.lab canvas{width:100%;height:auto;display:block;border-radius:10px;background:#fff}
.lab .readout{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:15px}
.lab .readout b{color:var(--brand)}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:700px){.two-col{grid-template-columns:1fr}}
.pill{display:inline-block;background:#eef2ff;color:#312e81;border-radius:999px;padding:2px 10px;font-size:13px;margin:0 2px}
.num{font-family:Consolas,monospace}
.unitnav{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin:-10px 0 20px}
.unitnav a{background:#fff;border:1px solid #c7d2fe;color:var(--brand);border-radius:999px;padding:6px 16px;text-decoration:none;font-size:14px;font-weight:700}
.unitnav a:hover{background:var(--accent-bg)}
.small{font-size:14px;color:var(--muted)}
/* ---- 5B 兩欄版面：左控制、右圖形，不必上下捲動 ---- */
.lab5b-grid{display:grid;grid-template-columns:286px minmax(0,1fr);gap:16px;align-items:start;margin-top:12px}
.lab5b-ctrl{display:flex;flex-direction:column;gap:12px;min-width:0}
.lab5b-ctrl .sl{display:flex;flex-direction:column;gap:5px}
.lab5b-ctrl .sl label{font-size:14px;color:#334155}
.lab5b-ctrl .sl label b{color:var(--brand);font-size:16px}
.lab5b-ctrl input[type=range]{width:100%;margin:0}
.lab5b-sec{border-top:1px solid #e2e8f0;padding-top:10px}
.lab5b-lab{font-size:13px;font-weight:700;color:var(--muted);letter-spacing:.05em;margin-bottom:6px}
.lab5b-btns{display:flex;flex-wrap:wrap;gap:6px}
.lab5b-btns .chip{font-size:13px;padding:5px 11px}
.lab .readout.lab5b-read{flex-direction:column;gap:5px;font-size:13.5px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:9px 12px;margin-top:0}
.lab5b-view{position:sticky;top:14px}
@media(max-width:900px){.lab5b-grid{grid-template-columns:1fr}.lab5b-view{position:static;order:-1}}
code{overflow-wrap:anywhere;word-break:break-word}
"""

def img(name):
    """把 figs/ 的圖縮到 1300 px、量化 128 色後內嵌（不另存 figs_web/）"""
    from PIL import Image
    import io
    im = Image.open(f"figs/{name}").convert("RGB")
    if im.width > 1300:
        im = im.resize((1300, int(im.height * 1300 / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.quantize(colors=128, method=Image.MEDIANCUT).save(buf, "PNG", optimize=True)
    b = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b}"

SURVEY = open("unit1b_survey.json", encoding="utf-8").read()
q = R["qepro_lamp"]; im = R["im2000"]; L = R["laser"]; uid = R["unknown_id"]
fmt = lambda x, d=2: f"{x:.{d}f}"
BA_ROWS = "\n".join(
    f"<tr><td class='num'>{p['reported']:.1f}</td><td class='num'>{p['lit']:.0f}</td><td class='num' style='color:var(--warn)'>{p['reported']-p['lit']:+.1f}</td>"
    f"<td class='num'>{p['corrected']:.1f}</td><td class='num' style='color:{'var(--ok)' if abs(p['corrected']-p['lit'])<=4 else 'var(--warn)'}'>{p['corrected']-p['lit']:+.1f}</td><td>{p['I']:.0f}%</td></tr>"
    for p in R["benzoic_table"])
CAF_ROWS = "\n".join(
    f"<tr><td class='num'>{p['reported']:.1f}</td><td class='num'>{p['corrected']:.1f}</td><td class='num'>{p['lit']:.0f}</td>"
    f"<td class='num' style='color:{'var(--ok)' if abs(p['corrected']-p['lit'])<=4 else 'var(--warn)'}'>{p['corrected']-p['lit']:+.1f}</td><td>{p['I']:.0f}%</td></tr>"
    for p in R["caffeine_table"])
QLINE_ROWS = "\n".join(
    f"<tr><td>{l['species']}</td><td class='num'>{l['true']:.3f}</td><td class='num'>{l['obs']:.3f}</td><td class='num' style='color:var(--warn)'>{l['obs']-l['true']:+.3f}</td></tr>"
    for l in q["lines"])
ILINE_ROWS = "\n".join(
    f"<tr><td>{l['species']}</td><td class='num'>{l['true']:.3f}</td><td class='num'>{l['obs']:.3f}</td><td class='num' style='color:var(--warn)'>{l['resid_nm_axis']:+.3f}</td><td class='num' style='color:var(--ok)'>{l['resid_wn_axis']:+.3f}</td></tr>"
    for l in im["lines"])
# 供互動實驗用的實測誤差點
PTS = json.dumps([[p["lit"], round(p["reported"] - p["lit"], 2), "BA"] for p in R["benzoic_table"]] +
                 [[p["lit"], round(p["reported"] - p["lit"], 2), "CAF"] for p in R["caffeine_table"]])

# Unit 1 二次式（見 Unit 1 §12），用來和物理模型比較
def unit1_quad(x): return -6.04936341303e-7 * x**2 + 0.998777978478 * x + 22.5143214517
def phys(x_rep):
    lam_rep = 1 / (1 / 785.0 - x_rep * 1e-7); lam_true = q["A"] * lam_rep + q["B"]
    return 1e7 * (1 / L["combined"] - 1 / lam_true)
CMP_ROWS = "\n".join(f"<tr><td class='num'>{x}</td><td class='num'>{unit1_quad(x):.1f}</td><td class='num'>{phys(x):.1f}</td><td class='num'>{phys(x)-unit1_quad(x):+.1f}</td></tr>"
                     for x in (500, 800, 1000, 1300, 1600, 2000, 2500, 2900))

HTML = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Unit 1B｜兩台儀器的體檢報告 — 波長軸、雷射波長與二階繞射</title>
<style>
__CSS__
</style>
</head>
<body>

<header class="hero">
  <h1>兩台儀器的體檢報告：波長軸、雷射波長與二階繞射</h1>
  <p>Unit 1 用一條二次式救回了 QEPro——這一課回答「它為什麼會偏 20 cm⁻¹」，順便發現「健康」的那台也有病</p>
  <div>
    <span class="badge">🔦 原子譜線</span><span class="badge">🧪 苯甲酸 × 咖啡因</span><span class="badge">🐍 Python</span><span class="badge">📊 R</span><span class="badge">📗 Excel</span><span class="badge">🎛 互動實驗 ×2</span><span class="badge">📝 計分測驗</span>
  </div>
</header>

<nav class="toc wrap" style="padding-top:28px">
  <div class="unitnav">
    <a href="raman_calibration_tutorial.html">← Unit 1　把跑掉的 QEPro 波數軸救回來</a>
    <a href="raman_food_additives_tutorial.html">Unit 2　食品添加物 →</a>
  </div>
  <b>本課目錄</b>
  <ol>
    <li><a href="#recap">劇情回顧：二次式救回了它，但沒說為什麼</a></li>
    <li><a href="#rulers">兩把尺：原子譜線 vs 分子拉曼峰</a></li>
    <li><a href="#qepro-lamp">體檢一：用日光燈檢查 QEPro 的波長軸</a></li>
    <li><a href="#im2000">體檢二：Im2000 Pro——nm 軸壞了、波數軸是好的、還有二階繞射</a></li>
    <li><a href="#decompose">拆解：一個偏差，兩個來源（互動實驗）</a></li>
    <li><a href="#fingerprint">三種誤差的指紋：八台儀器盲測（互動實驗）</a></li>
    <li><a href="#laser">反解雷射波長：苯甲酸與咖啡因的交叉驗證</a></li>
    <li><a href="#unknown">未知樣品是什麼？校正後才敢比對</a></li>
    <li><a href="#compare">物理模型 vs Unit 1 的二次式</a></li>
    <li><a href="#python">Python 實作</a></li>
    <li><a href="#rlang">R 實作</a></li>
    <li><a href="#excel">Excel 實作（LINEST + 網格搜尋）</a></li>
    <li><a href="#library">校正錯了會怎樣：資料庫搜尋崩潰</a></li>
    <li><a href="#quiz">隨堂測驗（自動計分）</a></li>
    <li><a href="#homework">重點整理與練習</a></li>
    <li><a href="#data">資料包與可重現性</a></li>
    <li><a href="#references">參考文獻</a></li>
  </ol>
</nav>

<div class="wrap">

<!-- ==================== 1 ==================== -->
<section id="recap">
<h2>1. 劇情回顧：二次式救回了它，但沒說為什麼</h2>
<div class="card">
<p>在 <a href="raman_calibration_tutorial.html#ocean">Unit 1 第 12 節</a>，我們發現 QEPro 的乙醯胺酚峰整體比 Imai Optics 那台<b>低約 20 cm⁻¹</b>，於是用 ASTM 參考峰配了一條二次修正式，再用萘與聚苯乙烯做外部驗證——RMSE 壓到 1 cm⁻¹ 以下。任務完成？</p>
<p class="keybox card" style="margin:10px 0">Unit 1 的做法是<b>經驗修正</b>：它把「症狀」修掉了，但沒有回答<b>病因</b>。一台光譜儀要算出拉曼位移，需要兩個東西都對：<br>
① <b>像素 → 波長</b> 的對應（波長軸）　② <b>雷射的真實波長</b> λ<sub>L</sub><br>
ν̃ = 10⁷ × (1/λ<sub>L</sub> − 1/λ)。任何一個錯，位移就錯；<b>兩個都錯，就會疊成我們看到的 −20 cm⁻¹</b>。</p>
<p>這一課用兩樣新工具把病因找出來：一支<b>日光燈</b>（它的原子譜線是波長標準）、兩瓶<b>藥局買得到的固體</b>（苯甲酸與一個「未知」樣品，它們的拉曼峰是位移標準）。過程中還會發現，Unit 1 當作「健康對照」的 Im2000 Pro，其實也有一條軸是錯的。</p>
<div class="flow">
  <span class="step">燈 → 波長軸對不對？</span><span class="arr">➜</span>
  <span class="step">苯甲酸 → 雷射波長是多少？</span><span class="arr">➜</span>
  <span class="step">未知樣品 → 這才敢比對</span><span class="arr">➜</span>
  <span class="step">資料庫搜尋 → Unit 6–7</span>
</div>
</div>
</section>

<!-- ==================== 2 ==================== -->
<section id="rulers">
<h2>2. 兩把尺：原子譜線 vs 分子拉曼峰</h2>
<div class="card">
<p>校正一台拉曼光譜儀，有兩種「尺」可以拿，量的東西不一樣<span class="cite"><a href="#ref7">[7]</a></span><span class="cite"><a href="#ref8">[8]</a></span>：</p>
<table>
<tr><th></th><th>波長標準（wavelength standard）</th><th>拉曼位移標準（Raman-shift standard）</th></tr>
<tr><td><b>是什麼</b></td><td>原子放電燈的發射線：Ne、Ar、Hg、Kr……<br>日光燈就是 Hg + Ar 放電管加磷光體</td><td>純物質的拉曼峰：ASTM E1840 的八種材料<span class="cite"><a href="#ref1">[1]</a></span>（萘、硫、環己烷、乙醯胺酚、聚苯乙烯……）</td></tr>
<tr><td><b>量到什麼</b></td><td>只檢查「像素 → 波長」對不對。<b>跟雷射無關</b>——量燈的時候雷射根本沒開</td><td>直接檢查「像素 → 位移」，因為位移本來就是相對雷射算的；<b>雷射波長被自動吸收進去</b></td></tr>
<tr><td><b>準確度</b></td><td>NIST 譜線表準到 0.001 nm 以下<span class="cite"><a href="#ref2">[2]</a></span>；瓶頸在你的峰位擬合（本課約 0.1 nm）</td><td>ASTM 值的標準差通常 < 1 cm⁻¹<span class="cite"><a href="#ref1">[1]</a></span>；非 ASTM 物質（苯甲酸、咖啡因）只能用文獻值，不確定度約 1–2 cm⁻¹</td></tr>
<tr><td><b>抓不到的</b></td><td>雷射漂移、雷射設定值錯誤</td><td>分不出「是波長軸錯，還是雷射錯」</td></tr>
<tr><td><b>優點</b></td><td>幾十條線、跨全範圍、便宜（一支燈管）；能<b>分離</b>兩個誤差來源</td><td>一步到位；日常確認最方便</td></tr>
</table>
<p>所以工業上常見的作法是<b>兩步法</b>：先用原子燈校波長軸，再用一個拉曼標準物（矽 520.7 cm⁻¹ 或 ASTM 材料）確認雷射波長<span class="cite"><a href="#ref7">[7]</a></span><span class="cite"><a href="#ref8">[8]</a></span>。Liu &amp; Hennelly (2024) 更進一步指出：用「光譜儀焦距、光柵角、雷射波長」這種<b>物理模型</b>校正，在參考峰範圍以外的表現比純多項式好<span class="cite"><a href="#ref3">[3]</a></span>——這正是 Unit 1 §16 建議清單裡的第 9 項，本課就來做。</p>
<div class="card tip" style="margin-top:14px"><b>空氣還是真空？</b> NIST 表在 200–2000 nm 區間預設給<b>空氣中波長</b>；OceanView、IMSpectralSuite 的波長軸也是空氣中波長，兩邊一致即可。真空與空氣在 800 nm 差約 0.22 nm（≈ 3 cm⁻¹），混用就會多出一個假偏差。本課全部用空氣值。</div>
</div>
</section>

<!-- ==================== 3 ==================== -->
<section id="qepro-lamp">
<h2>3. 體檢一：用日光燈檢查 QEPro 的波長軸</h2>
<div class="card">
<p><b>做法：</b>雷射關掉，把光纖對著實驗室的日光燈，用 OceanView 存下 783.7–1030.9 nm 的譜（<code>light1.xlsx</code>；換一條光纖再存一次成 <code>light2.xlsx</code>）。這個範圍內日光燈有一整排 <b>Ar I</b> 線（填充氣體）和一條 <b>Hg I 1013.975 nm</b>。</p>
<figure><img src="__FIG1__" alt="QEPro 燈譜與譜線指認" style="max-width:100%;border-radius:10px">
<figcaption>圖 1　上：QEPro 量到的日光燈譜（對數座標），綠線＝NIST 真值，紅線＝檔案裡的峰位——紅的<b>一律在綠的左邊</b>。下：偏差（紅點）與線性修正後殘差（綠方塊）。</figcaption></figure>
<h3>怎麼從譜裡找線？兩段式</h3>
<p>直接對整張譜「找峰」會被鄰線、雙線和磷光體的寬帶干擾。比較穩的做法是<b>反過來</b>：我們知道 Ar 線「應該」在哪裡，就到那附近 ±2.5 nm 找最大值，先估一個<b>粗略偏移量</b>（取中位數，對緊鄰雙線很穩），再以「真值＋偏移」為中心、±0.9 nm 做<b>強度加權質心</b>。</p>

<div class="evidence-note" id="intensity-centroid">
<h4><span lang="zh-Hant">原理補充：強度加權質心是什麼？</span><span lang="en">Background: what is an intensity-weighted centroid?</span></h4>
<p><span lang="zh-Hant"><b>強度加權質心（intensity-weighted centroid）就是一條譜峰的「訊號平衡點」。</b>想像把每個取樣波長當成尺上的位置，把該位置扣除背景後的強度當成砝碼重量：訊號越強，對平衡點的影響越大。因此它會利用峰範圍內的多個點，而不是只選最高的那一點。</span><span lang="en"><b>The intensity-weighted centroid is the "signal balance point" of a spectral peak.</b> Picture every sampled wavelength as a position on a ruler, and the background-subtracted intensity at that position as the weight placed there: the stronger the signal, the more it pulls the balance point. The centroid therefore uses many points across the peak instead of only the single highest one.</span></p>
<p><span lang="zh-Hant"><b>先扣背景，再算加權平均：</b></span><span lang="en"><b>Subtract the background first, then take the weighted average:</b></span><br>
S<sub>i</sub> = I<sub>i</sub> − B<sub>i</sub><br>
λ<sub>c</sub> = Σ<sub>i=1…n</sub>(λ<sub>i</sub> S<sub>i</sub>) / Σ<sub>i=1…n</sub>S<sub>i</sub></p>
<ul>
<li><span lang="zh-Hant"><b>i、n：</b>i 是選定峰範圍內的取樣點編號；n 是點數。Σ 表示把這些點的數值全部加起來。</span><span lang="en"><b>i, n:</b> i indexes the sampled points inside the chosen peak window; n is the number of points. Σ means summing the values of all of those points.</span></li>
<li><span lang="zh-Hant"><b>λ<sub>i</sub>：</b>第 i 點的觀測波長，單位 nm；<b>I<sub>i</sub></b> 是原始強度，單位 counts（儀器計數）。</span><span lang="en"><b>λ<sub>i</sub>:</b> the observed wavelength of point i, in nm; <b>I<sub>i</sub></b> is the raw intensity, in counts (instrument counts).</span></li>
<li><span lang="zh-Hant"><b>B<sub>i</sub>、S<sub>i</sub>：</b>該點估計的背景與扣背景後的淨強度，單位也是 counts。此處以非負淨強度作權重，且總和必須大於 0。</span><span lang="en"><b>B<sub>i</sub>, S<sub>i</sub>:</b> the estimated background at that point and the net intensity left after subtracting it, also in counts. Non-negative net intensities are used as the weights, and their sum must be greater than 0.</span></li>
<li><span lang="zh-Hant"><b>λ<sub>c</sub>：</b>質心波長，單位 nm。分子單位是 nm × counts，除以分母的 counts 後留下 nm。</span><span lang="en"><b>λ<sub>c</sub>:</b> the centroid wavelength, in nm. The numerator carries units of nm × counts; dividing by the counts in the denominator leaves nm.</span></li>
</ul>
<p><span lang="zh-Hant"><b>為什麼這是平衡點？</b>把公式移項，會得到 Σ S<sub>i</sub>(λ<sub>i</sub> − λ<sub>c</sub>) = 0。左側位置的距離為負，右側為正；「重量 × 距離」的總和互相抵消。這不表示左右兩邊的總強度一定相等。若全部淨強度一起乘上相同倍數，分子與分母會同時放大，質心位置不變。</span><span lang="en"><b>Why is this a balance point?</b> Rearranging the formula gives Σ S<sub>i</sub>(λ<sub>i</sub> − λ<sub>c</sub>) = 0. Distances to the left are negative and those to the right are positive, so the "weight × distance" terms cancel each other out. This does not mean the total intensity on the two sides must be equal. If every net intensity is multiplied by the same factor, the numerator and the denominator grow together and the centroid position is unchanged.</span></p>
<p><span lang="zh-Hant"><b>手算範例（示意資料，非本次實測）：</b>三個波長 800.0、800.2、800.4 nm，扣背景後的強度分別是 10、40、30 counts。</span><span lang="en"><b>Worked example (illustrative data, not measured in this lesson):</b> three wavelengths 800.0, 800.2 and 800.4 nm, with background-subtracted intensities of 10, 40 and 30 counts respectively.</span></p>
<p>λ<sub>c</sub> = (800.0 × 10 + 800.2 × 40 + 800.4 × 30) / (10 + 40 + 30)<br>
= 64020 / 80 = <b>800.25 nm</b><span lang="zh-Hant">。</span><span lang="en">.</span></p>
<p><span lang="zh-Hant">最高取樣點在 800.2 nm，但右側的 30 counts 比左側的 10 counts 重，所以質心向右移到 800.25 nm。它可以落在兩個取樣點之間；這是位置估計，<b>不代表儀器的光學解析度提高，也不代表這個值必然更接近真值</b>。</span><span lang="en">The highest sampled point is at 800.2 nm, but the 30 counts on the right outweigh the 10 counts on the left, so the centroid moves right to 800.25 nm. It can fall between two sampled points; this is a position estimate, and it <b>does not mean the instrument's optical resolution has improved, nor that this value is necessarily closer to the true value</b>.</span></p>
<p><span lang="zh-Hant"><b>本課的程式如何對應？</b>先用多條參考線估出粗略偏移，再於「參考波長＋粗略偏移」附近 ±0.9 nm 取點。程式以這個小範圍的最低強度作為固定背景 B，亦即 <code>yy = y[w] - y[w].min()</code>，接著以 <code>sum(x[w] * yy) / sum(yy)</code> 求質心。參考值只用來決定搜尋範圍；最後的觀測質心仍由範圍內的訊號決定。最低值法只是局部背景近似，並不是完整的基線擬合。</span><span lang="en"><b>How does the code in this lesson map onto this?</b> It first estimates a rough offset from several reference lines, then takes the points within ±0.9 nm of "reference wavelength + rough offset". The code uses the lowest intensity in that small window as a constant background B, that is <code>yy = y[w] - y[w].min()</code>, and then obtains the centroid with <code>sum(x[w] * yy) / sum(yy)</code>. The reference value only decides the search window; the final observed centroid is still determined by the signal inside that window. Taking the minimum is only a local background approximation, not a full baseline fit.</span></p>
<p><span lang="zh-Hant"><b>為什麼要扣背景、限制範圍？</b>未扣掉的均勻背景會把質心拉向所選範圍的中心；斜背景會造成額外偏移。範圍太窄會切掉峰翼，太寬會混入鄰峰與雜訊。±0.9 nm 是本例的設定，不是所有儀器通用的數字，應檢查是否涵蓋目標峰且避開鄰線，並比較稍微改變範圍後的位置是否穩定。</span><span lang="en"><b>Why subtract the background and limit the window?</b> An unsubtracted uniform background pulls the centroid toward the center of the chosen window, and a sloping background introduces a further shift. Too narrow a window cuts off the peak wings; too wide a one lets in neighboring lines and noise. The ±0.9 nm used here is the setting for this example, not a number that transfers to every instrument: check that it covers the target peak while avoiding adjacent lines, and compare the positions obtained after slightly changing the window to see whether they are stable.</span></p>
<p><span lang="zh-Hant"><b>適用條件與限制：</b>對孤立、近似對稱且背景處理良好的峰，質心可用來估計峰中心。遇到非對稱峰或未分離雙線，質心是整團訊號的加權位置，未必是其中任何一條線的真實峰位；雜訊、飽和與截斷也會影響結果。若淨強度總和為 0，公式無法計算，應跳過該範圍。以上離散公式對應本課的每像素訊號加權；若資料是明顯不等間距的「每 nm 強度密度」，估計面積質心時還需加入各點代表的波長寬度 Δλ<sub>i</sub> 作權重。</span><span lang="en"><b>Conditions and limitations:</b> for an isolated, approximately symmetric peak whose background has been handled well, the centroid can be used to estimate the peak center. For an asymmetric peak or an unresolved doublet, the centroid is the weighted position of the whole blend and is not necessarily the true peak position of any single line; noise, saturation and truncation also affect the result. If the net intensities sum to 0 the formula cannot be evaluated and that window should be skipped. The discrete formula above corresponds to this lesson's per-pixel signal weighting; if the data are a clearly unevenly spaced "intensity density per nm", estimating the area centroid additionally requires weighting each point by the wavelength width Δλ<sub>i</sub> it represents.</span></p>
<p class="small"><span lang="zh-Hant">延伸閱讀：<a href="https://learn.astropy.org/tutorials/1_SpectroscopicTraceTutorial.html" target="_blank" rel="noopener">Astropy 官方教學：強度加權一階矩與背景條件</a>；<a href="https://arxiv.org/abs/1809.10295" target="_blank" rel="noopener">Teague 與 Foreman-Mackey（2018）：譜線中心估計與方法限制</a>。</span><span lang="en">Further reading: <a href="https://learn.astropy.org/tutorials/1_SpectroscopicTraceTutorial.html" target="_blank" rel="noopener">Astropy official tutorial: the intensity-weighted first moment and its background conditions</a>; <a href="https://arxiv.org/abs/1809.10295" target="_blank" rel="noopener">Teague and Foreman-Mackey (2018): line-center estimation and the limits of the methods</a>.</span></p>
<details><summary><span lang="zh-Hant">理解檢查：把範例三個淨強度都乘以 2，質心會改變嗎？</span><span lang="en">Check your understanding: if all three net intensities in the example are multiplied by 2, does the centroid change?</span></summary><p><span lang="zh-Hant">不會，仍是 800.25 nm，因為分子與分母都乘以 2。若只增加右側的強度，質心才會向右移動。</span><span lang="en">No — it is still 800.25 nm, because the numerator and the denominator are both multiplied by 2. Only if the intensity on the right alone increases does the centroid move to the right.</span></p></details>
</div>

<table>
<tr><th>物種</th><th>NIST 真值 (nm)</th><th>檔案觀測 (nm)</th><th>偏差</th></tr>
__QLINE_ROWS__
</table>
<div class="metric-grid">
  <div class="metric"><strong>__Q_MEAN__ nm</strong><span>平均偏差（__Q_N__ 條線，SD __Q_SD__）</span></div>
  <div class="metric"><strong>≈ __Q_CM__ cm⁻¹</strong><span>換算成拉曼位移誤差（在 850 nm）</span></div>
  <div class="metric"><strong>__Q_FIBER__ nm</strong><span>換光纖後峰位最大差異 → 光纖無關</span></div>
</div>
<p>結論：<b>QEPro 的波長軸整體偏低約 1 nm</b>——大約 4 個像素。這是「像素 → 波長」的對應跑掉了，和雷射無關（量燈時雷射沒開）。一條線性修正就能把 12 條線壓到殘差 rms __Q_RES__ pm：</p>
<div class="formula">λ<sub>true</sub> = __Q_A__ × λ<sub>reported</sub> + __Q_B__</div>
<div class="card warnbox" style="margin-top:12px"><b>這一步只修好了一半。</b>波長軸偏低 0.94 nm，在 850 nm 對應約 13 cm⁻¹——可是 Unit 1 看到的是 −20 cm⁻¹。差的那 7 cm⁻¹ 從哪來？第 5 節揭曉。</div>
</div>
</section>

<!-- ==================== 4 ==================== -->
<section id="im2000">
<h2>4. 體檢二：Im2000 Pro——nm 軸壞了、波數軸是好的、還有二階繞射</h2>
<div class="card">
<p>Unit 1 把 Imai Optics Im2000 Pro 當作「健康對照組」。同一支日光燈也拿去給它量，IMSpectralSuite 可以匯出三種橫軸：<b>pixel、nm、wavenumber</b>（<code>light_pixel.txt</code>、<code>light_nm2.txt</code>、<code>light_wavenumber.txt</code>，三者強度互相關 0.998，是同一次量測）。</p>
<figure><img src="__FIG2__" alt="Im2000 Pro 軸檢查" style="max-width:100%;border-radius:10px">
<figcaption>圖 2　上：Im2000 Pro 的燈譜。<b>最強的峰（873 nm）根本不是一階線</b>，是 Hg 435.8 nm 的二階繞射；1088/1098 nm 那一團是綠色磷光體的二階。下：nm 軸偏高約 1.4 nm（藍），但把波數軸換算回 nm 卻只差 0.07 nm（綠）。</figcaption></figure>
<h3>發現一：nm 軸偏高 __I_MEAN__ nm</h3>
<p>方向跟 QEPro 相反、幅度更大。如果你拿這台的 nm 軸去做任何定量，會錯 17–20 cm⁻¹。</p>
<h3>發現二：波數軸卻是好的</h3>
<p>把波數軸的值取在每條譜線的像素位置，反推「軟體心中的雷射波長」：10 條線給出 <b>__I_LASER__ ± __I_LASER_SD__ nm</b>，全域一致；用它反算波長，殘差 rms 只有 <b>__I_WNRES__ nm ≈ 0.9 cm⁻¹</b>。也就是說，這台的 nm 軸和波數軸<b>不是同一組校正係數算出來的</b>——軟體內部不一致，該向原廠反映。</p>
<table>
<tr><th>物種</th><th>真值 (nm)</th><th>nm 軸觀測</th><th>nm 軸偏差</th><th>波數軸→nm 偏差</th></tr>
__ILINE_ROWS__
</table>
<h3>發現三：二階繞射陷阱</h3>
<p>光柵方程式 <span class="num">mλ = d(sinα + sinβ)</span> 對 m = 1、2、3 都成立：波長 435.8 nm 的光在二階（m = 2）會落在一階 871.7 nm 的位置。Im2000 Pro 沒有 order-sorting filter，所以可見光的 Hg 線與磷光體全部以「×2」的假波長混進來，而且<b>比真正的一階 Ar 線強十倍</b>。用寬頻燈校正時最容易把二階線誤認一階——本課反而把兩條乾淨的二階 Hg 線（407.8×2、435.8×2）當作額外錨點，因為它們的「等效波長」一樣準。</p>
<div class="lab" id="lab2">
<b>🔢 二階繞射換算器</b>　輸入一條可見光譜線的波長，看它會「假裝」出現在哪裡：
<div class="slider-row"><input type="number" id="vis" value="435.833" step="0.001" style="width:150px;padding:8px;border:1px solid #cbd5e1;border-radius:8px;font-size:16px"> nm（一階）→ 二階出現在 <b id="vis2" style="color:var(--warn)">871.666</b> nm、三階 <b id="vis3" style="color:var(--warn)">1307.5</b> nm</div>
<p class="small">試試 Hg 404.656、546.074，或 Tb 磷光體 543.5——你會發現 973 nm 與 1088 nm 那些「不明峰」都有主人。實際量拉曼時有 785 nm 長通濾片擋住可見光，二階通常不成問題；量燈時沒有。</p>
</div>
</div>
</section>

<!-- ==================== 5 ==================== -->
<section id="decompose">
<h2>5. 拆解：一個偏差，兩個來源（互動實驗）</h2>
<div class="card">
<p>把 ν̃ = 10⁷(1/λ<sub>L</sub> − 1/λ) 對兩個變數各微分一下，就知道兩種錯誤留下的「指紋」不一樣：</p>
<div class="two-col">
<div class="card" style="margin:0"><b>① 波長軸偏 Δλ</b><div class="formula" style="font-size:17px">Δν̃ ≈ 10⁷ · Δλ / λ²</div><p class="small">λ 越長（位移越大）分母越大 → 誤差<b>隨波數變小</b>。−0.94 nm 在 800 nm 是 −15 cm⁻¹，到 1020 nm 只剩 −9 cm⁻¹。</p></div>
<div class="card" style="margin:0"><b>② 雷射波長設錯 Δλ<sub>L</sub></b><div class="formula" style="font-size:17px">Δν̃ ≈ 10⁷ · Δλ<sub>L</sub> / λ<sub>L</sub>²</div><p class="small">跟 λ 無關 → 全譜<b>平移一個常數</b>。設 785.000 但實際 784.56，就是全譜 −7 cm⁻¹。</p></div>
</div>
<figure><img src="__FIG3__" alt="雙誤差分解" style="max-width:100%;border-radius:10px">
<figcaption>圖 3　綠虛線＝只有波長軸偏移；藍點線＝只有雷射設錯；黑實線＝兩者相加。紅點、橘三角＝苯甲酸與咖啡因實測誤差。實測點的斜率與黑線一致。注意：單靠這些拉曼峰無法唯一分開兩個來源（見下方旋鈕實驗），是燈先把 Δλ 釘住，剩下的常數才歸給雷射。</figcaption></figure>

<div class="lab" id="lab1">
<b>🎛 雙誤差旋鈕實驗：你能用兩個旋鈕解釋 25 個實測點嗎？</b>
<div class="lab5b-grid">
 <div class="lab5b-ctrl">
  <div class="sl"><label>波長軸偏移 Δλ：<b id="dlv">−0.94</b> nm</label><input type="range" id="dl" min="-2" max="2" step="0.01" value="-0.94"></div>
  <div class="sl"><label>真實雷射波長 λ<sub>L</sub>：<b id="llv">784.56</b> nm</label><input type="range" id="ll" min="783.5" max="786.5" step="0.01" value="784.56"></div>
  <div class="lab5b-sec">
   <div class="lab5b-lab">情境預設</div>
   <div class="lab5b-btns">
    <button class="chip" onclick="setLab(0,785)">都沒錯</button>
    <button class="chip" onclick="setLab(-0.94,785)">只有波長軸偏</button>
    <button class="chip" onclick="setLab(0,784.56)">只有雷射設錯</button>
    <button class="chip" onclick="setLab(__Q_MEAN__,__L_COMB__)">燈＋拉曼峰的解</button>
    <button class="chip" onclick="setLab(-1.46,785)">硬用一個旋鈕湊</button>
   </div>
  </div>
  <div class="readout lab5b-read">
   <span>模型 vs 實測 rms：<b id="rms">—</b> cm⁻¹</span>
   <span>在 1001 cm⁻¹ 的誤差：<b id="e1001">—</b></span>
   <span>在 2953 cm⁻¹ 的誤差：<b id="e2953">—</b></span>
  </div>
 </div>
 <div class="lab5b-view"><canvas id="labc" width="700" height="600"></canvas></div>
</div>
<p class="small">試「硬用一個旋鈕湊」：把 Δλ 拉到 −1.46 nm、雷射維持 785，rms 甚至比「燈＋拉曼峰的解」還略低（2.3 vs 2.7）——<b>光看拉曼峰，兩個旋鈕幾乎可以互相替代</b>（這就是第 2 節說「拉曼標準物分不開兩個來源」的意思）。真正把它們分開的是燈：燈獨立量到 Δλ = −0.94 ± 0.17 nm，−1.46 被排除了，剩下解釋不掉的 −7 cm⁻¹ 就只能是雷射。<b>一把尺釘住一個旋鈕，第二把尺才能量第二個。</b></p>
</div>
</div>
</section>


<!-- ==================== 5B ==================== -->
<section id="fingerprint">
<h2>5B. 三種誤差的指紋：八台儀器盲測（互動實驗）</h2>
<div class="card">
<p>第 5 節分開了「波長軸」與「雷射」。但<b>波長軸本身也會用不同方式壞掉</b>。光譜儀把像素換成波長，用的是一條三次多項式：</p>
<div class="formula">λ(p) = C<sub>0</sub> + C<sub>1</sub>·p + C<sub>2</sub>·p² + C<sub>3</sub>·p³</div>
<p>C<sub>0</sub> 決定軸<b>從哪裡開始</b>，C<sub>1</sub> 是<b>色散</b>（每個像素幾 nm），C<sub>2</sub>、C<sub>3</sub> 是成像的彎曲修正。哪一個係數錯，就留下哪一種指紋——把「報告 − 真實」對真實波長畫出來，形狀直接告訴你病因：</p>

<table>
<thead><tr><th>指紋</th><th>形狀</th><th>壞掉的係數</th><th>對拉曼的後果</th></tr></thead>
<tbody>
<tr><td><b>純平移</b></td><td>水平線</td><td>只有 C<sub>0</sub></td><td>波數誤差隨波數遞減（見第 5 節）；改 C<sub>0</sub> 即可</td></tr>
<tr><td><b>色散誤差</b></td><td>斜線</td><td>C<sub>1</sub>（連帶 C<sub>0</sub>）</td><td>改變<b>峰與峰的間距</b>；調整雷射波長救不回來，資料庫比對會崩</td></tr>
<tr><td><b>高次項</b></td><td>曲線</td><td>C<sub>2</sub>／C<sub>3</sub></td><td>通常代表光柵或感測器被動過，要整組重配</td></tr>
</tbody>
</table>

<div class="callout"><b>為什麼色散誤差比平移可怕？</b>波數軸整體平移一個常數，可以靠調整軟體裡的雷射波長設定吸收掉——這兩件事在數學上是<b>簡併</b>的。但色散誤差改變的是峰與峰之間的距離：本來相隔 1000 cm⁻¹ 的兩個峰會被量成 1000×(1+ε)。沒有任何單一參數救得回來，這正是第 12 節資料庫搜尋崩潰的物理根源。</div>

<h3>2026-09-07 全實驗室普查</h3>
<p>用一顆<b>延長線上的氖氣指示燈</b>（Ne-Ar 混合，五金行 NT$50 級），一天之內把八台光譜儀的波長軸掃過一遍。氖燈在 585–750 nm 有二十餘條又強又窄的線，積分只要 100 ms，是這個檢查最省的光源。下面的實驗用的就是這批真實資料。</p>

<div class="lab" id="lab5b">
<b>🎛 盲測診斷：這台儀器得了什麼病？</b>
<p class="small" style="margin:6px 0 12px">先在「盲測」模式下觀察形狀、猜是哪一種指紋，再用左邊的旋鈕去湊。湊好之後按「顯示答案」對照。</p>

<div class="slider-row" id="instchips" style="flex-wrap:wrap;gap:6px"></div>

<div class="lab5b-grid">
 <div class="lab5b-ctrl">
  <div class="sl"><label>平移 <b id="offv">0.00</b> nm</label><input type="range" id="off" min="-10" max="10" step="0.01" value="0"></div>
  <div class="sl"><label>斜率 <b id="slpv">0</b> ppm</label><input type="range" id="slp" min="-3000" max="3000" step="5" value="0"></div>
  <div class="sl"><label>曲率 <b id="curv">0</b>（任意單位）</label><input type="range" id="cur" min="-40" max="40" step="0.5" value="0"></div>

  <div class="lab5b-sec">
   <div class="lab5b-lab">你的判斷（先猜才會解鎖）</div>
   <div class="lab5b-btns">
    <button class="chip" onclick="judge('offset')">純平移</button>
    <button class="chip" onclick="judge('linear')">有色散誤差</button>
    <button class="chip" onclick="judge('curve')">有高次項</button>
   </div>
   <div id="judgefb" class="small" style="font-weight:700;margin-top:6px"></div>
  </div>

  <div class="lab5b-sec">
   <div class="lab5b-lab">自動擬合</div>
   <div class="lab5b-btns">
    <button class="chip" onclick="autoFit(0)">只用平移</button>
    <button class="chip" onclick="autoFit(1)">平移＋斜率</button>
    <button class="chip" onclick="autoFit(2)">再加曲率</button>
    <button class="chip" onclick="resetLab2()">歸零</button>
    <button class="chip" id="revealBtn" onclick="toggleReveal()">顯示答案</button>
   </div>
  </div>

  <div class="readout lab5b-read">
   <span>殘差 rms：<b id="rms2">—</b></span>
   <span>最佳純平移 rms：<b id="rmsOff">—</b></span>
   <span>最佳線性 rms：<b id="rmsLin">—</b></span>
   <span>最佳斜率：<b id="tstat">—</b></span>
   <span>判讀：<b id="verdict">—</b></span>
  </div>
 </div>

 <div class="lab5b-view"><canvas id="lab2c" width="700" height="620"></canvas></div>
</div>

<p class="small" style="margin:10px 0 0">斜率 s（ppm）與修正式的 A 互為 <span class="num">A = 1 − s×10⁻⁶</span>。判讀看的是 <b>t = 斜率 / 標準誤</b>，不是 rms 降了多少——這正是日光燈那次被騙的地方：單看 rms 會覺得有改善，但那條線的位置本身就系統性偏掉了。</p>
<div id="revealBox" style="display:none;margin-top:12px;padding:12px 16px;background:var(--accent-bg);border-radius:10px;font-size:15px"></div>
</div>

<h3>八台的診斷結果</h3>
<table>
<thead><tr><th>儀器</th><th>軸範圍 (nm)</th><th>nm/px</th><th>線數</th><th>修正式</th><th>rms</th><th>診斷</th></tr></thead>
<tbody id="surveyRows"></tbody>
</table>
<p class="small">rms 是「單條譜線位置」的散布，不是平均值的不確定度。QEPro-532 的 8 pm 相當於 1/20 個像素；Avantes NIR 用的是聚苯乙烯認證帶（1143、1680 nm，溯源 NIST SRM 2065）而非氖燈——氖在近紅外太弱。這一台<b>只能定平移</b>：它的色散不是「沒量夠」而是<b>原理上不可測</b>（256 像素 / 853 nm，3σ 偵測下限 ≥ 1500 ppm），推導見上方的延伸案例。</p>

<div class="callout warn"><b>這次踩到的坑：槓桿端只有一條弱線。</b>QEPro-532 最早用日光燈校，得到色散誤差 −1930 ppm（0.19%）。那是<b>錯的</b>——當時斜率幾乎只靠日光燈裡坐在螢光粉背景上的 Ar 696.5 nm 撐著，它被背景拉偏了約 140 pm。換成氖燈後同一條線乾淨了，真值是 −255 ppm，差了七倍。<b>那條線的重覆性 SD 只有 15 pm，看起來非常可靠，準確度卻差一個數量級。</b>重覆性是精密度，不是準確度；槓桿端只有一條線的時候特別危險。</div>

<div class="callout"><b>延伸案例：先算偵測極限，再決定要不要花錢。</b>
<p style="margin:8px 0">Avantes NIR 只有兩個點，很自然會想「那就再買一片標準濾片，多幾個點不就好了」。動手買之前，先把答案算出來。</p>
<p style="margin:8px 0"><b>第一步：免費的先試。</b>ASTM E1421 的聚苯乙烯除了 1143 與 1680，還有一條 1364.5 nm。回頭翻已經量過的薄片與厚片資料——<b>1364.5 nm 處的殘差只有 +0.1σ，什麼都沒有</b>。自動找峰會抓到 1389 nm 一個 3.4σ 的凸起，但它離 1364.5 有 25 nm（7.4 個像素）、落在大氣水氣吸收帶裡，而且<b>薄片與厚片的高度幾乎一樣</b>（+0.048 vs +0.045）。真的樣品帶必須隨厚度長高——1680 帶就從 0.319 長到 0.449。不隨厚度變的，就不是樣品的。</p>
<figure style="margin:10px 0"><img src="__FIG6__" alt="Avantes NIR 的 1364 nm 帶查核" style="max-width:100%;border-radius:10px">
<figcaption>(a) 兩種厚度的聚苯乙烯吸光度：只有 1680 帶清楚，1143 帶勉強，1364.5 nm 處平坦。(b) 扣二次基線後聚焦 1250–1500 nm：1364.5 nm（紅線）落在噪音裡；1390–1470 的隆起是大氣水氣帶，薄片與厚片一樣高，所以不是樣品的。</figcaption></figure>

<p style="margin:8px 0"><b>第二步：算槓桿。</b>就算 1364 量得到也沒用，因為它落在 1143 與 1680 的中點，對斜率幾乎沒有貢獻：斜率標準誤從 2370 ppm 只降到 2358 ppm，<b>改善 0.5%</b>。</p>
<p style="margin:8px 0"><b>第三步：算買了以後會怎樣。</b></p>
<table style="margin:6px 0">
<thead><tr><th>用什麼標準品</th><th>斜率標準誤</th><th>3σ 偵測下限</th><th>換算全軸端點差</th></tr></thead>
<tbody>
<tr><td>現況：PS 兩帶（實測 σ = 0.9 nm）</td><td>2370 ppm</td><td>7111 ppm</td><td>6.07 nm（1.81 px）</td></tr>
<tr><td>＋PS 1364 帶（若量得到）</td><td>2358 ppm</td><td>7074 ppm</td><td>6.04 nm（1.80 px）</td></tr>
<tr><td>稀土玻璃六個 NIR 峰（σ = 0.5 nm）</td><td>1221 ppm</td><td>3662 ppm</td><td>3.13 nm（0.93 px）</td></tr>
<tr><td>六峰 ＋ PS 1680（σ = 0.5 nm）</td><td>837 ppm</td><td>2510 ppm</td><td>2.14 nm（0.64 px）</td></tr>
<tr><td>同上，單點做到 σ = 0.3 nm（≈1/11 像素，樂觀值）</td><td>502 ppm</td><td><b>1506 ppm</b></td><td>1.29 nm（0.38 px）</td></tr>
</tbody>
</table>
<p style="margin:8px 0">對照：QEPro-532 的色散是 <span class="num">255 ppm</span>，USB2000 是 <span class="num">1749 ppm</span>。<b>最樂觀的偵測下限也是 1500 ppm</b>——QEPro-532 那個量級在這個通道上永遠測不到，USB2000 那個量級只是勉強擦邊。</p>
<p style="margin:8px 0"><b>結論：不要買。</b>限制不是點數不夠，是 <span class="num">256 像素 / 853 nm = 3.347 nm/px</span> 的硬體本身；單點峰位再準也就 1/10 個像素 ≈ 0.33 nm。所以這一台的正確表述不是「僅 2 點，不足以判色散」，而是<b>「僅能定平移；色散在本通道原理上不可測」</b>——前者是「我們沒量夠」，後者是「這台做不到，而且我們算得出來做不到」。</p>
<p style="margin:8px 0 0"><b>兩個帶走的東西：</b>(1) 增加資料點不等於增加資訊，<b>位置</b>才是；(2) 「量不到」和「不重要」在這裡剛好重合——一個小到躲得過七點擬合的色散誤差，攤在整條軸上也不到半個像素。</p>
</div>

<h3>想一想</h3>
<ol class="improve-list">
<li>把 USB2000 和 Hamamatsu 疊在一起看（兩台的波長範圍幾乎相同）。為什麼只有一台是斜的？如果你只量了 585–650 nm 這一小段，還分得出來嗎？</li>
<li>對 Avantes NIR 按「自動擬合：平移＋斜率」。rms 會變成 0——但這代表它沒有色散誤差嗎？（提示：兩個點永遠可以被一條直線完美穿過。）看完下面那個藍色方塊，再回答一次：要花多少錢，才能把這台的色散問題查清楚？</li>
<li>QEPro-532 的 C<sub>0</sub> 被填成 532.000，正好是標稱雷射波長。如果你是那個誤填的人，你當時可能在想什麼？要怎麼設計流程避免這件事？</li>
<li>八台裡六台是純平移。若某天一台原本純平移的儀器突然出現斜線指紋，最可能發生了什麼事？</li>
</ol>
</div>
</section>

<!-- ==================== 6 ==================== -->
<section id="laser">
<h2>6. 反解雷射波長：苯甲酸與咖啡因的交叉驗證</h2>
<div class="card">
<p>波長軸修好之後，剩下唯一的未知數就是 λ<sub>L</sub>。做法：把 OceanView 報告的位移還原成波長（它用 785.000 算的，所以可以精確反推）→ 套第 3 節的燈校正 → 再用「試驗 λ<sub>L</sub>」換算回位移 → 找一個 λ<sub>L</sub> 讓所有峰最貼近文獻值。</p>
<div class="flow">
  <span class="step">ν̃<sub>reported</sub></span><span class="arr">→</span>
  <span class="step">λ<sub>rep</sub> = 1/(1/785 − ν̃·10⁻⁷)</span><span class="arr">→</span>
  <span class="step">λ<sub>true</sub> = A·λ<sub>rep</sub> + B</span><span class="arr">→</span>
  <span class="step">ν̃ = 10⁷(1/λ<sub>L</sub> − 1/λ<sub>true</sub>)</span>
</div>
<h3>苯甲酸：環呼吸模不可能在 981</h3>
<p>單環取代苯的環呼吸振動是拉曼光譜裡最有名的峰之一：苯 992、甲苯 1004、苯甲酸 1001–1002 cm⁻¹。QEPro 報告它在 <b>981.0</b>——這不需要任何統計就知道錯了。</p>
<table>
<tr><th>OceanView 報告</th><th>文獻</th><th>原始誤差</th><th>修正後（λ<sub>L</sub>=__L_COMB__）</th><th>修正後誤差</th><th>相對強度</th></tr>
__BA_ROWS__
</table>
<figure><img src="__FIG4__" alt="修正前後" style="max-width:100%;border-radius:10px">
<figcaption>圖 4　藍＝OceanView 原始軸，紅＝修正後，灰線＝文獻峰位。修正後的紅線落在灰線上；藍線整體偏左 20 cm⁻¹。</figcaption></figure>
<h3>交叉驗證：兩個化學上無關的樣品，算出同一個雷射</h3>
<div class="metric-grid">
  <div class="metric"><strong>__L_BA__ nm</strong><span>苯甲酸單獨擬合（__L_BA_N__ 峰，rms __L_BA_RMS__）</span></div>
  <div class="metric"><strong>__L_CAF__ nm</strong><span>咖啡因單獨擬合（__L_CAF_N__ 峰，rms __L_CAF_RMS__）</span></div>
  <div class="metric"><strong>__L_COMB__ nm</strong><span>合併 __L_N__ 峰；rms __L_RMS__ cm⁻¹（硬用 785.000：__L_RMS785__）</span></div>
</div>
<p>兩個樣品的峰完全不同，卻給出相差不到 0.07 nm 的雷射波長；而且與 Im2000 Pro 波數軸隱含的 __I_LASER__ nm 也相符。標稱 785 nm 的二極體雷射實際落在 784.5–785.5 之間很常見，會隨溫度與電流漂移——這就是為什麼<b>雷射波長必須被當成一個要量的量，不是一個要抄的規格</b>。</p>
<h3>直接量測：把 USB4000 拿來當「第三把尺」</h3>
<p>反解出來的 784.56 nm 終究是推論。QEPro 看不到雷射線（雷射落在它前 4 個被遮罩的像素）、Im2000 Pro 的範圍從 789.9 nm 才開始，所以改用實驗室的通用型 <b>Ocean Optics USB4000</b>（345–1043 nm，3648 像素，約 0.19 nm/px）：先用燈檢查它自己的軸，再把雷射打在漫射面上收散射光。這一段做了兩次，因為第一次<b>做錯了</b>——而且錯得很有教育意義。</p>
<figure><img src="__FIG5__" alt="USB4000 雷射直接量測" style="max-width:100%;border-radius:10px">
<figcaption>圖 5　左：USB4000 波長軸的偏差。實心紅點＝Hg-Ar 黑光燈管、雷射開（700–950 nm 一致地偏低 0.51 ± 0.08 nm）；綠菱形＝同一支燈管、關雷射重量（7 條線 −0.50 ± 0.05）；空心藍圈＝一般日光燈（Ar 線弱，散布 ±0.17 且平均只有 −0.29）。熱像素已剔除。右：雷射線（紅）與同一台量到的 Ar 763.5 nm 燈線（綠）幾乎重疊——雷射本身很窄，紅側拖尾是這台儀器在此波段的線形。</figcaption></figure>
<table>
<tr><th>校正燈</th><th>785 附近 Ar 線峰高</th><th>700–950 nm 軸偏差（峰位法）</th><th>雷射修正後</th></tr>
<tr><td>一般日光燈（第一次）</td><td>700–1800 counts，SNR ≈ 10–20</td><td>−0.29 ± 0.17 nm（5 條線，散布大）</td><td>784.4 nm ← 和反解值差 0.2 nm，一度以為是雷射漂移</td></tr>
<tr><td><b>Hg-Ar 黑光燈管，雷射開（第二次）</b></td><td>2000–7900 counts，SNR ≈ 50–100</td><td><b>−0.51 ± 0.08 nm</b>（5 條線，一致；794.8 坐在雷射尾巴上不能用）</td><td><b>784.62 nm</b>；換用半高質心法 784.66</td></tr>
<tr><td><b>Hg-Ar 黑光燈管，關雷射、光纖直對燈管（第三次，500/750/1000 ms × 10）</b></td><td>2000–10 000 counts</td><td><b>−0.50 ± 0.05 nm</b>（7 條線；772.4 與 794.8 兩側夾住 785）</td><td><b>784.61 nm</b>（1000 ms）；三個積分時間平均 784.59</td></tr>
</table>
<div class="metric-grid">
  <div class="metric"><strong>784.11 nm</strong><span>雷射峰位（USB4000 原始軸）</span></div>
  <div class="metric"><strong>784.62 ± 0.07</strong><span>USB4000 直接量測（黑光燈校軸，四種估計散布 0.07，2026-09-04）</span></div>
  <div class="metric"><strong>784.56 ± 0.05</strong><span>由苯甲酸＋咖啡因反解（2026-08-19）</span></div>
</div>
<p>兩個完全獨立的方法——一個靠原子譜線與雷射的散射光，一個靠兩種固體的拉曼峰——在相隔兩週後給出<b>相差 0.06 nm（≈ 1 cm⁻¹）</b>的雷射波長。校正鏈閉合。</p>
<div class="card warnbox" style="margin-top:12px"><b>第一次為什麼錯？</b>日光燈的 Ar 線在 USB4000 上只有幾百到一千多 counts，峰頂是被雜訊啃過的平台，峰位估計散布 ±0.17 nm，而且系統性偏向零。換成 Hg-Ar 黑光燈管（同樣的 Ar 線強 3–7 倍），五條線的偏差立刻收斂到 ±0.08。這正是 Lellinger 等人跨十台儀器研究建議「校正峰 SNR 至少 100」的原因<span class="cite"><a href="#ref12">[12]</a></span>——<b>校正線的品質，比校正線的數量重要</b>。另一個細節：黑光燈那一檔是<b>雷射開著</b>量的（57 k counts，未飽和），所以軸檢查與雷射量測共用同一次曝光，儀器熱漂移一起抵消——這其實是比分兩次量更好的設計；代價是坐在雷射尾巴上的 Ar 794.8 nm 不能用，紅側只剩 811.5 nm 當錨點——所以第三次關掉雷射、光纖直對燈管再量（500/750/1000 ms × 10），把 794.8 加回來、兩側夾住 785，結果 784.61，與前一次一致到 0.01 nm。順帶一提：這次 365 nm 磷光體丘在 750 ms 以上就飽和了，但它和 Ar 線不在同一批像素，對峰位沒有影響——飽和只要不發生在你要用的線上就無妨。</div>
<div class="card tip" style="margin-top:12px"><b>一顆雷射，三把尺。</b>QEPro 與 Im2000 Pro 其實<b>共用同一顆 785 nm 雷射模組</b>。於是這顆雷射有三個彼此獨立的量測：Im2000 Pro 波數軸隱含 784.72（原廠校正時的值）、苯甲酸＋咖啡因反解 784.56（8/19）、USB4000 直接量測 784.62（9/04）。三者的散布 0.16 nm ≈ 2.6 cm⁻¹，就是「同一顆雷射在不同日期、不同方法下」的真實不確定度。實務上把 OceanView 與 IMSpectralSuite 的雷射設定都改成 784.6 即可，再用當天的 USB4000 值微調。</div>
<div class="card warnbox" style="margin-top:12px"><b>第二個陷阱：熱像素假扮譜線。</b>關掉雷射重量黑光燈的那一檔（<code>usb4000_blacklight_check2.csv</code>）沒有收到燈光，只剩雜訊——反而變成一張乾淨的<b>熱像素地圖</b>：558.0、607.6、634.0、702.6、715.6、764.6、917.9、1014.4 nm 這八個像素在每一檔裡都是單點尖峰。它們之前被當成「Hg 1014」「Ne 607/634/703」「2×Hg 870」寫進分析，全都是假的（真正的譜線至少寬 6–7 個像素）。判別方法很簡單：<b>沒有光源時還在的峰，就不是光</b>。剔除後雷射結果只動 0.02 nm，但圖 5 左邊那個 1014 nm 的點被拿掉了。</div>
<p class="small">資料：<code>unit1b_data/usb4000_blacklight_check.csv</code>、<code>usb4000_fl_lamp_check.csv</code>、<code>usb4000_785nm_check.csv</code>、<code>usb4000_blacklight_check2.csv</code>（熱像素地圖）、<code>usb4000_blacklight_check4_{500,750,1000}ms_avg10.csv</code>（關雷射燈譜）；腳本 <code>usb4000_laser_check.py</code>。USB4000 在 871.7 nm 沒有 2×Hg 435.8 的峰，代表它裝有 order-sorting 濾片——和 Im2000 Pro 不同。日常建議：每個量測日用 USB4000＋黑光燈管花兩分鐘記錄當天的 λ<sub>L</sub>。</p>
<div class="evidence-note"><b>誠實聲明。</b>① 苯甲酸與咖啡因都不在 ASTM E1840 名單裡<span class="cite"><a href="#ref1">[1]</a></span>，文獻峰位的不確定度約 1–2 cm⁻¹，所以本課的 λ<sub>L</sub> 不確定度約 ±0.05 nm（≈ ±1 cm⁻¹）；換不同的峰位質心方法（Python ALS 基線 vs R 滾動最小值）會讓 λ<sub>L</sub> 在 784.54–784.63 之間變動，這就是方法的極限。② 咖啡因有多晶型，但 Hédoux 等人證明 Form I/II 的差異主要在 100 cm⁻¹ 以下，100 以上的分子內振動幾乎不變<span class="cite"><a href="#ref5">[5]</a></span>。③ 苯甲酸曾被評估為 785 nm 光纖拉曼的次級校正物，但譜峰分布不均<span class="cite"><a href="#ref6">[6]</a></span>：1631 以上沒有峰，高波數端要靠咖啡因的 2953。④ 直接量測（上方 USB4000＋黑光燈管）給 784.62 ± 0.07 nm，與反解值一致到 0.06 nm；日常仍建議每次量測日記錄當天的 λ<sub>L</sub>（USB4000 兩分鐘，或矽晶圓 520.7 cm⁻¹——矽峰會隨功率與溫度位移<span class="cite"><a href="#ref9">[9]</a></span>）。</div>
</div>
</section>

<!-- ==================== 7 ==================== -->
<section id="unknown">
<h2>7. 未知樣品是什麼？校正後才敢比對</h2>
<div class="card">
<p>研究助理在 <code>unknown.xlsx</code> 存了一個沒標示的白色粉末。在原始軸上，它最強的兩個峰在 534 與 1309 cm⁻¹——查任何資料庫都對不到東西。套用修正後：</p>
<table>
<tr><th>原始</th><th>修正後</th><th>咖啡因文獻</th><th>誤差</th><th>相對強度</th></tr>
__CAF_ROWS__
</table>
<div class="metric-grid">
  <div class="metric"><strong>__U_CAF__ / __U_OF__</strong><span>峰對上咖啡因（平均 |誤差| __U_CAF_E__ cm⁻¹）</span></div>
  <div class="metric"><strong>__U_APAP__ / __U_OF__</strong><span>對上乙醯胺酚（平均 |誤差| __U_APAP_E__）</span></div>
  <div class="metric"><strong>__U_BA__ / __U_OF__</strong><span>對上苯甲酸</span></div>
</div>
<p>555（嘧啶環）與 1328 是咖啡因的招牌峰；1655/1700 是兩個 C=O；2953 是甲基 C–H。<b>它是咖啡因。</b>但請注意這個判定的邏輯順序：<b>先找峰 → 再問每個候選能解釋幾個峰</b>；不能反過來拿候選的峰位去譜上「找找看有沒有」，那樣什麼都對得上（R 版第一版就犯了這個錯，乙醯胺酚也對上 16/21）。</p>
<div class="card tip"><b>這件事和 Unit 6–7 的關係。</b>如果我們把<b>原始軸</b>的譜丟進 RamanBiolib 這類光譜資料庫去搜尋，會發生什麼？第 12 節用真實資料示範：Top-1 從「蔗糖」變成「胰島素」，相似度還高達 0.79。校正是所有後續分析的地基。</div>
</div>
</section>

<!-- ==================== 8 ==================== -->
<section id="compare">
<h2>8. 物理模型 vs Unit 1 的二次式</h2>
<div class="card">
<p>Unit 1 §12 用 19 個乙醯胺酚峰配出 <span class="num">y = −6.05×10⁻⁷x² + 0.99878x + 22.514</span>。本課的物理模型只有三個參數（A、B、λ<sub>L</sub>），而且每個都有物理意義。兩者給的修正量比一比：</p>
<table>
<tr><th>報告位移 x</th><th>Unit 1 二次式</th><th>本課物理模型</th><th>差</th></tr>
__CMP_ROWS__
</table>
<p>差異在 1–3 cm⁻¹ 之內，<b>與兩種方法各自的不確定度同量級</b>——所以 Unit 1 的二次式沒有錯，它是同一個物理現象的多項式近似。差別在於：</p>
<table>
<tr><th></th><th>Unit 1 二次式</th><th>物理模型</th></tr>
<tr><td>參數</td><td>3 個，無物理意義</td><td>3 個：波長軸斜率、截距、雷射波長</td></tr>
<tr><td>資料需求</td><td>一個跨全範圍的拉曼標準物</td><td>一支燈 + 任何一個已知拉曼標準物</td></tr>
<tr><td>外插</td><td>參考峰範圍外不可信<span class="cite"><a href="#ref3">[3]</a></span></td><td>由光柵幾何決定，外插行為受物理約束<span class="cite"><a href="#ref3">[3]</a></span></td></tr>
<tr><td>雷射漂移了怎麼辦</td><td>整條式重配</td><td>只改 λ<sub>L</sub> 一個數字</td></tr>
<tr><td>可解釋性</td><td>「就是這樣配比較準」</td><td>「波長軸偏 0.94 nm，雷射在 784.56」——可以拿去跟原廠溝通</td></tr>
</table>
<p class="small">為什麼本課的波長軸修正只用一次式？因為 QEPro 的原廠波長軸已經是三次多項式，燈只量到它整體偏了一個近乎常數的量（12 條線殘差 __Q_RES__ pm，看不出更高階的結構）。如果殘差有系統性彎曲，就該升到二次或三次<span class="cite"><a href="#ref10">[10]</a></span>。</p>
</div>
</section>

<!-- ==================== 9 ==================== -->
<section id="python">
<h2>9. Python 實作</h2>
<div class="card">
<p>完整腳本 <code>unit1b_calibration.py</code>（NumPy + SciPy + Matplotlib）會重算本課所有數字並輸出四張圖。這裡挑三段核心給你看：</p>
<span class="filehead">兩段式找線</span>
<pre><span class="kw">def</span> <span class="fn">locate_lines</span>(x, y, ref_lines, search_nm=<span class="num">2.5</span>, half_nm=<span class="num">0.9</span>):
    <span class="c"># 第 1 段：每條 NIST 線在 ±search_nm 找最大值，取偏移量的「中位數」當粗略偏移</span>
    rough = np.median([x[m][np.argmax(y[m])] - t
                       <span class="kw">for</span> t <span class="kw">in</span> ref_lines[<span class="st">"wavelength_air_nm"</span>]
                       <span class="kw">if</span> (m := (x &gt; t - search_nm) &amp; (x &lt; t + search_nm)).sum() &gt;= <span class="num">5</span>])
    <span class="c"># 第 2 段：以「真值 + 粗略偏移」為中心，±half_nm 做強度加權質心</span>
    out = []
    <span class="kw">for</span> t <span class="kw">in</span> ref_lines[<span class="st">"wavelength_air_nm"</span>]:
        w  = (x &gt; t + rough - half_nm) &amp; (x &lt; t + rough + half_nm)
        yy = y[w] - y[w].min()
        out.append((np.sum(x[w] * yy) / np.sum(yy), t))
    <span class="kw">return</span> out</pre>
<span class="filehead">燈校正：一次式</span>
<pre>obs, true = np.array(pairs).T
A, B = np.polyfit(obs, true, <span class="num">1</span>)          <span class="c"># λ_true = A·λ_reported + B</span>
<span class="fn">print</span>(A, B, (true - (A*obs + B)).std())  <span class="c"># __Q_A__  __Q_B__  ≈0.16 nm</span></pre>
<span class="filehead">反解雷射波長</span>
<pre><span class="kw">from</span> scipy.optimize <span class="kw">import</span> minimize_scalar
lam_rep  = <span class="num">1</span> / (<span class="num">1</span>/<span class="num">785.0</span> - x_reported * <span class="num">1e-7</span>)   <span class="c"># 還原 OceanView 的波長軸</span>
lam_true = A * lam_rep + B                       <span class="c"># 套燈校正</span>
<span class="kw">def</span> <span class="fn">rms</span>(laser):                                <span class="c"># 峰的 λ_true 換成位移，和文獻比</span>
    shift = <span class="num">1e7</span> * (<span class="num">1</span>/laser - <span class="num">1</span>/peak_lambda_true)
    <span class="kw">return</span> np.sqrt(np.mean((shift - literature)**<span class="num">2</span>))
laser = minimize_scalar(rms, bounds=(<span class="num">783.5</span>, <span class="num">786</span>), method=<span class="st">"bounded"</span>).x   <span class="c"># → __L_COMB__</span></pre>
<p class="small">腳本還做了一輪「剔除殘差 &gt; 5 cm⁻¹ 的峰再擬合」——被剔除的是苯甲酸 800（肩峰）與咖啡因 2953（文獻值本身分歧）。剔除規則要事先寫在程式裡，不能看結果再挑。</p>
</div>
</section>

<!-- ==================== 10 ==================== -->
<section id="rlang">
<h2>10. R 實作</h2>
<div class="card">
<p><code>unit1b_calibration.R</code> 只用 base R，不需安裝套件；燈校正的係數與 Python 版<b>完全相同</b>（都是最小平方），λ<sub>L</sub> 差 0.02 nm（峰位質心方法不同）。</p>
<span class="filehead">燈校正 + 反解雷射波長</span>
<pre>q     &lt;- locate_lines(lamp$wavelength_nm_reported, lamp$counts, USE_Q)
fit_q &lt;- lm(true_nm ~ obs_nm, data = q)          <span class="c"># λ_true = A·λ_reported + B</span>
A &lt;- coef(fit_q)[<span class="num">2</span>]; B &lt;- coef(fit_q)[<span class="num">1</span>]

lam_true &lt;- A * (<span class="num">1</span> / (<span class="num">1</span>/<span class="num">785</span> - x_rep * <span class="num">1e-7</span>)) + B
cost  &lt;- <span class="kw">function</span>(L) sqrt(mean((<span class="num">1e7</span> * (<span class="num">1</span>/L - <span class="num">1</span>/peak_lambda) - lit)^<span class="num">2</span>))
laser &lt;- optimize(cost, c(<span class="num">783.5</span>, <span class="num">786</span>))$minimum    <span class="c"># → 784.54</span></pre>
<p class="small">R 版第一次寫時，未知樣品辨識用「拿候選峰去譜上找」的方式，結果乙醯胺酚也對上 16/21——這是<b>確認偏誤</b>的程式版。改成「先找峰、再算每個候選解釋幾個」之後才變成 17 : 8 : 5。這個 bug 被刻意留在教材裡當反面教材。</p>
</div>
</section>

<!-- ==================== 11 ==================== -->
<section id="excel">
<h2>11. Excel 實作（LINEST + 網格搜尋）</h2>
<div class="card">
<p><code>unit1b_excel.xlsx</code> 有三張工作表，黃底是輸入、綠底是結果，全部用公式即時計算：</p>
<table>
<tr><th>工作表</th><th>做什麼</th><th>關鍵公式</th></tr>
<tr><td><b>1_燈校正</b></td><td>12 條線的觀測 vs 真值，LINEST 擬合 A、B</td><td><code>=INDEX(LINEST(真值範圍, 觀測範圍),1)</code> → A；<code>…,2)</code> → B</td></tr>
<tr><td><b>2_反解雷射波長</b></td><td>報告位移 → λ<sub>rep</sub> → λ<sub>true</sub> → 修正位移；改 D4 的試驗 λ<sub>L</sub> 看 rms</td><td><code>=1/(1/$D$3-A8*1E-7)</code>、<code>=1E7*(1/$D$4-1/D8)</code>；下方用 <b>網格搜尋</b>（784.20→785.00 每 0.05）列出 rms，<code>INDEX/MATCH(MIN)</code> 找最小</td></tr>
<tr><td><b>3_雙誤差拆解</b></td><td>改 Δλ 與真實 λ<sub>L</sub>，看三條誤差曲線</td><td><code>=1E7*(1/$D$4-1/(B8+$D$3))-A8</code></td></tr>
</table>
<p>網格搜尋是「不會用 Solver 也能做最佳化」的教學版：把候選值全部列出來、算每個的 rms、挑最小的。它比 Solver 慢，但<b>看得見整條曲線</b>——你會發現 rms 對 λ<sub>L</sub> 是一個很尖的 V 形，這就是為什麼兩個樣品能給出一致到 0.07 nm 的答案。</p>
</div>
</section>

<!-- ==================== 12 ==================== -->
<section id="library">
<h2>12. 校正錯了會怎樣：資料庫搜尋崩潰</h2>
<div class="card">
<p>Unit 6–7 會用 RamanBiolib（Terán 等人 2025 年公開的生物分子拉曼資料庫，202 條譜、141 種成分<span class="cite"><a href="#ref11">[11]</a></span>）做光譜相似度搜尋。我們拿 Im2000 Pro 量的四種真實食品成分（蔗糖、葡萄糖、果糖、檸檬酸；它的波數軸是好的），先用正確的軸搜尋，再<b>把 QEPro 實測到的誤差函數套上去</b>——模擬「如果這些樣品是用未校正的 QEPro 量的」——再搜尋一次：</p>
<table>
<tr><th>樣品（真實光譜）</th><th>正確軸：Top-1 / 排名</th><th>套上 QEPro 誤差（−20 cm⁻¹）：Top-1 / 排名</th></tr>
<tr><td>蔗糖 d-(+)-sucrose</td><td><span class="tag ok">✔ 蔗糖</span> 0.911，第 1</td><td><span class="tag no">✘ 胰島素 insulin</span> 0.789，蔗糖掉到第 <b>37</b></td></tr>
<tr><td>葡萄糖 d-(+)-glucose</td><td><span class="tag ok">✔ 葡萄糖</span> 0.899，第 1</td><td><span class="tag no">✘ 木聚糖酶 xylanase</span> 0.783，第 <b>38</b></td></tr>
<tr><td>果糖 d-(−)-fructose</td><td><span class="tag ok">✔ 果糖</span> 0.873，第 1</td><td><span class="tag no">✘ 胰島素</span> 0.727，第 <b>88</b></td></tr>
<tr><td>檸檬酸 citric acid</td><td><span class="tag ok">✔ 檸檬酸</span> 0.804，第 1</td><td><span class="tag no">✘ 磷酸丙糖異構酶</span> 0.726，第 <b>109</b></td></tr>
</table>
<p>四種糖與酸，全部被辨識成<b>蛋白質</b>，而且相似度還有 0.73–0.79——足以讓一個沒有戒心的學生寫進報告。這不是資料庫的錯、也不是演算法的錯，是<b>橫軸錯了 20 cm⁻¹</b>。Cosine 相似度比的是「同一個波數位置的強度」，整條譜平移 20 cm⁻¹（約 10 個資料點）後，糖的峰對到了蛋白質的峰。</p>
<p>還有一個更陰險的情況：<b>咖啡因根本不在 RamanBiolib 裡</b>。把校正好的咖啡因譜丟進去，Top-1 是「胃蛋白酶 pepsin」0.66。資料庫只會回答「最像誰」，不會回答「有沒有在裡面」——這正是 Unit 6–7 教材反覆強調的「候選 ≠ 確證」。</p>
<div class="card keybox"><b>橋接練習</b>（在 <code>ramanbiolib_teaching/notebooks/03_advanced_evaluation.ipynb</code> 第 6 節）：載入 Im2000 的蔗糖譜，用 <code>qepro_error()</code> 套上本課的誤差函數，跑 Cosine 與 PM（容差 0/2/5/10）搜尋，回答：容差開到 10 cm⁻¹ 救得回來嗎？（劇透：救不回來，因為 20 &gt; 10；但套用本課的修正式之後排名回到第 1。）</div>
</div>
</section>

<!-- ==================== 13 ==================== -->
<section id="quiz">
<h2>13. 隨堂測驗：檢查你的學習成效</h2>
<div class="card">
<p>共十題：<b>八題觀念選擇＋兩題計算填空</b>，數字全部來自本課的真實資料。作答完成按下批改。</p>

<div class="qq" data-q="1">
<h4>Q1（觀念）量日光燈的時候雷射是關的。這代表燈校正檢查的是什麼？</h4>
<label><input type="radio" name="q1" value="a"> 雷射的真實波長</label>
<label><input type="radio" name="q1" value="b"> 像素 → 波長的對應（波長軸），與雷射無關</label>
<label><input type="radio" name="q1" value="c"> 樣品的螢光背景</label>
<label><input type="radio" name="q1" value="d"> 拉曼位移軸，包含雷射</label>
<div class="fb"></div>
</div>

<div class="qq" data-q="2">
<h4>Q2（計算）QEPro 波長軸偏低 0.94 nm。在散射波長 850 nm 處，這會造成多少 cm⁻¹ 的位移誤差？（用 Δν̃ ≈ 10⁷·Δλ/λ²；±1 內算對）</h4>
<div style="display:flex;gap:10px;align-items:center"><input type="number" id="q2in" step="any" placeholder="輸入數字"><span>cm⁻¹</span></div>
<div class="fb"></div>
</div>

<div class="qq" data-q="3">
<h4>Q3（判讀）實測誤差從低波數的 −23 cm⁻¹ 變到高波數的 −15 cm⁻¹。這個「隨波數變小」的形狀，主要是哪個來源的指紋？</h4>
<label><input type="radio" name="q3" value="a"> 雷射波長設錯（它應該是常數）</label>
<label><input type="radio" name="q3" value="b"> 波長軸偏移（因為 Δν̃ ∝ 1/λ²）</label>
<label><input type="radio" name="q3" value="c"> 螢光背景</label>
<label><input type="radio" name="q3" value="d"> 光纖換了</label>
<div class="fb"></div>
</div>

<div class="qq" data-q="4">
<h4>Q4（觀念）Im2000 Pro 燈譜裡最強的峰在 873 nm。它是什麼？</h4>
<label><input type="radio" name="q4" value="a"> Ar I 的一階線</label>
<label><input type="radio" name="q4" value="b"> Hg 435.8 nm 的二階繞射（2 × 435.8 ≈ 871.7）</label>
<label><input type="radio" name="q4" value="c"> 雷射線</label>
<label><input type="radio" name="q4" value="d"> 宇宙射線</label>
<div class="fb"></div>
</div>

<div class="qq" data-q="5">
<h4>Q5（驗證設計）為什麼用「苯甲酸」和「咖啡因」兩個樣品分別反解雷射波長，比只用一個更有說服力？</h4>
<label><input type="radio" name="q5" value="a"> 兩個樣品加起來峰比較多，統計比較好看</label>
<label><input type="radio" name="q5" value="b"> 它們的峰位彼此無關，若各自算出的 λ<sub>L</sub> 一致，代表結果不是某個樣品的文獻值湊出來的</label>
<label><input type="radio" name="q5" value="c"> 因為 ASTM 規定要兩種</label>
<label><input type="radio" name="q5" value="d"> 咖啡因比較便宜</label>
<div class="fb"></div>
</div>

<div class="qq" data-q="6">
<h4>Q6（計算）修正後未知樣品最強峰在 555.8 cm⁻¹，雷射為 784.56 nm。這個峰的散射波長是多少 nm？（λ = 1/(1/λ<sub>L</sub> − ν̃·10⁻⁷)；±0.5 內算對）</h4>
<div style="display:flex;gap:10px;align-items:center"><input type="number" id="q6in" step="any" placeholder="輸入數字"><span>nm</span></div>
<div class="fb"></div>
</div>

<div class="qq" data-q="7">
<h4>Q7（推論邊界）把校正好的咖啡因譜丟進 RamanBiolib，Top-1 是「胃蛋白酶 pepsin」0.66。正確的解讀是？</h4>
<label><input type="radio" name="q7" value="a"> 樣品可能是胃蛋白酶</label>
<label><input type="radio" name="q7" value="b"> 校正還是錯的</label>
<label><input type="radio" name="q7" value="c"> 資料庫只回答「最像誰」；咖啡因不在庫裡，所以任何 Top-1 都不是確證，要先確認資料庫覆蓋</label>
<label><input type="radio" name="q7" value="d"> 相似度 0.66 已經夠高，可以下結論</label>
<div class="fb"></div>
</div>

<div class="qq" data-q="8">
<h4>Q8（方法）Unit 1 的二次式和本課的物理模型修正量只差 1–3 cm⁻¹。下列哪個說法最恰當？</h4>
<label><input type="radio" name="q8" value="a"> 二次式是錯的，應該全部改用物理模型</label>
<label><input type="radio" name="q8" value="b"> 兩者是同一個現象的不同近似；物理模型多了可解釋性與外插約束，雷射漂移時只需改一個參數</label>
<label><input type="radio" name="q8" value="c"> 物理模型是錯的，因為它用了非 ASTM 物質</label>
<label><input type="radio" name="q8" value="d"> 差 1–3 cm⁻¹ 代表兩者都不能用</label>
<div class="fb"></div>
</div>


<div class="qq" data-q="9">
<h4>Q9（判讀）把「報告 − 真實」對真實波長畫出來，得到一條明顯向下傾斜的直線。這代表哪一個波長校正係數出了問題？</h4>
<label><input type="radio" name="q9" value="a"> 只有 C₀（軸的起點）</label>
<label><input type="radio" name="q9" value="b"> C₁（色散），也就是整條軸被拉長或壓縮</label>
<label><input type="radio" name="q9" value="c"> 雷射波長設定</label>
<label><input type="radio" name="q9" value="d"> 感測器的暗電流</label>
<div class="fb"></div>
</div>

<div class="qq" data-q="10">
<h4>Q10（方法）某台儀器用日光燈校正，長波端只有一條譜線，該線重覆量三次的 SD 只有 15 pm。下列推論何者正確？</h4>
<label><input type="radio" name="q10" value="a"> SD 只有 15 pm，所以這條線的位置很準確，斜率可信</label>
<label><input type="radio" name="q10" value="b"> 重覆性好只代表精密度好；若該線微弱又坐在強背景上，位置仍可能系統性偏掉上百 pm，斜率不可信</label>
<label><input type="radio" name="q10" value="c"> 只要增加積分時間就能解決</label>
<label><input type="radio" name="q10" value="d"> 一條線就足夠定斜率，不必再找其他線</label>
<div class="fb"></div>
</div>

<button class="btn" onclick="grade()">批改</button>
<div id="scoreBox"></div>
</div>
</section>

<!-- ==================== 14 ==================== -->
<section id="homework">
<h2>14. 重點整理與練習</h2>
<div class="card">
<h3>三大重點</h3>
<ol class="improve-list">
<li><b>位移＝兩個數字的差。</b>ν̃ = 10⁷(1/λ<sub>L</sub> − 1/λ)：波長軸與雷射波長各自都可能錯，而且指紋不同——前者隨波數變小，後者是常數。看實測誤差的<b>斜率</b>就能分辨。</li>
<li><b>兩把尺各司其職。</b>原子燈只校波長軸、分得開兩個來源；拉曼標準物一步到位、但分不開。兩步法（燈 → 矽/ASTM）是業界慣例。</li>
<li><b>校正是地基。</b>20 cm⁻¹ 的錯會讓資料庫把糖辨識成蛋白質、相似度還有 0.79。任何相似度、分類、定量都建立在橫軸正確之上。</li>
</ol>
<h3>練習題</h3>
<ol class="improve-list">
<li>用 <code>qepro_light2_ArHg_lamp.csv</code>（另一條光纖）重跑第 3 節，報告 A、B 與 12 條線殘差。它和 light1 的結果差多少？這告訴你什麼？</li>
<li>把第 5 節旋鈕實驗的「硬用一個旋鈕湊」情境用 Excel 工作表 3 重現：Δλ 設多少可以讓 1001 cm⁻¹ 的誤差歸零？此時 2953 cm⁻¹ 差多少？</li>
<li>Im2000 Pro 的 nm 軸偏高 1.36 nm。如果有人用這條 nm 軸、雷射設 785.000 去算位移，1328 cm⁻¹ 的咖啡因峰會被報成多少？（提示：先算 λ，加 1.36，再換回位移。）</li>
<li>設計一張「每日開機確認表」：要量什麼、看哪個峰、允收多少、超出時第一步做什麼。限一頁。</li>
<li>（進階）NIST ASD 查 Ne I 在 780–1030 nm 的譜線。如果換一支 Ne 燈，可用的線變多還是變少？哪一段波數會多出錨點？</li>
</ol>
</div>
</section>

<!-- ==================== 15 ==================== -->
<section id="data">
<h2>15. 資料包與可重現性</h2>
<div class="card data-quality">
<p>本課所有數字都能從 <code>unit1b_data/</code> 的 7 個 CSV 用 <code>unit1b_calibration.py</code> 或 <code>unit1b_calibration.R</code> 重算；<code>README_unit1b_data.md</code> 列有每個檔案的 SHA-256、來源轉換與量測條件表（量測者尚需補齊功率、積分、光纖等欄位）。這回應了 Unit 1 §16 第 8 項「封裝可重現資料包」，也補上 <code>report-source.md</code> 指出的「QEPro 原始 CSV 缺失」。</p>
<table>
<tr><th>檔案</th><th>內容</th></tr>
<tr><td><code>qepro_light1 / light2_ArHg_lamp.csv</code></td><td>QEPro 日光燈譜，兩條光纖</td></tr>
<tr><td><code>qepro_benzoic_acid_3reps.csv</code></td><td>苯甲酸 3 次重複（互相關 0.995–0.998）</td></tr>
<tr><td><code>qepro_unknown_sample.csv</code></td><td>未知樣品（第 7 節辨識為咖啡因）</td></tr>
<tr><td><code>im2000_light_ArHg_lamp_axes.csv</code></td><td>Im2000 Pro 燈譜，pixel / nm / wavenumber 三軸併表</td></tr>
<tr><td><code>reference_lines_ArHg_NIST_air.csv</code></td><td>使用的 NIST 譜線（空氣中波長）含二階位置</td></tr>
<tr><td><code>reference_raman_peaks_literature.csv</code></td><td>苯甲酸、咖啡因文獻峰位（非認證值）</td></tr>
<tr><td><code>usb4000_blacklight_check.csv</code> / <code>usb4000_fl_lamp_check.csv</code> / <code>usb4000_785nm_check.csv</code> / <code>usb4000_blacklight_check2.csv</code></td><td>USB4000 黑光燈管（Hg-Ar）、日光燈、雷射線直接量測與熱像素地圖（§6）</td></tr>
<tr><td><code>unit1b_excel.xlsx</code></td><td>Excel 三軌實作</td></tr>
</table>
<p class="small">原始檔不覆寫；修正版由腳本另存為 <code>qepro_unknown_sample_CORRECTED.csv</code>。建置日期：__DATE__。</p>
</div>
</section>

<!-- ==================== 16 ==================== -->
<section id="references">
<h2>16. 參考文獻</h2>
<div class="card">
<ol class="references">
<li id="ref1">ASTM E1840-96(2022). <i>Standard Guide for Raman Shift Standards for Spectrometer Calibration.</i> ASTM International. <a href="https://doi.org/10.1520/E1840-96R22">doi:10.1520/E1840-96R22</a></li>
<li id="ref2">Kramida, A., Ralchenko, Yu., Reader, J., &amp; NIST ASD Team. <i>NIST Atomic Spectra Database</i> (ver. 5). National Institute of Standards and Technology. <a href="https://physics.nist.gov/asd">physics.nist.gov/asd</a>, <a href="https://doi.org/10.18434/T4W30F">doi:10.18434/T4W30F</a>（Ar I、Hg I 空氣中波長）</li>
<li id="ref3">Liu, D., &amp; Hennelly, B. M. (2024). Wavenumber calibration protocol for Raman spectrometers using physical modelling and a fast search algorithm. <i>Applied Spectroscopy</i>. <a href="https://doi.org/10.1177/00037028241254847">doi:10.1177/00037028241254847</a></li>
<li id="ref4">Fountain, A. W., Mann, C. K., &amp; Vickers, T. J. (1995). Routine wavenumber calibration of an FT-Raman spectrometer. <i>Applied Spectroscopy</i>, 49(7), 1048–1053. <a href="https://doi.org/10.1366/0003702953964886">doi:10.1366/0003702953964886</a>（以原子譜線做波數標準）</li>
<li id="ref5">Hédoux, A., Guinet, Y., Paccou, L., Danède, F., &amp; Derollez, P. (2011). Low- and high-frequency Raman investigations on caffeine: polymorphism, disorder and phase transformation. <i>Journal of Physical Chemistry B</i>. <a href="https://doi.org/10.1021/jp112074w">doi:10.1021/jp112074w</a></li>
<li id="ref6">Salinas-Luna, J., Mentado-Morales, J., &amp; Ximello, A. (2025). DMSO: a potential wavenumber calibrator of a coupled optical fiber Raman spectrograph. <i>Physica Scripta</i>, 100(12), 125535. <a href="https://doi.org/10.1088/1402-4896/ae296a">doi:10.1088/1402-4896/ae296a</a>（苯甲酸作為 785 nm 次級校正物的評估）</li>
<li id="ref7">Liu, D., Hennelly, B. M., &amp; O'Neill, L. (2018). Investigation of wavenumber calibration for Raman spectroscopy using a polymer standard. <i>Proc. SPIE</i>. <a href="https://doi.org/10.1117/12.2307574">doi:10.1117/12.2307574</a>（兩步法 vs 一步法）</li>
<li id="ref8">Itoh, N. (2023). Verification of Si wafer first-order phonon peaks for reliable calibration of Raman microscopes. <i>Journal of Raman Spectroscopy</i>, 55(3), 377–385. <a href="https://doi.org/10.1002/jrs.6630">doi:10.1002/jrs.6630</a>（Ne 線校波長 + 雷射真空波數的兩步作法）</li>
<li id="ref9">同上（Itoh 2023）：矽 520 cm⁻¹ 峰位隨溫度與雷射功率位移的量化。</li>
<li id="ref10">Carter, D. A., Thompson, W. R., Taylor, C. E., &amp; Pemberton, J. E. (1995). Frequency/wavelength calibration of multipurpose multichannel Raman spectrometers. <i>Applied Spectroscopy</i>, 49(11). <a href="https://doi.org/10.1366/0003702953965687">doi:10.1366/0003702953965687</a></li>
<li id="ref11">Terán, M., et al. (2025). Open Raman spectral library for biomolecule identification. <i>Chemometrics and Intelligent Laboratory Systems</i>, 264, 105476. <a href="https://doi.org/10.1016/j.chemolab.2025.105476">doi:10.1016/j.chemolab.2025.105476</a>；RamanBiolib：<a href="https://github.com/mteranm/ramanbiolib">github.com/mteranm/ramanbiolib</a>（程式 GPL-3.0，資料 ODbL-1.0）</li>
<li id="ref12">Lellinger, D., et al. (2025). Interlaboratory comparison of Raman shift calibration across ten instruments. <i>Applied Spectroscopy</i>. <a href="https://doi.org/10.1177/00037028251330654">doi:10.1177/00037028251330654</a>（校正峰 SNR 建議 ≥ 100；引自 Unit 1 參考文獻 [5]）</li>
</ol>
<div class="evidence-note">文內引註只支持所標示的具體主張。苯甲酸與咖啡因的文獻峰位彙整自多篇常規拉曼研究，未逐一列出；正式工作請以 ASTM E1840 材料或可溯源的雷射波長量測為準。</div>
</div>
</section>

<footer>
Unit 1B · 兩台 785 nm 拉曼光譜儀的體檢 · QEPro（QEP05121）× Im2000 Pro · 日光燈 Ar/Hg 譜線、苯甲酸、咖啡因 · Python / R / Excel · 建置 __DATE__
</footer>
</div>

<script>
// ---------- 二階繞射換算器 ----------
(function(){
  var v=document.getElementById('vis');
  function upd(){var x=parseFloat(v.value)||0;document.getElementById('vis2').textContent=(2*x).toFixed(3);document.getElementById('vis3').textContent=(3*x).toFixed(1);}
  v.addEventListener('input',upd);upd();
})();

// ---------- 雙誤差旋鈕實驗 ----------
var PTS=__PTS__;
var Q_A=__Q_A_RAW__, Q_B=__Q_B_RAW__;
function shiftFromLam(l,L){return 1e7*(1/L-1/l);}
function lamFromShift(s,L){return 1/(1/L-s*1e-7);}
function modelErr(nu,dl,LL){ // 真實位移 nu（相對真實雷射 LL）；儀器波長軸偏 dl；軟體用 785.000
  var lam=lamFromShift(nu,LL); return shiftFromLam(lam+dl,785.0)-nu;
}
function setLab(dl,LL){document.getElementById('dl').value=dl;document.getElementById('ll').value=LL;drawLab();}
function drawLab(){
  var dl=parseFloat(document.getElementById('dl').value), LL=parseFloat(document.getElementById('ll').value);
  document.getElementById('dlv').textContent=(dl>=0?'+':'')+dl.toFixed(2);document.getElementById('llv').textContent=LL.toFixed(2);
  var c=document.getElementById('labc'),ctx=c.getContext('2d'),W=c.width,H=c.height;
  var ml=76,mr=22,mt=22,mb=52,x0=250,x1=3050,y0=-32,y1=8;
  function X(v){return ml+(v-x0)/(x1-x0)*(W-ml-mr);} function Y(v){return mt+(y1-v)/(y1-y0)*(H-mt-mb);}
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='#e2e8f0';ctx.lineWidth=1;ctx.font='16px sans-serif';ctx.fillStyle='#64748b';ctx.textAlign='right';
  for(var g=-30;g<=5;g+=5){ctx.beginPath();ctx.moveTo(ml,Y(g));ctx.lineTo(W-mr,Y(g));ctx.stroke();ctx.fillText(g,ml-8,Y(g)+4);}
  ctx.textAlign='center';for(var gx=500;gx<=3000;gx+=500){ctx.fillText(gx,X(gx),H-mb+18);}
  ctx.fillText('文獻拉曼位移 (cm⁻¹)',(ml+W-mr)/2,H-6);
  ctx.save();ctx.translate(14,H/2);ctx.rotate(-Math.PI/2);ctx.fillText('報告值 − 真值 (cm⁻¹)',0,0);ctx.restore();
  ctx.strokeStyle='#64748b';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(ml,Y(0));ctx.lineTo(W-mr,Y(0));ctx.stroke();
  // 三條曲線
  function curve(fn,color,dash){ctx.strokeStyle=color;ctx.lineWidth=2.2;ctx.setLineDash(dash);ctx.beginPath();
    for(var i=0;i<=120;i++){var nu=x0+(x1-x0)*i/120,e=fn(nu);if(i==0)ctx.moveTo(X(nu),Y(e));else ctx.lineTo(X(nu),Y(e));}ctx.stroke();ctx.setLineDash([]);}
  curve(function(nu){return modelErr(nu,dl,785.0);},'#0d9488',[8,6]);
  curve(function(nu){return modelErr(nu,0,LL);},'#4f46e5',[2,5]);
  curve(function(nu){return modelErr(nu,dl,LL);},'#1e293b',[]);
  // 實測點
  var se=0;PTS.forEach(function(p){var m=modelErr(p[0],dl,LL);se+=(m-p[1])*(m-p[1]);
    ctx.fillStyle=p[2]=='BA'?'#dc2626':'#b45309';ctx.beginPath();
    if(p[2]=='BA'){ctx.arc(X(p[0]),Y(p[1]),5,0,6.283);}else{ctx.moveTo(X(p[0]),Y(p[1])-6);ctx.lineTo(X(p[0])+6,Y(p[1])+5);ctx.lineTo(X(p[0])-6,Y(p[1])+5);ctx.closePath();}
    ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1.2;ctx.stroke();});
  // 圖例
  ctx.font='16px sans-serif';ctx.textAlign='left';var lx=ml+12,ly=mt+14;
  [['#0d9488','只有波長軸偏移',[8,6]],['#4f46e5','只有雷射設錯',[2,5]],['#1e293b','兩者相加',[]]].forEach(function(l,i){ctx.strokeStyle=l[0];ctx.lineWidth=2.2;ctx.setLineDash(l[2]);ctx.beginPath();ctx.moveTo(lx,ly+i*18);ctx.lineTo(lx+30,ly+i*18);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#1e293b';ctx.fillText(l[1],lx+38,ly+i*18+4);});
  ctx.fillStyle='#dc2626';ctx.beginPath();ctx.arc(lx+170,ly,5,0,6.283);ctx.fill();ctx.fillStyle='#1e293b';ctx.fillText('苯甲酸實測',lx+180,ly+4);
  ctx.fillStyle='#b45309';ctx.beginPath();ctx.moveTo(lx+170,ly+18-6);ctx.lineTo(lx+176,ly+18+5);ctx.lineTo(lx+164,ly+18+5);ctx.closePath();ctx.fill();ctx.fillStyle='#1e293b';ctx.fillText('咖啡因實測',lx+180,ly+22);
  document.getElementById('rms').textContent=Math.sqrt(se/PTS.length).toFixed(2);
  document.getElementById('e1001').textContent=modelErr(1001,dl,LL).toFixed(1)+' cm⁻¹';
  document.getElementById('e2953').textContent=modelErr(2953,dl,LL).toFixed(1)+' cm⁻¹';
}
document.getElementById('dl').addEventListener('input',drawLab);document.getElementById('ll').addEventListener('input',drawLab);drawLab();


// ---------- 5B 指紋盲測實驗 ----------
var SURVEY=__SURVEY__;
var BLIND=['丁','乙','戊','甲','庚','丙','己','辛'];   // 固定打亂，讓盲測不按表順序
var cur2=0, revealed=false, judged=false;
(function(){
  var box=document.getElementById('instchips');
  SURVEY.forEach(function(s,i){
    var b=document.createElement('button');b.className='chip';b.id='ic'+i;
    b.textContent='儀器 '+BLIND[i];b.onclick=function(){cur2=i;resetLab2();};
    box.appendChild(b);
  });
  var rows=document.getElementById('surveyRows');
  SURVEY.forEach(function(s){
    var tr=document.createElement('tr');
    tr.innerHTML='<td>'+s.name+'</td><td class="num">'+s.rng[0].toFixed(1)+'–'+s.rng[1].toFixed(1)+'</td>'+
      '<td class="num">'+s.nmpx.toFixed(3)+'</td><td class="num">'+s.pts.length+'</td>'+
      '<td class="num" style="font-size:13px">'+s.formula+'</td><td class="num">'+s.rms+'</td>'+
      '<td><span style="color:'+(s.model=='linear'?'var(--warn)':'var(--ok)')+';font-weight:700">'+
      (s.vlabel||(s.model=='linear'?'色散誤差':'純平移'))+'</span>'+
      (s.note?'<div class="small" style="margin-top:3px;line-height:1.45">'+s.note+'</div>':'')+'</td>';
    rows.appendChild(tr);
  });
})();
function lab2ref(){var s=SURVEY[cur2];return (s.pts[0][0]+s.pts[s.pts.length-1][0])/2;}
function lab2model(lam,o,sl,cu){var d=lam-lab2ref();return o+sl*1e-6*d+cu*1e-6*d*d/100;}
function fitPoly(deg){
  var s=SURVEY[cur2],r=lab2ref(),n=s.pts.length;
  var X=[],Y=[];
  for(var i=0;i<n;i++){var d=s.pts[i][0]-r,row=[1];if(deg>=1)row.push(d*1e-6);if(deg>=2)row.push(d*d*1e-6/100);X.push(row);Y.push(s.pts[i][1]);}
  var m=deg+1,A=[],B=[];
  for(var a=0;a<m;a++){A.push([]);var sb=0;for(var b=0;b<m;b++){var sa=0;for(i=0;i<n;i++)sa+=X[i][a]*X[i][b];A[a].push(sa);}
    for(i=0;i<n;i++)sb+=X[i][a]*Y[i];B.push(sb);}
  for(a=0;a<m;a++){var p=A[a][a];if(Math.abs(p)<1e-30)return null;
    for(b=a;b<m;b++)A[a][b]/=p;B[a]/=p;
    for(var k=0;k<m;k++){if(k==a)continue;var f=A[k][a];for(b=a;b<m;b++)A[k][b]-=f*A[a][b];B[k]-=f*B[a];}}
  return B;
}
function rmsOf(o,sl,cu){var s=SURVEY[cur2],e=0;
  s.pts.forEach(function(p){var d=lab2model(p[0],o,sl,cu)-p[1];e+=d*d;});
  return Math.sqrt(e/s.pts.length)*1000;}
function autoFit(deg){
  var c=fitPoly(deg);if(!c)return;
  setSliders(c[0],deg>=1?c[1]:0,deg>=2?c[2]:0);
}
function setSliders(o,sl,cu){
  document.getElementById('off').value=Math.max(-10,Math.min(10,o));
  document.getElementById('slp').value=Math.max(-3000,Math.min(3000,sl));
  document.getElementById('cur').value=Math.max(-40,Math.min(40,cu));
  drawLab2();
}
function resetLab2(){revealed=false;judged=false;
  document.getElementById('revealBox').style.display='none';
  document.getElementById('revealBtn').textContent='顯示答案';
  document.getElementById('judgefb').textContent='';setSliders(0,0,0);}
function judge(g){
  var s=SURVEY[cur2],fb=document.getElementById('judgefb');
  if(s.pts.length<4){judged=true;fb.style.color='var(--muted)';
    fb.textContent='　只有 '+s.pts.length+' 個點——不管猜哪個都無法驗證，這本身就是答案。';drawLab2();return;}
  var truth=s.model; judged=true;
  fb.style.color=(g===truth)?'#16a34a':'#dc2626';
  fb.textContent=(g===truth?'　✔ 判斷正確':'　✘ 再看一次形狀')+'　（下方統計已解鎖）';
  drawLab2();
}
function toggleReveal(){
  revealed=!revealed;if(revealed)judged=true;var s=SURVEY[cur2],box=document.getElementById('revealBox');
  document.getElementById('revealBtn').textContent=revealed?'回到盲測':'顯示答案';
  box.style.display=revealed?'block':'none';
  if(revealed)box.innerHTML='<b>'+s.name+'</b>（'+s.rng[0].toFixed(1)+'–'+s.rng[1].toFixed(1)+' nm，'+s.px+' px，'+
    s.nmpx.toFixed(3)+' nm/px）<br>採用模型：<b style="color:'+(s.model=='linear'?'var(--warn)':'var(--ok)')+'">'+
    (s.model=='linear'?'線性（有色散誤差）':'純平移')+'</b>　<span class="num">'+s.formula+'</span>　殘差 rms '+s.rms+
    '<br><span class="small">'+s.note+'</span>';
  drawLab2();
}
function drawLab2(){
  var s=SURVEY[cur2];
  var o=parseFloat(document.getElementById('off').value),
      sl=parseFloat(document.getElementById('slp').value),
      cu=parseFloat(document.getElementById('cur').value);
  document.getElementById('offv').textContent=(o>=0?'+':'')+o.toFixed(2);
  document.getElementById('slpv').textContent=(sl>=0?'+':'')+sl.toFixed(0);
  document.getElementById('curv').textContent=(cu>=0?'+':'')+cu.toFixed(1);
  SURVEY.forEach(function(_,i){var b=document.getElementById('ic'+i);
    b.style.background=(i==cur2)?'var(--brand)':'';b.style.color=(i==cur2)?'#fff':'';
    b.textContent=revealed&&i==cur2?s.short:'儀器 '+BLIND[i];});
  var c=document.getElementById('lab2c'),ctx=c.getContext('2d'),W=c.width,H=c.height;
  var ml=86,mr=22,mt=22,mb=54;
  var xs=s.pts.map(function(p){return p[0];}),ys=s.pts.map(function(p){return p[1];});
  var xlo=Math.min.apply(null,xs),xhi=Math.max.apply(null,xs),pad=(xhi-xlo)*0.10+4;
  xlo-=pad;xhi+=pad;
  var mv=[];for(var i=0;i<=120;i++){mv.push(lab2model(xlo+(xhi-xlo)*i/120,o,sl,cu));}
  var ylo=Math.min(Math.min.apply(null,ys),Math.min.apply(null,mv)),
      yhi=Math.max(Math.max.apply(null,ys),Math.max.apply(null,mv));
  var yp=Math.max((yhi-ylo)*0.25,0.06);ylo-=yp;yhi+=yp;
  function X(v){return ml+(v-xlo)/(xhi-xlo)*(W-ml-mr);}
  function Y(v){return mt+(yhi-v)/(yhi-ylo)*(H-mt-mb);}
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
  // 格線
  var step=Math.pow(10,Math.floor(Math.log(yhi-ylo)/Math.LN10-0.5));
  if((yhi-ylo)/step>8)step*=2;if((yhi-ylo)/step>8)step*=2.5;
  ctx.font='16px sans-serif';ctx.strokeStyle='#e2e8f0';ctx.lineWidth=1;ctx.fillStyle='#64748b';ctx.textAlign='right';
  for(var g=Math.ceil(ylo/step)*step;g<=yhi;g+=step){
    ctx.beginPath();ctx.moveTo(ml,Y(g));ctx.lineTo(W-mr,Y(g));ctx.stroke();
    ctx.fillText(Math.abs(g)<1e-9?'0':g.toFixed(step<0.1?2:(step<1?1:0)),ml-8,Y(g)+4);}
  ctx.textAlign='center';
  var xstep=Math.pow(10,Math.floor(Math.log(xhi-xlo)/Math.LN10));if((xhi-xlo)/xstep<3)xstep/=2;
  for(var gx=Math.ceil(xlo/xstep)*xstep;gx<=xhi;gx+=xstep){ctx.fillText(gx.toFixed(0),X(gx),H-mb+18);}
  ctx.fillText('真實波長 (nm)',(ml+W-mr)/2,H-8);
  ctx.save();ctx.translate(16,H/2);ctx.rotate(-Math.PI/2);ctx.fillText('報告 − 真實 (nm)',0,0);ctx.restore();
  if(ylo<0&&yhi>0){ctx.strokeStyle='#94a3b8';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(ml,Y(0));ctx.lineTo(W-mr,Y(0));ctx.stroke();}
  // 模型曲線
  ctx.strokeStyle='#dc2626';ctx.lineWidth=2.4;ctx.beginPath();
  for(i=0;i<=120;i++){var lam=xlo+(xhi-xlo)*i/120;if(i==0)ctx.moveTo(X(lam),Y(mv[i]));else ctx.lineTo(X(lam),Y(mv[i]));}
  ctx.stroke();
  // 實測點
  s.pts.forEach(function(p){ctx.fillStyle='#4f46e5';ctx.beginPath();ctx.arc(X(p[0]),Y(p[1]),5,0,6.283);ctx.fill();
    ctx.strokeStyle='#fff';ctx.lineWidth=1.2;ctx.stroke();});
  // 圖例
  ctx.textAlign='left';ctx.fillStyle='#4f46e5';ctx.beginPath();ctx.arc(ml+14,mt+12,4.5,0,6.283);ctx.fill();
  ctx.fillStyle='#1e293b';ctx.fillText('實測譜線（'+s.pts.length+' 條）',ml+24,mt+16);
  ctx.strokeStyle='#dc2626';ctx.lineWidth=2.4;ctx.beginPath();ctx.moveTo(ml+14,mt+32);ctx.lineTo(ml+44,mt+32);ctx.stroke();
  ctx.fillStyle='#1e293b';ctx.fillText('你的模型',ml+52,mt+36);
  // 讀數
  var c0=fitPoly(0),c1=fitPoly(1);
  var r0=c0?rmsOf(c0[0],0,0):NaN, r1=c1?rmsOf(c1[0],c1[1],0):NaN;
  function fmtR(v){return isNaN(v)?'—':(v>=1000?(v/1000).toFixed(2)+' nm':v.toFixed(0)+' pm');}
  document.getElementById('rms2').textContent=fmtR(rmsOf(o,sl,cu));
  document.getElementById('rmsOff').textContent=(judged||revealed)?fmtR(r0):'—';
  document.getElementById('rmsLin').textContent=(judged||revealed)?fmtR(r1):'—';
  var v=document.getElementById('verdict');
  if(!judged&&!revealed){v.textContent='先自己判斷';v.style.color='var(--muted)';
    document.getElementById('tstat').textContent='—';}
  else if(s.pts.length<4){v.textContent='點數不足（'+s.pts.length+' 點），判不出來';v.style.color='var(--muted)';
    document.getElementById('tstat').textContent='—';}
  else{
    // 斜率的標準誤與 t 值：斜率是否顯著，不是看 rms 降多少
    var n=s.pts.length,mx=0;s.pts.forEach(function(p){mx+=p[0];});mx/=n;
    var sxx=0;s.pts.forEach(function(p){sxx+=(p[0]-mx)*(p[0]-mx);});
    var sres=0;s.pts.forEach(function(p){var e=lab2model(p[0],c1[0],c1[1],0)-p[1];sres+=e*e;});
    var sig=Math.sqrt(sres/(n-2)), se=sig/Math.sqrt(sxx)*1e6, tv=c1[1]/se;
    document.getElementById('tstat').textContent=c1[1].toFixed(0)+' ± '+se.toFixed(0)+' ppm（t = '+tv.toFixed(1)+'）';
    if(Math.abs(tv)>3){v.textContent='斜率顯著 → 有色散誤差';v.style.color='var(--warn)';}
    else{v.textContent='斜率不顯著 → 純平移';v.style.color='var(--ok)';}
  }
}
['off','slp','cur'].forEach(function(id){document.getElementById(id).addEventListener('input',drawLab2);});
drawLab2();

// ---------- 測驗 ----------
function grade(){
  var score=0,total=10;
  var ans={1:"b",3:"b",4:"b",5:"b",7:"c",8:"b",9:"b",10:"b"};
  var explain={
    1:"燈只檢查像素→波長。雷射沒開，所以它對雷射波長一無所知——這正是它能『分離』兩個誤差來源的原因。",
    2:"10⁷ × 0.94 / 850² ≈ 13.0 cm⁻¹。這只是 −20 的一部分，剩下的 ≈7 來自雷射波長設定。",
    3:"Δν̃ ≈ 10⁷·Δλ/λ²，λ 越長分母越大；雷射設錯則是常數。看到有斜率就知道波長軸一定有份。",
    4:"光柵方程式 mλ 對 m=2 也成立。沒有 order-sorting filter 的儀器，可見光線會以兩倍波長混入。",
    5:"獨立樣品給出一致的 λ_L（784.60 vs 784.54）是最強的自洽證據；峰多不等於證據強。",
    6:"λ = 1/(1/784.56 − 555.8×10⁻⁷) ≈ 820.4 nm。",
    7:"相似度搜尋只回答『庫裡最像誰』。先確認資料庫覆蓋，再談候選，最後才談確證。",
    8:"兩者差 1–3 cm⁻¹，與各自不確定度同量級。物理模型的價值在可解釋、可外插、雷射漂移時只改一個參數。",
    9:"水平線＝只有 C₀ 錯（純平移）；斜線＝C₁ 也錯（色散誤差），整條軸被拉長或壓縮；曲線＝高次項。雷射設錯只影響波數軸，不會讓波長的偏差出現斜率。",
    10:"重覆性（精密度）與準確度是兩回事。QEPro-532 就是這樣被騙的：日光燈裡的 Ar 696.5 重覆 SD 只有 15 pm，但坐在螢光粉背景上被拉偏 140 pm，害色散誤差估成 7 倍大。槓桿端只有一條線時要格外小心。"};
  document.querySelectorAll(".qq").forEach(function(q){
    var n=q.dataset.q,ok=false,fb=q.querySelector(".fb");fb.style.display="block";
    if(ans[n]){var sel=q.querySelector("input:checked");ok=(sel&&sel.value===ans[n]);}
    else if(n==="2"){var v=parseFloat(document.getElementById("q2in").value);ok=!isNaN(v)&&Math.abs(v-13.0)<=1;}
    else if(n==="6"){var v=parseFloat(document.getElementById("q6in").value);ok=!isNaN(v)&&Math.abs(v-820.4)<=0.5;}
    q.classList.toggle("right",ok);q.classList.toggle("wrong",!ok);
    fb.textContent=(ok?"✔ 答對！ ":"✘ 答錯了。 ")+explain[n];fb.style.color=ok?"#16a34a":"#dc2626";if(ok)score++;});
  var box=document.getElementById("scoreBox");box.style.display="block";
  var msg=score===10?"🏆 滿分！你已經能分辨『波長軸病』和『雷射病』，可以去幫別人的光譜儀看診了。":
          score>=8?"👍 不錯！錯的題目看解析後再想一次就通了。":
          score>=4?"📖 觀念還有縫，建議把第 5 與 5B 節的兩個互動實驗再玩一次。":
          "💪 別氣餒！從第 2 節的『兩把尺』重新開始，其實只有一條公式。";
  box.innerHTML="得分：<span style='font-size:30px;color:var(--brand)'>"+score+" / "+total+"</span><br>"+msg;
}
</script>
</body>
</html>
"""

sub = {
    "__CSS__": CSS, "__FIG1__": img("fig1_qepro_lamp_check.png"), "__FIG2__": img("fig2_im2000_axes_check.png"),
    "__FIG3__": img("fig3_two_error_sources.png"), "__FIG4__": img("fig4_benzoic_caffeine_before_after.png"), "__FIG5__": img("fig5_usb4000_laser_check.png"), "__FIG6__": img("fig6_avantes_nir_1364.png"),
    "__SURVEY__": SURVEY,
    "__QLINE_ROWS__": QLINE_ROWS, "__ILINE_ROWS__": ILINE_ROWS, "__BA_ROWS__": BA_ROWS, "__CAF_ROWS__": CAF_ROWS, "__CMP_ROWS__": CMP_ROWS,
    "__Q_MEAN__": fmt(q["mean_dev_nm"]), "__Q_SD__": fmt(q["sd_dev_nm"]), "__Q_N__": str(q["n_lines"]),
    "__Q_CM__": fmt(1e7 * abs(q["mean_dev_nm"]) / 850**2, 0), "__Q_FIBER__": fmt(q["fiber_max_diff_nm"]),
    "__Q_RES__": fmt(q["resid_rms_pm"], 0), "__Q_A__": fmt(q["A"], 6), "__Q_B__": fmt(q["B"], 4),
    "__Q_A_RAW__": repr(q["A"]), "__Q_B_RAW__": repr(q["B"]),
    "__I_MEAN__": fmt(im["mean_dev_nm"]), "__I_LASER__": fmt(im["laser_implied_nm"]), "__I_LASER_SD__": fmt(im["laser_implied_sd"], 3),
    "__I_WNRES__": fmt(im["wn_axis_resid_rms_nm"], 3),
    "__L_BA__": fmt(L["benzoic"], 3), "__L_CAF__": fmt(L["caffeine"], 3), "__L_COMB__": fmt(L["combined"], 2),
    "__L_BA_N__": str(L["n_benzoic"]), "__L_CAF_N__": str(L["n_caffeine"]), "__L_N__": str(L["n_pairs"]),
    "__L_BA_RMS__": fmt(L["rms_benzoic"]), "__L_CAF_RMS__": fmt(L["rms_caffeine"]), "__L_RMS__": fmt(L["rms_combined"]), "__L_RMS785__": fmt(L["rms_if_785"]),
    "__U_CAF__": str(uid["caffeine"]["matched"]), "__U_OF__": str(uid["caffeine"]["of"]), "__U_CAF_E__": fmt(uid["caffeine"]["mean_abs_err"], 1),
    "__U_APAP__": str(uid["acetaminophen"]["matched"]), "__U_APAP_E__": fmt(uid["acetaminophen"]["mean_abs_err"], 1), "__U_BA__": str(uid["benzoic acid"]["matched"]),
    "__PTS__": PTS, "__DATE__": datetime.date.today().isoformat(),
}
out = HTML
for k, v in sub.items():
    out = out.replace(k, v)
assert "__" not in re.sub(r"data:image[^\"]+", "", out).replace("__init__", ""), [m for m in re.findall(r"__[A-Z0-9_]+__", re.sub(r"data:image[^\"]+", "", out))][:5]
open("raman_calibration_unit1b.html", "w", encoding="utf-8").write(out)
print("wrote raman_calibration_unit1b.html", len(out.encode()) // 1024, "KB")
