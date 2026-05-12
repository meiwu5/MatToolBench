import originpro as op
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional

# ==================== Configuration Parameters ====================

# K-point labels (high-symmetry points)
K_LABELS = ['M', 'G', 'L', 'M', 'G', 'K']  # G represents Gamma

# K-point positions (fill in if exact positions are known, otherwise set to None for auto-distribution)
K_POSITIONS = None  # e.g.: [0.0, 0.15, 0.3, 0.45, 0.6, 0.87]

# Band labels and colors
BAND_LABELS = ['CS', 'Cpy', 'Cpz', 'Cpx']
BAND_COLORS = {
    'CS': '#E53935',   # red
    'Cpy': '#FFB300',  # orange-yellow
    'Cpz': '#43A047',  # green
    'Cpx': '#1E88E5'   # blue
}

# Plotting parameters
FERMI_ENERGY = 0.0       # Fermi level
ENERGY_MIN = -20         # Y-axis minimum
ENERGY_MAX = 8           # Y-axis maximum
MAX_WEIGHT = 2.0         # Maximum weight (approximately 1.93 based on data)
MIN_MARKER_SIZE = 1      # Minimum marker size
MAX_MARKER_SIZE = 100    # Maximum marker size (adjustable: 80-150)

# Save path
SAVE_PATH = r'..\output_result\band_structure.png'
DPI = 330

# ==================== Data Loading ====================

def read_data_from_origin():
    """Read band structure data from OriginPro"""
    try:
        wks = op.find_sheet()
        if wks is None:
            raise ValueError("No active worksheet found")

        df = wks.to_df()
        print(f"Reading worksheet: {df.shape[0]} rows x {df.shape[1]} columns")

        # Read K-points (column A, index 0)
        k_points = pd.to_numeric(df.iloc[:, 0], errors='coerce').values
        valid_mask = ~np.isnan(k_points)
        k_points = k_points[valid_mask]

        print(f"K-point range: {k_points.min():.4f} to {k_points.max():.4f}")

        # Column indices: CS(2,3), Cpy(5,6), Cpz(8,9), Cpx(11,12)
        column_map = {
            'CS': (2, 3),
            'Cpy': (5, 6),
            'Cpz': (8, 9),
            'Cpx': (11, 12)
        }
        
        band_data = {}
        for label, (e_col, w_col) in column_map.items():
            if e_col >= df.shape[1] or w_col >= df.shape[1]:
                print(f"Warning: {label} column index out of range, skipping")
                continue

            energy = pd.to_numeric(df.iloc[:, e_col], errors='coerce').values[valid_mask]
            weight = pd.to_numeric(df.iloc[:, w_col], errors='coerce').values[valid_mask]

            # Check for valid data
            valid_data = ~(np.isnan(energy) | np.isnan(weight))
            if valid_data.sum() > 0:
                band_data[label] = (energy, weight)
                print(f"{label}: Energy[{np.nanmin(energy):.2f}, {np.nanmax(energy):.2f}] eV, "
                      f"Weight[{np.nanmin(weight):.4f}, {np.nanmax(weight):.4f}]")
            else:
                print(f"Warning: {label} has no valid data")

        return k_points, band_data

    except Exception as e:
        print(f"Read failed: {e}")
        print("Using simulated data...")

        # Simulated data
        k_points = np.linspace(0, 0.87, 300)
        band_data = {
            'CS': (-19 + 1.0 * np.sin(k_points * 10), 0.5 + 0.5 * np.random.rand(300)),
            'Cpy': (-15 + 2.0 * np.cos(k_points * 8), 0.4 + 0.4 * np.random.rand(300)),
            'Cpz': (-5 + 1.5 * np.sin(k_points * 6), 0.6 + 0.4 * np.random.rand(300)),
            'Cpx': (0 + 2.5 * np.cos(k_points * 5), 0.3 + 0.3 * np.random.rand(300))
        }
        return k_points, band_data

# ==================== Plotting Functions ====================

def plot_band_structure(k_points, band_data, save_path=None):
    """Plot the projected band structure"""

    # Set matplotlib style
    plt.rcParams.update({
        'font.family': 'Times New Roman',
        'font.weight': 'bold',
        'axes.labelweight': 'bold',
        'axes.linewidth': 1.8,
        'xtick.major.width': 1.8,
        'ytick.major.width': 1.8
    })
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot each band
    size_range = MAX_MARKER_SIZE - MIN_MARKER_SIZE

    for label in BAND_LABELS:
        if label not in band_data:
            continue

        energy, weight = band_data[label]
        color = BAND_COLORS[label]

        # Background line
        ax.plot(k_points, energy,
                color='lightgray',
                linewidth=0.3,
                alpha=0.4,
                zorder=1)

        # Calculate marker sizes
        weight_norm = np.clip(weight / MAX_WEIGHT, 0, 1)
        marker_sizes = MIN_MARKER_SIZE + weight_norm * size_range

        # Draw scatter plot
        ax.scatter(k_points, energy,
                   c=color,
                   s=marker_sizes,
                   alpha=0.75,
                   edgecolors='none',
                   label=label,
                   zorder=2)
    
    # Fermi level
    ax.axhline(FERMI_ENERGY, color='gray', linestyle='--',
               linewidth=1.2, alpha=0.7, zorder=0)

    # K-point labels and divider lines
    if K_POSITIONS is not None:
        k_ticks = K_POSITIONS
    else:
        k_ticks = np.linspace(k_points.min(), k_points.max(), len(K_LABELS))
    
    for tick in k_ticks:
        ax.axvline(tick, color='black', linestyle='--', 
                   linewidth=1.0, alpha=0.6)
    
    ax.set_xticks(k_ticks)
    ax.set_xticklabels(K_LABELS, fontsize=22, fontweight='bold')
    
    # Axis settings
    ax.set_xlim(k_points.min(), k_points.max())
    ax.set_ylim(ENERGY_MIN, ENERGY_MAX)
    ax.set_ylabel('Energy (eV)', fontsize=24, fontweight='bold', labelpad=15)
    ax.set_yticks(np.arange(ENERGY_MIN, ENERGY_MAX + 1, 5))
    ax.tick_params(axis='both', labelsize=20, width=1.8, length=8)

    # Border
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Legend
    handles = [plt.Line2D([0], [0], marker='o', color='w',
                          markerfacecolor=BAND_COLORS[l],
                          markersize=14, linewidth=0)
               for l in BAND_LABELS if l in band_data]
    
    ax.legend(handles, 
              [l for l in BAND_LABELS if l in band_data],
              loc='lower center',
              bbox_to_anchor=(0.5, -0.13),
              ncol=len(handles),
              fontsize=18,
              frameon=False,
              columnspacing=2.0)
    
    plt.tight_layout()
    
    # Save
    if save_path:
        plt.savefig(save_path, dpi=DPI, bbox_inches='tight',
                   facecolor='white', pad_inches=0.15)
        print(f"Image saved: {save_path}")

    plt.show()

# ==================== Main Program ====================

if __name__ == '__main__':
    print("="*60)
    print("Reading data...")
    k_points, band_data = read_data_from_origin()

    print("\nStarting plot...")
    plot_band_structure(k_points, band_data, SAVE_PATH)

    print("="*60)
    print("Done!")