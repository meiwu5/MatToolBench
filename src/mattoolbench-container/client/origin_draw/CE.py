import originpro as op
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

# --- User Input and Configuration ---

# Define all possible series with names, colors, and Z-order
ALL_SERIES_CONFIG = [
    # Colors modified per user input
    {'name': 'Bare Zn', 'color': '#86B5E8', 'zorder': 0}, # blue (Z=0, topmost layer)
    {'name': 'FAZ@Zn', 'color':'#D989A9' , 'zorder': 1},  # pink (Z=1)
    {'name': 'Sample C', 'color': '#A9A9A9', 'zorder': 2},
    # ... add more series as needed ...
]

LINEWIDTH = 1.5
DPI = 300
save_path_vt = r'..\output_result\voltage_time_curve_with_inset_optimized.png'

# --- Annotation and Inset Zoom Configuration ---

USE_RATE_MODE_ANNOTATION = False
DEFAULT_TOP_ANNOTATION = r'$\mathbf{1\ mA\ cm^{-2},\ 1\ mAh\ cm^{-2}}$'
RATE_PERFORMANCE_ANNOTATION = r'$\mathbf{Unit: mA\ cm^{-2}}$'

# 2. Inset zoom configuration
ENABLE_INSET = False

# X-axis range for inset zoom region (in main plot coordinates)
INSET_XLIM = (20, 60)
# Y-axis range for inset zoom (to zoom in on polarization plateau)
INSET_YLIM = (-0.05, 0.05)
# Inset position: [left, bottom, width, height] (relative to main axes, 0 to 1)
INSET_POSITION = [0.55, 0.5, 0.3, 0.35]


# --- 1. OriginPro Data Loading and Preparation ---
data_series: List[Dict[str, np.ndarray]] = []
start_col_index = 2
try:
    wks_vt = op.find_sheet()
    df_vt = wks_vt.to_df()
    print('df_vt shape:', df_vt.shape)

    df_data_vt = df_vt.iloc[1:]
    # Clean NaN values; use infer_objects(copy=False) to avoid FutureWarning
    df_data_vt = df_data_vt.replace(['', '--', '---', 'None'], np.nan).infer_objects(copy=False)

    total_cols = df_data_vt.shape[1]
    REQUIRED_SERIES_COUNT = 2

    if total_cols < start_col_index + REQUIRED_SERIES_COUNT * 2:
         raise ValueError(f"Insufficient columns in worksheet. Need {start_col_index + REQUIRED_SERIES_COUNT * 2} columns to read {REQUIRED_SERIES_COUNT} series.")

    for i in range(REQUIRED_SERIES_COUNT):
        x_col = start_col_index + i * 2
        y_col = start_col_index + i * 2 + 1

        x_data = pd.to_numeric(df_data_vt.iloc[:, x_col], errors='coerce').values
        y_data = pd.to_numeric(df_data_vt.iloc[:, y_col], errors='coerce').values

        valid_indices = ~np.isnan(x_data) & ~np.isnan(y_data)

        data_series.append({
            'name': ALL_SERIES_CONFIG[i]['name'],
            'color': ALL_SERIES_CONFIG[i]['color'],
            'zorder': ALL_SERIES_CONFIG[i]['zorder'],
            'x': x_data[valid_indices],
            'y': y_data[valid_indices]
        })
        print(f"Successfully loaded series {ALL_SERIES_CONFIG[i]['name']} (cols {x_col} and {y_col}), {len(x_data[valid_indices])} data points")

    if not data_series:
         raise ValueError("No valid data series loaded from Origin. Check start column index and data format.")

except Exception as e:
    print(f"Failed to load Origin data: {e}. Using simulated data as fallback.")

    # --- Simulated data (using 160h as total duration) ---
    T_max = 160
    data_series = []

    # 1. Bare Zn (blue, Z=1)
    time_zn = np.linspace(0, T_max, 1000)
    potential_zn = np.sin(time_zn / 100) * 0.002 + np.random.uniform(-0.005, 0.005, 1000)
    data_series.append({'name': 'Bare Zn', 'color': ALL_SERIES_CONFIG[0]['color'], 'zorder': 1, 'x': time_zn, 'y': potential_zn})

    # 2. FAZ@Zn (pink, Z=0)
    time_faz = np.linspace(0, T_max, 1000)
    potential_faz = np.clip(np.sin(time_faz / 50) * 0.005, -0.05, 0.05) + np.random.uniform(-0.02, 0.02, 1000)
    data_series.append({'name': 'FAZ@Zn', 'color': ALL_SERIES_CONFIG[1]['color'], 'zorder': 0, 'x': time_faz, 'y': potential_faz})


