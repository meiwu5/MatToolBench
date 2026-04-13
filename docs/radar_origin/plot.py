"""
Plot Origin Plotting Quality Scores — 1×4 radar chart grid.

Usage:
    python plot_radar_quality.py
    python plot_radar_quality.py --legend-fontsize 12   # change legend font size

Output:
    radar_quality.png   (same directory)
    radar_quality.pdf
"""

import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ── 中文字体支持 ──────────────────────────────────────────────────────────────
import matplotlib.font_manager as fm

# WSL 直接用 Windows 字体（无需安装任何东西）
_cjk_candidates = [
    '/mnt/c/Windows/Fonts/msyh.ttc',     # 微软雅黑
    '/mnt/c/Windows/Fonts/simhei.ttf',   # 黑体
    '/mnt/c/Windows/Fonts/simsun.ttc',   # 宋体
]
for _p in _cjk_candidates:
    try:
        fm.fontManager.addfont(_p)
        plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=_p).get_name()]
        break
    except Exception:
        continue

plt.rcParams['axes.unicode_minus'] = False  # 修复负号"-"显示为方块
# ── Data ──────────────────────────────────────────────────────────────────────
# AXES  = ['Ours', 'Baseline 1', 'Baseline 2', 'Baseline 3', 'Baseline 4']
AXES  = ['我们的', '基准 1', '基准 2', '基准 3', '基准 4']
SPECS = ['Raman', 'XRD', 'XPS', 'FTIR']

# SPEC_DATA[spec][evaluator_idx] = [score_Ours, score_B1, score_B2, score_B3, score_B4]
SPEC_DATA = {
    'Raman': [
        [4.17, 3.83, 4.33, 4.00, 4.50],   # Users
        [4.60, 3.60, 4.50, 4.40, 4.27],   # GPT-4.5
        [4.97, 3.30, 4.80, 4.80, 4.77],   # Gemini 3.1 pro
        [4.93, 3.97, 4.87, 4.40, 4.90],   # Seed-1-8
        [4.93, 4.33, 4.93, 4.57, 4.77],   # Qwen3-VL-235B
    ],
    'XRD': [
        [4.00, 3.83, 4.17, 4.17, 4.17],
        [4.67, 4.40, 4.20, 4.73, 4.53],
        [4.83, 4.77, 4.70, 4.87, 4.80],
        [4.90, 4.73, 4.57, 4.87, 4.60],
        [4.93, 4.37, 4.67, 4.90, 4.50],
    ],
    'XPS': [
        [4.33, 3.83, 4.50, 5.00, 4.83],
        [4.50, 4.10, 4.37, 4.00, 4.50],
        [4.73, 4.60, 4.57, 4.73, 4.80],
        [4.83, 4.70, 4.27, 4.73, 4.80],
        [5.00, 4.83, 4.70, 4.67, 4.93],
    ],
    'FTIR': [
        [4.00, 2.67, 3.89, 3.78, 4.11],
        [4.53, 3.40, 3.77, 4.13, 4.10],
        [4.93, 2.20, 3.40, 4.70, 4.53],
        [4.93, 3.27, 4.37, 4.57, 4.57],
        [4.97, 3.40, 4.57, 4.50, 4.73],
    ],
}

# evaluators: (label, hex_color, linestyle)
EVALS = [
    ('用户',          '#E07820', (0, (5, 3))),   # dashed
    ('GPT-4.5',        '#2A9D8F', '-'),
    ('Gemini 3.1 pro', '#E63946', '-'),
    ('Seed-1-8',       '#457B9D', '-'),
    ('Qwen3-VL-235B',  '#7B2D8B', '-'),
]

# subplot title colors matching the website rc-header dots
TITLE_COLORS = {
    'Raman': '#2060a8',
    'XRD':   '#2e8b48',
    'XPS':   '#d07810',
    'FTIR':  '#8e44ad',
}

VMIN, VMAX = 2.0, 5.0
BG_COLOR   = '#ffffff'          # pure white background


# ── Helpers ───────────────────────────────────────────────────────────────────
def radar_factory(n):
    """Return evenly-spaced angles for n axes (closed loop)."""
    angles = np.linspace(0, 2 * math.pi, n, endpoint=False).tolist()
    angles += angles[:1]          # close the polygon
    return angles


