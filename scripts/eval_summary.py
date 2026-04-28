#!/usr/bin/env python3
"""
Summarize evaluation results for a given result directory (e.g., resultgpt/0/avantage).

Usage:
    python eval_summary.py <result_dir> [--task-json-dir <task_json_dir>]

Example:
    python eval_summary.py resultgpt/0/avantage
    python eval_summary.py resultgpt/0/avantage --task-json-dir src/mattoolbench-container/client/evaluation_examples_windows/examples/avantage
"""

import json
import os
import sys
import argparse
from pathlib import Path


def load_eval_detail(task_dir: Path):
    p = task_dir / "eval_detail.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def load_task_json(task_id: str, task_json_dir: Path):
    """Try to find the task JSON file and return 'difficulty' field."""
    if task_json_dir is None:
        return "N/A"
    p = task_json_dir / f"{task_id}.json"
    if not p.exists():
        return "N/A"
    with open(p) as f:
        d = json.load(f)
    return d.get("difficulty", "N/A")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", help="Path to result directory (e.g. resultgpt/0/avantage)")
    parser.add_argument(
        "--task-json-dir",
        default=None,
        help="Path to task JSON directory. If omitted, auto-detected from result_dir structure.",
    )
    args = parser.parse_args()

    result_dir = Path(args.result_dir).resolve()
    if not result_dir.exists():
        print(f"Error: {result_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # Auto-detect task JSON dir relative to the script's project root
    task_json_dir = None
    if args.task_json_dir:
        task_json_dir = Path(args.task_json_dir).resolve()
    else:
        # Guess: derive tool name from last component of result_dir
        tool_name = result_dir.name
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        candidate = (
            project_root
            / "src/mattoolbench-container/client/evaluation_examples_windows/examples"
            / tool_name
        )
        if candidate.exists():
            task_json_dir = candidate

    # Collect task directories (skip 'evaluate')
    task_dirs = sorted(
        [d for d in result_dir.iterdir() if d.is_dir() and d.name != "evaluate"]
    )

    rows = []
    for task_dir in task_dirs:
        task_id = task_dir.name
        detail = load_eval_detail(task_dir)
        if detail is None:
            print(f"Warning: no eval_detail.json in {task_dir}", file=sys.stderr)
            continue

        difficulty = load_task_json(task_id, task_json_dir)
        subtask_scores = [s["score"] for s in detail.get("subtasks", [])]
        steps_taken = detail.get("steps_taken", 0)
        max_steps = detail.get("max_steps", 50)
        total_score = detail.get("total_score", 0.0)
        max_score = detail.get("max_score", 1)
        success_rate = detail.get("success_rate", 0)
        step_efficiency = detail.get("step_efficiency", 0.0)

        rows.append(
            {
                "task_id": task_id,
                "difficulty": difficulty,
                "subtask_scores": subtask_scores,
                "steps_taken": steps_taken,
                "max_steps": max_steps,
                "total_score": total_score,
                "max_score": max_score,
                "success_rate": success_rate,
                "step_efficiency": step_efficiency,
            }
        )

    if not rows:
        print("No results found.")
        return

    # ── Print table ──────────────────────────────────────────────────────────
    col_widths = {
        "difficulty": max(6, max(len(r["difficulty"]) for r in rows)),
        "task_id": max(7, max(len(r["task_id"]) for r in rows)),
        "score": max(5, max(len(str([int(s) if s in (0,1) else s for s in r["subtask_scores"]])) for r in rows)),
        "steps": 5,
    }

    header = (
        f"{'Level':<{col_widths['difficulty']}}  "
        f"{'Task_id':<{col_widths['task_id']}}  "
        f"{'Score':<{col_widths['score']}}  "
        f"{'Steps'}"
    )
    print(header)
    print("-" * len(header))

    for r in rows:
        score_str = str([int(s) if s in (0, 1) else round(s, 4) for s in r["subtask_scores"]])
        print(
            f"{r['difficulty']:<{col_widths['difficulty']}}  "
            f"{r['task_id']:<{col_widths['task_id']}}  "
            f"{score_str:<{col_widths['score']}}  "
            f"{r['steps_taken']}"
        )

    # ── Aggregate metrics ────────────────────────────────────────────────────
    n = len(rows)
    total_score_sum = sum(r["total_score"] for r in rows)
    total_max_score = sum(r["max_score"] for r in rows)
    n_success = sum(1 for r in rows if r["success_rate"] == 1)

    # Eff: mean step_efficiency across ALL tasks
    eff = sum(r["step_efficiency"] for r in rows) / n

    # Eff*: mean step_efficiency across SUCCESSFUL tasks only
    success_rows = [r for r in rows if r["success_rate"] == 1]
    eff_star = (
        sum(r["step_efficiency"] for r in success_rows) / len(success_rows)
        if success_rows
        else float("nan")
    )

    # FTR: among tasks that terminated early (steps_taken < max_steps),
    #       fraction that failed (success_rate == 0)
    early_terminated = [r for r in rows if r["steps_taken"] < r["max_steps"]]
    early_failed = [r for r in early_terminated if r["success_rate"] == 0]
    ftr = len(early_failed) / len(early_terminated) if early_terminated else float("nan")

    score_pct = total_score_sum / total_max_score * 100 if total_max_score else 0
    sr_pct = n_success / n * 100
    eff_pct = eff * 100
    eff_star_pct = eff_star * 100
    ftr_pct = ftr * 100

    print()
    print(f"Total tasks : {n}")
    print(f"Score       : {total_score_sum:.1f} / {total_max_score}  ({score_pct:.1f}%)")
    print(f"SR          : {n_success} / {n}  ({sr_pct:.1f}%)")
    print(f"Eff         : {eff_pct:.1f}%")
    print(f"Eff*        : {eff_star_pct:.1f}%")
    print(f"FTR         : {len(early_failed)} / {len(early_terminated)}  ({ftr_pct:.1f}%)")


if __name__ == "__main__":
    main()
