import originpro as op
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Sequence, Optional, List

# --- User Input and Configuration ---
# Colors: pink for Bare Zn (Capacity), blue for FAZ@Zn (Capacity and CE)
COLOR_ZN = '#D989A9'  # soft pink
COLOR_FAZ = '#86B5E8'  # soft blue
# very light gray, almost white
COLOR_MARKER_FACE = '#EEEEEE' # circle fill color set to very light gray

# Style
MARKER_STYLE = 'o'
LINEWIDTH = 0.5     # reduced line width
MARKERSIZE = 10      # enlarged marker size
MARKER_EDGE_WIDTH = 0.5 # edge line width
DPI = 300
is_vertical_line = True # global flag to control whether to draw separator line

# File save path
save_path = r'..\output_result\battery_cycle_performance_dynamic_vertical_line.png'

# --- 1. OriginPro Data Loading and Preparation ---
try:
    wks = op.find_sheet()
    df = wks.to_df()
    print('df shape:', df)

    # Key fix: use .iloc[1:] to skip the units row (row 0), then cast to float
    df_data = df.iloc[1:]

    # Clean common null markers and convert to numeric
    df_data = df_data.replace(['', '--', '---', 'None'], np.nan)    # skip units row + clean null markers

    # Pandas Series for NaN detection (contains NaN)
    n_series = pd.to_numeric(df_data.iloc[:, 0], errors='coerce')  # Cycle Series
    cap_zn_series = pd.to_numeric(df_data.iloc[:, 2], errors='coerce') # Bare Zn Capacity Series (contains NaN)

    # NumPy arrays for plotting (NaN filled with 0)
    n       = n_series.fillna(0).values
    cap_zn  = cap_zn_series.fillna(0).values # for plotting, NaN filled with 0
    cap_faz = pd.to_numeric(df_data.iloc[:, 4], errors='coerce').fillna(0).values
    ce_faz  = pd.to_numeric(df_data.iloc[:, 6], errors='coerce').fillna(0).values

except Exception as e:
    # If OriginPro data loading fails, use simulated data as fallback
    print(f"Error initializing data: {e}. Using simulated data as fallback.")
    n_cycles = np.arange(1, 1001)

    # Simulate Bare Zn dropping at cycle 300 with NaN values for detection testing
    cap_zn_list = np.linspace(170, 150, 300).tolist() + [np.nan] * 700

    # Convert simulated data to Series for NaN detection
    n_series = pd.Series(n_cycles)
    cap_zn_series = pd.Series(cap_zn_list)

    # Plotting data (NaN filled with 0)
    n = n_cycles
    cap_zn = np.array(cap_zn_series.fillna(0).tolist())
    cap_faz = np.concatenate([np.linspace(200, 170, 600), np.linspace(170, 165, 400)])
    ce_faz = np.full(1000, 101)


# --- 2. Draw dual-Y-axis cycle plot (based on NaN detection) ---

