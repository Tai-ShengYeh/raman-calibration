# 拉曼光譜儀波長校正教材（Raman calibration teaching unit）

線上閱讀：<https://tai-shengyeh.github.io/raman-calibration/>

| 檔案 | 內容 |
|---|---|
| `raman_calibration_tutorial.html` | 校正原理：從像素到波長、波數，用國中代數＋十行程式碼自己算 |
| `raman_calibration_unit1b.html` | 兩台儀器的體檢報告：波長軸、雷射波長與二階繞射（含互動練習） |
| `raman_food_additives_tutorial.html` | 食品添加物拉曼指紋（被 unit1b 連結） |
| `worksheets/` | 四張學習單（學生版） |
| `unit1b_data/`、`README_unit1b_data.md` | 原始量測資料與 SHA-256、量測條件 |
| `unit1b_calibration.py` / `.R`、`usb4000_laser_check.py` | 重算所有數值與 `figs/` 圖 |
| `build_unit1b.py` | 由 `unit1b_results.json`、`unit1b_survey.json`、`figs/` 組出 `raman_calibration_unit1b.html` |
| `lamp_survey/` | 多台光譜儀燈源普查的擬合腳本與結果 |

重現流程：`python unit1b_calibration.py && python usb4000_laser_check.py && python build_unit1b.py`
