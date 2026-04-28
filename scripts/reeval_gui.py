"""
Re-evaluate GUI-based tasks (avantage, jade, dm, ms, vesta, oqmd, origin, etc.)
using updated task JSON files. Reads existing screenshots, runs OCR-based
getters, and writes updated eval_detail.json + result.txt.

Usage:
    python scripts/reeval_gui.py \
        --result_dir result_local/Experiment1/pyautogui/screenshot/<model>/0/<category> \
        [--task_id <uuid>]   # optional: single task

The script auto-detects the category from the result_dir name.
"""

import argparse
import datetime
import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLIENT_DIR = REPO_ROOT / "src/mattoolbench-container/client"
EXAMPLES_ROOT = CLIENT_DIR / "evaluation_examples_windows/examples"

sys.path.insert(0, str(CLIENT_DIR))

# Import getter modules directly (bypasses __init__.py which loads chrome/playwright)
import importlib.util as _ilu

def _load_getter_module(name):
    path = CLIENT_DIR / "desktop_env/evaluators/getters" / f"{name}.py"
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class _Getters:
    pass

getters = _Getters()
_loaded_mods = {}
for _mod_name in ("avantage", "jade", "dm", "ms", "vesta", "general", "file"):
    try:
        _mod = _load_getter_module(_mod_name)
        _loaded_mods[_mod_name] = _mod
        for _name in dir(_mod):
            if _name.startswith("get_"):
                setattr(getters, _name, getattr(_mod, _name))
    except Exception as _e:
        print(f"[WARN] Could not load getter module '{_mod_name}': {_e}")

_dm_mod    = _loaded_mods.get("dm")
_vesta_mod = _loaded_mods.get("vesta")


# ── Mock env ──────────────────────────────────────────────────────────────────
class MockEnv:
    def __init__(self, task_result_dir: str, result_base_dir: str):
        self.cache_dir = task_result_dir
        self.result_dir = result_base_dir
        self.action_history = []


# ── Score extraction ──────────────────────────────────────────────────────────
def compute_score(result_state):
    """
    GUI getters return a dict with a 'score' key (0 or 1).
    exact_match(dict, {"expected": True}) is always False, so we use
    result_state['score'] directly.
    """
    if isinstance(result_state, dict) and "score" in result_state:
        return float(result_state["score"])
    if isinstance(result_state, bool):
        return 1.0 if result_state else 0.0
    if isinstance(result_state, (int, float)):
        return float(result_state)
    return 0.0


