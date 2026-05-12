import os
import re

import originpro as op
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

# ====================== User Settings ======================
sample_sheets = ['WRTZSX5', 'WRTZSX6', 'WRTZSX7']
pdf_sheets    = ['PDF990073', 'PDF990030']
sample_labels = ['WRTZSX5', 'WRTZSX6', 'WRTZSX7']
pdf_labels    = ['PDF#99-0073', 'PDF#99-0030']

# ====================== Color Palettes ======================
# 修改 ACTIVE_PALETTE 切换配色，samples 和 pdf 成对设计
XRD_PALETTES = {
    # 期刊风格
    "tab10":      {"sample": ['#D62728', '#1F77B4', '#2CA02C'],          "pdf": ['#1A6FDF', '#37AD6B']},
    "nature":     {"sample": ['#E64B35', '#4DBBD5', '#00A087'],          "pdf": ['#3C5488', '#F39B7F']},
    "science":    {"sample": ['#3B4992', '#EE0011', '#008B45'],          "pdf": ['#7B4F9E', '#E87D21']},
    "cell":       {"sample": ['#DF8244', '#5B9BD5', '#70AD47'],          "pdf": ['#8E44AD', '#C0392B']},

    # 色盲安全
    "okabe_ito":  {"sample": ['#E69F00', '#56B4E9', '#009E73'],          "pdf": ['#0072B2', '#D55E00']},
    "tol_bright": {"sample": ['#EE6677', '#4477AA', '#228833'],          "pdf": ['#CCBB44', '#AA3377']},

    # 暖色系样品 + 冷色 PDF
    "warm_cool":  {"sample": ['#C0392B', '#E67E22', '#D4AC0D'],          "pdf": ['#2471A3', '#1A5276']},

    # 冷色系样品 + 暖色 PDF
    "cool_warm":  {"sample": ['#2980B9', '#8E44AD', '#17A589'],          "pdf": ['#C0392B', '#D68910']},

    # 低饱和度（适合黑白打印仍有层次）
    "muted":      {"sample": ['#7B3F00', '#1A5276', '#1E8449'],          "pdf": ['#515A5A', '#935116']},

    # 灰度（纯黑白打印）
    "grayscale":  {"sample": ['#111111', '#555555', '#999999'],          "pdf": ['#333333', '#777777']},

    # 黑白简洁（纯黑样品线 + 虚线风格区分，PDF 用深浅灰）
    "bw_clean":   {"sample": ['#000000', '#000000', '#000000'],          "pdf": ['#000000', '#000000']},

    # 蓝 / 红 / 黑
    "brk":        {"sample": ['#1F77B4', '#D62728', '#000000'],          "pdf": ['#555555', '#AAAAAA']},
}

ACTIVE_PALETTE = "tab10"   # ← 改这里切换
colors_sample  = XRD_PALETTES[ACTIVE_PALETTE]["sample"]
colors_pdf     = XRD_PALETTES[ACTIVE_PALETTE]["pdf"]

# bw_clean 模式下用线型区分三条曲线，其他模式统一实线
if ACTIVE_PALETTE == "bw_clean":
    linestyles_sample = ['-', '--', ':']
else:
    linestyles_sample = ['-', '-', '-']

save_path = os.path.join('..', 'output_result', 'XRD_final.png')
save_path = r'C:\Users\wu\Desktop\XRD_终极完美版.png'
is_hkl          = True
is_sample_legend = True
is_pdf_legend    = True

# 样品名标注位置："right" = 曲线右侧图内，"top" = 图顶部横向图例
label_position  = "right"

# =========== Parameter Settings ============================
pdf_height_ratio    = 0.40
gap_ratio           = 0.28
pdf_gap_from_sample = 0.5
search_window       = 0.4     # hkl 匹配容差 (°)
min_peak_height_ratio = 0.38  # 只标注主峰
min_peak_distance_deg = 1.8   # 最小峰间距
# ===========================================================

# 1. Read sample data
samples = []
for name in sample_sheets:
    wks = op.find_sheet('w', name)
    df  = wks.to_df()
    samples.append((df.iloc[:, 0].values, df.iloc[:, 1].values))

