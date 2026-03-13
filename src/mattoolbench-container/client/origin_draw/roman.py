import originpro as op
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Sequence, Optional, List

colors = ['#EF0000', '#FEC211', '#3BC371']

# User input
lamda = ['ex: 532 nm']
label=[]
is_2D_mark = False
is_Roman_ratio = True
is_Ratio__mark=True
is_Peak_annotate= True
is_Peak_label=True
peak_label_style="horizontal"
save_path = r'..\output_result\raman_stack.png'

# 1. Read data
wks = op.find_sheet()
df = wks.to_df()
print('df',df)
x = df.iloc[:, 0].values
y1 = df.iloc[:, 1].values
y2 = df.iloc[:, 3].values
y3 = df.iloc[:, 5].values
y=[y1,y2,y3]

# ==================== Select soft x-axis bounds near highest peak ====================
def soft_scale(p_list, x_data, is_2D_mark=True):
    """
    Select soft x-axis bounds for wavenumber range.
    If is_2D_mark=False, ignore the 2D peak (>2400 cm⁻¹) when computing bounds.
    """
    peaks = np.array(p_list)
    if len(peaks) == 0:
        raise ValueError("peaks_list cannot be empty!")

    if is_2D_mark==False:
        peaks = peaks[peaks < 2400]
        if len(peaks) == 0:
            peaks = np.array(p_list)

    center = peaks.mean()
    span = np.ptp(peaks)
    base_margin = span * 2.0
    total_width = span + 2 * base_margin
    extra_expand = total_width * 0.12

    xmin_raw = center - base_margin - extra_expand
    xmax_raw = center + base_margin + extra_expand

    x_low = np.percentile(x_data, 15)
    x_high = np.percentile(x_data, 85)
    xmin = min(x_low, xmin_raw)
    xmax = max(x_high, xmax_raw)

    if is_2D_mark==False and xmax > 2400:
        xmax = 2400

    return xmin, xmax

# ==================== Select appropriate Raman spectrum x-axis ticks ====================
def raman_ticks(xmin, xmax, is_2D_mark=True):
    """
    Choose appropriate x-axis ticks based on data range.
    7-10 ticks is considered ideal; unified scoring.
    If is_2D_mark=False, xmax is capped at 2400.
    """
    width = xmax - xmin
    candidates = [50, 100, 150, 200, 250, 300, 400, 450, 500]

    best_step = 100
    best_score = float('inf')

    for step in candidates:
        n_ticks = int(width / step) + 1

        if 7 <= n_ticks <= 10:
            score = 0  # ideal tick count
        elif n_ticks < 7:
            score = 100 + (7 - n_ticks)
        else:  # n_ticks > 10
            score = 100 + (n_ticks - 10)

        if score < best_score:
            best_score = score
            best_step = step

    xmin_aligned = np.floor(xmin / best_step) * best_step
    xmax_aligned = np.ceil(xmax / best_step) * best_step

    if xmax_aligned - xmax > best_step:
        xmax_aligned -= best_step
    if xmin - xmin_aligned > best_step:
        xmin_aligned += best_step

    # If 2D peak is hidden, cap xmax at 2400
    if not is_2D_mark and xmax_aligned > 2400:
        xmax_aligned = 2400

    return xmin_aligned, xmax_aligned, best_step


# ==================== Stacked spectrum offset calculation ====================
def auto_offset(x, y_list, xmin=None, xmax=None, gap_ratio=0.25):
    '''
    Inputs: raw x, raw y_list, xmin/xmax for display range, gap_ratio to control
    vertical spacing between stacked spectra.
    Returns: x_masked, y_shifted, y_original (for ratio calculation),
             shifts, maxima, minima within display range.
    '''
    y_list = [np.asarray(y) for y in y_list]
    n_spectra = len(y_list)

    if n_spectra == 0:
        raise ValueError("y_list cannot be empty!")

    # 1. Determine display range
    if xmin is None or xmax is None:
        xmin_use = 200 if xmin is None else xmin
        xmax_use = 2800 if xmax is None else xmax
    else:
        xmin_use, xmax_use = xmin, xmax

    mask = (x >= xmin_use) & (x <= xmax_use)
    x_masked = x[mask]

    # Crop all spectra
    y_masked = [y[mask] for y in y_list]

    # 2. Compute max and min within display range for each spectrum
    maxima = [y.max() for y in y_masked]
    minima = [y.min() for y in y_masked]

    # 3. Strict separation offset calculation (bottom to top)
    shifts = [0.0] # first spectrum has zero offset
    current_top = maxima[0] # current highest occupied position

    for i in range(1, n_spectra):
        # The bottom of this spectrum must be above the previous top + safety gap
        required_shift = current_top - minima[i] + (maxima[0] * gap_ratio)
        shifts.append(required_shift)
        current_top = maxima[i] + required_shift

    # 4. Apply offsets
    y_shifted = [y_masked[i] + shifts[i] for i in range(n_spectra)]

    return x_masked, y_shifted, y_masked, shifts, maxima, minima

