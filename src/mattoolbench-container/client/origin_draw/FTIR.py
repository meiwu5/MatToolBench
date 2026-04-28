import os
import originpro as op
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from typing import Sequence, Optional

# ====================== Color Palette Options ======================
COLOR_PALETTES = {
    "default":    ['#000000', '#D62728', '#1F77B4', '#2CA02C'],
    "nature":     ['#E64B35', '#4DBBD5', '#00A087', '#3C5488'],
    "tab10":      ['#1F77B4', '#D62728', '#2CA02C', '#FF7F0E'],
    "okabe_ito":  ['#000000', '#E69F00', '#56B4E9', '#009E73'],
    "warm":       ['#C0392B', '#E67E22', '#D4AC0D', '#6E2C00'],
    "cool":       ['#2980B9', '#8E44AD', '#17A589', '#1A5276'],
    "grayscale":  ['#000000', '#444444', '#888888', '#BBBBBB'],
}
ACTIVE_PALETTE = "default"
colors = COLOR_PALETTES[ACTIVE_PALETTE]

# ====================== User Settings ======================
lamda = ''          # 标注文字，空字符串则不显示
label = ['']
is_Absorbance  = False       # True = 吸光度（Y轴正向），False = 透过率（Y轴反向）
is_peak_label  = True        # 是否在峰位标注波数值
peak_min_prom  = 0.10        # 峰显著性阈值：prominence 占谱高度的比例（越大标注越少）
peak_min_height = 0.15       # 峰高度阈值：峰值偏离基线需超过谱高度的比例（过滤平坦小起伏）
zoom_range = None  # 局部放大范围，如 [3600, 2800]，顺序无关；None 则自动全谱
save_path = os.path.join('..', 'output_result', 'ftir_stack.png')
# save_path = r'C:\Users\wu\desktop\ftir_stack.png'
# 1. Read data  （格式：x1,y1,x2,y2,x3,y3 … paired 排列）
# 手动指定标签（留空列表则自动从 Long Name 行读取）
label_override = ['EtOH','Gel','Gel after vacuum dry']

import pandas as pd

wks = op.find_sheet()
df_raw = wks.to_df()   # 原始，含 Long Name 等字符串行

# ── 从 Long Name 行提取标签 ──────────────────────────────
# Y 列（奇数列）中第一个非空字符串行即为 Long Name
auto_labels = []
y_col_indices = list(range(1, df_raw.shape[1], 2))  # 1,3,5,...
for c in y_col_indices:
    label_found = ''
    for val in df_raw.iloc[:, c]:
        s = str(val).strip()
        if s and s.lower() not in ('nan', 'none', ''):
            # 尝试转数值，失败则是文字标签
            try:
                float(s)
            except ValueError:
                label_found = s
                break
    auto_labels.append(label_found if label_found else f'Spectrum {len(auto_labels)+1}')

# ── 清洗：转数值，删掉非数值行（表头行）───────────────────
df = df_raw.apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=[df.columns[0]]).reset_index(drop=True)

# ── 读取各对 (x_i, y_i)，对齐长度 ────────────────────────
pairs = []   # list of (x_arr, y_arr)
for c in y_col_indices:
    xc = c - 1   # 对应的 x 列
    if c >= df.shape[1]:
        break
    xi = df.iloc[:, xc].dropna().values.astype(float)
    yi = df.iloc[:, c ].dropna().values.astype(float)
    n  = min(len(xi), len(yi))
    if n == 0:
        continue
    pairs.append((xi[:n], yi[:n]))

# 共用第一条谱的 x 作为主 x（FTIR 各谱 x 通常相同）
x = pairs[0][0]
y = [p[1][:len(x)] for p in pairs]

label = label_override if len(label_override) == len(y) else auto_labels
print(f"检测到 {len(y)} 条谱，标签：{label}")

# ==================== FTIR tick selector ====================
def ftir_ticks(xmin, xmax):
    width = xmax - xmin
    if width <= 200:
        candidates = [10, 20, 25, 50]
    elif width <= 500:
        candidates = [50, 100, 200]
    elif width <= 1000:
        candidates = [100, 200, 250]
    else:
        candidates = [200, 400, 500, 800, 1000]

    best_step  = candidates[0]
    best_score = float('inf')
    for step in candidates:
        n_ticks = int(width / step) + 1
        if 4 <= n_ticks <= 12:
            score = abs(n_ticks - 10)
        elif n_ticks < 4:
            score = 100 + (4 - n_ticks)
        else:
            score = 100 + (n_ticks - 10)
        if score < best_score:
            best_score = score
            best_step  = step

    xmin_aligned = np.floor(xmin / best_step) * best_step
    xmax_aligned = np.ceil(xmax  / best_step) * best_step
    return xmin_aligned, xmax_aligned, best_step


