import originpro as op
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Sequence, Optional, List

colors = ['#000000', '#FF0000', '#FEC211', '#3BC371']

# ==================== User Input (FTIR-specific) ===================
lamda = []
label = ['Gel afer vacuum dry']
is_Absorbance = False
zoom_range = [(1140, 1260)]
save_path = r'..\output_result\ftir_stack.png'

# 1. Read data
wks = op.find_sheet()
df = wks.to_df()
print('df', df)
x = df.iloc[:, 0].values
y1 = df.iloc[:, 1].values
#y3 = df.iloc[:, 3].values
y = [y1]

# ==================== FTIR-specific: Auto-select appropriate IR ticks ====================
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
    
    best_step = candidates[0]
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
            best_step = step
    
    xmin_aligned = np.floor(xmin / best_step) * best_step
    xmax_aligned = np.ceil(xmax / best_step) * best_step
    return xmin_aligned, xmax_aligned, best_step

# ==================== Auto-select display range based on strongest absorption peak ====================
def soft_scale_ftir(p_list, x_data):
    peaks = np.array(p_list)
    if len(peaks) == 0:
        raise ValueError("peaks_list cannot be empty!")
    center = peaks.mean()
    span = np.ptp(peaks)
    base_margin = max(800, span * 2.5)
    extra_expand = base_margin * 0.15
    xmin_raw = center - base_margin - extra_expand
    xmax_raw = center + base_margin + extra_expand
    xmin = max(400, min(x_data.min(), xmin_raw))
    xmax = min(4000, max(x_data.max(), xmax_raw))
    return xmin, xmax

# ==================== Stacked spectrum offset calculation ====================
def auto_offset(x, y_list, xmin=None, xmax=None, gap_ratio=0.25):
    if zoom_range is not None:
        gap_ratio=0
    y_list = [np.asarray(y) for y in y_list]
    n_spectra = len(y_list)
    if n_spectra == 0:
        raise ValueError("y_list cannot be empty!")
    xmin_use = 400 if xmin is None else xmin
    xmax_use = 4000 if xmax is None else xmax
    mask = (x >= xmin_use) & (x <= xmax_use)
    x_masked = x[mask]
    y_masked = [y[mask] for y in y_list]
    maxima = [y.max() for y in y_masked]
    minima = [y.min() for y in y_masked]
    shifts = [0.0]
    current_top = maxima[0]
    for i in range(1, n_spectra):
        required_shift = current_top - minima[i] + (maxima[0] * gap_ratio)
        shifts.append(required_shift)
        current_top = maxima[i] + required_shift
    y_shifted = [y_masked[i] + shifts[i] for i in range(n_spectra)]
    return x_masked, y_shifted, y_masked, shifts, maxima, minima

# ==================== Auto-detect the strongest real absorption peak ====================
def find_real_peak_ftir(x, y_list, prominence_ratio=0.12, edge_ignore=0.05):
    x = np.asarray(x)
    peaks_found = []
    start = int(len(x) * edge_ignore)
    end = int(len(x) * (1 - edge_ignore))
    x_mid = x[start:end]
    for y in y_list:
        y = np.asarray(y)
        y_mid = y[start:end]
        peaks, props = find_peaks(y_mid, prominence=y_mid.max() * prominence_ratio)
        if len(peaks) == 0:
            best_pos = float(x_mid[np.argmax(y_mid)])
        else:
            best_idx = peaks[np.argmax(props['prominences'])]
            best_pos = float(x_mid[best_idx])
        peaks_found.append(best_pos)
    return peaks_found