# ==================== Key: intelligently find the "true highest peak" ====================
def find_real_peak(x, y_list, prominence_ratio=0.15, edge_ignore=0.07):
    """
    Select the highest among prominent peaks.
    prominence_ratio: peak must be at least 15% above surrounding valleys to count.
    edge_ignore: ignore the front and back 7% of data as edge zones.
    """
    x = np.asarray(x)
    peaks_found = []

    start = int(len(x) * edge_ignore)
    end = int(len(x) * (1 - edge_ignore))
    x_mid = x[start:end]

    for y in y_list:
        y = np.asarray(y)
        y_mid = y[start:end]

        # Find prominent peaks
        peaks, props = find_peaks(y_mid, prominence=y_mid.max() * prominence_ratio)

        if len(peaks) == 0: # No prominent peaks → fall back to highest point in middle region
            best_pos = float(x_mid[np.argmax(y_mid)])
        else:
            # Select peak with maximum prominence
            best_idx = peaks[np.argmax(props['prominences'])]
            best_pos = float(x_mid[best_idx])

        peaks_found.append(best_pos)

    return peaks_found

# ==================== Calculate ID/IG and I₂D/IG ====================
def calculate_raman_ratios(
    x: np.ndarray,
    y_original_list: Sequence[np.ndarray],
    D_pos: float = 1350,
    G_pos: float = 1580,
    D2_pos: float = 2700
) -> tuple[List[float], List[float]]:
    """
    Calculate Iᴅ/Iɢ and I₂ᴅ/Iɢ values for each spectrum (no plotting).

    Returns:
        ID_IG_list  : [0.95, 1.92, 0.32, ...]
        I2D_IG_list : [0.38, 1.12, 2.41, ...]
    """
    def _intensity_at(y: np.ndarray, pos: float) -> float:
        idx = np.argmin(np.abs(x - pos))
        return float(y[idx])

    ID_IG_list  = []
    I2D_IG_list = []

    for y in y_original_list:
        y = np.asarray(y)
        I_D  = _intensity_at(y, D_pos)
        I_G  = _intensity_at(y, G_pos)
        I_2D = _intensity_at(y, D2_pos)

        ID_IG  = I_D  / I_G if I_G > 0 else 0.0
        I2D_IG = I_2D / I_G if I_G > 0 else 0.0

        ID_IG_list.append(round(ID_IG, 3))
        I2D_IG_list.append(round(I2D_IG, 3))

    return ID_IG_list, I2D_IG_list

