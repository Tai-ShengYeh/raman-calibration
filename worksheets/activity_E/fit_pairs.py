# 活動 E｜三軌一致性：Python 軌
# 用法：python fit_pairs.py [pairs.csv]      CSV 兩欄：nist_nm, measured_nm（第一列是標題）
# 擬合 λ_true = A·λ_measured + B；輸出與 Excel LINEST、R lm() 應一致到小數第 6 位
import sys
import numpy as np

f = sys.argv[1] if len(sys.argv) > 1 else "pairs_example.csv"
d = np.loadtxt(f, delimiter=",", skiprows=1)
y, x = d[:, 0], d[:, 1]                       # y = NIST 真值, x = 量到的峰位
(A, B), cov = np.polyfit(x, y, 1, cov=True)   # cov 以殘差變異 / (n-2) 縮放，與 LINEST、lm 相同
n = len(x)
res = y - (A * x + B)
sey = np.sqrt(np.sum(res**2) / (n - 2))       # 殘差標準誤（LINEST 第 3 列第 2 欄；R 的 Residual standard error）
se_A = np.sqrt(cov[0, 0])
print(f"n      = {n}")
print(f"A      = {A:.8f}")
print(f"B      = {B:.5f} nm")
print(f"SE_A   = {se_A:.3e}")
print(f"t      = (A-1)/SE_A = {(A - 1) / se_A:.2f}")
print(f"殘差標準誤 = {sey * 1000:.1f} pm")
