# 拉曼光譜儀波長校正教材（Raman calibration teaching unit）

線上閱讀（中英雙語，右上角可切換）：<https://tai-shengyeh.github.io/raman-calibration/>
Read online (bilingual, toggle at the top-right): <https://tai-shengyeh.github.io/raman-calibration/>
直接開英文版 / English by default: <https://tai-shengyeh.github.io/raman-calibration/?lang=en>

| 檔案 / File | 內容 / Contents |
|---|---|
| `index.html` | 首頁與學習地圖 / Landing page and learning map |
| `raman_calibration_tutorial.html` | 校正原理：從像素到波長、波數，用國中代數＋十行程式碼自己算 / Calibration principles: pixel → wavelength → wavenumber with junior-high algebra and ten lines of code |
| `raman_calibration_unit1b.html` | 兩台儀器的體檢報告：波長軸、雷射波長與二階繞射（含互動練習） / Health check of two instruments: wavelength axis, laser wavelength and second-order diffraction (interactive exercises) |
| `raman_food_additives_tutorial.html` | 食品添加物拉曼指紋（被 unit1b 連結） / Raman fingerprints of food additives (linked from Unit 1B) |
| `glossary.js` | 中英專有名詞對照與說明；每頁底部自動產生對照表，內文名詞可懸停或點選查看 / Bilingual glossary with explanations; rendered at the bottom of every page, and terms in the text show a popover on hover or tap |
| `i18n.js`、`i18n.css` | 中英切換機制（`?lang=en` 或 `?lang=zh`，偏好會記在瀏覽器） / Language toggle (`?lang=en` or `?lang=zh`; the choice is remembered in the browser) |
| `worksheets/` | 四張學習單（學生版） / Four student worksheets |
| `unit1b_data/`、`README_unit1b_data.md` | 原始量測資料與 SHA-256、量測條件 / Raw measurements with SHA-256 and acquisition conditions |
| `unit1b_calibration.py` / `.R`、`usb4000_laser_check.py` | 重算所有數值與 `figs/` 圖 / Recompute every number and the figures in `figs/` |
| `build_unit1b.py` | 由 `unit1b_results.json`、`unit1b_survey.json`、`figs/` 組出 `raman_calibration_unit1b.html`（雙語標記是在產出後加入的） / Builds `raman_calibration_unit1b.html` from the results, survey and figures (the bilingual markup was added after the build) |
| `lamp_survey/` | 多台光譜儀燈源普查的擬合腳本與結果 / Lamp-line survey fits for several spectrometers |
| `tools/i18n_check.py` | 檢查雙語標記是否完整（`python tools/i18n_check.py *.html`） / Checks that every page is fully paired (`python tools/i18n_check.py *.html`) |

重現流程 / Reproduce: `python unit1b_calibration.py && python usb4000_laser_check.py && python build_unit1b.py`

## 雙語標記方式 / How the bilingual markup works

每段文字都寫成相鄰的一對：`<span lang="zh-Hant">中文</span><span lang="en">English</span>`；`i18n.css` 依 `<html lang>` 只顯示其中一種，`i18n.js` 負責切換按鈕、記住偏好、把 `?lang=` 帶到站內連結，並根據 `glossary.js` 自動在內文標出專有名詞。
Every text run is an adjacent pair of `<span lang="zh-Hant">` / `<span lang="en">`; `i18n.css` shows one of them according to `<html lang>`, and `i18n.js` provides the toggle, remembers the preference, carries `?lang=` across internal links, and annotates technical terms in the text from `glossary.js`.
