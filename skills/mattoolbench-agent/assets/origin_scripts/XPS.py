import os
import originpro as op
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ====================== User Settings ======================

# 1. Sheet name
SHEET_NAME = 'book4'

# Whether Col 3 is a fitted background column (True) or first component (False)
HAS_BG_COLUMN = True

# Spectrum and component labels  ← moved here from data-loading block
SPECTRUM_LABEL   = 'Zn 2p'
COMPONENT_LABELS = ['Zn $2p_{1/2}$', 'Zn $2p_{3/2}$']

# 2. Style settings
raw_color = '#555555'        # raw data scatter
sum_color = '#C0392B'        # fit total curve (deep red, less saturated)
bg_color  = '#2C3E50'        # background curve (dark slate)

# Component fill color presets — change ACTIVE_COMP_PALETTE to switch
COMP_PALETTES = {
    "two_comp":   ['#AED6F1', '#F9E79F'],                          # blue / yellow (2-comp, e.g. Zn 2p)
    "three_comp": ['#AED6F1', '#A9DFBF', '#F9E79F'],               # blue / green / yellow
    "four_comp":  ['#AED6F1', '#A9DFBF', '#F9E79F', '#F1948A'],    # + pink
    "tol_safe":   ['#77AADD', '#EE8866', '#AAAA00', '#BBCC33',     # Paul Tol colorblind-safe
                   '#44BB99', '#EEDD88', '#DDDDDD', '#000000'],
    "nature":     ['#4DBBD5', '#E64B35', '#00A087', '#3C5488',
                   '#F39B7F', '#8491B4', '#91D1C2', '#DC0000'],
}
ACTIVE_COMP_PALETTE = "two_comp"
component_colors = COMP_PALETTES[ACTIVE_COMP_PALETTE]

save_path = os.path.join('..', 'output_result', 'XPS_Fitted_Spectra_Plot.png')
save_path = r'C:\Users\wu\Desktop\XPS_Fitted_Spectra_Plot.png' # 图像保存路径
# 3. Feature flags
is_fit_total_curve        = True   # draw total fit curve
is_raw_data               = True   # draw raw data scatter
is_bg_curve               = True   # draw background curve
is_residual               = True   # draw residual (Raw − Fit Total) at top
is_component_labeled_on_peak = False  # annotate labels on peaks instead of legend
is_sample_legend          = True   # show legend

# 4. X-axis padding (eV)
X_PADDING = 0.5

# ===========================================================

# Load data from Origin
try:
    wks = op.find_sheet('w', SHEET_NAME)
    if wks is None:
        raise ValueError(f"Sheet '{SHEET_NAME}' not found in Origin.")
    df = wks.to_df()

    # 空单元格 → NaN，再删掉 X/Y 为空的行
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=[df.columns[0], df.columns[1]]).reset_index(drop=True)

    X_DATA      = df.iloc[:, 0].values.astype(float)
    Y_RAW       = df.iloc[:, 1].values.astype(float)
    Y_FIT_TOTAL = df.iloc[:, 2].values.astype(float)

    if HAS_BG_COLUMN:
        Y_BG       = df.iloc[:, 3].values.astype(float)
        COMP_START = 4
    else:
        Y_BG       = np.full_like(X_DATA, np.min(Y_RAW))
        COMP_START = 3

    # 跳过全为 NaN 的空列
    COMPONENTS = [df.iloc[:, c].values.astype(float)
                  for c in range(COMP_START, df.shape[1])
                  if df.iloc[:, c].notna().any()]

    if len(COMPONENT_LABELS) != len(COMPONENTS):
        print(f"Warning: {len(COMPONENT_LABELS)} labels but "
              f"{len(COMPONENTS)} components — extras labelled Comp N.")

    DYNAMIC_XMIN = np.min(X_DATA) - X_PADDING
    DYNAMIC_XMAX = np.max(X_DATA) + X_PADDING

except Exception as e:
    print(f"Error loading data from '{SHEET_NAME}': {e}")
    X_DATA = Y_RAW = Y_FIT_TOTAL = Y_BG = np.array([])
    COMPONENTS   = []
    DYNAMIC_XMIN = 1010.0
    DYNAMIC_XMAX = 1050.0

# ===========================================================