# ── Getter registry ───────────────────────────────────────────────────────────
GETTER_MAP = {
    # avantage
    "check_multiple_files_imported":       getters.get_check_multiple_files_imported,
    "check_file_duplicated":               getters.get_check_file_duplicated,
    "check_duplicate_files_imported":      getters.get_check_duplicate_files_imported,
    "check_stacked_graph":                 getters.get_check_stacked_graph,
    "check_image_zoom":                    getters.get_check_image_zoom,
    "check_background_added_successfully": getters.get_check_background_added_successfully,
    "check_dialog_exists":                 getters.get_check_dialog_exists,
    "check_dialog_parameter":              getters.get_check_dialog_parameter,
    "check_border_color":                  getters.get_check_border_color,
    "check_grid_layout":                   getters.get_check_grid_layout,
    "check_energy_axis_reversed":          getters.get_check_energy_axis_reversed,
    # jade
    "check_file_opened_jade":              getters.get_check_file_opened_jade,
    "check_peak_finding":                  getters.get_check_peak_finding,
    "check_peak_add_two":                  getters.get_check_peak_add_two,
    "check_background_removal":            getters.get_check_background_removal,
    "check_smoothing":                     getters.get_check_smoothing,
    "check_smoothing_and_background":      getters.get_check_smoothing_and_background,
    "check_axis_switch":                   getters.get_check_axis_switch,
    "check_axes_menu":                     getters.get_check_axes_menu,
    "check_wpf_refinement":                getters.get_check_wpf_refinement,
    "check_refinement_result":             getters.get_check_refinement_result,
    "check_dialog_title_jade":             getters.get_check_dialog_title_jade,
    "check_search_match_elements":         getters.get_check_search_match_elements,
    # dm
    "check_file_import":                   getters.get_check_file_import,
    "check_ocr_text":                      getters.get_check_ocr_text,
    "check_drawing_tool":                  getters.get_check_drawing_tool,
    "check_text_color":                    getters.get_check_text_color,
    "check_checkbox_selected":             getters.get_check_checkbox_selected,
    "check_data_bar_by_text":              getters.get_check_data_bar_by_text,
    "check_dialog_opened_dm":              getters.get_check_dialog_opened_dm,
    "check_roi_copy_and_enlarge":          getters.get_check_roi_copy_and_enlarge,
    "check_filled_box_with_corners":       getters.get_check_filled_box_with_corners,
    "check_text_count_in_dialog":          getters.get_check_text_count_in_dialog,
    # ms
    "check_file_in_title":                 getters.get_check_file_in_title,
    "check_dialog_title_ms":               getters.get_check_dialog_title_ms,
    "check_text_keyword":                  getters.get_check_text_keyword,
    "check_field_value":                   getters.get_check_field_value,
    "check_multiple_fields":               getters.get_check_multiple_fields,
    "check_visual_similarity":             getters.get_check_visual_similarity,
    # vesta
    "check_file_opened_vesta":             getters.get_check_file_opened_vesta,
    "check_dialog_opened_vesta":           getters.get_check_dialog_opened_vesta,
    "check_standard_orientation":          getters.get_check_standard_orientation,
    "check_rotation_90_up":                getters.get_check_rotation_90_up,
    "check_translation":                   getters.get_check_translation,
    "check_style_change":                  getters.get_check_style_change,
    "check_atom_info_dialog":              getters.get_check_atom_info_dialog,
    "check_atom_deletion":                 getters.get_check_atom_deletion,
    "check_bond_display":                  getters.get_check_bond_display,
    "check_zoom":                          getters.get_check_zoom,
    "check_axes_toggle":                   getters.get_check_axes_toggle,
    "check_properties_field":              getters.get_check_properties_field,
    "check_polyhedral_style":              getters.get_check_polyhedral_style,
    "check_orientation_vector":            getters.get_check_orientation_vector,
    "check_lattice_plane":                 getters.get_check_lattice_plane,
    "check_boundary_settings":             getters.get_check_boundary_settings,
    "check_multiple_lattice_planes":       getters.get_check_multiple_lattice_planes,
    "check_bonds_cleared":                 getters.get_check_bonds_cleared,
    "check_atom_coordinates_in_edit_data": getters.get_check_atom_coordinates_in_edit_data,
    "check_properties_radius":             None,  # replaced by check_properties_field in task JSONs
    # file_exists: VM not accessible during reeval, skip (score=0)
    "file_exists":                         None,
    "validate_image_with_model":           None,
}


