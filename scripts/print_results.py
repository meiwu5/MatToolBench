"""
Print scores from experiment result directories.

Usage (from the repo root):
    # Print main benchmark table (LLM comparison)
    python scripts/print_results.py --prefix main_

    # Print ablation tables
    python scripts/print_results.py --prefix ablation_

    # Print all results
    python scripts/print_results.py

    # Specify a custom results directory
    python scripts/print_results.py --dir src/mattoolbench-container/client/results --prefix main_
"""
import argparse
import os
import glob

# Default results directory (relative to repo root)
DEFAULT_RESULTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "mattoolbench-container", "client", "results"
)

# ── Sub-categories per task group ─────────────────────────────────────────────
SUBCATS = {
    "origin": ["xrd", "xps", "raman", "cycle", "step", "ce"],
    "gui":    ["jade", "avantage", "vesta", "dm", "ms"],
    "code":   ["mp", "oqmd", "pymatgen", "optimade"],
}

# ── Human-readable labels for known result directory names ────────────────────
KNOWN_LABELS = {
    # Main experiment
    "main_gpt_5":               "GPT-5",
    "main_gpt_5_mini":          "GPT-5-mini",
    "main_claude_sonnet_4_6":   "Claude Sonnet 4.6",
    "main_qwen_max":            "Qwen-Max",
    "main_gemini_1.5_pro":      "Gemini 1.5 Pro",
    # Ablation: origin script
    "ablation_origin_script":   "Origin + Template Script",
    "ablation_origin_noscript": "Origin — No Script",
    # Ablation: GUI SoM
    "ablation_gui_oss":         "GUI SoM: OSS / OCR",
    "ablation_gui_a11y":        "GUI SoM: A11y tree",
    "ablation_gui_mixed":       "GUI SoM: Mixed-OSS",
    "ablation_gui_omni":        "GUI SoM: OmniParser",
}


def load_scores(result_dir: str):
    """Return {domain: [score, ...]} from scores_summary.csv."""
    csv_path = os.path.join(result_dir, "scores_summary.csv")
    if not os.path.exists(csv_path):
        return {}
    scores = {}
    with open(csv_path, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 3)
            if len(parts) < 3:
                continue
            domain, _task_id, score_str = parts[0], parts[1], parts[2]
            try:
                scores.setdefault(domain.lower(), []).append(float(score_str))
            except ValueError:
                pass
    return scores


def avg(lst):
    return sum(lst) / len(lst) * 100 if lst else float("nan")


def fmt(v):
    if v != v:  # nan check
        return "  —  "
    return f"{v:5.1f}"


def print_table(title, rows, subcats):
    """Print a formatted results table."""
    col_w = max(len(c) for c in subcats) + 2
    label_w = max((len(r[0]) for r in rows), default=28) + 2
    label_w = max(label_w, 28)

    hdr_label = f"{'Model / Setting':<{label_w}}"
    hdr_cols  = "".join(f"{c:^{col_w}}" for c in subcats) + f"{'Overall':^9}"
    sep = "-" * (label_w + col_w * len(subcats) + 9)

    print(f"\n{'=' * len(sep)}")
    print(title)
    print(f"{'=' * len(sep)}")
    print(f"{hdr_label}{hdr_cols}")
    print(sep)

    for label, scores_map in rows:
        cat_avgs = []
        row = f"{label:<{label_w}}"
        for cat in subcats:
            cat_scores = scores_map.get(cat.lower(), [])
            cat_avgs.append(cat_scores)
            row += f"{fmt(avg(cat_scores)):^{col_w}}"
        all_scores = [s for sl in cat_avgs for s in sl]
        row += f"{fmt(avg(all_scores)):^9}"
        print(row)
    print(sep)


def main():
    parser = argparse.ArgumentParser(description="Print MatToolBench results tables.")
    parser.add_argument("--dir", default=DEFAULT_RESULTS_DIR, help="Root results directory")
    parser.add_argument("--prefix", default="", help="Filter by folder prefix (e.g. 'main_' or 'ablation_')")
    args = parser.parse_args()

    results_dir = os.path.normpath(args.dir)
    result_dirs = sorted(glob.glob(os.path.join(results_dir, f"{args.prefix}*")))
    if not result_dirs:
        print(f"No result directories found under '{results_dir}' with prefix '{args.prefix}'.")
        return

    entries = []
    for d in result_dirs:
        name = os.path.basename(d)
        label = KNOWN_LABELS.get(name, name)
        scores = load_scores(d)
        if scores:
            entries.append((label, scores))

    if not entries:
        print("No scores_summary.csv files found in the matched directories.")
        return

    all_domains = set(dom for _, s in entries for dom in s)
    groups_with_data = [g for g, cats in SUBCATS.items() if any(c in all_domains for c in cats)]

    prefix = args.prefix
    if prefix.startswith("main"):
        header = "Main Benchmark Results — LLM Comparison  (scores: % tasks passed)"
        group_prefix = "  "
    elif prefix.startswith("ablation"):
        header = "Ablation Study Results  (scores: % tasks passed)"
        group_prefix = "  Ablation — "
    else:
        header = "MatToolBench Results  (scores: % tasks passed)"
        group_prefix = "  "

    print(f"\n{header}\n")
    for group in groups_with_data:
        print_table(f"{group_prefix}{group.upper()} Tasks", entries, SUBCATS[group])


if __name__ == "__main__":
    main()
