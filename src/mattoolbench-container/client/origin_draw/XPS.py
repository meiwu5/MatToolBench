import originpro as op
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend import Legend
from scipy.signal import find_peaks

# ====================== User Settings (XPS Configuration) ======================

# 1. Data Structure Control
# IMPORTANT: Set according to the actual column structure of your Origin file (book4)!
# ---
# If 'book4' contains a Y_BG column (index 3), set to True.
# If no Y_BG column, set to False.
HAS_BG_COLUMN = True

# --- NEW: Direct Data Loading based on user's input (book4) ---
# Warning: Ensure the 'book4' sheet exists in Origin and column order matches HAS_BG_COLUMN setting.
try:
    # Find and read 'book4'
    wks = op.find_sheet('w', 'book4')
    if wks is None:
        raise ValueError("Error: Could not find sheet 'book4'. Please confirm that a sheet named 'book4' exists in Origin.")
    df = wks.to_df()

    # Assumption: Col 0=X, Col 1=Y_Raw, Col 2=Y_Fit_Total
    X_DATA = df.iloc[:, 0].values.astype(float)
    Y_RAW = df.iloc[:, 1].values.astype(float)
    Y_FIT_TOTAL = df.iloc[:, 2].values.astype(float) # Total fit curve (including BG)

    COMPONENTS = []

    if HAS_BG_COLUMN:
        # Col 3 contains Y_BG (fitted background)
        Y_BG = df.iloc[:, 3].values.astype(float)
        COMP_START_COL = 4 # Components start from Col 4 (index 4)
    else:
        # Col 3 is the first component. Y_BG is set to min of RAW data as fill baseline.
        Y_BG = np.min(Y_RAW) * np.ones_like(X_DATA)
        COMP_START_COL = 3 # Components start from Col 3 (index 3)

    # Read all fitted components (fix: use df.shape[1] instead of df.shape.length)
    for col_idx in range(COMP_START_COL, df.shape[1]):
        COMPONENTS.append(df.iloc[:, col_idx].values.astype(float))

    # Define spectrum info (for legend and labels)
    SPECTRUM_LABEL = 'Zn 2p'
    # Fitted component labels; adjust for actual number of components
    COMPONENT_LABELS = ['Zn $2p_{1/2}$', 'Zn $2p_{3/2}$']

    # Dynamically compute X-axis range
    padding = 0.5 # add 0.5 eV padding
    DYNAMIC_XMIN = np.min(X_DATA) - padding
    DYNAMIC_XMAX = np.max(X_DATA) + padding

except Exception as e:
    # If data loading fails, set empty data to prevent crash and print error
    print(f"Error loading data from 'book4': {e}")
    X_DATA, Y_RAW, Y_FIT_TOTAL, Y_BG, COMPONENTS = np.array([]), np.array([]), np.array([]), np.array([]), []
    SPECTRUM_LABEL = 'No Data'
    COMPONENT_LABELS = []
    # Use default fallback range on failure
    DYNAMIC_XMIN = 1010.0
    DYNAMIC_XMAX = 1050.0

# ------------------------------------------------------------------------

# 2. Style Settings
# Colors for raw data and fitted curves
raw_color = 'gray'
sum_color = '#EF0000' # red
bg_color = '#000000'  # new: background curve color (black)
# Fill colors for fitted components (up to 10)
component_colors = [
    '#B4D8E7', '#C2B9DF', '#B2D8BB', '#FFB7B2', '#FFC8DD',
    '#C4E0F0', '#B0C4DE', '#A3D2CC', '#E8C3B9', '#B7D5D4'
]
save_path = r'..\output_result\XPS_Fitted_Spectra_Plot.png' # figure save path

# 3. Plot Feature Control
is_fit_total_curve = True # whether to draw total fit curve
is_raw_data = True        # whether to draw raw data points
is_bg_curve = True        # whether to draw background curve
# == Final choice: labels placed on peaks ==
is_component_labeled_on_peak = False # NEW: whether to label directly on peaks (recommended for scientific plots)
is_sample_legend = True             # whether to show main legend (Raw/Fit Total/BG only)

# 4. Axis Range Settings
# Minimum binding energy (dynamically determined)
xmin = DYNAMIC_XMIN
# Maximum binding energy (dynamically determined)
xmax = DYNAMIC_XMAX

# ==================== Main Plotting Function ====================