# ==================== Auto display range ====================
def soft_scale_ftir(p_list, x_data):
    peaks       = np.array(p_list)
    center      = peaks.mean()
    span        = np.ptp(peaks)
    base_margin = max(800, span * 2.5)
    extra       = base_margin * 0.15
    xmin_raw    = center - base_margin - extra
    xmax_raw    = center + base_margin + extra
    xmin        = max(400,  min(x_data.min(), xmin_raw))
    xmax        = min(4000, max(x_data.max(), xmax_raw))
    return xmin, xmax


# ==================== Stacked offset ====================
def auto_offset(x, y_list, xmin=None, xmax=None, gap_ratio=0.25, is_zoom=False):
    """is_zoom=True 时 gap_ratio 强制为 0（局部放大不需要间距）"""
    if is_zoom:
        gap_ratio = 0.0
    y_list   = [np.asarray(y) for y in y_list]
    n        = len(y_list)
    xmin_use = 400  if xmin is None else xmin
    xmax_use = 4000 if xmax is None else xmax
    mask     = (x >= xmin_use) & (x <= xmax_use)
    x_masked = x[mask]
    y_masked = [y[mask] for y in y_list]
    maxima   = [y.max() for y in y_masked]
    minima   = [y.min() for y in y_masked]
    shifts   = [0.0]
    cur_top  = maxima[0]
    for i in range(1, n):
        shift = cur_top - minima[i] + maxima[0] * gap_ratio
        shifts.append(shift)
        cur_top = maxima[i] + shift
    y_shifted = [y_masked[i] + shifts[i] for i in range(n)]
    return x_masked, y_shifted, y_masked, shifts, maxima, minima


# ==================== Peak finder ====================
def find_real_peak_ftir(x, y_list, prominence_ratio=0.12, edge_ignore=0.05):
    x      = np.asarray(x)
    start  = int(len(x) * edge_ignore)
    end    = int(len(x) * (1 - edge_ignore))
    x_mid  = x[start:end]
    found  = []
    for y in y_list:
        y_mid  = np.asarray(y)[start:end]
        peaks, props = find_peaks(y_mid, prominence=y_mid.max() * prominence_ratio)
        if len(peaks) == 0:
            found.append(float(x_mid[np.argmax(y_mid)]))
        else:
            found.append(float(x_mid[peaks[np.argmax(props['prominences'])]]))
    return found


