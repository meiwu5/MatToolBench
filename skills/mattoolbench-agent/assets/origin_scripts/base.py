"""
base.py — Generic fallback script for unknown or uncategorised Origin plotting tasks.

Handles the most common layout: paired (x, y) columns in a single active worksheet,
auto-detects labels from the Long Name row, then draws a stacked or overlaid line plot.

If the worksheet has a different layout (e.g. fixed column indices, multiple named sheets),
adapt the Data Loading section accordingly.
"""

import originpro as op
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# ====================== User Settings ======================
# 1. Output path — MUST be the EXACT path from the task instruction
save_path = r'C:\Users\Docker\Desktop\setup\output_result\origin\output.png'

# 2. Sample labels — overrides auto-detected Long Name labels when non-empty
label_override = []          # e.g. ['Sample A', 'Sample B', 'Sample C']

# 3. Color palette
COLOR_PALETTES = {
    "default":   ['#1F77B4', '#D62728', '#2CA02C', '#FF7F0E', '#9467BD', '#8C564B'],
    "nature":    ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4'],
    "grayscale": ['#111111', '#444444', '#777777', '#AAAAAA', '#CCCCCC'],
}
ACTIVE_PALETTE = "default"
colors = COLOR_PALETTES[ACTIVE_PALETTE]

# 4. Layout — "stacked" offsets spectra vertically; "overlay" draws them on the same baseline
plot_mode = "stacked"        # "stacked" | "overlay"
gap_ratio = 0.30             # vertical gap between stacked spectra (fraction of first spectrum height)

# 5. Axis labels — update to match the physical quantities in the task
x_label = 'X'
y_label = 'Intensity (a.u.)'

# 6. Output quality
DPI = 300

# ====================== Data Loading ======================
# Read the active worksheet.
# If you need a specific named sheet, use: op.find_sheet('w', 'SheetName')
wks = op.find_sheet()
df_raw = wks.to_df()
print(f"Worksheet shape: {df_raw.shape[0]} rows × {df_raw.shape[1]} cols")

# ── Auto-detect labels from Long Name row ────────────────────────────────────
# Y columns assumed at odd indices (1, 3, 5, …) for paired (x, y) layout.
# If your columns are arranged differently, update y_col_indices below.
y_col_indices = list(range(1, df_raw.shape[1], 2))

auto_labels = []
for c in y_col_indices:
    label_found = ''
    for val in df_raw.iloc[:, c]:
        s = str(val).strip()
        if s and s.lower() not in ('nan', 'none', ''):
            try:
                float(s)
            except ValueError:
                label_found = s
                break
    auto_labels.append(label_found or f'Series {len(auto_labels) + 1}')

# ── Clean: convert to numeric, drop non-numeric rows ────────────────────────
df = df_raw.apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=[df.columns[0]]).reset_index(drop=True)

# ── Read paired (x, y) columns ───────────────────────────────────────────────
pairs = []
for c in y_col_indices:
    xc = c - 1
    if c >= df.shape[1]:
        break
    xi = df.iloc[:, xc].dropna().values.astype(float)
    yi = df.iloc[:, c].dropna().values.astype(float)
    n = min(len(xi), len(yi))
    if n == 0:
        continue
    pairs.append((xi[:n], yi[:n]))

# Fallback: if paired layout yields nothing, treat col 0 as shared x
if not pairs:
    x_shared = df.iloc[:, 0].dropna().values.astype(float)
    for c in range(1, df.shape[1]):
        yi = df.iloc[:, c].dropna().values.astype(float)
        n = min(len(x_shared), len(yi))
        if n > 0:
            pairs.append((x_shared[:n], yi[:n]))

if not pairs:
    raise RuntimeError("No numeric data found in the active worksheet.")

# Resolve final labels
label = label_override if len(label_override) == len(pairs) else auto_labels[:len(pairs)]
print(f"Loaded {len(pairs)} series.  Labels: {label}")

# ====================== Stacked offset calculation ======================
def compute_offsets(pairs, gap_ratio=0.30):
    """Compute per-series vertical offsets for a stacked display."""
    offsets = [0.0]
    cur_top = pairs[0][1].max()
    base_h  = pairs[0][1].max() - pairs[0][1].min()
    for i in range(1, len(pairs)):
        yi    = pairs[i][1]
        shift = cur_top - yi.min() + base_h * gap_ratio
        offsets.append(shift)
        cur_top = yi.max() + shift
    return offsets

if plot_mode == "stacked" and len(pairs) > 1:
    offsets = compute_offsets(pairs, gap_ratio)
else:
    offsets = [0.0] * len(pairs)

# ====================== Plot ======================
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.linewidth'] = 1.5

fig, ax = plt.subplots(figsize=(10, 8))

for i, ((xi, yi), offset) in enumerate(zip(pairs, offsets)):
    lbl = label[i] if i < len(label) else None
    ax.plot(xi, yi + offset,
            color=colors[i % len(colors)],
            linewidth=2.0,
            label=lbl)

ax.set_xlabel(x_label, fontsize=20, fontweight='bold', labelpad=12)
ax.set_ylabel(y_label, fontsize=20, fontweight='bold', labelpad=15)
ax.set_yticks([])
ax.tick_params(axis='x', labelsize=16, length=6, width=1.5)
for spine in ax.spines.values():
    spine.set_linewidth(1.5)

if label and any(str(l).strip() for l in label):
    ax.legend(fontsize=14, frameon=False,
              loc='upper center', bbox_to_anchor=(0.5, 1.0),
              ncol=min(len(label), 4), borderaxespad=0.3)

plt.tight_layout()
plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"Plot saved: {save_path}")
plt.show()
