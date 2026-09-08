# Unit 1B — 兩台 785 nm 拉曼光譜儀的體檢（R 版，只用 base R，不需安裝套件）
# 執行：  Rscript unit1b_calibration.R      或在 RStudio 逐段執行
# 輸入：  ./unit1b_data/*.csv
# 對應 Python 版 unit1b_calibration.py；數值應在 ±0.05 nm / ±0.5 cm⁻¹ 內一致

LASER_NOMINAL <- 785.000                   # 兩套軟體算波數時用的標稱雷射波長

# ---- 工具函式 -------------------------------------------------------------
shift_from_wavelength <- function(lam, laser) 1e7 * (1 / laser - 1 / lam)   # nm → cm⁻¹
wavelength_from_shift <- function(shift, laser) 1 / (1 / laser - shift * 1e-7)

# 兩段式找線：先用中位數估粗略偏移，再以「真值 + 偏移」為中心做加權質心
locate_lines <- function(x, y, ref_nm, search = 2.5, half = 0.9) {
  rough <- sapply(ref_nm, function(t) {
    m <- x > t - search & x < t + search
    if (sum(m) < 5) return(NA)
    x[m][which.max(y[m])] - t
  })
  rough <- median(rough, na.rm = TRUE)
  obs <- sapply(ref_nm, function(t) {
    w <- x > t + rough - half & x < t + rough + half
    yy <- y[w] - min(y[w])
    sum(x[w] * yy) / sum(yy)
  })
  data.frame(true_nm = ref_nm, obs_nm = obs, dev_nm = obs - ref_nm)
}

# ---- §3 QEPro：日光燈檢查波長軸 ---------------------------------------------
cat("== §3 QEPro 波長軸體檢 ==\n")
lamp <- read.csv("unit1b_data/qepro_light1_ArHg_lamp.csv")
USE_Q <- c(794.8176, 801.4786, 810.3693, 811.5311, 826.4522, 840.8210, 842.4648,
           852.1442, 866.7944, 912.2967, 922.4499, 1013.975)          # NIST 空氣中波長
q <- locate_lines(lamp$wavelength_nm_reported, lamp$counts, USE_Q)
print(round(q, 3))
cat(sprintf("平均偏差 %+.3f nm（SD %.3f）\n", mean(q$dev_nm), sd(q$dev_nm)))
fit_q <- lm(true_nm ~ obs_nm, data = q)                                 # λ_true = A·λ_reported + B
A <- coef(fit_q)[2]; B <- coef(fit_q)[1]
cat(sprintf("線性修正： λ_true = %.8f × λ_reported + %.5f   殘差 rms %.0f pm\n",
            A, B, sd(resid(fit_q)) * 1000))

# ---- §4 Im2000 Pro：nm 軸與波數軸 ---------------------------------------------
cat("\n== §4 Im2000 Pro ==\n")
im <- read.csv("unit1b_data/im2000_light_ArHg_lamp_axes.csv")
USE_I <- c(811.5311, 815.566, 826.4522, 840.8210, 842.4648, 852.1442, 871.666,
           912.2967, 922.4499, 1013.975)                              # 含兩條二階 Hg 線
i <- locate_lines(im$wavelength_nm_reported, im$counts_pixel_file, USE_I, search = 2.6)
cat(sprintf("nm 軸偏差 %+.3f nm（SD %.3f）→ nm 軸偏高\n", mean(i$dev_nm), sd(i$dev_nm)))
wn_at <- approx(im$wavelength_nm_reported, im$raman_shift_reported_cm.1, xout = i$obs_nm)$y
laser_implied <- 1 / (wn_at * 1e-7 + 1 / i$true_nm)
cat(sprintf("波數軸隱含的雷射波長 %.4f ± %.4f nm\n", mean(laser_implied), sd(laser_implied)))
resid_wn <- wavelength_from_shift(wn_at, mean(laser_implied)) - i$true_nm
cat(sprintf("用它反算波長的殘差 rms %.3f nm → 波數軸是好的\n", sd(resid_wn)))

# ---- §5–6 苯甲酸與咖啡因：反解雷射波長 ----------------------------------------
cat("\n== §5–6 反解雷射波長 ==\n")
lit <- read.csv("unit1b_data/reference_raman_peaks_literature.csv")
ba  <- read.csv("unit1b_data/qepro_benzoic_acid_3reps.csv")
un  <- read.csv("unit1b_data/qepro_unknown_sample.csv")
x_rep    <- ba$raman_shift_reported_cm.1
lam_rep  <- wavelength_from_shift(x_rep, LASER_NOMINAL)               # 還原 OceanView 波長軸
lam_true <- A * lam_rep + B                                           # 套用燈校正

