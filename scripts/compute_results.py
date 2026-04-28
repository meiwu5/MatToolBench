"""
Compute and print the overall benchmark results table from a result directory.

Usage:
    python scripts/compute_results.py --result_dir result_50steps/Experiment1/pyautogui/screenshot/<model>/0

Output columns per domain/category:
    N          - number of tasks with eval_detail.json
    SR (%)     - success rate  (success_rate field, %)
    Avg Steps  - average steps_taken
    Step Eff   - average step_efficiency  (first_success_step / steps_taken, 0 if never succeeded)
    Steps×Eff  - Avg Steps × Step Eff  (a combined cost-quality metric)
    Eff*       - fraction of tasks where step_efficiency > 0  (i.e. succeeded at least once)
"""

import argparse
import json
import os
from pathlib import Path

# ── Category groupings ────────────────────────────────────────────────────────
GUI_DOMAINS    = ["jade", "avantage", "vesta", "dm", "ms"]
ORIGIN_DOMAINS = ["origin"]
CODE_DOMAINS   = ["mp", "oqmd", "pymatgen", "optimade"]

# Origin sub-categories (read from task JSON "origin_category" field)
ORIGIN_SUBCATS = ["xrd", "xps", "raman", "ftir", "cycle", "step", "ce", "bs"]


def load_eval_details(domain_dir: Path) -> list:
    """Return list of eval_detail dicts for all tasks in a domain directory."""
    records = []
    if not domain_dir.is_dir():
        return records
    for task_dir in domain_dir.iterdir():
        if not task_dir.is_dir():
            continue
        ed = task_dir / "eval_detail.json"
        if not ed.exists():
            continue
        try:
            with open(ed, encoding="utf-8") as f:
                records.append(json.load(f))
        except Exception:
            pass
    return records


def load_task_difficulty(domain: str, task_id: str, examples_root: Path) -> str:
    """Read difficulty field from the task example JSON."""
    p = examples_root / domain / f"{task_id}.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f).get("difficulty", "unknown")
        except Exception:
            pass
    return "unknown"


def load_task_origin_category(domain: str, task_id: str, examples_root: Path) -> str:
    """Read origin_category field from the task example JSON."""
    p = examples_root / domain / f"{task_id}.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f).get("origin_category", "unknown").lower()
        except Exception:
            pass
    return "unknown"


def compute_metrics(records: list) -> dict:
    """Compute aggregate metrics from a list of eval_detail dicts."""
    if not records:
        return {"n": 0, "sr": 0.0, "avg_steps": 0.0, "step_eff": 0.0,
                "steps_x_eff": 0.0, "eff_star": 0.0}
    n = len(records)
    sr      = sum(r.get("success_rate", 0) for r in records) / n * 100
    steps   = [r.get("steps_taken", 0) for r in records]
    avg_steps = sum(steps) / n
    eff     = [r.get("step_efficiency", 0.0) or 0.0 for r in records]
    avg_eff = sum(eff) / n
    eff_star = sum(1 for e in eff if e > 0) / n  # fraction that succeeded at least once
    steps_x_eff = avg_steps * avg_eff
    return {
        "n":           n,
        "sr":          round(sr, 2),
        "avg_steps":   round(avg_steps, 1),
        "step_eff":    round(avg_eff, 4),
        "steps_x_eff": round(steps_x_eff, 2),
        "eff_star":    round(eff_star, 4),
    }


def fmt_row(label, m, width=18):
    if m["n"] == 0:
        return f"  {label:<{width}}  {'—':>5}  {'—':>7}  {'—':>10}  {'—':>10}  {'—':>10}  {'—':>8}"
    return (
        f"  {label:<{width}}"
        f"  {m['n']:>5}"
        f"  {m['sr']:>7.2f}"
        f"  {m['avg_steps']:>10.1f}"
        f"  {m['step_eff']:>10.4f}"
        f"  {m['steps_x_eff']:>10.2f}"
        f"  {m['eff_star']:>8.4f}"
    )


def print_section(title, rows):
    hdr = (f"  {'Domain/Category':<18}  {'N':>5}  {'SR(%)':>7}  "
           f"{'AvgSteps':>10}  {'StepEff':>10}  {'Steps×Eff':>10}  {'Eff*':>8}")
    sep = "  " + "-" * (len(hdr) - 2)
    print(f"\n{'='*len(hdr)}")
    print(f"  {title}")
    print(f"{'='*len(hdr)}")
    print(hdr)
    print(sep)
    for label, m in rows:
        print(fmt_row(label, m))
    print(sep)


def main():
    parser = argparse.ArgumentParser(description="Compute MatToolBench results table.")
    parser.add_argument("--result_dir", required=True,
                        help="Path to the trial result dir (e.g. result_50steps/Exp1/pyautogui/screenshot/<model>/0)")
    parser.add_argument("--examples_root", default=None,
                        help="Path to evaluation_examples_windows/examples/ (auto-detected if omitted)")
    args = parser.parse_args()

    result_dir = Path(args.result_dir).resolve()
    if args.examples_root:
        examples_root = Path(args.examples_root).resolve()
    else:
        # Auto-detect: walk up from this script to find the client/evaluation_examples_windows/examples
        repo_root = Path(__file__).resolve().parent.parent
        examples_root = repo_root / "src/mattoolbench-container/client/evaluation_examples_windows/examples"

    # ── Load all domain records ────────────────────────────────────────────────
    domain_records = {}
    for d in result_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            domain_records[d.name.lower()] = load_eval_details(d)

    # ── GUI section ───────────────────────────────────────────────────────────
    gui_rows = []
    all_gui = []
    for dom in GUI_DOMAINS:
        recs = domain_records.get(dom, [])
        all_gui.extend(recs)
        gui_rows.append((dom.upper(), compute_metrics(recs)))
    gui_rows.append(("GUI (total)", compute_metrics(all_gui)))
    print_section("GUI Tasks", gui_rows)

    # ── Origin section ────────────────────────────────────────────────────────
    origin_recs = domain_records.get("origin", [])
    # Attach sub-category
    subcat_map = {}
    for r in origin_recs:
        tid = r.get("task_id", "")
        cat = load_task_origin_category("origin", tid, examples_root)
        subcat_map.setdefault(cat, []).append(r)

    origin_rows = []
    for sc in ORIGIN_SUBCATS:
        if sc in subcat_map:
            origin_rows.append((sc.upper(), compute_metrics(subcat_map[sc])))
    origin_rows.append(("Origin (total)", compute_metrics(origin_recs)))
    print_section("Origin Tasks", origin_rows)

    # ── Code section ─────────────────────────────────────────────────────────
    code_rows = []
    all_code = []
    for dom in CODE_DOMAINS:
        recs = domain_records.get(dom, [])
        all_code.extend(recs)
        code_rows.append((dom.upper(), compute_metrics(recs)))
    code_rows.append(("Code (total)", compute_metrics(all_code)))
    print_section("Code Tasks", code_rows)

    # ── Overall ───────────────────────────────────────────────────────────────
    all_recs = all_gui + origin_recs + all_code
    print(f"\n  OVERALL ({len(all_recs)} tasks): "
          f"SR={compute_metrics(all_recs)['sr']:.2f}%  "
          f"AvgSteps={compute_metrics(all_recs)['avg_steps']:.1f}  "
          f"StepEff={compute_metrics(all_recs)['step_eff']:.4f}")


if __name__ == "__main__":
    main()
