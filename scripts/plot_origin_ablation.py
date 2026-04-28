"""
Plot Origin ablation figure for paper.
Two side-by-side bar charts: File Exists Rate (SR) and Normalized Score.
Usage: python scripts/plot_origin_ablation.py [--out figures/origin_ablation.pdf]
"""
import argparse
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.titlesize': 9,
    'axes.labelsize': 8.5,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.color': '#e0e4ec',
    'grid.linewidth': 0.6,
    'axes.axisbelow': True,
})

# ── Data ──────────────────────────────────────────────────────────────────────
CONDITIONS  = ['script', 'no\_script', 'no\_hint']   # LaTeX underscore escape
CONDITIONS_DISPLAY = ['script', 'no_script', 'no_hint']

DATA = {
    'SR (\%)':          [56.3, 50.0, 18.8],
    'Norm. Score (\%)': [53.1, 40.6, 16.2],
}

# Three shades of Claude purple
BASE_COLOR = '#7b3fa8'
BAR_COLORS = ['#7b3fa8', '#a96fd4', '#d4b3f0']
EDGE_COLORS = ['#5a2d80', '#8350a8', '#b48fd0']

# ── Plot ──────────────────────────────────────────────────────────────────────
def plot(out_path: str):
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.5), sharey=False)
    fig.subplots_adjust(wspace=0.38, left=0.10, right=0.97, top=0.88, bottom=0.18)

    x = np.arange(len(CONDITIONS_DISPLAY))
    bar_w = 0.52

    for ax, (metric_label, values) in zip(axes, DATA.items()):
        bars = ax.bar(
            x, values,
            width=bar_w,
            color=BAR_COLORS,
            edgecolor=EDGE_COLORS,
            linewidth=0.9,
            zorder=3,
        )
        # Value labels on top of bars
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.2,
                f'{val:.1f}',
                ha='center', va='bottom',
                fontsize=7.5, fontweight='600', color='#3a3a5c',
            )

        ax.set_xticks(x)
        ax.set_xticklabels(CONDITIONS_DISPLAY, fontsize=8)
        ax.set_ylabel(metric_label, labelpad=4)
        ax.set_ylim(0, 75)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%g'))
        ax.set_yticks([0, 20, 40, 60])

        # Subtle spine
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#c0c8d8')
            ax.spines[spine].set_linewidth(0.8)

    # ── Shared title / legend ────────────────────────────────────────────────
    patches = [
        mpatches.Patch(facecolor=c, edgecolor=e, label=lbl, linewidth=0.8)
        for c, e, lbl in zip(BAR_COLORS, EDGE_COLORS, CONDITIONS_DISPLAY)
    ]
    fig.legend(
        handles=patches,
        loc='upper center',
        ncol=3,
        fontsize=7.5,
        frameon=False,
        bbox_to_anchor=(0.53, 1.01),
        handlelength=1.1,
        handleheight=0.9,
        columnspacing=1.0,
    )

    fig.suptitle(
        'Claude Sonnet 4.6 — Origin Task Ablation',
        fontsize=9, fontweight='700', color='#2a1a42', y=1.07,
    )

    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    print(f'Saved → {out_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='figures/origin_ablation.pdf',
                        help='Output path (.pdf or .png)')
    args = parser.parse_args()

    import os
    os.makedirs(os.path.dirname(args.out) if os.path.dirname(args.out) else '.', exist_ok=True)
    plot(args.out)