# ==================== Plot ====================
def plot_offset_stacked_ftir(
    x_masked: np.ndarray,
    y_shifted: Sequence[np.ndarray],
    y_masked:  Sequence[np.ndarray],
    shifts:    Sequence[float],
    xmin: float,
    xmax: float,
    step: float,
    colors: Sequence[str],
    lamda: str = "ATR-FTIR",
    label: Optional[Sequence[str]] = None,
    save_path: Optional[str] = None,
    is_Absorbance: bool = True,
    is_peak_label: bool = True,
    peak_min_prom: float = 0.10,
    peak_min_height: float = 0.15,
):
    y_shifted = [np.asarray(y) for y in y_shifted]
    n = len(y_shifted)

    plt.rcParams['font.family'] = 'Times New Roman'
    fig, ax = plt.subplots(figsize=(10, 8))

    for i, y in enumerate(y_shifted):
        lbl = label[i] if (label and i < len(label)) else None
        ax.plot(x_masked, y, color=colors[i % len(colors)], linewidth=2.0, label=lbl)

    # X axis
    ax.set_xlim(xmin, xmax)
    ax.invert_xaxis()
    ticks = np.arange(np.ceil(xmin / step) * step,
                      np.floor(xmax / step) * step + step * 0.6,
                      step)
    ax.set_xticks(ticks)
    ax.tick_params(axis='x', labelsize=18, length=8, width=1.5)

    # Y axis
    ax.set_yticks([])
    ax.tick_params(axis='y', left=False)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    # ylim — 必须在 invert_yaxis 之前设置，否则会被覆盖
    all_mins = [y.min() for y in y_shifted]
    all_maxs = [y.max() for y in y_shifted]
    h0       = all_maxs[0] - all_mins[0]
    ax.set_ylim(min(all_mins) - h0 / 4, max(all_maxs) + h0 / 2)

    # 透过率模式：set_ylim 之后再翻转，才能生效
    if not is_Absorbance:
        ax.invert_yaxis()

    # Labels
    ax.set_xlabel('Wavenumber (cm$^{-1}$)', fontsize=22, fontweight='bold', labelpad=12)
    ylabel = 'Absorbance (a.u.)' if is_Absorbance else 'Transmittance (%)'
    ax.set_ylabel(ylabel, fontsize=22, fontweight='bold', labelpad=15)

    if lamda:
        ax.text(0.98, 0.94, lamda, transform=ax.transAxes,
                fontsize=20, fontweight='bold', ha='right', va='top', color='black')

    # ── 峰位标注 ──────────────────────────────────────────────
    if is_peak_label:
        for i, (y_sh, y_ma) in enumerate(zip(y_shifted, y_masked)):
            color = colors[i % len(colors)]
            h0    = np.max(y_sh) - np.min(y_sh)

            y_range       = np.max(y_ma) - np.min(y_ma)
            prom_thresh   = y_range * peak_min_prom
            height_thresh = y_range * peak_min_height

            # 吸光度和透过率都找谷值（原始数据中吸收都表现为极小值）
            max_h  = np.max(y_ma) - height_thresh
            peaks, _ = find_peaks(-y_ma,
                                  prominence=prom_thresh,
                                  height=-max_h)
            for pk in peaks:
                px, py = x_masked[pk], y_sh[pk]
                if not (xmin <= px <= xmax):
                    continue
                if is_Absorbance:
                    # 轴翻转：低数据值 = 视觉高位；标注锚点往更低值偏移，va='bottom'
                    # 使文字向更低数据值方向（视觉上方）延伸，远离曲线
                    ax.text(px, py - h0 * 0.06, f'{px:.0f}',
                            ha='center', va='bottom',
                            fontsize=9, color=color, rotation=90)
                else:
                    # 正常轴：低数据值 = 视觉低位；往下偏移，va='top' 使文字向下延伸
                    ax.text(px, py - h0 * 0.06, f'{px:.0f}',
                            ha='center', va='top',
                            fontsize=9, color=color, rotation=90)

    if label and any(str(l).strip() for l in label):
        patches = [plt.Line2D([0], [0], color=colors[i % len(colors)], lw=2.5)
                   for i in range(len(label))]
        ax.legend(patches, label,
                  loc='upper center',
                  bbox_to_anchor=(0.5, 1.0),
                  ncol=len(label),
                  fontsize=14, frameon=False,
                  handlelength=2.0, handletextpad=0.6,
                  columnspacing=2.0, borderaxespad=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=600, bbox_inches='tight',
                    pad_inches=0.3, facecolor='white')
        print(f"FTIR plot saved: {save_path}")
    plt.show()


# ==================== Main ====================
p_list = find_real_peak_ftir(x, y)
print(f"FTIR strongest peak(s): {', '.join(map(str, map(int, p_list)))} cm⁻¹")

is_zoom = zoom_range is not None
if is_zoom:
    xmin, xmax = min(zoom_range), max(zoom_range)
    print(f"Zoom mode: {xmin:.0f} → {xmax:.0f} cm⁻¹")
else:
    xmin, xmax = soft_scale_ftir(p_list, x)
    print(f"Auto range: {xmin:.0f} → {xmax:.0f} cm⁻¹")

xmin, xmax, step = ftir_ticks(xmin, xmax)
print(f"Display range: {xmin:.0f} → {xmax:.0f} cm⁻¹  step={step}")

x_masked, y_shifted, y_masked, shifts, maxima, minima = auto_offset(
    x, y, xmin=xmin, xmax=xmax, gap_ratio=0.25, is_zoom=is_zoom)

plot_offset_stacked_ftir(x_masked, y_shifted, y_masked, shifts,
                         xmin, xmax, step, colors, lamda, label,
                         save_path, is_Absorbance,
                         is_peak_label=is_peak_label,
                         peak_min_prom=peak_min_prom,
                         peak_min_height=peak_min_height)

print("FTIR plot done.")