# 簡單基線：滾動最小值再平滑（教學用；Python 版用 ALS）
rolling_baseline <- function(y, k = 61) {
  n <- length(y); b <- numeric(n)
  for (j in seq_len(n)) { lo <- max(1, j - k); hi <- min(n, j + k); b[j] <- min(y[lo:hi]) }
  stats::filter(b, rep(1 / k, k), sides = 2, circular = TRUE)
}
# 在文獻峰附近（報告值大約低 20 cm⁻¹，所以往下找）做質心
find_near <- function(y, lit_cm, guess_offset = -20, half_cm = 9) {
  yc <- y - rolling_baseline(y)
  t(sapply(lit_cm, function(L) {
    w <- x_rep > L + guess_offset - half_cm & x_rep < L + guess_offset + half_cm
    yy <- yc[w] - min(yc[w])
    c(lit = L, reported = sum(x_rep[w] * yy) / sum(yy), lambda_true = sum(lam_true[w] * yy) / sum(yy),
      height = max(yc[w]) / max(yc))
  }))
}
fit_laser <- function(tab, reject = 5) {
  cost <- function(L, keep) sqrt(mean((shift_from_wavelength(tab[keep, "lambda_true"], L) - tab[keep, "lit"])^2))
  keep <- rep(TRUE, nrow(tab))
  L1 <- optimize(cost, c(783.5, 786), keep = keep)$minimum
  keep <- abs(shift_from_wavelength(tab[, "lambda_true"], L1) - tab[, "lit"]) <= reject
  L2 <- optimize(cost, c(783.5, 786), keep = keep)$minimum
  list(laser = L2, rms = cost(L2, keep), n = sum(keep))
}
ba_lit  <- lit$raman_shift_literature_cm.1[lit$compound == "benzoic acid"]
caf_lit <- lit$raman_shift_literature_cm.1[lit$compound == "caffeine"]
tab_ba  <- find_near(rowMeans(ba[, c("rep1", "rep2", "rep3")]), ba_lit)
tab_caf <- find_near(un$counts, caf_lit)
tab_ba  <- tab_ba[tab_ba[, "height"] > 0.05, ]; tab_caf <- tab_caf[tab_caf[, "height"] > 0.03, ]
cat("苯甲酸原始誤差（報告 − 文獻）：", round(tab_ba[, "reported"] - tab_ba[, "lit"], 1), "\n")
f_ba <- fit_laser(tab_ba); f_caf <- fit_laser(tab_caf); f_all <- fit_laser(rbind(tab_ba, tab_caf))
cat(sprintf("苯甲酸 → λ_L = %.3f nm（%d 峰，rms %.2f）\n", f_ba$laser, f_ba$n, f_ba$rms))
cat(sprintf("咖啡因 → λ_L = %.3f nm（%d 峰，rms %.2f）\n", f_caf$laser, f_caf$n, f_caf$rms))
cat(sprintf("合併   → λ_L = %.3f nm（%d 峰，rms %.2f）\n", f_all$laser, f_all$n, f_all$rms))
LASER <- f_all$laser

# ---- §7 未知樣品：修正後與三個候選比對 ----------------------------------------
cat("\n== §7 未知樣品辨識 ==\n")
apap_lit <- c(213, 329, 391, 465, 504, 651, 710, 798, 834, 858, 1105, 1169, 1236, 1278,
              1323, 1371, 1516, 1561, 1611, 1648, 2931)
# 先「找峰」（局部極大值），再問每個候選物能解釋幾個峰——不能反過來拿候選峰去湊
detect_peaks <- function(y, win = 3, min_rel = 0.03) {
  yc <- y - rolling_baseline(y); ys <- stats::filter(yc, rep(1/5, 5), sides = 2); ys[is.na(ys)] <- 0
  n <- length(ys); idx <- which(sapply(seq_len(n), function(j) {
    lo <- max(1, j - win); hi <- min(n, j + win); ys[j] == max(ys[lo:hi]) && ys[j] > min_rel * max(ys)
  }))
  sapply(idx, function(j) { w <- max(1, j - 2):min(n, j + 2); yy <- ys[w] - min(ys[w]); sum(lam_true[w] * yy) / sum(yy) })
}
pk_lambda <- detect_peaks(un$counts)                       # 未知樣品的峰（以校正後波長表示）
pk_cm     <- shift_from_wavelength(pk_lambda, LASER)       # 修正後的拉曼位移
cat("未知樣品修正後的峰位：", round(pk_cm, 0), "\n")
score <- function(lit_cm, tol = 10) {
  err <- sapply(pk_cm, function(v) min(abs(v - lit_cm)))
  c(matched = sum(err < tol), of_peaks = length(pk_cm), mean_abs_err = round(mean(err[err < tol]), 2))
}
print(rbind(caffeine = score(caf_lit), acetaminophen = score(apap_lit), benzoic_acid = score(ba_lit)))

# ---- 修正處方與另存 --------------------------------------------------------------
cat(sprintf("\n修正處方： λ_true = %.8f·λ_reported + %.5f ；  ν̃ = 1e7·(1/%.3f − 1/λ_true)\n", A, B, LASER))
un$wavelength_true_nm <- A * wavelength_from_shift(un$raman_shift_reported_cm.1, LASER_NOMINAL) + B
un$raman_shift_corrected_cm.1 <- shift_from_wavelength(un$wavelength_true_nm, LASER)
write.csv(un, "qepro_unknown_sample_CORRECTED_R.csv", row.names = FALSE)   # 另存，不覆寫原始檔
