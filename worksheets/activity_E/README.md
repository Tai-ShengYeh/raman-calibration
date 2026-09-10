# 活動 E｜三把尺量同一根線：三軌一致性 / Activity E: three tools, one line

同一組 (NIST 波長, 量到的峰位) 資料，用三種工具各擬合一次 λ_true = A·λ_measured + B。
三者的 A、B、SE_A、t、殘差標準誤應一致到小數第 6 位——最小平方只有一個解，工具只是算術。
The same pairs fitted three ways; slope, intercept, standard errors and residual SE must agree to 6 decimals.

| 檔案 / file | 工具 / tool | 怎麼用 / how |
|---|---|---|
| `fit_pairs.xlsx` | Excel | 把兩欄數字貼進 A2:B13，E 欄自動算（LINEST）/ paste the two columns into A2:B13 |
| `fit_pairs.py` | Python | `python fit_pairs.py your_pairs.csv` |
| `fit_pairs.R` | R | `Rscript fit_pairs.R your_pairs.csv` |
| `pairs_example.csv` | 範例 / example | QEPro-785 (QEP05121) 日光燈 Ar/Hg 12 條線，2026-08 實測 |

CSV 格式 / format: `nist_nm,measured_nm`，第一列標題 / header row first.
