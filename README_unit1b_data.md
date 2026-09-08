# Unit 1B 資料包說明（README_unit1b_data.md）

本資料夾是教材《兩台儀器的體檢報告：波長軸、雷射波長與二階繞射》（`raman_calibration_unit1b.html`）的原始資料。
**原始檔一律不覆寫**；所有修正版由腳本另存（檔名含 `_CORRECTED`）。

## 檔案清單與 SHA-256

| 檔案 | 位元組 | SHA-256 |
|---|---:|---|
| `im2000_light_ArHg_lamp_axes.csv` | 91,524 | `1f3380478025019d2f4d0b0f097da60315bd773a068025ec2e45d8e596858fb4` |
| `qepro_benzoic_acid_3reps.csv` | 40,009 | `896663877ac5b8ed11375e260f6a6cf2e37f407992b535c3fddef4a6f57a5b4a` |
| `qepro_light1_ArHg_lamp.csv` | 20,152 | `d776b03350de51951bce1beca90756526b9f6e0bea464419beb115a655e3272d` |
| `qepro_light2_ArHg_lamp.csv` | 19,627 | `dbe2f1e71773925a14bd084f8c59c068de094551723a4119d1cab09c83b2aa4d` |
| `qepro_unknown_sample.csv` | 19,287 | `df77ff7a58760aad68baa023a77a98a97e9e7288c079b6333b9e834b4378f3da` |
| `reference_lines_ArHg_NIST_air.csv` | 407 | `e6a40aef0838754ff520266e210b35cf06630bb068a998965c0f7cefbbf29b6b` |
| `reference_raman_peaks_literature.csv` | 447 | `04d42f4cb53bc471504be20f773430f0eea181752ece4234fd6f7e510cef3da4` |

## 各檔案內容

| 檔案 | 儀器 | 內容 | 來源與轉換 |
|---|---|---|---|
| `qepro_light1_ArHg_lamp.csv` | Ocean Optics QEPro（序號 QEP05121） | 日光燈（Ar/Hg 放電）發射譜，光纖 1；1044 點，783.748–1030.894 nm | 由 OceanView 匯出的 `light1.xlsx` 轉 CSV，波長為軟體報告值 |
| `qepro_light2_ArHg_lamp.csv` | 同上 | 同一支燈，**換另一條光纖** | `light2.xlsx` |
| `qepro_benzoic_acid_3reps.csv` | 同上 | 苯甲酸固體，3 次重複；x 軸為 OceanView 以 785.000 nm 算出的拉曼位移，1038 點 | `qepro785_0819_2026/benzoic_acid.xlsx` |
| `qepro_unknown_sample.csv` | 同上 | 未知固體樣品（教材第 7 節辨識為咖啡因） | `qepro785_0819_2026/unknown.xlsx` |
| `im2000_light_ArHg_lamp_axes.csv` | Imai Optics Im2000 Pro | 同一支燈；IMSpectralSuite 三種匯出軸（pixel / nm / wavenumber）併成一表，2048 點。`counts_pixel_file`、`counts_nm2_file`、`counts_wavenumber_file` 為同一次量測的三個匯出（互相關 0.998）；`counts_nm_file_weak` 是另一次訊號極弱的掃描，僅供對照 | `IMSpectralSuit/light_*.txt` |
| `reference_lines_ArHg_NIST_air.csv` | — | 教材使用的 Ar I / Hg I 譜線（**空氣中波長**），含四條二階繞射位置（可見光 Hg 線 × 2） | NIST Atomic Spectra Database |
| `reference_raman_peaks_literature.csv` | — | 苯甲酸與咖啡因的常見文獻峰位。**不是認證值**；ASTM E1840 未收錄這兩種物質 | 文獻整理，見教材參考文獻 |

