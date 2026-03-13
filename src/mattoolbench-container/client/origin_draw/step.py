import originpro as op
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple, Sequence, Optional
import pandas as pd
import math # kept for log calculations if needed

# ====================== Free Energy Diagram Configuration (User Settings) ======================

# --- 1. Data Configuration ---
# Reaction step labels (X-axis ticks)
REACTION_STEPS = ['*+H₂O', '*OH', '*O', '*OOH', '*+O₂']
# Free energy data (Gibbs Free Energy, G in eV)
# Order must match REACTION_STEPS
GIBBS_ENERGY = {
    # Path Td1 (blue line) - using exact data provided
    'Co₃O₄ᵀᵈ¹': [0.00, -0.29252, 1.07561, 2.67048, 4.92],
    # Path Td_r (red line) - using exact data provided
    'RuO₂@Co₃O₄ᵀᵈ¹_Ruᴼʰ¹': [0.00, 1.35469, 2.17548, 4.03248, 4.92]
}

# --- 2. Chart Style Configuration ---
COLORS = {
    'Co₃O₄ᵀᵈ¹': '#00A1F0',      # bright blue
    'RuO₂@Co₃O₄ᵀᵈ¹_Ruᴼʰ¹': '#EF5C73' # bright red (similar to example figure)
}
# Theoretical OER potential
U_OER = 1.23 # V
# Chart save path
SAVE_PATH = r'..\output_result\free_energy_diagram.png'
DPI = 330

# --- 3. Plot Parameter Tuning ---
# Vertical offset for energy value labels (fine-tune text position)
TEXT_OFFSET_Y = 0.25
# Vertical position for PDS/eta annotation (Y-axis fraction) - ignored, using exact position
ETA_TEXT_Y_POS_REL = 0.75

# ====================== Data Processing and Calculation (PDS & Overpotential) ======================

def calculate_pds_and_eta(G_list: List[float], label: str, u_oer: float, reaction_steps: Sequence[str]) -> Tuple[float, str, float]:
    """
    Calculate the maximum free energy change (Potential Determining Step, PDS) and overpotential (eta).
    eta = max(Delta G) - U_OER
    """
    delta_g = []
    # Calculate Delta G_i = G_i - G_{i-1} starting from the second step
    for i in range(1, len(G_list)):
        delta_g.append(G_list[i] - G_list[i-1])

    # Find the maximum energy change
    max_delta_g_index = np.argmax(delta_g)
    max_delta_g = delta_g[max_delta_g_index]

    # Determine PDS step
    # PDS occurs at REACTION_STEPS[max_delta_g_index] -> REACTION_STEPS[max_delta_g_index + 1]
    pds_step = f"{reaction_steps[max_delta_g_index]} → {reaction_steps[max_delta_g_index + 1]}"

    # Calculate overpotential
    eta = max_delta_g - u_oer

    return max_delta_g, pds_step, eta

def read_free_energy_data_or_use_hardcoded(
    g_data: Dict[str, List[float]],
    steps: Sequence[str]
) -> Dict[str, List[float]]:
    """
    Try to read data from OriginPro. If failed or not in Origin environment,
    use hardcoded data as fallback.
    """
    # Always return hardcoded data to ensure the code works outside of Origin
    return g_data


# ----------------------------------------------------------------------
## Plot free energy diagram function
# ----------------------------------------------------------------------