# ==================== Plot FTIR offset-stacked spectrum ====================
def plot_offset_stacked_ftir(
    x_masked: np.ndarray,
    y_shifted: Sequence[np.ndarray],
    y_masked: Sequence[np.ndarray],
    shifts: Sequence[float],
    xmin: float,
    xmax: float,
    step: float,
    colors: Sequence[str],
    lamda: str = "ATR-FTIR",
    label: Optional[Sequence[str]] = None,
    save_path: Optional[str] = None,
    is_Absorbance: bool = True
):
    y_shifted = [np.asarray(y) for y in y_shifted]
    n = len(y_shifted)
    plt.rcParams['font.family'] = 'Times New Roman'
    fig, ax = plt.subplots(figsize=(10, 8))

    #for i, y in enumerate(y_shifted):
        #ax.plot(x_masked, y, color=colors[i % len(colors)], linewidth=2.5)
    for i, y in enumerate(y_shifted):
        lbl = label[i] if (label and i < len(label)) else None
        ax.plot(x_masked, y, color=colors[i % len(colors)], linewidth=2.5, label=lbl)

    # ============ X 轴完美刻度（关键修复）============
    ax.set_xlim(xmin, xmax)
    ax.invert_xaxis()

    # 使用主流程中已经算好的、对齐后的 xmin/xmax/step
    start_tick = np.ceil(xmin / step) * step
    end_tick   = np.floor(xmax / step) * step

    if start_tick <= xmin: start_tick = xmin
    if end_tick >= xmax:   end_tick = xmax - (xmax - end_tick) % step

    ticks = np.arange(start_tick, end_tick + step*0.6, step)
    ax.set_xticks(ticks)
    ax.tick_params(axis='x', labelsize=18, length=8, width=1.5)

    # ============ Y 轴 ============
    ax.set_yticks([])
    ax.tick_params(axis='y', left=False)
    if not is_Absorbance:
        ax.invert_yaxis()
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    # ============ 自动 ylim ============
    all_mins = [y.min() for y in y_shifted]
    all_maxs = [y.max() for y in y_shifted]
    first_height = all_maxs[0] - all_mins[0]
    extra_gap = first_height / 4
    bottom = min(all_mins) - extra_gap
    top = max(all_maxs) + 2 * extra_gap
    ax.set_ylim(bottom, top)

    # ============ 标签 ============
    ax.set_xlabel('Wavenumber (cm$^{-1}$)', fontsize=22, fontweight='bold', labelpad=12)
    ylabel = ' Absorbance(a.u.)' if is_Absorbance else 'Transmittance (%)'
    ax.set_ylabel(ylabel, fontsize=22, fontweight='bold', labelpad=15)

    if lamda:
        ax.text(0.98, 0.94, lamda[0], transform=ax.transAxes, fontsize=20,
                fontweight='bold', ha='right', va='top', color='black')

    #if label and len(label) == n and any(str(l).strip() for l in label):
        #ylim = ax.get_ylim()
        #total_h = ylim[1] - ylim[0]
        #for i, name in enumerate(label):
            #name_str = str(name).strip()
            #if name_str and name_str.lower() not in ['none', 'nan', '']:
                #y_center = np.mean(y_shifted[i])
                #y_rel = (y_center - ylim[0]) / total_h
                #y_rel = np.clip(y_rel, 0.08, 0.92)
                #ax.text(0.02, y_rel, name_str, transform=ax.transAxes,
                        #fontsize=20, fontweight='bold', color=colors[i % len(colors)],
                        #va='center', ha='left')
    
    if label and any(str(l).strip() for l in label):
        ax.legend(
        loc='upper right',
        fontsize=22,
        frameon=False,
        handlelength=2.0,
        handletextpad=0.8,
        labelspacing=0.5
    )
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                    pad_inches=0.4, transparent=True, facecolor='white')
        print(f"Publication-quality FTIR stacked spectrum saved: {save_path}")
    plt.show()

# ==================== Main workflow ====================
p_list = find_real_peak_ftir(x, y)
print(f"FTIR auto-detected strongest absorption peak(s): {', '.join(map(str, map(int, p_list)))} cm⁻¹")

if zoom_range:
    xmin, xmax = zoom_range[0][0], zoom_range[0][1]
    print(f"FTIR local zoom mode: {xmin:.0f} → {xmax:.0f} cm⁻¹")
else:
    xmin, xmax = soft_scale_ftir(p_list, x)
    print(f"FTIR auto-range: {xmin:.0f} → {xmax:.0f} cm⁻¹")
xmin, xmax, step = ftir_ticks(xmin, xmax)
print(f"FTIR display range: {xmin:.0f} → {xmax:.0f} cm⁻¹ (step {step})")

x_masked, y_shifted, y_masked, shifts, maxima, minima = auto_offset(
    x, y, xmin=xmin, xmax=xmax, gap_ratio=0.25)

plot_offset_stacked_ftir(x_masked, y_shifted, y_masked, shifts,
                         xmin, xmax, step, colors, lamda, label, save_path, is_Absorbance)

print("Publication-quality FTIR stacked spectrum generated successfully!")