# 2. Read PDF (bar drawing + hkl matching)
pdf_data      = []
standard_peaks = []

for idx, name in enumerate(pdf_sheets):
    wks   = op.find_sheet('w', name)
    df    = wks.to_df()
    x_pdf = df.iloc[:, 0].values.astype(float)
    inten = df.iloc[:, 1].values.astype(float)

    # Extract hkl indices
    data_part = df.iloc[:, 4:] if df.shape[1] > 4 else df.iloc[:, 2:]
    hkl_list  = []
    for row in data_part.values.astype(str):
        items  = [s.strip() for s in row if s.strip() not in ('nan', '', '<undefined>', 'None')]
        digits = []
        for item in items:
            m = re.search(r'-?\d+', item)
            if m:
                digits.append(m.group())
            if len(digits) >= 3:
                break
        hkl_list.append(f"({digits[0]}{digits[1]}{digits[2]})" if len(digits) == 3 else "")
    hkl_arr = np.array(hkl_list)

    pdf_data.append((x_pdf, inten, hkl_arr))
    inten_norm = inten / inten.max() if inten.max() > 0 else inten
    standard_peaks.append(list(zip(x_pdf, hkl_arr, inten_norm)))

# 3. Display range
all_x = np.concatenate([x for x, _ in samples])
xmin  = max(10, np.percentile(all_x, 3))
xmax  = min(90, np.percentile(all_x, 97))

# 4. Stacked offsets
def calculate_offsets(y_list, gap_ratio=0.28):
    maxima    = [np.max(y) for y in y_list]
    minima    = [np.min(y) for y in y_list]
    offsets   = [0.0]
    current_top = maxima[0]
    for i in range(1, len(y_list)):
        shift = current_top - minima[i] + maxima[0] * gap_ratio
        offsets.append(shift)
        current_top = maxima[i] + shift
    return offsets, maxima[0]

y_only = [y for _, y in samples]
offsets_sample, base_height = calculate_offsets(y_only, gap_ratio)
y_shifted        = [y + off for y, off in zip(y_only, offsets_sample)]
lowest_sample_y  = min(arr.min() for arr in y_shifted)
highest_sample_y = max(arr.max() for arr in y_shifted)

# ==================== Plot ====================
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.linewidth'] = 1.5
fig, ax = plt.subplots(figsize=(10, 8))

# 1. Sample curves
for i, ((x, y), offset, label) in enumerate(zip(samples, offsets_sample, sample_labels)):
    ax.plot(x, y + offset, color=colors_sample[i],
            linewidth=0.9, linestyle=linestyles_sample[i])

# 2. hkl annotations — 三条曲线各自标注
if is_hkl and standard_peaks:
    all_ref_peaks = [
        (pos, hkl, inten)
        for peaks_list in standard_peaks
        for pos, hkl, inten in peaks_list
        if inten > 0.15
    ]
    all_ref_peaks.sort(key=lambda t: t[2], reverse=True)

    for i, ((x_sam, y_sam), offset, color) in enumerate(zip(samples, offsets_sample, colors_sample)):
        y_sh = y_sam + offset
        peaks, _ = find_peaks(
            y_sh,
            height=np.max(y_sh) * min_peak_height_ratio,
            distance=len(x_sam) * min_peak_distance_deg / (xmax - xmin),
            prominence=np.max(y_sh) * 0.12,
        )
        labeled = set()
        for peak_idx in peaks:
            pos = x_sam[peak_idx]
            if not (xmin <= pos <= xmax) or round(pos, 1) in labeled:
                continue
            best_hkl, best_dist = None, float('inf')
            for ref_pos, hkl, _ in all_ref_peaks:
                d = abs(pos - ref_pos)
                if d < search_window and d < best_dist:
                    best_dist, best_hkl = d, hkl
            if best_hkl:
                ax.text(pos, y_sh[peak_idx] + base_height * 0.06,
                        best_hkl, ha='center', va='bottom',
                        fontsize=9, fontweight='normal', color=color)
                labeled.add(round(pos, 1))