# ----------------------------------------------------------------------
## Plot voltage-time curve function (optimized inset)
# ----------------------------------------------------------------------

def plot_voltage_time_multi(data_series: List[Dict], save_path: str, use_rate_mode: bool, enable_inset: bool, xlim_inset: Tuple, ylim_inset: Tuple, inset_pos: List):

    plt.rcParams['font.family'] = 'Arial'
    plt.rcParams['font.weight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.linewidth'] = 1.5

    fig, ax = plt.subplots(figsize=(10, 5))

    # Draw main plot
    # Smaller Z-order = on top. Sort ascending (Z=0 first means it draws on top last)
    data_series.sort(key=lambda s: s['zorder'])
    for series in data_series:
        ax.plot(series['x'], series['y'],
                 color=series['color'],
                 linewidth=LINEWIDTH,
                 label=series['name'],
                 zorder=series['zorder'])


    # -------------------
    # Axis and tick settings
    # -------------------

    # Dynamically adjust Y-axis (compute limits first)
    all_y_min = min(s['y'].min() if s['y'].size > 0 else 0 for s in data_series)
    all_y_max = max(s['y'].max() if s['y'].size > 0 else 0 for s in data_series)
    y_range = all_y_max - all_y_min
    if y_range == 0: y_range = 0.4
    y_buffer = y_range * 0.1
    Y_MIN_LIMIT = min(-0.2, all_y_min - y_buffer)
    Y_MAX_LIMIT = max(0.4, all_y_max + y_buffer)

    ax.set_ylabel('Potential (V)', color='black', fontsize=20, fontweight='bold', labelpad=15)
    ax.set_ylim(Y_MIN_LIMIT, Y_MAX_LIMIT)
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=5))
    ax.tick_params(axis='y', labelsize=16, width=1.5, length=8)

    # X-axis
    all_x_max = [s['x'].max() if s['x'].size > 0 else 0 for s in data_series]
    x_limit = max(all_x_max)
    ax.set_xlabel('Time (h)', fontsize=20, fontweight='bold', labelpad=12)
    ax.set_xlim(0, x_limit * 1.05)
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=8, integer=True, prune='upper'))
    ax.tick_params(axis='x', labelsize=16, width=1.5, length=8)


    # -------------------
    # Inset zoom feature - optimized indicator box
    # -------------------
    if enable_inset:
        # 1. Create inset axes
        ax_inset = ax.inset_axes(inset_pos, transform=ax.transAxes)

        # 2. Draw all series in inset
        # Keep Z-order consistent for color/order matching
        for series in data_series:
             ax_inset.plot(series['x'], series['y'],
                           color=series['color'],
                           linewidth=LINEWIDTH * 0.8,
                           zorder=series['zorder'])

        # 3. Set inset X and Y limits
        ax_inset.set_xlim(xlim_inset)
        ax_inset.set_ylim(ylim_inset)

        # 4. Set inset style
        ax_inset.tick_params(axis='both', labelsize=10, width=1, length=5)
        ax_inset.set_facecolor('white') # ensure inset background is white

        # 5. Optimized indicator box: using mark_inset
        mark_inset(ax, ax_inset,
                   loc1=1, loc2=2, # connector positions (1-4 for four corners)
                   fc="none", # fill color: none
                   ec="black", # edge color
                   lw=1.5, # line width
                   ls='-') # line style


    # -------------------
    # Top annotation and legend
    # -------------------

    if use_rate_mode:
        top_text = RATE_PERFORMANCE_ANNOTATION
    else:
        top_text = DEFAULT_TOP_ANNOTATION

    ax.text(0.5, 0.95,
            top_text,
            transform=ax.transAxes,
            fontsize=18,
            fontweight='bold',
            ha='center',
            va='center')

    ax.legend(fontsize=14, loc='upper right', frameon=False)

    # Save and display
    fig.subplots_adjust(right=0.9, left=0.15, bottom=0.15, top=0.9)

    if save_path:
        plt.savefig(save_path,
                    dpi=DPI,
                    bbox_inches='tight',
                    pad_inches=0.1,
                    transparent=True)
        print(f"Voltage-time curve saved: {save_path}")

    plt.show()

# --- 3. Execute plotting ---

# Function call with INSET config parameters
plot_voltage_time_multi(
    data_series,
    save_path_vt,
    USE_RATE_MODE_ANNOTATION,
    ENABLE_INSET,
    INSET_XLIM,
    INSET_YLIM,
    INSET_POSITION
)

print("Voltage-time plot successfully generated.")