def plot_xps_spectra_fitted():
    """
    Plot a single XPS fitted spectrum using pre-loaded X_DATA, Y_RAW,
    Y_FIT_TOTAL, Y_BG, and COMPONENTS.
    """

    if len(X_DATA) == 0 or len(COMPONENTS) == 0:
        print("Required XPS data (X, Y_Raw, Components) is missing. Exiting.")
        return

    # 1. Determine plot baseline and range
    offset = 0.0 # No vertical offset for single-panel plot
    # base_height used to calculate y-axis margins
    base_height = np.max(Y_RAW) - np.min(Y_RAW)

    # Y-axis minimum set to lowest point of BG curve
    total_ymin = np.min(Y_BG)
    total_ymax = np.max(Y_RAW)

    # ==================== Matplotlib Plot Settings ====================
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['axes.unicode_minus'] = False

    # Adjust figsize for single-panel plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # 2. Core plot: draw single fitted spectrum
    all_legend_handles = []
    all_legend_labels = []

    # 2.0. Draw BG curve, controlled by is_bg_curve
    if is_bg_curve:
        bg_line, = ax.plot(X_DATA, Y_BG,
                           color=bg_color,
                           linewidth=1.2,
                           linestyle='--',
                           label='BG')
        all_legend_handles.append(bg_line)
        all_legend_labels.append('BG')

    # 2.1. Draw component fill regions (curve fitting)
    # Fill baseline is now Y_BG
    base_y = Y_BG

    # Assume COMPONENTS data already includes Y_BG (Gross Component)
    for j, comp_y_gross in enumerate(COMPONENTS):
        color = component_colors[j % len(component_colors)]

        # fill_between: from baseline (Y_BG) to Gross Component
        fill_handle = ax.fill_between(X_DATA, base_y, comp_y_gross,
                                      color=color,
                                      alpha=0.7,
                                      linewidth=0)

        comp_label = COMPONENT_LABELS[j] if j < len(COMPONENT_LABELS) else f'Comp {j+1}'

        # Based on setting, annotate label directly on peak
        if is_component_labeled_on_peak:
            # Find peak maximum
            max_index = np.argmax(comp_y_gross)
            peak_x = X_DATA[max_index]
            peak_y = comp_y_gross[max_index]

            # Annotate component label on peak
            # Adjust vertical offset multiplier from 0.015 to 0.030
            ax.text(peak_x, peak_y + base_height * 0.030, # slightly above peak
                    comp_label,
                    ha='center',
                    va='bottom',
                    fontsize=12,
                    color='black',
                    fontweight='bold')
        else:
            # Default: add to legend
            all_legend_handles.append(fill_handle)
            all_legend_labels.append(comp_label)

    # 2.2. Draw total fit curve, controlled by is_fit_total_curve
    if is_fit_total_curve:
        fit_total_line, = ax.plot(X_DATA, Y_FIT_TOTAL,
                            color=sum_color,
                            linewidth=1.5,
                            label='Fit Total')
        all_legend_handles.append(fit_total_line)
        all_legend_labels.append('Fit Total')

    # 2.3. Draw raw data, controlled by is_raw_data
    if is_raw_data:
        raw_scatter = ax.plot(X_DATA, Y_RAW,
                              'o',
                              markersize=2.5,
                              markeredgecolor=raw_color,
                              markerfacecolor='none',
                              markeredgewidth=0.8,
                              linewidth=0, # do not draw connecting lines
                              label='Raw')
        all_legend_handles.append(raw_scatter[0])
        all_legend_labels.append('Raw')

    # 2.4. Annotate spectrum label (as legend/main label)
    ax.text(xmax, total_ymax + base_height * 0.05,
            SPECTRUM_LABEL,
            ha='right', va='center',
            fontsize=16,
            fontweight='bold',
            color='k')

    # 3. Axis range and labels
    ax.set_xlim(xmin, xmax)

    # Key XPS step: invert X-axis (binding energy)
    ax.invert_xaxis()

    ax.set_xlabel(r'Binding Energy ($\text{eV}$)', fontsize=20, fontweight='bold', labelpad=12)
    ax.set_ylabel('Intensity (a.u.)', fontsize=20, fontweight='bold', labelpad=18)

    # 4. Tick marks and spine style
    ax.tick_params(axis='both', labelsize=18, length=8, width=1.5)

    # Hide Y-axis ticks and labels
    ax.set_yticks([])

    # Set Y-axis range to ensure spectrum is visible
    ax.set_ylim(total_ymin - base_height * 0.1, total_ymax + base_height * 0.21)

    # Set spine line width
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    # 5. Legend
    # When is_component_labeled_on_peak=True, legend only contains Raw, Fit Total, BG
    if is_sample_legend and all_legend_handles:
        ax.legend(all_legend_handles, all_legend_labels,
                  loc='upper right',
                  fontsize=14,
                  ncol=3,            # use three-column layout to save space
                  frameon=True,      # show legend box
                  handlelength=1.5,
                  labelspacing=0.5)


    # 6. Save figure
    plt.tight_layout(pad=1.2)
    plt.savefig(save_path, dpi=600, bbox_inches='tight', facecolor='white')

    print(f"XPS fitted spectrum plot complete. Saved to: {save_path}")
    plt.show()

# Script entry point
if __name__ == '__main__':
    # Ensure running in Origin environment
    try:
        plot_xps_spectra_fitted()
    except Exception as e:
        print(f"An error occurred during execution: {e}")