# 3. PDF bars
actual_pdf_bottom = lowest_sample_y - base_height * pdf_gap_from_sample
if pdf_data:
    pdf_h   = base_height * pdf_height_ratio
    start_y = lowest_sample_y - base_height * pdf_gap_from_sample

    for idx, (x_pdf, inten, hkl) in enumerate(pdf_data):
        if inten.max() == 0:
            continue
        scaled = inten / inten.max() * pdf_h
        bottom = start_y - idx * (pdf_h + base_height * 0.18)
        mask   = (x_pdf >= xmin - 1) & (x_pdf <= xmax + 1)
        ax.bar(x_pdf[mask], scaled[mask], bottom=bottom, width=0.15,
               color=colors_pdf[idx], alpha=1.0, align='center')
        actual_pdf_bottom = bottom

# ==================== Aesthetics ====================
ax.set_xlim(xmin, xmax)
ax.set_xlabel(r'2$\theta$ (°)', fontsize=20, fontweight='bold', labelpad=10)
ax.set_ylabel('Intensity (a.u.)', fontsize=20, fontweight='bold', labelpad=14)

step = 10 if (xmax - xmin) <= 60 else 20
ax.set_xticks(np.arange(np.ceil(xmin / step) * step, xmax + step, step))
# 内刻度（Nature/Science 风格）
ax.tick_params(axis='x', labelsize=16, length=5, width=1.5, direction='in',
               top=True)
ax.tick_params(axis='y', left=False, right=False)
ax.set_yticks([])

# 四边框全显示（封闭 box）
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(1.5)

# Y limits
if pdf_data:
    total_ymin = actual_pdf_bottom - base_height * 0.15
else:
    total_ymin = lowest_sample_y - base_height * 0.4
total_ymax = highest_sample_y + base_height * 0.80
ax.set_ylim(total_ymin, total_ymax)

# ── 样品名标注 ──
if is_sample_legend:
    if label_position == "top":
        # 顶部横向图例（彩色线段 + 文字）
        sample_patches = [plt.Line2D([0], [0], color=colors_sample[i],
                                     lw=2.5, linestyle=linestyles_sample[i])
                          for i in range(len(sample_labels))]
        leg = ax.legend(sample_patches, sample_labels,
                        loc='upper center',
                        bbox_to_anchor=(0.5, 1.0),
                        ncol=len(sample_labels),
                        fontsize=13, frameon=False,
                        columnspacing=2.0, handlelength=2.0,
                        borderaxespad=0.3)
        ax.add_artist(leg)
    else:
        # right 模式：曲线右侧图内 1/4 处
        for i, (label, offset) in enumerate(zip(sample_labels, offsets_sample)):
            y_min_i = offset + np.min(y_only[i])
            y_max_i = offset + np.max(y_only[i])
            y_label = y_min_i + (y_max_i - y_min_i) * 0.25
            ax.text(0.97, (y_label - total_ymin) / (total_ymax - total_ymin),
                    label,
                    transform=ax.transAxes,
                    color=colors_sample[i],
                    fontsize=12, fontweight='bold',
                    va='center', ha='right')

# ── PDF 标签：标在条形右侧，图内 ──
if pdf_data and is_pdf_legend:
    pdf_h   = base_height * pdf_height_ratio
    start_y = lowest_sample_y - base_height * pdf_gap_from_sample
    for idx in range(len(pdf_data)):
        bottom  = start_y - idx * (pdf_h + base_height * 0.18)
        y_label = bottom + pdf_h * 0.2  # 条形高度 1/5 处
        ax.text(0.97, (y_label - total_ymin) / (total_ymax - total_ymin),
                pdf_labels[idx],
                transform=ax.transAxes,
                color=colors_pdf[idx],
                fontsize=11, fontweight='bold',
                va='center', ha='right')

plt.tight_layout(pad=1.5)
plt.savefig(save_path, dpi=600, bbox_inches='tight', facecolor='white')
print(f"XRD plot saved: {save_path}")
plt.show()