### 追加（2026-09-03）：USB4000 直接量測
| 檔案 | 儀器 | 內容 |
|---|---|---|
| `usb4000_blacklight_check.csv` | Ocean Optics USB4000（序號 USB4F00653） | Hg-Ar 黑光燈管＋雷射同時開；Ar 線 2000–7900 counts，雷射 57.7 k（未飽和）。**軸檢查的主要依據** |
| `usb4000_fl_lamp_check.csv` | 同上 | 一般日光燈；Ar 線只有 700–1800 counts → 反面教材（弱線把軸偏差估成 −0.29 ± 0.17） |
| `usb4000_785nm_check.csv` | 同上 | 只有雷射漫射光；峰 34 k counts，雜訊 σ ≈ 800 counts（未平均） |
| `usb4000_blacklight_check2.csv` | 同上 | 關雷射重量黑光燈，但未收到燈光（365 nm 磷光體、Ar 線皆無）→ 當熱像素地圖用：558.0、607.6、634.0、702.6、715.6、764.6、917.9、1014.4 nm 為單點熱像素 |

| `usb4000_blacklight_check4_{500,750,1000}ms_avg10.csv` | 同上 | 關雷射、光纖直對黑光燈管，10 次平均；Ar 線 2000–10 000 counts，365 nm 磷光體丘在 ≥750 ms 飽和（不影響 Ar 峰位） |

結果（`usb4000_laser_check.py`）：黑光燈 700–950 nm 的線給軸偏差 −0.51 ± 0.08（雷射開，5 條）／ −0.50 ± 0.05 nm（關雷射，7 條，含 794.8）；雷射峰位 784.11 → **784.62 ± 0.07 nm**（四種估計散布 0.07 nm；熱像素已剔除，1014.4 nm 不是 Hg 線）。與 8/19 苯甲酸＋咖啡因反解值 784.56 ± 0.05 一致到 0.06 nm。

## 量測條件（請量測者補齊空白，這是可重現性的一部分）

| 項目 | QEPro | Im2000 Pro |
|---|---|---|
| 軟體 / 版本 | OceanView（版本：____） | IMSpectralSuite（版本：____） |
| 雷射標稱波長 | 785 nm | 785 nm |
| 雷射實測波長 | **未直接量測**；本教材由苯甲酸＋咖啡因反解為 784.559 nm | 未直接量測；波數軸隱含 784.719 nm |
| 雷射功率 / 積分時間 / 平均次數 | 燈：____；苯甲酸、未知：____（檔頭 `RamanShift:204`） | ____ |
| 光柵 / 狹縫 / 光纖 | 光纖 1：____；光纖 2：____ | ____ |
| 量測日期 | 燈：2026-08-19；樣品：2026-08-19 | 2026-08-19 |
| 室溫 | ____ | ____ |
| 波長軸校正日期（原廠或自校） | ____ | ____ |

## 主要結果（由 `unit1b_calibration.py` 重算）

- QEPro 波長軸：檔案值比 NIST 真值**低 0.94 nm**（12 條線，SD 0.17）；線性修正 λ_true = 0.99927773·λ_reported + 1.56232
- 換光纖不影響波長軸（兩條光纖峰位差 ≤ 0.09 nm）
- Im2000 Pro：nm 軸**高 1.36 nm**，但波數軸自洽（殘差 rms 0.072 nm），隱含雷射波長 784.719 nm；譜中最強峰（873 nm）是 Hg 435.8 nm 的二階繞射
- QEPro 苯甲酸峰位比文獻低 15–26 cm⁻¹；拆成兩個來源：波長軸偏移（在 1001 cm⁻¹ 貢獻 -13.1）＋ 雷射波長設定（貢獻 -7.2）
- 苯甲酸與咖啡因分別反解得 λ_L = 784.603 / 784.536 nm；合併 784.559 nm，rms 1.95 cm⁻¹（若硬用 785.000：7.52）
- 未知樣品：修正後 16/20 峰對上咖啡因（平均 |誤差| 1.9 cm⁻¹）；乙醯胺酚只對上 7/20

> 峰位質心方法不同（Python ALS 基線 vs R 滾動最小值 vs 手動）會讓 λ_L 在約 784.54–784.63 nm 之間變動，相當於 ±1 cm⁻¹；這就是本方法的不確定度量級。

## 授權

資料由 Tai-Sheng Yeh 量測，供教學使用（CC BY 4.0）。NIST ASD 資料為公有領域；文獻峰位請引用教材參考文獻。
