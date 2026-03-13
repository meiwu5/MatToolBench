"""
Read scores_summary.csv from each experiment's result_dir and print
ablation tables ready to copy into a paper.

Usage:
    python print_ablation_results.py
"""
import json
import os
import glob

# ── Map config files to human-readable row labels ─────────────────────────
EXPERIMENTS = [
    # (label, result_dir, group)
    # Origin
    ("Full System (w/ Script)",   "./results/origin_script_gpt4o",    "origin"),
    ("w/o Script (ablation)",     "./results/origin_noscript_gpt4o",  "origin"),
    # ("w/ Qwen (ablation)",        "./results/origin_script_qwen",     "origin"),
    # GUI
    ("OSS / OCR (full system)",   "./results/gui_oss_gpt4o",          "gui"),
    ("A11y only",                 "./results/gui_a11y_gpt4o",         "gui"),
    ("Mixed-OSS",                 "./results/gui_mixed_gpt4o",        "gui"),
    ("OmniParser",                "./results/gui_omni_gpt4o",         "gui"),
    # Code
    ("3 retries (full system)",   "./results/code_retries3_gpt4o",    "code"),
    ("1 retry / no correction",   "./results/code_retries1_gpt4o",    "code"),
]

# Sub-categories per group (must match domain names in scores_summary.csv)
SUBCATS = {
    "origin": ["xrd", "xps", "raman", "cycle", "step", "ce"],
    "gui":    ["jade", "avantage", "vesta", "dm", "ms"],
    "code":   ["mp", "oqmd", "pymatgen", "optimade"],
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
            domain, task_id, score = parts[0], parts[1], parts[2]
            try:
                scores.setdefault(domain, []).append(float(score))
            except ValueError:
                pass
    return scores


def avg(lst):
    return sum(lst) / len(lst) * 100 if lst else float("nan")


def fmt(v):
    if v != v:  # nan
        return "  —  "
    return f"{v:5.1f}"


def print_table(group: str):
    subcats = SUBCATS[group]
    col_w = max(len(c) for c in subcats) + 2

    # header
    hdr_label = f"{'Experiment':<35s}"
    hdr_cols  = "".join(f"{c:^{col_w}}" for c in subcats) + f"{'Overall':^9}"
    sep = "-" * (35 + col_w * len(subcats) + 9)
    print(sep)
    print(f"{hdr_label}{hdr_cols}")
    print(sep)

    for label, result_dir, grp in EXPERIMENTS:
        if grp != group:
            continue
        scores_map = load_scores(result_dir)

        # per-category averages
        cat_avgs = []
        row = f"{label:<35s}"
        for cat in subcats:
            cat_scores = []
            for domain, slist in scores_map.items():
                if domain.lower() == cat.lower():
                    cat_scores.extend(slist)
            v = avg(cat_scores)
            cat_avgs.append(cat_scores)
            row += f"{fmt(v):^{col_w}}"

        # overall
        all_scores = [s for sl in cat_avgs for s in sl]
        row += f"{fmt(avg(all_scores)):^9}"
        print(row)

    print(sep)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Table 1 — Origin Tasks  (score = % tasks passed)")
    print("=" * 70)
    print_table("origin")

    print("=" * 70)
    print("Table 2 — GUI Tasks  (score = % tasks passed)")
    print("=" * 70)
    print_table("gui")

    print("=" * 70)
    print("Table 3 — Code Tasks  (score = % tasks passed)")
    print("=" * 70)
    print_table("code")
