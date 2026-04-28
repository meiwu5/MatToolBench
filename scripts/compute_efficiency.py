"""
Compute efficiency metrics from eval_detail.json files produced by MatToolBench runs.

Efficiency is measured independently of accuracy:
  - step_efficiency  = 1 - (steps_taken - 1) / (max_steps - 1)   [all tasks]
  - code_efficiency  = (max_steps - first_success_step + 1) / max_steps  [code tasks only]

Usage:
    python compute_efficiency.py --result_dir ./results/Experiment1
    python compute_efficiency.py --result_dir ./results/Experiment1 --per_domain
    python compute_efficiency.py --result_dir r1 --result_dir r2  # compare models
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


def load_eval_details(result_dir: Path) -> list[dict]:
    """Recursively find all eval_detail.json under result_dir."""
    records = []
    for path in sorted(result_dir.rglob("eval_detail.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Infer domain from directory name (e.g. results/mp/task-uuid/)
        parts = path.parts
        try:
            domain_idx = parts.index(result_dir.name) + 1
            domain = parts[domain_idx] if domain_idx < len(parts) - 1 else "unknown"
        except ValueError:
            domain = "unknown"
        data["_domain"] = domain
        data["_path"] = str(path)
        records.append(data)
    return records


def compute_metrics(records: list[dict]) -> dict:
    """Aggregate efficiency metrics across records."""
    total = len(records)
    if total == 0:
        return {}

    step_effs = []
    code_effs = []
    success_step_effs = []  # step_efficiency only for tasks that succeeded

    domain_stats: dict[str, dict] = defaultdict(lambda: {
        "n": 0, "step_eff_sum": 0.0, "code_eff_sum": 0.0,
        "code_n": 0, "success_n": 0, "success_step_eff_sum": 0.0
    })

    for r in records:
        domain = r.get("_domain", "unknown")
        steps_taken = r.get("steps_taken")
        max_steps = r.get("max_steps")
        step_eff = r.get("step_efficiency")
        first_ok = r.get("first_success_step")
        success_rate = r.get("success_rate", 0)

        ds = domain_stats[domain]
        ds["n"] += 1

        if step_eff is not None:
            step_effs.append(step_eff)
            ds["step_eff_sum"] += step_eff

        if success_rate and step_eff is not None:
            success_step_effs.append(step_eff)
            ds["success_n"] += 1
            ds["success_step_eff_sum"] += step_eff

        if first_ok is not None and max_steps:
            ce = max(0.0, min(1.0, (max_steps - first_ok + 1) / max_steps))
            code_effs.append(ce)
            ds["code_eff_sum"] += ce
            ds["code_n"] += 1

    def safe_avg(lst):
        return round(sum(lst) / len(lst), 4) if lst else None

    per_domain = {}
    for domain, ds in sorted(domain_stats.items()):
        per_domain[domain] = {
            "n_tasks": ds["n"],
            "avg_step_efficiency": round(ds["step_eff_sum"] / ds["n"], 4) if ds["n"] else None,
            "avg_step_efficiency_success_only": (
                round(ds["success_step_eff_sum"] / ds["success_n"], 4)
                if ds["success_n"] else None
            ),
            "n_success": ds["success_n"],
            "avg_code_efficiency": (
                round(ds["code_eff_sum"] / ds["code_n"], 4) if ds["code_n"] else None
            ),
            "n_code_tasks": ds["code_n"],
        }

    return {
        "total_tasks": total,
        "avg_step_efficiency": safe_avg(step_effs),
        "avg_step_efficiency_success_only": safe_avg(success_step_effs),
        "n_successful_tasks": len(success_step_effs),
        "avg_code_efficiency": safe_avg(code_effs),
        "n_code_tasks": len(code_effs),
        "per_domain": per_domain,
    }


def print_report(label: str, metrics: dict):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if not metrics:
        print("  (no data)")
        return
    print(f"  Total tasks         : {metrics['total_tasks']}")
    print(f"  Avg step efficiency : {metrics['avg_step_efficiency']}  (all tasks)")
    print(f"  Avg step efficiency : {metrics['avg_step_efficiency_success_only']}"
          f"  (successful tasks only, n={metrics['n_successful_tasks']})")
    print(f"  Avg code efficiency : {metrics['avg_code_efficiency']}"
          f"  (code tasks, n={metrics['n_code_tasks']})")

    if metrics.get("per_domain"):
        print(f"\n  {'Domain':<14} {'N':>4} {'StepEff':>8} {'StepEff(ok)':>11} "
              f"{'CodeEff':>8} {'N_code':>6} {'N_ok':>5}")
        print(f"  {'-'*14} {'-'*4} {'-'*8} {'-'*11} {'-'*8} {'-'*6} {'-'*5}")
        for domain, ds in metrics["per_domain"].items():
            se = ds["avg_step_efficiency"] or "-"
            se_ok = ds["avg_step_efficiency_success_only"] or "-"
            ce = ds["avg_code_efficiency"] or "-"
            print(f"  {domain:<14} {ds['n_tasks']:>4} {str(se):>8} {str(se_ok):>11} "
                  f"{str(ce):>8} {ds['n_code_tasks']:>6} {ds['n_success']:>5}")


def main():
    parser = argparse.ArgumentParser(description="Compute efficiency metrics from MatToolBench results.")
    parser.add_argument("--result_dir", action="append", required=True,
                        help="Path to result directory (repeat for multi-model comparison)")
    parser.add_argument("--per_domain", action="store_true", default=True,
                        help="Show per-domain breakdown (default: True)")
    parser.add_argument("--output_json", default=None,
                        help="Save combined report to this JSON file")
    args = parser.parse_args()

    all_reports = {}
    for rdir in args.result_dir:
        p = Path(rdir)
        if not p.exists():
            print(f"WARNING: {rdir} does not exist, skipping.", file=sys.stderr)
            continue
        records = load_eval_details(p)
        metrics = compute_metrics(records)
        all_reports[p.name] = metrics
        print_report(p.name, metrics)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(all_reports, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved to {args.output_json}")


if __name__ == "__main__":
    main()
