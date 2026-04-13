"""
Generate ablation figure (figures/ablation.pdf) for MatToolBench paper.

Layout  : 1 row × 2 columns — GUI (left) and Code (right).
Style   : line chart.
          hint    = solid thick line + filled marker
          no_hint = dashed line + open marker
          Shaded band between hint and no_hint.
Width   : 6.75 in (NeurIPS textwidth).
Run     : python plot_ablation.py
Output  : ablation.pdf  +  ablation.png (300 dpi)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────────────
GUI_LABELS  = ["JADE", "DM", "MS"]
CODE_LABELS = ["MP", "OQMD", "OPTIMADE", "Pymatgen"]

ABL = {
    "gui": {
        "seed": {"hint":    [0.25, 0.20, 0.15],
                 "no_hint": [0.05, 0.00, 0.15]},
        "gpt":  {"hint":    [0.20, 0.20, 0.30],
                 "no_hint": [0.05, 0.10, 0.10]},
    },
    "code": {
        "seed": {"hint":    [0.25, 0.10, 0.70, 0.30],
                 "no_hint": [0.20, 0.00, 0.70, 0.20]},
        "gpt":  {"hint":    [0.15, 0.45, 0.85, 0.35],
                 "no_hint": [0.00, 0.45, 0.75, 0.35]},
    },
}

# Blue for Seed, Orange for GPT  — high contrast, colourblind-safe
CLR_SEED = "#1f6fbf"
CLR_GPT  = "#d4600a"

# ── Global style ───────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         8.5,
    "axes.linewidth":    0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "pdf.fonttype":      42,
})

FIG_W, FIG_H = 6.75, 2.7
fig, axes = plt.subplots(1, 2, figsize=(FIG_W, FIG_H))

# ── Draw one panel ─────────────────────────────────────────────────────────────
def draw_panel(ax, task_key, labels):
    x = np.arange(len(labels))
    d = ABL[task_key]

    for color, model_key in [(CLR_SEED, "seed"), (CLR_GPT, "gpt")]:
        hint    = np.array(d[model_key]["hint"])
        no_hint = np.array(d[model_key]["no_hint"])

        # hint: thick solid line + filled marker
        ax.plot(x, hint,
                color=color, linewidth=2.5,
                marker="o", markersize=7,
                markerfacecolor=color, markeredgecolor="white",
                markeredgewidth=1.5,
                zorder=4)

        # no_hint: dashed line + open marker (same colour, clearly different style)
        ax.plot(x, no_hint,
                color=color, linewidth=2.0,
                linestyle="--", dashes=(6, 3),
                marker="o", markersize=7,
                markerfacecolor="white", markeredgecolor=color,
                markeredgewidth=2.0,
                zorder=4)

        # shaded band between the two lines
        ax.fill_between(x, hint, no_hint,
                        color=color, alpha=0.10, zorder=2)

    # ── Axes cosmetics
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_xlim(-0.35, len(labels) - 0.65)
    ax.set_ylim(-0.02, 1.02)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda v, _: f"{int(round(v*100))}%"))
    ax.grid(axis="y", color="#dde6f0", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#b0bec8")
    ax.spines["left"].set_color("#b0bec8")
    ax.tick_params(colors="#536278")


draw_panel(axes[0], "gui",  GUI_LABELS)
draw_panel(axes[1], "code", CODE_LABELS)

axes[0].set_title("(a) GUI Tasks",  fontsize=9, fontweight="bold", pad=7)
axes[1].set_title("(b) Code Tasks", fontsize=9, fontweight="bold", pad=7)
axes[0].set_ylabel("Success Rate", fontsize=8.5, color="#536278")

# ── Shared legend ──────────────────────────────────────────────────────────────
legend_elements = [
    Line2D([0], [0], color=CLR_SEED, linewidth=2.5,
           marker="o", markersize=7,
           markerfacecolor=CLR_SEED, markeredgecolor="white", markeredgewidth=1.5,
           label="doubao-seed-1-8  (hint)"),
    Line2D([0], [0], color=CLR_SEED, linewidth=2.0,
           linestyle="--", dashes=(6, 3),
           marker="o", markersize=7,
           markerfacecolor="white", markeredgecolor=CLR_SEED, markeredgewidth=2.0,
           label="doubao-seed-1-8  (no hint)"),
    Line2D([0], [0], color=CLR_GPT, linewidth=2.5,
           marker="o", markersize=7,
           markerfacecolor=CLR_GPT, markeredgecolor="white", markeredgewidth=1.5,
           label="GPT-5.4  (hint)"),
    Line2D([0], [0], color=CLR_GPT, linewidth=2.0,
           linestyle="--", dashes=(6, 3),
           marker="o", markersize=7,
           markerfacecolor="white", markeredgecolor=CLR_GPT, markeredgewidth=2.0,
           label="GPT-5.4  (no hint)"),
]
fig.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=4,
    fontsize=8,
    frameon=True,
    framealpha=0.92,
    edgecolor="#d6e2f0",
    bbox_to_anchor=(0.5, -0.06),
    handlelength=2.4,
    columnspacing=1.2,
)

plt.tight_layout(rect=[0, 0.08, 1, 1])
fig.savefig("ablation.pdf", bbox_inches="tight", dpi=300)
fig.savefig("ablation.png", bbox_inches="tight", dpi=300)
print("Saved ablation.pdf and ablation.png")
plt.close(fig)