def plot_battery_cycle(n, cap_zn, cap_faz, ce_faz, color_zn, color_faz, save_path, is_vertical_line: bool):

    # New detection logic: find the first NaN occurrence
    def find_crash_by_nan(n_series: pd.Series, cap_series: pd.Series) -> Optional[float]:
        """
        Find the first NaN in the capacity Series and return the corresponding cycle number.
        """
        # Find the index of the first NaN value (i.e., cycle where failure occurs)
        first_nan_index = cap_series.isna().idxmax()

        # Exclude the case where the Series starts with NaN, and verify NaN was found
        if cap_series.iloc[first_nan_index] is not None and np.isnan(cap_series.iloc[first_nan_index]):
            # Return the cycle number corresponding to this NaN
            return n_series.loc[first_nan_index]

        return None

    # Call detection function
    # Note: passing Series that may contain NaN
    crash_cycle = find_crash_by_nan(n_series, cap_zn_series)
    print('crash_cycle', crash_cycle)

    # Font settings
    plt.rcParams['font.family'] = 'Arial'
    plt.rcParams['font.weight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.linewidth'] = 1.5

    fig, ax1 = plt.subplots(figsize=(10, 8))

    # -------------------
    # Y1 axis: Specific Capacity
    # -------------------
    ax1.set_xlabel('Cycle number (n)', fontsize=22, fontweight='bold', labelpad=12)
    ax1.set_ylabel(r'Specific capacity ($\bf{mAh\ g^{-1}}$)', color='black', fontsize=22, fontweight='bold', labelpad=15)

    # Bare Zn Capacity (hollow circles)
    ax1.plot(n, cap_zn,
             color=color_zn,
             marker=MARKER_STYLE,
             linestyle='-',
             linewidth=LINEWIDTH,
             markersize=MARKERSIZE,
             markerfacecolor=COLOR_MARKER_FACE,
             markeredgecolor=color_zn,
             markeredgewidth=MARKER_EDGE_WIDTH)

    # FAZ@Zn Capacity (hollow circles)
    ax1.plot(n, cap_faz,
             color=color_faz,
             marker=MARKER_STYLE,
             linestyle='-',
             linewidth=LINEWIDTH,
             markersize=MARKERSIZE,
             markerfacecolor=COLOR_MARKER_FACE,
             markeredgecolor=color_faz,
             markeredgewidth=MARKER_EDGE_WIDTH)

    # Y1 axis ticks and range
    ax1.tick_params(axis='y', labelsize=18, width=1.5, length=8)
    ax1.set_ylim(0, 500)
    ax1.set_yticks(np.arange(0, 501, 100))

    # -------------------
    # Y2 axis: Coulombic Efficiency
    # -------------------
    ax2 = ax1.twinx()
    ax2.set_ylabel(r'Colombic efficiency ($\bf{\%}$)', color='black', fontsize=22, fontweight='bold', labelpad=15)

    # FAZ@Zn CE (hollow circles)
    ax2.plot(n, ce_faz,
             color=color_faz,
             marker=MARKER_STYLE,
             linestyle='-',
             linewidth=LINEWIDTH,
             markersize=MARKERSIZE,
             markerfacecolor=COLOR_MARKER_FACE,
             markeredgecolor=color_faz,
             markeredgewidth=MARKER_EDGE_WIDTH)

    # Y2 axis ticks and range
    ax2.tick_params(axis='y', labelsize=18, width=1.5, length=8)
    ax2.set_ylim(0, 120)
    ax2.set_yticks(np.arange(0, 121, 20))

    # -------------------
    # X-axis settings and annotations
    # -------------------

    ax1.tick_params(axis='x', labelsize=18, width=1.5, length=8)
    ax1.set_xlim(0, 1000)
    ax1.set_xticks(np.arange(0, 1001, 300))

    # >>> Optional vertical separator line (based on NaN detection) <<<
    if is_vertical_line and crash_cycle is not None:
        # Vertical separator line at detected cycle number
        ax1.axvline(x=crash_cycle, color='gray', linestyle='-', linewidth=1.5)
        print(f"Detected cliff-edge drop (NaN value) at cycle: {crash_cycle}")
    elif is_vertical_line:
        # If no NaN detected but line requested, print warning
        print("Warning: is_vertical_line is True, but no NaN detected in Bare Zn capacity. No separator line drawn.")


    # Key parameter annotation (top-left)
    ax1.text(0.02, 0.98,
             'Current density: $\\bf{5\ A\ g^{-1}}$\nMass loading: $\\bf{5.02\ mg\ cm^{-2}}$',
             transform=ax1.transAxes,
             fontsize=18,
             fontweight='bold',
             ha='left',
             va='top')

    # Label annotation (top-right)
    ax1.text(0.98, 0.94, 'Bare Zn',
             transform=ax1.transAxes,
             fontsize=18,
             color=color_zn,
             ha='right', va='center', fontweight='bold')

    ax1.text(0.98, 0.89, 'FAZ@Zn',
             transform=ax1.transAxes,
             fontsize=18,
             color=color_faz,
             ha='right', va='center', fontweight='bold')

    # Indicator arrows
    # Specific capacity arrow (Y1): pointing down
    ax1.annotate('', xy=(0.02, 0.4), xytext=(0.02, 0.1),
                 arrowprops=dict(arrowstyle="<-", connectionstyle="arc3,rad=0",
                                 linewidth=1.5, color='black'),
                 xycoords='axes fraction', textcoords='axes fraction')

    # Coulombic efficiency arrow (Y2): pointing up
    ax2.annotate('', xy=(0.99, 0.8), xytext=(0.99, 0.98),
                 arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0",
                                 linewidth=1.5, color='black'),
                 xycoords='axes fraction', textcoords='axes fraction')

    # Save and display
    fig.subplots_adjust(right=0.88, left=0.12, bottom=0.15)

    if save_path:
        plt.savefig(save_path,
                    dpi=DPI,
                    bbox_inches='tight',
                    pad_inches=0.1,
                    transparent=True)
        print(f"Battery cycle plot saved: {save_path}")
    plt.show()

# --- 3. Execute plotting ---
plot_battery_cycle(n, cap_zn, cap_faz, ce_faz, COLOR_ZN, COLOR_FAZ, save_path, is_vertical_line=is_vertical_line)

print("Battery cycle plot successfully generated.")
