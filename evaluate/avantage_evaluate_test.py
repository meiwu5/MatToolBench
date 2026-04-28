"""
Avantage XPS Batch Evaluation System
Features:
1. Define theoretical scores for each trajectory
2. Run 400 (20×20) evaluation experiments in batch
3. Generate Excel comparison report
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Import the AvantageEvaluator
sys.path.append(str(Path(__file__).parent))


# ============ THEORETICAL SCORE DEFINITIONS ============

# Mapping of trajectory IDs to instructions
TRAJECTORY_INSTRUCTIONS = {
    "in1": "in1: Open ADVANTAGE software, import Avantage/C1s Scan.VGD",
    "in2": "in2: Open ADVANTAGE software, import four files: Avantage/C1s Scan.VGD, Avantage/O1s Scan.VGD, Avantage/Zn2p Scan.VGD, and Avantage/XPS Survey.VGD",
    "in3": "in3: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, double-click to zoom in the C1s Scan image then double-click to zoom out",
    "in4": "in4: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, select stacked graph mode in Display Modes to show the selected data",
    "in5": "in5: Open ADVANTAGE software, import Avantage/XPS Survey.VGD, copy the spectrum to window B",
    "in6": "in6: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, add background using smart parameters",
    "in7": "in7: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, adjust X-Axis font size to 20",
    "in8": "in8: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, set X-Axis title color to Red",
    "in9": "in9: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, reverse the X-axis energy axis",
    "in10": "in10: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, adjust grid properties to Rows=3, Columns=3",
    
    "in11": "in11: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, perform automatic peak fitting",
    "in12": "in12: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, perform charge correction, shift by amount +0.14 eV",
    "in13": "in13: Open ADVANTAGE software, import Avantage/XPS Survey.VGD, smooth the spectrum, change FWHM to 2.115",
    "in14": "in14: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, smart-add O1s peak, set background average width to 20 eV",
    "in15": "in15: Open ADVANTAGE software, import Avantage/C1s Scan.VGD and Avantage/XPS Survey.VGD, select and arrange these two spectra vertically",
    
    "in16": "in16: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, add and lock Shirley baseline, perform charge correction by +0.14 eV",
    "in17": "in17: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, smart-add baseline and perform automatic peak fitting",
    "in18": "in18: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, copy to window B, add 3333 to window B values, arrange vertically",
    "in19": "in19: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, add Peak (start 545, end 540 eV), lock and then fit",
    "in20": "in20: Open ADVANTAGE software, import C1s, O1s, and Survey Scan, smart-add peaks for C1s, apply charge shift of +1360 eV to all spectra",
}

# Operations actually performed in each trajectory (inferred from instructions)
# Notes:
# - imported_files: files primarily operated on (explicitly required by the instruction)
# - other_files: files that may be opened during the process but are not the primary target
# - operations: specific operations performed
TRAJECTORY_COMPLETIONS = {
    # Simple tasks (in1-in10)
    "in1": {
        "imported_files": ["C1s Scan"],
        "other_files": [],  # No other files opened during the process
        "operations": []
    },
    "in2": {
        "imported_files": ["C1s Scan", "O1s Scan", "Zn2p Scan", "XPS Survey"],
        "other_files": ["C1s Scan"],  # May be opened repeatedly during the process
        "operations": []
    },
    "in3": {
        "imported_files": ["C1s Scan"],
        "other_files": ["O1s Scan"],  # Other files opened during the process
        "operations": ["image_zoom"]  # Zoom in and out
    },
    "in4": {
        "imported_files": ["O1s Scan"],
        "other_files": [],
        "operations": ["stacked_graph"]  # Stacked graph
    },
    "in5": {
        "imported_files": ["XPS Survey", "XPS Survey"],  # 2 copies after duplication
        "other_files": ["C1s Scan"],  # Other files opened during the process
        "operations": ["duplicate_files"]
    },
    "in6": {
        "imported_files": ["Zn2p Scan"],
        "other_files": ["C1s Scan"],  # Other files opened during the process
        "operations": ["background_added"]  # Smart background
    },
    "in7": {
        "imported_files": ["Zn2p Scan"],
        "other_files": ["C1s Scan", "O1s Scan"],  # Other files opened during the process
        "operations": ["chart_dialog", "font_20pt"]
    },
    "in8": {
        "imported_files": ["Zn2p Scan"],
        "other_files": ["C1s Scan", "O1s Scan"],  # Other files opened during the process
        "operations": ["chart_dialog", "color_red"]
    },
    "in9": {
        "imported_files": ["O1s Scan"],
        "other_files": ["C1s Scan", "Zn2p Scan"],  # Other files opened during the process
        "operations": ["energy_axis_reversed"]
    },
    "in10": {
        "imported_files": ["C1s Scan"],
        "other_files": [],
        "operations": ["grid_3x3"]
    },
    
    # Medium tasks (in11-in15)
    "in11": {
        "imported_files": ["Zn2p Scan"],
        "other_files": ["C1s Scan"],  # Other files opened during the process
        "operations": ["peak_fitting_dialog"]
    },
    "in12": {
        "imported_files": ["O1s Scan"],
        "other_files": [],
        "operations": ["charge_shift_dialog", "shift_0.14"]
    },
    "in13": {
        "imported_files": ["XPS Survey"],
        "other_files": [],
        "operations": ["smoothing_dialog", "fwhm_2.115"]
    },
    "in14": {
        "imported_files": ["O1s Scan"],
        "other_files": [["C1s Scan"]],
        "operations": ["peak_add_dialog", "eV_20"]
    },
    "in15": {
        "imported_files": ["C1s Scan", "XPS Survey"],
        "other_files": [],
        "operations": ["lightbox_dialog", "stacked_view"]
    },
    
    # Complex tasks (in16-in20)
    "in16": {
        "imported_files": ["C1s Scan"],
        "other_files": [],
        "operations": ["peak_add_dialog", "iterations_param", "charge_shift_dialog", "shift_19.00"]
    },
    "in17": {
        "imported_files": ["O1s Scan"],
        "other_files": [],
        "operations": ["peak_add_dialog", "peak_fitting_dialog"]
    },
    "in18": {
        "imported_files": ["C1s Scan", "C1s Scan"],  # original + copy
        "other_files": [],
        "operations": ["file_duplicated", "add_constant_dialog", "constant_3333", "lightbox_dialog"]
    },
    "in19": {
        "imported_files": ["O1s Scan"],
        "other_files": [],
        "operations": ["peak_add_dialog", "start_545_end_540", "peak_fitting_dialog"]
    },
    "in20": {
        "imported_files": ["C1s Scan", "O1s Scan", "Survey Scan"],
        "other_files": [],
        "operations": ["peak_add_dialog", "peak_fitting_dialog", "charge_shift_dialog", "shift_360"]
    },
}


def normalize_filename(filename: str) -> str:
    """Normalize filename, remove extension"""
    if not filename:
        return ""
    
    # Remove common extensions
    for ext in ['.VGD', '.vgd', '.vgp', '.VGP']:
        if filename.endswith(ext):
            return filename[:-len(ext)]
    
    return filename


def files_match(expected: str, actual: str) -> bool:
    """Check if two filenames match (ignoring extension and case)"""
    exp_norm = normalize_filename(expected).lower().replace(' ', '')
    act_norm = normalize_filename(actual).lower().replace(' ', '')
    
    return exp_norm in act_norm or act_norm in exp_norm


def calculate_checkpoint_score(check: Dict, traj_data: Dict) -> int:
    """
    Calculate theoretical score for a single checkpoint
    
    Args:
        check: checkpoint configuration {'function': '...', 'args': {...}}
        traj_data: 轨迹数据 {'imported_files': [...], 'other_files': [...], 'operations': [...]}
    
    Returns:
        该检查点应该得到的分数
    """
    func_name = check['function']
    args = check.get('args', {})
    
    # Get all files: primary files + other files
    imported_files = traj_data.get('imported_files', [])
    other_files = traj_data.get('other_files', [])
    all_files = imported_files + other_files  # merge all files
    
    traj_ops = traj_data.get('operations', [])
    
    # === Checkpoint 1: File import ===
    if func_name == 'check_multiple_files_imported':
        expected_files = args.get('expected_files', [])
        match_mode = args.get('match_mode', 'contains')  # 默认为 contains 模式
        
        # other_files supports multiple possible states:
        # Format 1: [] - empty list, only imported_files
        # Format 2: [["C1s Scan"]] - single state
        # Format 3: [["C1s Scan"], ["C1s Scan", "O1s Scan"]] - multiple possible states
        
        # Build all possible file combinations
        all_possible_states = []
        
        if not other_files:
            # No other files, use imported_files only
            all_possible_states = [imported_files]
        else:
            # Check format of other_files
            if other_files and isinstance(other_files[0], list):
                # Multi-level list: each sub-list is one possible state
                for state in other_files:
                    all_possible_states.append(imported_files + state)
            else:
                # Single-level list (legacy format compatibility)
                all_possible_states = [imported_files + other_files]
        
        # Try matching any possible state
        for possible_files in all_possible_states:
            matched_count = 0
            matched_set = set()
            
            # Count matched expected files
            for exp_file in expected_files:
                for traj_file in possible_files:
                    if files_match(exp_file, traj_file):
                        matched_count += 1
                        matched_set.add(exp_file)
                        break
            
            # Decision based on match_mode
            if match_mode == 'exact':
                # Strict mode: count must be equal + all files match
                expected_set = set(f.lower().replace(' ', '') for f in expected_files)
                possible_set = set(normalize_filename(f).lower().replace(' ', '') for f in possible_files)
                
                if len(possible_files) == len(expected_files) and expected_set == possible_set:
                    return 1
            else:  # contains 模式（默认）
                # Inclusion mode: just need to contain all expected files
                if matched_count == len(expected_files):
                    return 1
        
        # No possible state matches
        return 0
    
    # === Checkpoint 2: Image zoom in/out ===
    elif func_name == 'check_image_zoom':
        return 1 if 'image_zoom' in traj_ops else 0
    
    # === Checkpoint 3: Stacked graph ===
    elif func_name == 'check_stacked_graph':
        return 1 if 'stacked_graph' in traj_ops else 0
    
    # === Checkpoint 4: Duplicate files ===
    elif func_name == 'check_duplicate_files_imported':
        expected_files = args.get('expected_files', [])
        # Check if imported file count matched (including duplicates)
        # Only count imported_files, as these are the primarily operated files
        return 1 if len(imported_files) >= len(expected_files) else 0
    
    # === Checkpoint 5: Background addition ===
    elif func_name == 'check_background_added_successfully':
        return 1 if 'background_added' in traj_ops else 0
    
    # === Checkpoint 6: Dialog exists ===
    elif func_name == 'check_dialog_exists':
        dialog_title = args.get('dialog_title', '')
        
        # Map dialog title to operation
        dialog_op_map = {
            'Chart': 'chart_dialog',
            'Grid Properties': 'grid_properties_dialog',
            'Peak Fitting': 'peak_fitting_dialog',
            'Charge Shift': 'charge_shift_dialog',
            'Smoothing': 'smoothing_dialog',
            'Peak Add': 'peak_add_dialog',
            'LightBox': 'lightbox_dialog',
            'Add Constant': 'add_constant_dialog',
        }
        
        for key, op in dialog_op_map.items():
            if key in dialog_title:
                return 1 if op in traj_ops else 0
        
        return 0
    
    # === Checkpoint 7: Dialog parameters ===
    elif func_name == 'check_dialog_parameter':
        param_names = args.get('parameter_name', [])
        expected_values = args.get('expected_value', [])
        
        # If not a list, convert to list
        if not isinstance(param_names, list):
            param_names = [param_names]
        if not isinstance(expected_values, list):
            expected_values = [expected_values]
        
        # Check each parameter
        score = 0
        max_score = len(param_names)
        
        for param, value in zip(param_names, expected_values):
            # Build operation identifier
            if 'Font' in param and '20' in str(value):
                if 'font_20pt' in traj_ops:
                    score += 1
            elif 'colour' in param.lower() and value == 'Red':
                if 'color_red' in traj_ops:
                    score += 1
            elif 'Rows' in param and value == '3':
                if 'grid_3x3' in traj_ops:
                    score += 1
            elif 'Columns' in param and value == '3':
                if 'grid_3x3' in traj_ops:
                    score += 1
            elif 'Shift By' in param:
                if f"shift_{value}" in traj_ops:
                    score += 1
            elif 'FWHM' in param:
                if f"fwhm_{value}" in traj_ops:
                    score += 1
            elif 'eV' in param:
                if f"eV_{value}" in traj_ops:
                    score += 1
            elif 'Constant' in param:
                if f"constant_{value}" in traj_ops:
                    score += 1
            elif 'Start' in param or 'End' in param:
                if f"start_{expected_values[0]}_end_{expected_values[1]}" in traj_ops:
                    score += 1
            elif not expected_values or expected_values == []:
                # Only check if parameter name exists (e.g. Iterations, C1s Scan)
                # In this case, if the corresponding dialog is present, give score
                dialog_in_ops = False
                if 'Iterations' in param and 'peak_add_dialog' in traj_ops:
                    dialog_in_ops = True
                elif param in ['C1s Scan', 'XPS Survey', 'O1s Scan'] and 'lightbox_dialog' in traj_ops:
                    dialog_in_ops = True
                
                if dialog_in_ops:
                    score += 1
        
        return score
    
    # === Checkpoint 8: Energy axis reversed ===
    elif func_name == 'check_energy_axis_reversed':
        return 1 if 'energy_axis_reversed' in traj_ops else 0
    
    # === Checkpoint 9: File copy ===
    elif func_name == 'check_file_duplicated':
        return 1 if 'file_duplicated' in traj_ops else 0
    
    return 0


def generate_theoretical_scores_detailed() -> Dict[str, Any]:
    """
    生成详细的理论得分矩阵（包含每个检查点的得分）
    
    Returns:
        {
            'summary': DataFrame (20轨迹 × 20任务的总分),
            'details': Dict[trajectory_id][task_name] = {
                'checkpoint_scores': [check1_score, check2_score, ...],
                'checkpoint_names': [check1_name, check2_name, ...],
                'total_score': int
            }
        }
    """
    
    # Import task configs
    from avantage_evaluator import TASK_CONFIGS
    
    trajectories = [f"in{i}" for i in range(1, 21)]
    tasks = list(TASK_CONFIGS.keys())
    
    # Total score matrix
    summary_matrix = pd.DataFrame(0, index=trajectories, columns=tasks)
    
    # Detailed scores: {trajectory_id: {task_name: {...}}}
    detailed_scores = {}
    
    for traj_id, traj_data in TRAJECTORY_COMPLETIONS.items():
        detailed_scores[traj_id] = {}
        
        for task_name, task_checks in TASK_CONFIGS.items():
            checkpoint_scores = []
            checkpoint_names = []
            
            for check_idx, check in enumerate(task_checks):
                # Calculate theoretical score for this checkpoint
                score = calculate_checkpoint_score(check, traj_data)
                checkpoint_scores.append(score)
                
                # Generate checkpoint names
                func_name = check['function']
                args = check.get('args', {})
                
                if func_name == 'check_multiple_files_imported':
                    files = args.get('expected_files', [])
                    check_name = f"import:{','.join(files[:2])}" if len(files) <= 2 else f"import:{len(files)}_files"
                elif func_name == 'check_dialog_exists':
                    check_name = f"dialog:{args.get('dialog_title', '')[:15]}"
                elif func_name == 'check_dialog_parameter':
                    check_name = f"param-settings"
                else:
                    # Remove check_ prefix
                    check_name = func_name.replace('check_', '').replace('_', ' ')
                
                checkpoint_names.append(f"CP{check_idx+1}:{check_name}")
            
            detailed_scores[traj_id][task_name] = {
                'checkpoint_scores': checkpoint_scores,
                'checkpoint_names': checkpoint_names,
                'total_score': sum(checkpoint_scores)
            }
            
            summary_matrix.loc[traj_id, task_name] = sum(checkpoint_scores)
    
    return {
        'summary': summary_matrix,
        'details': detailed_scores
    }


def run_batch_evaluation(base_dir: str, output_dir: str = None) -> Dict[str, Any]:
    """
    批量运行评估实验（20轨迹 × 20任务 = 400个实验）
    
    Args:
        base_dir: base directory containing in1-in20 subfolders
        output_dir: output directory (optional)
    
    Returns:
        {
            'summary': DataFrame (实际总分矩阵),
            'details': Dict[task_name][trajectory_id] = {
                'checkpoint_results': [...],
                'checkpoint_scores': [0/1, ...],
                'total_score': int
            }
        }
    """
    
    # Import AvantageEvaluator
    from avantage_evaluator import AvantageEvaluator, TASK_CONFIGS
    
    base_path = Path(base_dir).resolve()
    if output_dir is None:
        output_dir = base_path.parent / "batch_evaluation_results"
    else:
        output_dir = Path(output_dir).resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"{'='*70}")
    print(f"Avantage XPS Batch Evaluation System")
    print(f"{'='*70}")
    print(f"基础目录: {base_path}")
    print(f"输出目录: {output_dir}")
    print(f"{'='*70}\n")
    
    # Initialize result storage
    trajectories = [f"in{i}" for i in range(1, 21)]
    tasks = list(TASK_CONFIGS.keys())
    
    actual_scores_summary = pd.DataFrame(0, index=trajectories, columns=tasks)
    actual_scores_detailed = {}
    error_log = []
    
    # Iterate over all trajectories
    for traj_id in trajectories:
        traj_folder = base_path / traj_id
        
        if not traj_folder.exists():
            print(f"⚠️  警告: 轨迹文件夹不存在: {traj_folder}")
            error_log.append(f"{traj_id}: folder does not exist")
            continue
        
        print(f"\n{'='*70}")
        print(f"正在处理轨迹: {traj_id}")
        print(f"{'='*70}")
        
        # Initialize detailed score dict for this trajectory
        actual_scores_detailed[traj_id] = {}
        
        try:
            # Create evaluator
            evaluator = AvantageEvaluator(str(traj_folder))
            
            # Iterate over all tasks
            for task_name, task_checks in TASK_CONFIGS.items():
                try:
                    print(f"\n  → 测试任务: {task_name}")
                    
                    # Run evaluation
                    result = evaluator.evaluate_task(task_name, task_checks)
                    
                    # Extract checkpoint results
                    checkpoint_results = result['checks']
                    checkpoint_scores = [check['score'] for check in checkpoint_results]
                    total_score = sum(checkpoint_scores)
                    
                    # Save detailed results
                    actual_scores_detailed[traj_id][task_name] = {
                        'checkpoint_results': checkpoint_results,
                        'checkpoint_scores': checkpoint_scores,
                        'checkpoint_names': [
                            f"CP{i+1}:{check['function'].replace('check_', '')}" 
                            for i, check in enumerate(checkpoint_results)
                        ],
                        'total_score': total_score
                    }
                    
                    # Record total score
                    actual_scores_summary.loc[traj_id, task_name] = total_score
                    
                    print(f"    Score: {total_score}/{result['max_score']}")
                    print(f"    Checkpoints: {checkpoint_scores}")
                    
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    error_log.append(f"{traj_id} - {task_name}: {str(e)}")
                    
                    # Record failed checkpoints
                    actual_scores_detailed[traj_id][task_name] = {
                        'checkpoint_results': [],
                        'checkpoint_scores': [],
                        'checkpoint_names': [],
                        'total_score': 0,
                        'error': str(e)
                    }
                    continue
        
        except Exception as e:
            print(f"❌ 轨迹 {traj_id} 初始化失败: {str(e)}")
            error_log.append(f"{traj_id}: initialization failed - {str(e)}")
            # Record errors for all tasks
            for task_name in tasks:
                actual_scores_detailed[traj_id][task_name] = {
                    'checkpoint_results': [],
                    'checkpoint_scores': [],
                    'checkpoint_names': [],
                    'total_score': 0,
                    'error': f"Trajectory initialization failed: {str(e)}"
                }
            continue
    
    # Save error log
    if error_log:
        error_file = output_dir / "error_log.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Batch evaluation error log\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n\n")
            for err in error_log:
                f.write(f"{err}\n")
        print(f"\n⚠️  错误日志已保存: {error_file}")
    
    print(f"\n{'='*70}")
    print(f"批量评估完成!")
    print(f"{'='*70}\n")
    
    return {
        'summary': actual_scores_summary,
        'details': actual_scores_detailed
    }


def generate_comparison_report(theoretical_data: Dict,
                               actual_data: Dict,
                               output_dir: str) -> Dict[str, Any]:
    """
    生成检查点级别的对比报告
    
    Args:
        theoretical_data: 理论得分数据 {'summary': DataFrame, 'details': Dict}
        actual_data: 实际得分数据 {'summary': DataFrame, 'details': Dict}
        output_dir: output directory
    
    Returns:
        统计信息字典
    """
    
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    
    theo_summary = theoretical_data['summary']
    theo_details = theoretical_data['details']
    actual_summary = actual_data['summary']
    actual_details = actual_data['details']
    
    print("\nGenerating checkpoint-level comparison table...")
    
    excel_file = output_path / f"checkpoint_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Sheet 1: Total score comparison (summary)
        rows = []
        for task_name in theo_summary.columns:
            for traj_id in theo_summary.index:
                theo_score = theo_summary.loc[traj_id, task_name]
                actual_score = actual_summary.loc[traj_id, task_name]
                match = '✓' if theo_score == actual_score else '✗'
                
                rows.append({
                    '任务': task_name,
                    '轨迹': traj_id,
                    '理论总分': theo_score,
                    '实际总分': actual_score,
                    '匹配': match
                })
        
        summary_df = pd.DataFrame(rows)
        summary_df.to_excel(writer, sheet_name='总分对比', index=False)
        
        # Sheet 2-N: Checkpoint detail comparison for each task
        for task_name in sorted(theo_details[list(theo_details.keys())[0]].keys()):
            rows = []
            
            for traj_id in sorted(theo_details.keys()):
                theo_info = theo_details[traj_id][task_name]
                actual_info = actual_details.get(traj_id, {}).get(task_name, {})
                
                theo_checkpoints = theo_info['checkpoint_scores']
                actual_checkpoints = actual_info.get('checkpoint_scores', [])
                checkpoint_names = theo_info['checkpoint_names']
                
                # Align checkpoint counts
                if len(actual_checkpoints) < len(theo_checkpoints):
                    actual_checkpoints.extend([0] * (len(theo_checkpoints) - len(actual_checkpoints)))
                
                for idx, (cp_name, theo_score, actual_score) in enumerate(
                    zip(checkpoint_names, theo_checkpoints, actual_checkpoints)
                ):
                    match = '✓' if theo_score == actual_score else '✗'
                    
                    rows.append({
                        '轨迹': traj_id,
                        'checkpoint': f"CP{idx+1}",
                        '检查内容': cp_name,
                        '理论得分': theo_score,
                        '实际得分': actual_score,
                        'whether matched': match,
                        '差异': actual_score - theo_score
                    })
            
            df = pd.DataFrame(rows)
            # Excel sheet names are limited to 31 characters
            sheet_name = task_name[:31] if len(task_name) > 31 else task_name
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Sheet N+1: Statistical summary
        stats = calculate_statistics(theo_summary, actual_summary, theo_details, actual_details)
        stats_df = pd.DataFrame([stats]).T
        stats_df.columns = ['数值']
        stats_df.to_excel(writer, sheet_name='统计摘要')
    
    print(f"✓ 检查点对比报告已保存: {excel_file}")
    
    # Generate total score matrix comparison Excel
    excel_summary = output_path / f"summary_matrices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(excel_summary, engine='openpyxl') as writer:
        theo_summary.to_excel(writer, sheet_name='理论总分矩阵')
        actual_summary.to_excel(writer, sheet_name='实际总分矩阵')
        
        diff_matrix = actual_summary - theo_summary
        diff_matrix.to_excel(writer, sheet_name='差异矩阵')
        
        accuracy_matrix = calculate_accuracy_matrix(theo_summary, actual_summary)
        accuracy_matrix.to_excel(writer, sheet_name='准确率(%)')
    
    print(f"✓ 总分矩阵对比已保存: {excel_summary}")
    
    # Print statistics
    print(f"\n{'='*70}")
    print(f"评估统计")
    print(f"{'='*70}")
    for key, value in stats.items():
        print(f"{key}: {value}")
    print(f"{'='*70}\n")
    
    return stats


def calculate_accuracy_matrix(theo_summary: pd.DataFrame, 
                              actual_summary: pd.DataFrame) -> pd.DataFrame:
    """Calculate accuracy matrix"""
    accuracy_matrix = pd.DataFrame(0.0, 
                                   index=actual_summary.index, 
                                   columns=actual_summary.columns)
    
    for row in actual_summary.index:
        for col in actual_summary.columns:
            theoretical = theo_summary.loc[row, col]
            actual = actual_summary.loc[row, col]
            
            if theoretical == 0:
                accuracy_matrix.loc[row, col] = 100.0 if actual == 0 else 0.0
            else:
                accuracy_matrix.loc[row, col] = (actual / theoretical) * 100
    
    return accuracy_matrix


def calculate_statistics(theo_summary: pd.DataFrame,
                         actual_summary: pd.DataFrame,
                         theo_details: Dict,
                         actual_details: Dict) -> Dict[str, Any]:
    """Calculate statistics"""
    
    # Score-level statistics
    total_tests = len(theo_summary.index) * len(theo_summary.columns)
    diff_matrix = actual_summary - theo_summary
    perfect_matches = (diff_matrix == 0).sum().sum()
    
    # Checkpoint-level statistics
    total_checkpoints = 0
    checkpoint_matches = 0
    
    for traj_id in theo_details.keys():
        for task_name in theo_details[traj_id].keys():
            theo_info = theo_details[traj_id][task_name]
            actual_info = actual_details.get(traj_id, {}).get(task_name, {})
            
            theo_checkpoints = theo_info['checkpoint_scores']
            actual_checkpoints = actual_info.get('checkpoint_scores', [])
            
            # Align length
            if len(actual_checkpoints) < len(theo_checkpoints):
                actual_checkpoints.extend([0] * (len(theo_checkpoints) - len(actual_checkpoints)))
            
            for theo_score, actual_score in zip(theo_checkpoints, actual_checkpoints):
                total_checkpoints += 1
                if theo_score == actual_score:
                    checkpoint_matches += 1
    
    stats = {
        '总测试数(任务级)': total_tests,
        '完全匹配数(任务级)': perfect_matches,
        'task_match_rate(%)': f"{(perfect_matches / total_tests * 100):.1f}",
        '高估数(任务级)': (diff_matrix > 0).sum().sum(),
        '低估数(任务级)': (diff_matrix < 0).sum().sum(),
        '总检查点数': total_checkpoints,
        '检查点匹配数': checkpoint_matches,
        'checkpoint_match_rate(%)': f"{(checkpoint_matches / total_checkpoints * 100):.1f}",
    }
    
    return stats


def main():
    """Main function: generate theoretical scores + run batch evaluation + generate comparison report"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Avantage XPS Batch Evaluation System')
    parser.add_argument('--base_dir', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\pyautogui\a11y_tree\gpt-5\0\avantage',
                       help='包含in1-in20的基础目录')
    parser.add_argument('--output_dir', type=str, default=r'D:\ChemLLM\science_agent\results\pyautogui\a11y_tree\gpt-5\0\avantage\test',
                       help='输出目录（默认为base_dir的父目录）')
    parser.add_argument('--theoretical_only', action='store_true',
                       help='仅生成理论得分矩阵（不运行实际评估）')
    
    args = parser.parse_args()
    
    # Step 1: Generate theoretical scores
    print("Step 1: Generating theoretical score matrix (checkpoint level)...")
    theoretical_data = generate_theoretical_scores_detailed()
    
    output_dir = args.output_dir or str(Path(args.base_dir).parent / "batch_evaluation_results")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save theoretical scores
    theoretical_file = output_path / "theoretical_scores_summary.xlsx"
    theoretical_data['summary'].to_excel(theoretical_file)
    print(f"✓ 理论总分矩阵已保存: {theoretical_file}")
    
    # Save theoretical score details (JSON)
    theoretical_detail_file = output_path / "theoretical_scores_detailed.json"
    serializable_details = {}
    for traj_id, traj_data in theoretical_data['details'].items():
        serializable_details[traj_id] = {}
        for task_name, task_info in traj_data.items():
            serializable_details[traj_id][task_name] = {
                'checkpoint_scores': task_info['checkpoint_scores'],
                'checkpoint_names': task_info['checkpoint_names'],
                'total_score': task_info['total_score']
            }
    
    with open(theoretical_detail_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_details, f, indent=2, ensure_ascii=False)
    print(f"✓ 理论详细得分已保存: {theoretical_detail_file}\n")
    
    if args.theoretical_only:
        print("Only generating theoretical scores, program ends.")
        return
    
    # Step 2: Run batch evaluation
    print("\nStep 2: Running batch evaluation (400 experiments, recording checkpoints)...")
    actual_data = run_batch_evaluation(args.base_dir, output_dir)
    
    # Save actual scores
    actual_file = output_path / "actual_scores_summary.xlsx"
    actual_data['summary'].to_excel(actual_file)
    print(f"✓ 实际总分矩阵已保存: {actual_file}")
    
    # Save actual score details (JSON)
    actual_detail_file = output_path / "actual_scores_detailed.json"
    serializable_actual = {}
    for traj_id, traj_data in actual_data['details'].items():
        serializable_actual[traj_id] = {}
        for task_name, task_info in traj_data.items():
            serializable_actual[traj_id][task_name] = {
                'checkpoint_scores': task_info.get('checkpoint_scores', []),
                'checkpoint_names': task_info.get('checkpoint_names', []),
                'total_score': task_info.get('total_score', 0),
                'error': task_info.get('error', None)
            }
    
    with open(actual_detail_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_actual, f, indent=2, ensure_ascii=False)
    print(f"✓ 实际详细得分已保存: {actual_detail_file}\n")
    
    # Step 3: Generate checkpoint-level comparison report
    print("\nStep 3: Generating checkpoint-level comparison report...")
    stats = generate_comparison_report(theoretical_data, actual_data, output_dir)
    
    print("\n✅ All steps complete!")
    print(f"\n输出文件位置: {output_path}")


if __name__ == "__main__":
    main()