def plot_xps_spectra_fitted():
    if len(X_DATA) == 0 or len(COMPONENTS) == 0:
        print("Required XPS data is missing. Exiting.")
        return

    base_height = np.max(Y_RAW) - np.min(Y_RAW)
    xmin, xmax  = DYNAMIC_XMIN, DYNAMIC_XMAX

    plt.rcParams['font.family']       = 'Times New Roman'
    plt.rcParams['axes.unicode_minus'] = False

    # ── Layout: optional residual panel on top ──────────────
    if is_residual:
        fig, (ax_res, ax) = plt.subplots(
            2, 1, figsize=(10, 8),
            gridspec_kw={'height_ratios': [1, 4], 'hspace': 0.05},
            sharex=True,
        )
        residual = Y_RAW - Y_FIT_TOTAL
        res_range = np.max(np.abs(residual))
        ax_res.plot(X_DATA, residual, color='#7F8C8D', linewidth=1.0)
        ax_res.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax_res.set_ylim(-res_range * 2.5, res_range * 2.5)
        ax_res.set_yticks([])
        ax_res.set_ylabel('Residual', fontsize=13, fontweight='bold', labelpad=8)
        for spine in ax_res.spines.values():
            spine.set_linewidth(1.2)
        ax_res.tick_params(axis='x', bottom=False, labelbottom=False)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))

    # ── Legend lists (built in display order: Raw → Fit → Comp → BG) ──
    leg_handles, leg_labels = [], []

    # Raw data  (added to legend first)
    if is_raw_data:
        raw_h, = ax.plot(X_DATA, Y_RAW,
                         'o', markersize=3.5,
                         markeredgecolor=raw_color,
                         markerfacecolor='none',
                         markeredgewidth=0.9,
                         linewidth=0,
                         label='Raw')
        leg_handles.append(raw_h)
        leg_labels.append('Raw')

    # Fit total
    if is_fit_total_curve:
        fit_h, = ax.plot(X_DATA, Y_FIT_TOTAL,
                         color=sum_color, linewidth=1.8,
                         label='Fit Total')
        leg_handles.append(fit_h)
        leg_labels.append('Fit Total')

    # Components (fills)
    for j, comp_y in enumerate(COMPONENTS):
        color      = component_colors[j % len(component_colors)]
        comp_label = (COMPONENT_LABELS[j] if j < len(COMPONENT_LABELS)
                      else f'Comp {j + 1}')
        fill_h = ax.fill_between(X_DATA, Y_BG, comp_y,
                                 color=color, alpha=0.75, linewidth=0)

        if is_component_labeled_on_peak:
            peak_idx = np.argmax(comp_y)
            ax.text(X_DATA[peak_idx],
                    comp_y[peak_idx] + base_height * 0.03,
                    comp_label,
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold', color='black')
        else:
            leg_handles.append(fill_h)
            leg_labels.append(comp_label)

    # Background
    if is_bg_curve:
        bg_h, = ax.plot(X_DATA, Y_BG,
                        color=bg_color, linewidth=1.2,
                        linestyle='--', label='BG')
        leg_handles.append(bg_h)
        leg_labels.append('BG')

    # ── Axes ────────────────────────────────────────────────
    ax.set_xlim(xmin, xmax)
    ax.invert_xaxis()   # XPS convention: high BE on left
    ax.set_ylim(np.min(Y_BG) - base_height * 0.10,
                np.max(Y_RAW) + base_height * 0.22)

    ax.set_xlabel(r'Binding Energy (eV)', fontsize=20, fontweight='bold', labelpad=12)
    ax.set_ylabel('Intensity (a.u.)',     fontsize=20, fontweight='bold', labelpad=18)
    ax.set_yticks([])
    ax.tick_params(axis='both', labelsize=18, length=8, width=1.5)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    # Spectrum label — axes fraction 坐标，避免受 invert_xaxis 影响
    ax.text(0.97, 0.95, SPECTRUM_LABEL,
            transform=ax.transAxes,
            ha='right', va='top',
            fontsize=16, fontweight='bold', color='black')

    # ── Legend ──────────────────────────────────────────────
    if is_sample_legend and leg_handles:
        # 超过 3 项时换成两列，避免单行过宽
        ncol = 1 if len(leg_handles) <= 2 else 2
        ax.legend(leg_handles, leg_labels,
                  loc='upper left',
                  fontsize=14,
                  ncol=ncol,
                  frameon=True,
                  framealpha=0.85,
                  handlelength=1.5,
                  labelspacing=0.4,
                  borderpad=0.6)

    # ── Save ────────────────────────────────────────────────
    plt.tight_layout(pad=1.2)
    plt.savefig(save_path, dpi=600, bbox_inches='tight', facecolor='white')
    print(f"XPS plot saved: {save_path}")
    plt.show()


if __name__ == '__main__':
    try:
        plot_xps_spectra_fitted()
    except Exception as e:
        print(f"Error during execution: {e}")
