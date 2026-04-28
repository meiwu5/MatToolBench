"""
DigitalMicrograph Batch Evaluation System
For running 400 (20×20) evaluation experiments in batch and generating comparison reports

Task structure:
  - in1  ~ in10  (10 tasks)
  - in11 ~ in15  (5 tasks)
  - in16 ~ in20  (5 tasks)
  Total: 20 tasks

Trajectory definitions (in1 ~ in20): each trajectory records the operations when a task is completed correctly
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# ============ TRAJECTORY COMPLETION DEFINITIONS ============

TRAJECTORY_COMPLETIONS = {

    # ---------- Simple task trajectories ----------

    "in1": {
        "opened_file": "dm1.dm3",
        "operations": [
            "file_import",          # File imported
            "scale_bar_5nm"         # Add 5nm scale bar
        ]
    },

    "in2": {
        "opened_file": "dm2.dm3",
        "operations": [
            "file_import",
            "foreground_color_dialog",
            "scale_bar_red_nm"
        ]
    },

    "in3": {
        "opened_file": "dm3.dm3",
        "operations": [
            "file_import",
            "scale_bar_nm_added"   # Performed scale bar addition (from none)
        ]
    },

    "in4": {
        "opened_file": "dm4.dm3",
        "operations": [
            "file_import",
            "tool_box",             # Use Box tool
            "border_red_box"        # Draw red rectangle
        ]
    },

    "in5": {
        "opened_file": "dm5.dm3",
        "operations": [
            "file_import",
            "tool_oval",            # Use Oval tool
            "border_red_oval"       # Draw red oval
        ]
    },

    "in6": {
        "opened_file": "dm6.dm3",
        "operations": [
            "file_import",
            "filter_sobel"          # Apply Sobel filter
        ]
    },

    "in7": {
        "opened_file": "dm7.dm3",
        "operations": [
            "file_import",
            "dialog_scale",         # Open Scale dialog
            "scale_value_2000"      # Set size to 2000
        ]
    },

    "in8": {
        "opened_file": "dm8.dm3",
        "operations": [
            "file_import",
            "operation_rotate",     # Rotation operation
            "rotate_p50"            # Rotation angle p50
        ]
    },

    "in9": {
        "opened_file": "dm9.dm3",
        "operations": [
            "file_import",
            "analysis_mean_std",    # Mean and standard deviation analysis
            "results_shown"         # Results shown (contains Standard Deviation)
        ]
    },

    "in10": {
        "opened_file": "dm10.dm3",
        "operations": [
            "file_import",
            "dialog_customize",     # Open Customize dialog
            "checkbox_mask"         # Check the Mask checkbox
        ]
    },

    # ---------- Medium task trajectories ----------

    "in11": {
        "opened_file": "dm1.dm3",
        "operations": [
            "file_import",
            "tool_rectangleroi",    # Draw RectangleROI
            "menu_add_data_bar",    # Click Add Data Bar
            "data_bar_visible"      # Data Bar text info visible
        ]
    },

    "in12": {
        "opened_file": "dm2.dm3",
        "operations": [
            "file_import",
            "tool_rectangleroi",
            "roi_copy_and_enlarge"  # Copy and enlarge ROI to cover original area
        ]
    },

    "in13": {
        "opened_file": "dm4.dm3",
        "operations": [
            "file_import",
            "profile_of_dm4",               # Generate Profile of dm4
            "dialog_change_profile_info",   # Open Change Profile Info dialog
            "integration_width_80"          # Set Integration Width = 80
        ]
    },

    "in14": {
        "opened_file": "dm4.dm4",
        "operations": [
            "file_import",
            "fft_of_dm4"            # Perform FFT, generate FFT of dm4 image
        ]
    },

    "in15": {
        "opened_file": "dm5.dm5",
        "operations": [
            "file_import",
            "tool_box",
            "dialog_foreground",    # Open foreground color setting
            "filled_white_box"      # Fill Box interior with white
        ]
    },

    # ---------- Complex task trajectories ----------

    "in16": {
        "opened_file": "dm1.dm3",
        "operations": [
            "file_import",
            "tool_box",
            "tool_rectangleroi",
            "roi_copy_and_enlarge"  # Copy and enlarge ROI
        ]
    },

    "in17": {
        "opened_file": "dm2.dm3",
        "operations": [
            "file_import",
            "profile_of_dm2",       # Generate Profile of dm2
            "nm_count_5"            # nm appears 5 times in Profile popup
        ]
    },

    "in18": {
        "opened_file": "dm6.dm3",
        "operations": [
            "file_import",
            "fft_of_dm6",           # Perform FFT
            "ifft_of_fft_of_dm6"    # Perform IFFT (generates IFFT of FFT of ...)
        ]
    },

    "in19": {
        "opened_file": "dm9.dm3",
        "operations": [
            "file_import",
            "fft_of_dm9",
            "spot_mask",            # Add SpotMask
            "ifft_of_fft_of_dm9"    # Perform IFFT
        ]
    },

    "in20": {
        "opened_file": "dm7.dm3",
        "operations": [
            "file_import",
            "fft_of_dm7",
            "ifft_of_fft_of_dm7",
            "dialog_image_display_info",    # Open Image Display Info dialog
            "brightness_0.3",               # Set Brightness = 0.3
            "contrast_0.2"                  # Set Contrast = 0.2
        ]
    }
}


# ============ THEORETICAL SCORE CALCULATION ============

def calculate_checkpoint_score(check: Dict, traj_data: Dict) -> int:
    """
    Calculate theoretical score for a single checkpoint

    Args:
        check    : 检查点配置 {'function': '...', 'args': {...}}
        traj_data: 轨迹数据   {'opened_file': '...', 'operations': [...]}

    Returns:
        该检查点应得分数（0 或 1）
    """
    func_name = check['function']
    args       = check.get('args', {})

    opened_file = traj_data.get('opened_file', '')
    traj_ops    = traj_data.get('operations', [])

    # ── 1. File import ──────────────────────────────────────────────
    if func_name == 'check_file_import':
        expected = args.get('expected_filename', '')
        # Do loose matching after removing extension
        exp_base  = expected.rsplit('.', 1)[0].lower()
        open_base = opened_file.rsplit('.', 1)[0].lower()
        # Same filename AND marked as imported in trajectory
        return 1 if (exp_base == open_base and 'file_import' in traj_ops) else 0

    # ── 2. OCR text detection ──────────────────────────────────────────
    elif func_name == 'check_ocr_text':
        targets = args.get('target_text', [])
        if isinstance(targets, str):
            targets = [targets]

        # Define trajectory operation tags for each OCR target
        ocr_op_map = {
            '5nm':                  'scale_bar_5nm',
            'nm':                   ['scale_bar_nm', 'scale_bar_5nm', 'scale_bar_red_nm'],
            'foreground color':     'foreground_color_dialog',
            'foreground':           'dialog_foreground',
            'sobel':                'filter_sobel',
            'scale':                'dialog_scale',
            '2000':                 'scale_value_2000',
            'rotate':               'operation_rotate',
            'p50':                  'rotate_p50',
            'mean and std':         'analysis_mean_std',
            'results':              'results_shown',
            'standard deviation':   'results_shown',
            'customize':            'dialog_customize',
            'add data bar':         'menu_add_data_bar',
            'profile of dm4':       'profile_of_dm4',
            'profile of dm2':       'profile_of_dm2',
            'profile of':           ['profile_of_dm2', 'profile_of_dm4'],
            'fft of dm4':           'fft_of_dm4',
            'fft of dm6':           'fft_of_dm6',
            'fft of dm7':           'fft_of_dm7',
            'fft of dm9':           'fft_of_dm9',
            'fft of':               ['fft_of_dm4', 'fft_of_dm6', 'fft_of_dm7', 'fft_of_dm9'],
            'ifft of fft of':       ['ifft_of_fft_of_dm6', 'ifft_of_fft_of_dm7', 'ifft_of_fft_of_dm9'],
            'spotmask':             'spot_mask',
        }

        for target in targets:
            key = target.lower().strip()
            required_ops = ocr_op_map.get(key)
            if required_ops is None:
                continue
            if isinstance(required_ops, str):
                required_ops = [required_ops]
            if any(op in traj_ops for op in required_ops):
                return 1
        return 0

    # ── 3. Drawing tool ──────────────────────────────────────────────
    elif func_name == 'check_drawing_tool':
        tool_name = args.get('tool_name', '').lower()
        tool_op_map = {
            'box':          'tool_box',
            'oval':         'tool_oval',
            'rectangleroi': 'tool_rectangleroi',
        }
        required_op = tool_op_map.get(tool_name)
        return 1 if (required_op and required_op in traj_ops) else 0

    # ── 4. Border color ──────────────────────────────────────────────
    elif func_name == 'check_border_color':
        box_color  = args.get('box_color', '').lower()
        shape_type = args.get('shape_type', 'box').lower()
        op_name    = f'border_{box_color}_{shape_type}'
        return 1 if op_name in traj_ops else 0

    # ── 5. Text color ──────────────────────────────────────────────
    elif func_name == 'check_text_color':
        color_name = args.get('color_name', '').lower()
        op_name    = f'scale_bar_{color_name}_nm'
        return 1 if op_name in traj_ops else 0

    # ── Text color: from none to some ──────────────────────────────────────────
    elif func_name == 'check_text_color_newly_appears':
        color_name = args.get('color_name', '').lower()
        op_name    = f'scale_bar_{color_name}_nm'
        return 1 if op_name in traj_ops else 0

    # ── 6. Checkbox ────────────────────────────────────────────────
    elif func_name == 'check_checkbox_selected':
        checkbox_text = args.get('checkbox_text', '').lower().replace(' ', '_')
        op_name       = f'checkbox_{checkbox_text}'
        return 1 if op_name in traj_ops else 0

    # ── 7. Data Bar text features ──────────────────────────────────────
    elif func_name == 'check_data_bar_by_text':
        return 1 if 'data_bar_visible' in traj_ops else 0

    # ── 8. ROI copy & enlarge ───────────────────────────────────────────
    elif func_name == 'check_roi_copy_and_enlarge':
        return 1 if 'roi_copy_and_enlarge' in traj_ops else 0

    # ── 9. Dialog detection (with field check) ────────────────────────────────
    elif func_name == 'check_dialog_opened':
        title_kw     = args.get('title_keyword', '').lower()
        field_checks = args.get('field_checks', {})

        # Dialog open operation flag
        dialog_op_map = {
            'change profile info':    'dialog_change_profile_info',
            'image display info':     'dialog_image_display_info',
            'properties':             'dialog_properties',
        }
        dialog_op = dialog_op_map.get(title_kw, f'dialog_{title_kw.replace(" ", "_")}')

        if dialog_op not in traj_ops:
            return 0   # 弹窗未打开

        if not field_checks:
            return 1   # 无需字段检查

        # Field check: each field 0/1, strictest — all must be satisfied to get 1
        for field_name, expected_value in field_checks.items():
            field_op = f'{field_name.lower().replace(" ", "_")}_{expected_value}'
            if field_op not in traj_ops:
                return 0
        return 1

    # ── 10. Fill Box ──────────────────────────────────────────────
    elif func_name == 'check_filled_box_with_corners':
        fill_color = args.get('fill_color', 'white').lower()
        op_name    = f'filled_{fill_color}_box'
        return 1 if op_name in traj_ops else 0

    # ── 11. Popup text count ──────────────────────────────────────────
    elif func_name == 'check_text_count_in_dialog':
        target_text    = args.get('target_text', '').lower()
        expected_count = args.get('expected_count', 0)
        op_name        = f'{target_text}_count_{expected_count}'
        return 1 if op_name in traj_ops else 0

    # ── Unknown checkpoint ────────────────────────────────────────────
    return 0


# ============ THEORETICAL SCORE MATRIX GENERATION ============

def generate_theoretical_scores_detailed(task_configs: Dict) -> Dict[str, Any]:
    """
    生成详细的理论得分矩阵（检查点级别）

    Returns:
        {
            'summary': DataFrame (20轨迹 × 20任务 的总分),
            'details': {轨迹ID: {任务名: {checkpoint_scores, checkpoint_names, total_score}}}
        }
    """
    trajectories = list(TRAJECTORY_COMPLETIONS.keys())   # in1 ~ in20
    tasks        = list(task_configs.keys())              # in1 ~ in20

    summary_matrix  = pd.DataFrame(0, index=trajectories, columns=tasks)
    detailed_scores = {}

    for traj_id, traj_data in TRAJECTORY_COMPLETIONS.items():
        detailed_scores[traj_id] = {}

        for task_name, task_checks in task_configs.items():
            cp_scores = []
            cp_names  = []

            for idx, check in enumerate(task_checks):
                score = calculate_checkpoint_score(check, traj_data)
                cp_scores.append(score)

                # Generate readable checkpoint names
                func = check['function']
                a    = check.get('args', {})

                if func == 'check_file_import':
                    label = f"import:{a.get('expected_filename','')}"
                elif func == 'check_drawing_tool':
                    label = f"tool:{a.get('tool_name','')}"
                elif func == 'check_ocr_text':
                    label = f"OCR:{a.get('target_text','')}"
                elif func == 'check_ocr_text_newly_appears':
                    label = f"OCR_new:{a.get('target_text','')}"
                elif func == 'check_border_color':
                    label = f"border_color:{a.get('box_color','')}-{a.get('shape_type','box')}"
                elif func == 'check_text_color':
                    label = f"text_color:{a.get('color_name','')}"
                elif func == 'check_text_color_newly_appears':
                    label = f"text_color_change:{a.get('text','')}→{a.get('color_name','')}"
                elif func == 'check_dialog_opened':
                    label = f"dialog:{a.get('title_keyword','')}"
                else:
                    label = func.replace('check_', '').replace('_', ' ')[:20]

                cp_names.append(f"CP{idx+1}:{label}")

            total = sum(cp_scores)
            detailed_scores[traj_id][task_name] = {
                'checkpoint_scores': cp_scores,
                'checkpoint_names':  cp_names,
                'total_score':       total
            }
            summary_matrix.loc[traj_id, task_name] = total

    return {'summary': summary_matrix, 'details': detailed_scores}


# ============ BATCH EVALUATION RUNNER ============

def run_batch_evaluation(base_dir: str,
                         task_configs: Dict,
                         output_dir: str = None) -> Dict[str, Any]:
    """
    批量运行 DM 评估实验（20 轨迹 × 20 任务 = 400 个实验）

    Args:
        base_dir    : root directory containing in1~in20 subfolders
        task_configs: TASK_CONFIGS 字典（从 dm_evaluator 导入）
        output_dir  : output directory (optional)

    Returns:
        {'summary': DataFrame, 'details': Dict}
    """
    # Lazy import to avoid circular dependency
    from dm_evaluator import DMEvaluator

    base_path  = Path(base_dir).resolve()
    output_dir = Path(output_dir).resolve() if output_dir else base_path.parent / "batch_evaluation_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"DigitalMicrograph Batch Evaluation System")
    print(f"{'='*70}")
    print(f"基础目录 : {base_path}")
    print(f"输出目录 : {output_dir}")
    print(f"轨迹数量 : {len(TRAJECTORY_COMPLETIONS)}")
    print(f"任务数量 : {len(task_configs)}")
    print(f"总实验数 : {len(TRAJECTORY_COMPLETIONS) * len(task_configs)}")
    print(f"{'='*70}\n")

    trajectories = list(TRAJECTORY_COMPLETIONS.keys())
    tasks        = list(task_configs.keys())

    actual_summary  = pd.DataFrame(0.0, index=trajectories, columns=tasks)
    actual_details  = {}
    error_log       = []

    for traj_id in trajectories:
        traj_folder = base_path / traj_id

        if not traj_folder.exists():
            print(f"⚠  轨迹文件夹不存在: {traj_folder}")
            error_log.append(f"{traj_id}: folder does not exist")
            # Record all zeros
            actual_details[traj_id] = {
                t: {'checkpoint_scores': [], 'checkpoint_names': [], 'total_score': 0,
                    'error': '文件夹不存在'}
                for t in tasks
            }
            continue

        print(f"\n{'='*70}")
        print(f"处理轨迹: {traj_id}")
        print(f"{'='*70}")

        actual_details[traj_id] = {}

        try:
            evaluator = DMEvaluator(str(traj_folder))
            print(f"  ✓ Screenshot count: {len(evaluator.screenshots)}")

            for t_idx, (task_name, task_checks) in enumerate(task_configs.items(), 1):
                try:
                    print(f"  [{t_idx:02d}/{len(tasks):02d}] {task_name}  "
                          f"(checkpoints: {len(task_checks)})")

                    result = evaluator.evaluate_task(task_name, task_checks)

                    cp_scores = [c['score'] for c in result['checks']]
                    cp_names  = [
                        f"CP{i+1}:{c['function'].replace('check_','')}"
                        for i, c in enumerate(result['checks'])
                    ]
                    total = result['total_score']

                    actual_details[traj_id][task_name] = {
                        'checkpoint_results': result['checks'],
                        'checkpoint_scores':  cp_scores,
                        'checkpoint_names':   cp_names,
                        'total_score':        total
                    }
                    actual_summary.loc[traj_id, task_name] = total
                    print(f"       Score: {total}/{result['max_score']}  "
                          f"checkpoints: {cp_scores}")

                except Exception as e:
                    print(f"       ❌ Error: {e}")
                    error_log.append(f"{traj_id} - {task_name}: {e}")
                    actual_details[traj_id][task_name] = {
                        'checkpoint_results': [],
                        'checkpoint_scores':  [],
                        'checkpoint_names':   [],
                        'total_score':        0,
                        'error':              str(e)
                    }

        except Exception as e:
            print(f"❌ 轨迹 {traj_id} 初始化失败: {e}")
            import traceback; traceback.print_exc()
            error_log.append(f"{traj_id}: initialization failed - {e}")
            for task_name in tasks:
                actual_details[traj_id][task_name] = {
                    'checkpoint_results': [],
                    'checkpoint_scores':  [],
                    'checkpoint_names':   [],
                    'total_score':        0,
                    'error':              f'初始化失败: {e}'
                }

    # Save error log
    if error_log:
        err_file = output_dir / "error_log.txt"
        with open(err_file, 'w', encoding='utf-8') as f:
            f.write(f"Batch evaluation error log  {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*70}\n")
            f.writelines(f"{e}\n" for e in error_log)
        print(f"\n⚠  错误日志: {err_file}")

    print(f"\n{'='*70}")
    print(f"批量评估完成 — 共处理 "
          f"{len([t for t in trajectories if t in actual_details])} trajectories")
    print(f"{'='*70}\n")

    return {'summary': actual_summary, 'details': actual_details}


# ============ COMPARISON REPORT GENERATION ============

def calculate_accuracy_matrix(theo: pd.DataFrame,
                               actual: pd.DataFrame) -> pd.DataFrame:
    """Calculate accuracy matrix (%) by element"""
    acc = pd.DataFrame(0.0, index=actual.index, columns=actual.columns)
    for row in actual.index:
        for col in actual.columns:
            t = theo.loc[row, col]
            a = actual.loc[row, col]
            acc.loc[row, col] = 100.0 if t == 0 and a == 0 else (
                (a / t * 100) if t > 0 else 0.0
            )
    return acc


def calculate_statistics(theo_summary:   pd.DataFrame,
                          actual_summary: pd.DataFrame,
                          theo_details:   Dict,
                          actual_details: Dict) -> Dict[str, Any]:
    """Summary statistics: task-level + checkpoint-level"""
    diff        = actual_summary - theo_summary
    total_tests = diff.size
    exact_match = (diff == 0).sum().sum()

    total_cp = 0
    match_cp = 0
    for traj_id in theo_details:
        for task_name in theo_details[traj_id]:
            theo_cp   = theo_details[traj_id][task_name]['checkpoint_scores']
            actual_cp = actual_details.get(traj_id, {}).get(
                task_name, {}).get('checkpoint_scores', [])
            # Align length
            actual_cp = (actual_cp + [0] * len(theo_cp))[:len(theo_cp)]
            for t, a in zip(theo_cp, actual_cp):
                total_cp += 1
                match_cp += int(t == a)

    return {
        '总测试数(任务级)':     int(total_tests),
        '完全匹配数(任务级)':   int(exact_match),
        'task_match_rate(%)':        f"{exact_match / total_tests * 100:.1f}",
        '高估数(理论>实际)':    int((diff < 0).sum().sum()),
        '低估数(理论<实际)':    int((diff > 0).sum().sum()),
        '总检查点数':           int(total_cp),
        '检查点匹配数':         int(match_cp),
        'checkpoint_match_rate(%)':      f"{match_cp / total_cp * 100:.1f}" if total_cp else "N/A",
    }


def generate_comparison_report(theoretical_data: Dict,
                                actual_data:      Dict,
                                output_dir:       str) -> Dict[str, Any]:
    """
    生成检查点级别对比 Excel 报告

    输出文件：
      - checkpoint_comparison_<timestamp>.xlsx  (checkpoint details per task)
      - summary_matrices_<timestamp>.xlsx       (total score/diff/accuracy matrices)
    """
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    theo_summary   = theoretical_data['summary']
    theo_details   = theoretical_data['details']
    actual_summary = actual_data['summary']
    actual_details = actual_data['details']

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    # ── Checkpoint detail report ────────────────────────────────────────────
    cp_file = output_path / f"checkpoint_comparison_{ts}.xlsx"
    with pd.ExcelWriter(cp_file, engine='openpyxl') as writer:

        # Sheet1: Total score comparison (wide table)
        rows = []
        for task in theo_summary.columns:
            for traj in theo_summary.index:
                t = theo_summary.loc[traj, task]
                a = actual_summary.loc[traj, task]
                rows.append({'任务': task, '轨迹': traj,
                             '理论总分': t, '实际总分': a,
                             '匹配': '✓' if t == a else '✗',
                             '差异': a - t})
        pd.DataFrame(rows).to_excel(writer, sheet_name='总分对比', index=False)

        # Sheet2+: Checkpoint details for each task
        all_tasks = list(theo_details[list(theo_details.keys())[0]].keys())
        for task_name in all_tasks:
            rows = []
            for traj_id in sorted(theo_details.keys()):
                theo_info   = theo_details[traj_id][task_name]
                actual_info = actual_details.get(traj_id, {}).get(task_name, {})

                theo_cp   = theo_info['checkpoint_scores']
                actual_cp = actual_info.get('checkpoint_scores', [])
                cp_names  = theo_info['checkpoint_names']
                actual_cp = (actual_cp + [0] * len(theo_cp))[:len(theo_cp)]

                for idx, (name, t, a) in enumerate(zip(cp_names, theo_cp, actual_cp)):
                    rows.append({
                        '轨迹':    traj_id,
                        'checkpoint':  f"CP{idx+1}",
                        '检查内容': name,
                        '理论得分': t,
                        '实际得分': a,
                        'whether matched': '✓' if t == a else '✗',
                        '差异':    a - t
                    })

            sheet = task_name[:31]
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet, index=False)

        # Statistics summary
        stats = calculate_statistics(
            theo_summary, actual_summary, theo_details, actual_details)
        pd.DataFrame(list(stats.items()), columns=['指标', '数值']).to_excel(
            writer, sheet_name='统计摘要', index=False)

    print(f"✓ 检查点对比报告: {cp_file}")

    # ── Total score matrix report ──────────────────────────────────────────
    mat_file = output_path / f"summary_matrices_{ts}.xlsx"
    with pd.ExcelWriter(mat_file, engine='openpyxl') as writer:
        theo_summary.to_excel(writer,   sheet_name='理论总分矩阵')
        actual_summary.to_excel(writer, sheet_name='实际总分矩阵')
        (actual_summary - theo_summary).to_excel(writer, sheet_name='差异矩阵')
        calculate_accuracy_matrix(
            theo_summary, actual_summary).to_excel(writer, sheet_name='准确率(%)')

    print(f"✓ 总分矩阵对比报告: {mat_file}")

    # Print statistics
    print(f"\n{'='*70}")
    print("Evaluation statistics")
    print(f"{'='*70}")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"{'='*70}\n")

    return stats


# ============ MAIN FUNCTION ============

def main():
    import argparse

    parser = argparse.ArgumentParser(description='DigitalMicrograph Batch Evaluation System')
    parser.add_argument(
        '--base_dir', type=str, required=True,
        help='包含 in1~in20 子文件夹的根目录')
    parser.add_argument(
        '--output_dir', type=str, default=None,
        help='输出目录（默认 base_dir/../batch_evaluation_results）')
    parser.add_argument(
        '--theoretical_only', action='store_true',
        help='仅生成理论得分矩阵，不运行实际评估')
    args = parser.parse_args()

    # Import DM task configs
    from dm_evaluator import TASK_CONFIGS

    print(f"\n{'='*70}")
    print(f"DigitalMicrograph Batch Evaluation System")
    print(f"{'='*70}\n")

    output_dir = args.output_dir or str(
        Path(args.base_dir).parent / "batch_evaluation_results")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ── Step 1: Theoretical scores ──────────────────────────────────────────
    print("Step 1: Generating theoretical score matrix (checkpoint level)...")
    theoretical_data = generate_theoretical_scores_detailed(TASK_CONFIGS)

    theo_xlsx = Path(output_dir) / "theoretical_scores_summary.xlsx"
    theoretical_data['summary'].to_excel(theo_xlsx)
    print(f"  ✓ Theoretical total score matrix: {theo_xlsx}")

    theo_json = Path(output_dir) / "theoretical_scores_detailed.json"
    with open(theo_json, 'w', encoding='utf-8') as f:
        json.dump(
            {traj: {task: {k: v for k, v in info.items()}
                    for task, info in tasks.items()}
             for traj, tasks in theoretical_data['details'].items()},
            f, indent=2, ensure_ascii=False)
    print(f"  ✓ Theoretical detailed scores: {theo_json}\n")

    if args.theoretical_only:
        print("Only generating theoretical scores, program ends.")
        return

    # ── Step 2: Batch actual evaluation ──────────────────────────────────────────
    print("Step 2: Running batch evaluation (400 experiments)...")
    actual_data = run_batch_evaluation(
        args.base_dir, TASK_CONFIGS, output_dir)

    actual_xlsx = Path(output_dir) / "actual_scores_summary.xlsx"
    actual_data['summary'].to_excel(actual_xlsx)
    print(f"  ✓ Actual total score matrix: {actual_xlsx}")

    actual_json = Path(output_dir) / "actual_scores_detailed.json"
    with open(actual_json, 'w', encoding='utf-8') as f:
        serializable = {
            traj: {
                task: {
                    'checkpoint_scores': info.get('checkpoint_scores', []),
                    'checkpoint_names':  info.get('checkpoint_names', []),
                    'total_score':       info.get('total_score', 0),
                    'error':             info.get('error', None)
                }
                for task, info in tasks.items()
            }
            for traj, tasks in actual_data['details'].items()
        }
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Actual detailed scores: {actual_json}\n")

    # ── Step 3: Comparison report ──────────────────────────────────────────
    print("Step 3: Generating checkpoint-level comparison report...")
    generate_comparison_report(theoretical_data, actual_data, output_dir)

    print("\n✅ All done!")
    print(f"输出目录: {output_dir}\n")


if __name__ == "__main__":
    main()