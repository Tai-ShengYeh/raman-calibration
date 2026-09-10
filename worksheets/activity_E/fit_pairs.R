# 活動 E｜三軌一致性：R 軌（只用 base R）
# 用法：Rscript fit_pairs.R [pairs.csv]      CSV 兩欄：nist_nm, measured_nm（第一列是標題）
# 擬合 λ_true = A·λ_measured + B；輸出與 Excel LINEST、Python polyfit 應一致到小數第 6 位
args <- commandArgs(trailingOnly = TRUE)
f <- if (length(args) > 0) args[1] else "pairs_example.csv"
d <- read.csv(f)
fit <- lm(nist_nm ~ measured_nm, data = d)   # y = NIST 真值, x = 量到的峰位
s <- summary(fit)
A <- unname(coef(fit)[2]); B <- unname(coef(fit)[1])
se_A <- s$coefficients[2, 2]
cat(sprintf("n      = %d\n", nrow(d)))
cat(sprintf("A      = %.8f\n", A))
cat(sprintf("B      = %.5f nm\n", B))
cat(sprintf("SE_A   = %.3e\n", se_A))
cat(sprintf("t      = (A-1)/SE_A = %.2f\n", (A - 1) / se_A))
cat(sprintf("殘差標準誤 = %.1f pm\n", s$sigma * 1000))   # Residual standard error = LINEST 第 3 列第 2 欄
