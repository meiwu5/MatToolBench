"""
Compute per-difficulty benchmark results from a result directory.

Usage:
    python scripts/compute_difficulty_results.py --result_dir result_50steps/Experiment1/pyautogui/screenshot/<model>/0

Output: tables broken down by difficulty (easy / medium / hard) per domain,
        plus an aggregated difficulty-level table across all domains.
Also saves a JSON file: <result_dir>/difficulty_summary.json
"""

import argparse
import json
import os
from pathlib import Path

DIFFICULTIES = ["easy", "medium", "hard"]
GUI_DOMAINS    = ["jade", "avantage", "vesta", "dm", "ms"]
ORIGIN_DOMAINS = ["origin"]
CODE_DOMAINS   = ["mp", "oqmd", "pymatgen", "optimade"]
ALL_DOMAINS    = GUI_DOMAINS + ORIGIN_DOMAINS + CODE_DOMAINS


def load_task_difficulty(domain: str, task_id: str, examples_root: Path) -> str:
    p = examples_root / domain / f"{task_id}.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f).get("difficulty", "unknown")
        except Exception:
            pass
    return "unknown"


def load_eval_details_with_difficulty(domain_dir: Path, domain: str, examples_root: Path) -> list:
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
                r = json.load(f)
            task_id = task_dir.name
            r["_difficulty"] = load_task_difficulty(domain, task_id, examples_root)
            r["_domain"] = domain
            records.append(r)
        except Exception:
            pass
    return records


def compute_metrics(records: list) -> dict:
    if not records:
        return {"n": 0, "sr": 0.0, "avg_steps": 0.0, "step_eff": 0.0, "steps_x_eff": 0.0}
    n = len(records)
    sr        = sum(r.get("success_rate", 0) for r in records) / n * 100
    avg_steps = sum(r.get("steps_taken", 0) for r in records) / n
    avg_eff   = sum(r.get("step_efficiency", 0.0) or 0.0 for r in records) / n
    return {
        "n":           n,
        "sr":          round(sr, 2),
        "avg_steps":   round(avg_steps, 1),
        "step_eff":    round(avg_eff, 4),
        "steps_x_eff": round(avg_steps * avg_eff, 2),
    }


def fmt_row(label, m, width=22):
    if m["n"] == 0:
        return f"  {label:<{width}}  {'—':>5}  {'—':>7}  {'—':>10}  {'—':>10}  {'—':>10}"
    return (
        f"  {label:<{width}}"
        f"  {m['n']:>5}"
        f"  {m['sr']:>7.2f}"
        f"  {m['avg_steps']:>10.1f}"
        f"  {m['step_eff']:>10.4f}"
        f"  {m['steps_x_eff']:>10.2f}"
    )


def print_table(title, rows, width=22):
    hdr = (f"  {'Domain / Difficulty':<{width}}  {'N':>5}  {'SR(%)':>7}  "
           f"{'AvgSteps':>10}  {'StepEff':>10}  {'Steps×Eff':>10}")
    sep = "  " + "-" * (len(hdr) - 2)
    print(f"\n{'='*len(hdr)}")
    print(f"  {title}")
    print(f"{'='*len(hdr)}")
    print(hdr)
    print(sep)
    for label, m in rows:
        print(fmt_row(label, m, width))
    print(sep)


def main():
    parser = argparse.ArgumentParser(description="Compute per-difficulty results table.")
    parser.add_argument("--result_dir", required=True,
                        help="Trial result dir (e.g. result_50steps/Exp1/pyautogui/screenshot/<model>/0)")
    parser.add_argument("--examples_root", default=None)
    args = parser.parse_args()

    result_dir = Path(args.result_dir).resolve()
    if args.examples_root:
        examples_root = Path(args.examples_root).resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent
        examples_root = repo_root / "src/mattoolbench-container/client/evaluation_examples_windows/examples"

    # ── Load all records with difficulty ──────────────────────────────────────
    all_records = []
    domain_records = {}
    for d in result_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            dom = d.name.lower()
            recs = load_eval_details_with_difficulty(d, dom, examples_root)
            domain_records[dom] = recs
            all_records.extend(recs)

    # ── Per-domain × difficulty table ─────────────────────────────────────────
    for dom in ALL_DOMAINS:
        recs = domain_records.get(dom, [])
        if not recs:
            continue
        rows = []
        for diff in DIFFICULTIES:
            subset = [r for r in recs if r["_difficulty"] == diff]
            rows.append((f"  {diff.capitalize()}", compute_metrics(subset)))
        rows.append(("  Total", compute_metrics(recs)))
        print_table(f"{dom.upper()} — by difficulty", rows)

    # ── Aggregated across all domains by difficulty ───────────────────────────
    agg_rows = []
    for diff in DIFFICULTIES:
        subset = [r for r in all_records if r["_difficulty"] == diff]
        agg_rows.append((f"  {diff.capitalize()}", compute_metrics(subset)))
    agg_rows.append(("  Total", compute_metrics(all_records)))
    print_table("ALL DOMAINS — aggregated by difficulty", agg_rows)

    # ── Save JSON summary ─────────────────────────────────────────────────────
    summary = {
        "by_difficulty": {
            diff: compute_metrics([r for r in all_records if r["_difficulty"] == diff])
            for diff in DIFFICULTIES
        },
        "by_domain_and_difficulty": {
            dom: {
                diff: compute_metrics([r for r in domain_records.get(dom, []) if r["_difficulty"] == diff])
                for diff in DIFFICULTIES
            }
            for dom in ALL_DOMAINS if domain_records.get(dom)
        },
        "total": compute_metrics(all_records),
    }
    out_path = result_dir / "difficulty_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