def reeval_task(task_json_path: Path, task_result_dir: Path, result_base_dir: Path) -> dict:
    with open(task_json_path) as f:
        task = json.load(f)

    task_id    = task.get("id", task_result_dir.name)
    instruction = task.get("instruction", "")
    evaluator  = task.get("evaluator", {})

    env = MockEnv(str(task_result_dir), str(result_base_dir))

    func_list   = evaluator.get("func", [])
    result_cfgs = evaluator.get("result", [])
    if isinstance(func_list, str):
        func_list   = [func_list]
        result_cfgs = [result_cfgs]

    subtasks = []
    scores   = []

    for idx, (func_name, cfg) in enumerate(zip(func_list, result_cfgs)):
        if not isinstance(cfg, dict):
            print(f"  [SKIP] subtask {idx+1}: cfg is not a dict ({cfg})")
            scores.append(0.0)
            subtasks.append({"index": idx+1, "name": "unknown", "score": 0.0, "error": "empty config"})
            continue

        rtype  = cfg.get("type", f"sub-task-{idx+1}")
        getter = GETTER_MAP.get(rtype)

        if getter is None:
            print(f"  [WARN] No getter for type '{rtype}', skipping")
            scores.append(0.0)
            subtasks.append({"index": idx+1, "name": rtype, "score": 0.0, "error": "no getter"})
            continue

        try:
            result_state = getter(env, cfg)
            score  = compute_score(result_state)
            detail = result_state if isinstance(result_state, dict) else {"raw": result_state}
        except Exception as e:
            print(f"  [ERROR] subtask {idx+1} ({rtype}): {e}")
            score  = 0.0
            detail = {"error": str(e)}

        scores.append(score)
        subtasks.append({"index": idx+1, "name": rtype, "score": score, "detail": detail})
        print(f"  subtask {idx+1} ({rtype}): {score}")

    total     = sum(scores)
    max_score = len(scores)
    precision = round(total / max_score, 4) if max_score else 0.0
    success   = 1 if total >= max_score else 0

    return {
        "task_id":      task_id,
        "instruction":  instruction,
        "total_score":  total,
        "max_score":    max_score,
        "precision":    precision,
        "success_rate": success,
        "subtasks":     subtasks,
        "timestamp":    datetime.datetime.now().isoformat(),
        "reeval":       True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result_dir", required=True,
        help="Path to category result dir (e.g. .../0/jade)")
    parser.add_argument("--task_id", default=None,
        help="Re-eval only this task UUID")
    args = parser.parse_args()

    result_dir     = Path(args.result_dir).resolve()
    result_base_dir = result_dir.parent          # e.g. .../0
    category        = result_dir.name            # e.g. jade
    examples_dir    = EXAMPLES_ROOT / category

    if not examples_dir.exists():
        print(f"[ERROR] No examples dir for category '{category}': {examples_dir}")
        sys.exit(1)

    task_dirs = ([result_dir / args.task_id] if args.task_id
                 else [d for d in sorted(result_dir.iterdir())
                       if d.is_dir() and not d.name.startswith('.')])

    changed = 0
    summary = []
    results_map = {}

    for task_dir in task_dirs:
        task_id   = task_dir.name
        task_json = examples_dir / f"{task_id}.json"

        if not task_json.exists():
            print(f"[SKIP] No task JSON: {task_id}")
            continue

        old_score = None
        rf = task_dir / "result.txt"
        if rf.exists():
            try:
                old_score = float(rf.read_text().strip())
            except (ValueError, OSError):
                pass

        print(f"\n[{task_id}]")
        eval_log  = reeval_task(task_json, task_dir, result_base_dir)
        new_score = eval_log["total_score"]

        (task_dir / "result.txt").write_text(f"{new_score}\n")
        with open(task_dir / "eval_detail.json", "w") as f:
            json.dump(eval_log, f, ensure_ascii=False, indent=2)

        changed_flag = (old_score != new_score)
        if changed_flag:
            changed += 1
        print(f"  score: {old_score} → {new_score}" if changed_flag else f"  score: unchanged ({new_score})")
        summary.append({"task_id": task_id, "old": old_score, "new": new_score})
        results_map[task_id] = {
            "total_score":  eval_log["total_score"],
            "max_score":    eval_log["max_score"],
            "precision":    eval_log["precision"],
            "success_rate": eval_log["success_rate"],
            "instruction":  eval_log["instruction"],
            "subtasks": [
                {"index": s["index"], "name": s["name"], "score": s["score"]}
                for s in eval_log["subtasks"]
            ],
        }

    print(f"\n{'='*60}")
    print(f"Category: {category} | Re-evaluated {len(summary)} tasks, {changed} scores changed")
    if changed:
        print("Changed tasks:")
        for s in summary:
            if s["old"] != s["new"]:
                print(f"  {s['task_id']}: {s['old']} → {s['new']}")

    # Save aggregate results file
    if results_map:
        output_dir = REPO_ROOT / "output"
        output_dir.mkdir(exist_ok=True)
        out_path = output_dir / f"{category}_result.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results_map, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(results_map)} task results → {out_path}")


if __name__ == "__main__":
    main()