def draw_radar(ax, angles, values, color, linestyle, alpha_fill=0.12, lw=1.5):
    vals = list(values) + [values[0]]
    ax.plot(angles, vals, color=color, linestyle=linestyle,
            linewidth=lw, solid_capstyle='round')
    ax.fill(angles, vals, color=color, alpha=alpha_fill)


# ── Main ──────────────────────────────────────────────────────────────────────
def plot(legend_fontsize: int = 11, out_prefix: str = 'radar_quality'):
    n_axes   = len(AXES)
    angles   = radar_factory(n_axes)
    n_cols   = len(SPECS)

    fig, axes = plt.subplots(
        1, n_cols,
        figsize=(4.2 * n_cols, 4.0),
        subplot_kw=dict(polar=True),
        facecolor=BG_COLOR,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.14,
                        wspace=0.38)

    for col, spec in enumerate(SPECS):
        ax = axes[col]
        ax.set_facecolor(BG_COLOR)
        # put 'Ours' (first axis) at the top, go clockwise
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)

        # ── grid & ticks ──
        ax.set_ylim(VMIN, VMAX)
        ax.set_yticks([2, 3, 4, 5])
        ax.set_yticklabels(['2', '3', '4', '5'],
                           fontsize=6, color='#888', va='center')
        ax.yaxis.set_tick_params(pad=1)

        # ── spokes & labels ──
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(
            AXES,
            fontsize=10,
        )
        # highlight "Ours" (first spoke) in blue, bold
        for lbl, ang in zip(ax.get_xticklabels(), angles[:-1]):
        #     lbl.set_fontsize(10 if lbl.get_text() != 'Ours' else 11)
        #     lbl.set_fontweight('bold' if lbl.get_text() == 'Ours' else 'normal')
        #     lbl.set_color('#1a5cc8' if lbl.get_text() == 'Ours' else '#445566')
            lbl.set_fontsize(10 if lbl.get_text() != '我们的' else 11)
            lbl.set_fontweight('bold' if lbl.get_text() == '我们的' else 'normal')
            lbl.set_color('#1a5cc8' if lbl.get_text() == '我们的' else '#445566')


        ax.tick_params(pad=4)
        ax.grid(color='#aabbd0', linewidth=0.5, alpha=0.6)
        ax.spines['polar'].set_color('#aabbd0')
        ax.spines['polar'].set_linewidth(0.6)

        # ── data series ──
        for eval_idx, (label, color, ls) in enumerate(EVALS):
            vals = SPEC_DATA[spec][eval_idx]
            draw_radar(ax, angles, vals, color, ls)

        # ── title ──
        ax.set_title(spec, fontsize=12, fontweight='bold', pad=14,
                     color=TITLE_COLORS[spec])

    # ── shared legend ──
    legend_elements = [
        Line2D([0], [0], color=color, linestyle=ls, linewidth=1.8, label=label)
        for label, color, ls in EVALS
    ]
    fig.legend(
        handles=legend_elements,
        loc='lower center',
        ncol=len(EVALS),
        fontsize=legend_fontsize,          # ← adjust this parameter
        frameon=False,
        handlelength=2.2,
        columnspacing=1.4,
        bbox_to_anchor=(0.5, 0.0),
    )

    # ── save ──
    fig.savefig(f'{out_prefix}.png', dpi=180, bbox_inches='tight',
                facecolor=BG_COLOR)
    fig.savefig(f'{out_prefix}.pdf', bbox_inches='tight',
                facecolor=BG_COLOR)
    print(f'Saved {out_prefix}.png and {out_prefix}.pdf')
    plt.close(fig)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot Origin radar quality chart.')
    parser.add_argument('--legend-fontsize', type=int, default=11,
                        help='Font size for the legend labels (default: 11)')
    parser.add_argument('--out', default='radar_quality_chinese',
                        help='Output filename prefix (no extension)')
    args = parser.parse_args()

    plot(legend_fontsize=args.legend_fontsize, out_prefix=args.out)