def plot_free_energy(
    g_data: Dict[str, List[float]],
    steps: Sequence[str],
    colors: Dict[str, str],
    u_oer: float,
    text_offset_y: float,
    eta_y_rel: float, # kept for interface compatibility, not used
    save_path: Optional[str] = None
):

    # --- Style settings (matching example figure style) ---
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['mathtext.fontset'] = 'stix'
    plt.rcParams['font.weight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.linewidth'] = 1.5

    fig, ax = plt.subplots(figsize=(10, 8))

    n_steps = len(steps)
    # X-axis coordinates: [0, 1, 2, 3, 4]
    x_positions = np.arange(n_steps)

    # Number of reaction paths
    n_paths = len(g_data)

    # Store all calculation results for annotation
    path_results = {}

    # ------------------ 1. Iterate and draw each reaction path ------------------
    for idx, (path_name, G_list) in enumerate(g_data.items()):
        color = colors.get(path_name, 'black')

        # --- Determine line style to match target figure ---
        if 'Co₃O₄ᵀᵈ¹' in path_name:
            # Blue line: staircase and connector lines use dashed style
            linestyle_step = '--'
            linestyle_connect = '--'
            # Slightly shift text up for blue path G labels
            path_text_offset_y = text_offset_y + 0.05
        else:
            # Red line: staircase and connector lines use dashed style
            linestyle_step = '--'
            linestyle_connect = '--'
            # Normal text offset for red path G labels
            path_text_offset_y = text_offset_y - 0.05

        # Calculate PDS and eta
        max_delta_g, pds_step, eta = calculate_pds_and_eta(G_list, path_name, u_oer, steps)
        path_results[path_name] = {'max_dg': max_delta_g, 'pds': pds_step, 'eta': eta}

        # X-axis coords for staircase lines (Steps) and connector lines (Dashed)
        # Staircase x: [0, 0, 1, 1, 2, 2, 3, 3]
        x_step = np.repeat(x_positions, 2)[1:-1]
        # Staircase y: [G0, G1, G1, G2, G2, G3, G3, G4]
        y_step = np.repeat(G_list, 2)[:-2]

        # Connector x: [0, 1, 1, 2, 2, 3, 3, 4]
        x_connect = np.repeat(x_positions, 2)[2:]
        # Connector y: [G0, G0, G1, G1, G2, G2, G3, G3]
        y_connect = np.repeat(G_list, 2)[1:-1]

        # ------------------ 1.1 Draw staircase and connector lines ------------------
        # Draw staircase lines
        ax.plot(x_step, y_step,
                color=color,
                linewidth=3.5,
                label=path_name,
                linestyle=linestyle_step) # use dynamic style

        # Draw connector lines (vertical)
        ax.plot(x_connect, y_connect,
                color=color,
                linewidth=1.5,
                linestyle=linestyle_connect) # use dynamic style

        # ------------------ 1.2 Annotate free energy values (G in eV) ------------------
        for i, G in enumerate(G_list):
            # Do not annotate the last *+O2 (4.92)
            if i == n_steps - 1:
                continue

            # Adjust X position to center labels; shift left for *+H2O to avoid overlap with 0.00
            x_label_pos = x_positions[i]
            ha_align = 'center'

            if i == 0:
                # Initial state 0.00 label shifted slightly left
                x_label_pos = x_positions[i] - 0.15
                ha_align = 'left'

            # G value text
            ax.text(x_label_pos, G + path_text_offset_y,
                    f"{G:.2f}",
                    color=color,
                    fontsize=16,
                    fontweight='bold',
                    ha=ha_align,
                    va='center')

    # ------------------ 2. Annotate PDS and eta (matching target figure layout) ------------------

    # Find Y-axis position for maximum G value (4.92)
    max_g_limit = np.max([G for G_list in g_data.values() for G in G_list])

    for path_name, G_list in g_data.items():
        res = path_results[path_name]

        # Find index of the PDS step (G_i -> G_{i+1})
        dg = np.array([G_list[i] - G_list[i-1] for i in range(1, len(G_list))])
        pds_idx = np.argmax(dg)

        # PDS occurs between X coordinates pds_idx and pds_idx+1
        x_end = x_positions[pds_idx + 1]

        # Y position is G_end of this step (highest point)
        y_step_end = G_list[pds_idx + 1]

        # Adjust PDS text X, Y positions by path type (manually tuned to match target figure)
        if 'Co₃O₄ᵀᵈ¹' in path_name:
            # Blue path (PDS: *OOH -> *+O2, index 3). eta=1.02V
            # Text position at lower right
            text_x = 3.8
            text_y = 2.1

            # Arrow target point (PDS text area)
            arrow_target = (text_x - 0.1, text_y + 0.3)
            # Arrow start (mid-upper part of PDS step vertical line, x=4, y≈4.0)
            arrow_start = (x_end - 0.05, 4.0)

        else:
            # Red path (PDS: *O -> *OOH, index 2). eta=0.63V
            # Text position at center-upper area
            text_x = 2.8
            text_y = 3.6

            # Arrow target point (PDS text area)
            arrow_target = (text_x + 0.2, text_y + 0.2)
            # Arrow start (top of PDS step vertical line, x=3, y=4.03)
            arrow_start = (x_end, y_step_end)

        # ------------------ 2.1 Draw PDS text and eta annotation ------------------

        # PDS text
        ax.text(text_x, text_y,
                "PDS",
                color=colors[path_name],
                fontsize=18,
                fontweight='bold',
                ha='center',
                va='bottom')

        # eta annotation
        ax.text(text_x, text_y - 0.4, # leave space below text
                f"$\eta$={res['eta']:.2f}V",
                color=colors[path_name],
                fontsize=18,
                fontweight='bold',
                ha='center',
                va='top')

        # ------------------ 2.2 Draw PDS arrow ------------------
        # Arrow from PDS step to text position (dashed)
        ax.annotate('',
                    xy=arrow_target,
                    xytext=arrow_start,
                    arrowprops=dict(
                        arrowstyle="->",
                        color=colors[path_name],
                        lw=2,
                        ls='--')
                    )


    # ------------------ 3. Axis settings ------------------

    # X-axis settings: reaction coordinate
    ax.set_xticks(x_positions)
    ax.set_xticklabels(steps, fontsize=20, fontweight='bold')
    ax.set_xlabel('Reaction coordinate', fontsize=22, fontweight='bold', labelpad=15)

    # Y-axis settings: free energy
    ax.set_ylabel('Free energy (eV)', fontsize=22, fontweight='bold', labelpad=15)

    # Y-axis range: -1 to 6 (matching example figure)
    ax.set_ylim(-1.0, 6.0)

    # U=0 zero potential line annotation
    ax.text(-0.4, 0.05, "U=0", fontsize=18, fontweight='bold', ha='left', va='bottom', color='black')
    ax.axhline(0, color='gray', linestyle='-', linewidth=1.5, zorder=0)

    # Ticks and spines
    ax.tick_params(axis='both', labelsize=18, width=1.5, length=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Legend
    ax.legend(loc='upper left', frameon=False, fontsize=18, ncol=1)

    # Adjust layout
    fig.subplots_adjust(left=0.15, right=0.9, bottom=0.15, top=0.9)

    if save_path:
        plt.savefig(save_path,
                    dpi=DPI,
                    bbox_inches='tight',
                    pad_inches=0.1,
                    transparent=True)
        print(f"Free energy diagram saved: {save_path}")

    plt.show()

# ----------------------------------------------------------------------
## Execute plotting
# ----------------------------------------------------------------------

# 1. Load/prepare data
# Note: this function returns hardcoded data even if OriginPro loading fails
final_g_data = read_free_energy_data_or_use_hardcoded(GIBBS_ENERGY, REACTION_STEPS)

# 2. Draw figure
plot_free_energy(
    final_g_data,
    REACTION_STEPS,
    COLORS,
    U_OER,
    TEXT_OFFSET_Y,
    ETA_TEXT_Y_POS_REL,
    SAVE_PATH
)

print("Free energy step diagram successfully generated!")