# ==================== Draw stacked spectra ====================
def plot_offset_stacked(
    x_masked: np.ndarray,
    y_shifted: Sequence[np.ndarray], # list of spectra with offsets already applied
    y_masked: Sequence[np.ndarray],  # used for ratio calculation
    shifts: Sequence[float], # offset for each spectrum (first is usually 0)
    xmin: float,
    xmax: float,
    colors: Sequence[str],
    lamda: str = "ex: 532 nm",
    label: Optional[Sequence[str]] = None,
    save_path: Optional[str] = None,
    is_Raman_ratio: bool = True,
    is_Ratio__mark=True,
    is_Peak_annotate=True
):
    """
    Parameters:
        x_masked : cropped wavenumber array
        y_shifted : list of offset-adjusted spectra [y1, y2+shift2, y3+shift3, ...]
        shifts : per-spectrum offsets (used for ylim calculation)
        xmin, xmax : display range
        colors : color list
        lamda : excitation wavelength, e.g. 'ex: 532 nm'
        label : sample name list (e.g. ['GO', 'rGO', 'Annealed']), None or empty = no labels
        save_path : save path (e.g. 'raman.pdf')
        is_Raman_ratio : whether to display ID/IG and I2D/IG ratios
        is_Ratio__mark : whether to annotate D/G/2D peak positions
        is_Peak_annotate : whether to use arrows to indicate G-peak shift
    """
    y_shifted = [np.asarray(y) for y in y_shifted]
    n = len(y_shifted)

    plt.rcParams['font.family'] = 'Times New Roman'
    fig, ax = plt.subplots(figsize=(10, 8))

    # Draw all spectra
    for i, y in enumerate(y_shifted):
        ax.plot(x_masked, y, color=colors[i], linewidth=3)

    # X-axis
    ax.set_xlim(xmin, xmax)
    step = 200 if (xmax - xmin) <= 2000 else 400
    ax.set_xticks(np.arange(
        np.ceil(xmin / step) * step,
        np.floor(xmax / step) * step + step,
        step
    ))
    ax.tick_params(axis='x', labelsize=18, length=8, width=1.5)

    # Hide Y-axis + draw all spines
    ax.set_yticks([])
    ax.tick_params(axis='y', left=False)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    # Auto-calculate optimal ylim
    all_mins = [y.min() for y in y_shifted]
    all_maxs = [y.max() for y in y_shifted]
    first_height = all_maxs[0] - all_mins[0]
    extra_gap = first_height / 4
    bottom = min(all_mins) - extra_gap
    top = max(all_maxs) + 2 * extra_gap
    ax.set_ylim(bottom, top)

    # Fixed axis labels
    ax.set_xlabel('Raman Shift (cm$^{-1}$)', fontsize=22, fontweight='bold', labelpad=12)
    ax.set_ylabel('Intensity (a.u.)', fontsize=22, fontweight='bold', labelpad=15)

    # Excitation wavelength
    if lamda:
        ax.text(0.98, 0.94, lamda[0], transform=ax.transAxes, fontsize=20, fontweight='bold',
                ha='right', va='top', color='black')

    # Sample labels (key fix: hide if label is empty or None)
    if label and len(label) == n and any(str(l).strip() for l in label):  # ← perfect check
        ylim = ax.get_ylim()
        total_h = ylim[1] - ylim[0]
        for i, name in enumerate(label):
            name_str = str(name).strip()
            if name_str and name_str.lower() not in ['none', 'nan', '']:
                y_center = np.mean(y_shifted[i])
                y_rel = (y_center - ylim[0]) / total_h
                y_rel = np.clip(y_rel, 0.08, 0.92)
                ax.text(0.02, y_rel, name_str, transform=ax.transAxes,
                        fontsize=20, fontweight='bold', color=colors[i],
                        va='center', ha='left')

    ID_IG_vals, I2D_IG_vals = calculate_raman_ratios(x_masked, y_masked)
    # Annotate ID/IG and I2D/IG
    if is_Raman_ratio and y_masked is not None:
        try:
            base_x = 0.02
            base_y = 0.98
            line_spacing = 0.06
            col_spacing = 0.07

            def color_for(i):
                return colors[i] if i < len(colors) else colors[-1]

            # -------------------------
            # Row 1: Iᴅ/Iɢ
            # -------------------------
            ax.text(base_x, base_y, "Iᴅ/Iɢ =", transform=ax.transAxes,
                    fontsize=16, fontweight='bold', color='black',
                    ha='left', va='top')

            current_x = base_x + 0.09
            for i, val in enumerate(ID_IG_vals):
                ax.text(current_x, base_y, f"{val:>.3f}",
                        transform=ax.transAxes,
                        fontsize=16, fontweight='bold', color=color_for(i),
                        ha='left', va='top')
                current_x += col_spacing

            # -------------------------
            # Row 2: I₂ᴅ/Iɢ
            # -------------------------
            if is_2D_mark:
                ax.text(base_x, base_y - line_spacing, "I₂ᴅ/Iɢ =", transform=ax.transAxes,
                        fontsize=16, fontweight='bold', color='black',
                        ha='left', va='top')

                current_x = base_x + 0.09
                for i, val in enumerate(I2D_IG_vals):
                    ax.text(current_x, base_y - line_spacing, f"{val:>.3f}",
                            transform=ax.transAxes,
                            fontsize=16, fontweight='bold', color=color_for(i),
                            ha='left', va='top')

        except Exception as e:
            print(f"Failed to annotate ID/IG: {e}")


    # Whether to annotate peak positions
    peak_positions = [1350, 1580, 2700]
    peak_labels = ['D', 'G', '2D']

    for pos, lab in zip(peak_positions, peak_labels):
        if lab == '2D' and not is_2D_mark:
            continue  # skip 2D peak annotation
        ax.axvline(pos, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax.text(pos, 0.02, lab, transform=ax.get_xaxis_text1_transform(0)[0],
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')

    # Whether to use arrows to indicate G-peak shift
    if is_Peak_annotate==True:
        ax.annotate('', xy=(1580, 0.9), xytext=(1594, 0.9),
                arrowprops=dict(arrowstyle='fancy', color='black', linewidth=2,
                mutation_scale=30),
                xycoords='data', textcoords='data')
    # Whether to write peak positions
    if is_Peak_label:
        nominal_positions = [1350, 1580, 2700]
        peak_names = ['D', 'G', '2D']

        if not is_2D_mark:
            nominal_positions = [1350, 1580]
            peak_names = ['D', 'G']

        search_tol = 40   # search within ±40 cm⁻¹ of nominal peak position

        # Process each spectrum independently
        for idx_spectrum, (y_shift, y_mask) in enumerate(zip(y_shifted, y_masked)):

            for pos_nom, pname in zip(nominal_positions, peak_names):

                # Crop window near nominal peak position
                mask_win = (x_masked >= pos_nom - search_tol) & (x_masked <= pos_nom + search_tol)

                if np.any(mask_win):
                    x_win = x_masked[mask_win]
                    y_win = np.array(y_mask)[mask_win]  # use masked original spectrum for peak finding

                    # Find prominent peaks (5% of local max as prominence threshold)
                    prom = max(y_win.max() * 0.05, 1e-12)
                    peaks_rel, props = find_peaks(y_win, prominence=prom)

                    if len(peaks_rel) > 0:
                        # Select peak with maximum prominence
                        best_idx = peaks_rel[np.argmax(props["prominences"])]
                        peak_x = float(x_win[best_idx])
                        peak_y_unshifted = float(y_win[best_idx])
                    else:
                        # No prominent peak in window → fall back to highest point
                        best_idx = int(np.argmax(y_win))
                        peak_x = float(x_win[best_idx])
                        peak_y_unshifted = float(y_win[best_idx])

                else:
                    # Outside window → fall back to nearest point in full data
                    gidx = int(np.argmin(np.abs(x_masked - pos_nom)))
                    peak_x = float(x_masked[gidx])
                    peak_y_unshifted = float(y_mask[gidx])

                # Display y must include the spectrum's offset
                peak_y_display = float(peak_y_unshifted + shifts[idx_spectrum])

                # Horizontal or vertical label format
                if peak_label_style.lower() == "horizontal":
                    text_str = f"{peak_x:.0f}"
                elif peak_label_style.lower() == "vertical":
                    text_str = "\n".join(list(f"{int(peak_x)}"))
                else:
                    raise ValueError("peak_label_style must be 'horizontal' or 'vertical'")

                # Annotate peak position
                ax.text(
                    peak_x,
                    peak_y_display,
                    text_str,
                    ha="center", va="bottom",
                    fontsize=18, fontweight='bold'
                )

    plt.tight_layout()
    if save_path:
        if save_path:
            plt.savefig(save_path,
                        dpi=300,
                        bbox_inches='tight',
                        pad_inches=0.4,
                        transparent=True,
                        facecolor='white')
            print(f"Publication-quality Raman plot saved: {save_path}")
        print(f"Plot saved: {save_path}")
    plt.show()

# ==================== Main flow ====================
# Draw stacked plot: identify highest peak, select soft x range near peak,
# choose appropriate tick spacing, compute vertical offsets, then plot.
p_list = find_real_peak(x, y)
print(f"Intelligently identified true highest peaks → {', '.join(map(str, map(int, p_list)))} cm⁻¹ (edge false peaks excluded)")
xmin, xmax = soft_scale(p_list, x, is_2D_mark=is_2D_mark)
xmin, xmax, step = raman_ticks(xmin, xmax)
print(f"100% data-driven display range: {xmin:.0f} → {xmax:.0f} cm⁻¹ (step {step})")
[x_masked, y_shifted, y_masked, shifts, maxima, minima] = auto_offset(x, y, xmin=xmin, xmax=xmax, gap_ratio=0.25)
plot_offset_stacked(x_masked, y_shifted, y_masked,shifts, xmin, xmax, colors, lamda, label, save_path,is_Raman_ratio=is_Roman_ratio,is_Ratio__mark=is_Ratio__mark,is_Peak_annotate=is_Peak_annotate)
print("Stacked Raman spectrum plot successfully generated!")
