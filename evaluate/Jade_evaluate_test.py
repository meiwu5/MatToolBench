"""
Jade XRD Batch Evaluation System v3
Features:
1. Generate theoretical score matrix (20 trajectories × 20 tasks) - checkpoint level
2. Automatically run 400 evaluation experiments - record each checkpoint
3. Output Excel comparison report - checkpoint-level comparison
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
import traceback
from datetime import datetime

# Import the JadeEvaluator
sys.path.append(str(Path(__file__).parent))


# ============ THEORETICAL SCORE DEFINITIONS ============

# Mapping of trajectory IDs to instructions
TRAJECTORY_INSTRUCTIONS = {
    "in1": "in1: Import 'Jade/WRT-ZSX-5.txt' using Jade",
    "in2": "in2: Open 'Jade/XRD4.xrdml' with Jade, perform peak finding with default parameters",
    "in3": "in3: Open 'Jade/XRD1.xrdml' with Jade, perform background subtraction with default parameters",
    "in4": "in4: Open 'Jade/XRD4.xrdml' with Jade, apply smoothing once",
    "in5": "in5: Open 'Jade/XRD4.xrdml' with Jade, apply smoothing once and background subtraction",
    "in6": "in6: Open Jade/XRD1.xrdml with Jade, switch x-axis from 2-theta to d-spacing, then back to 2-theta",
    "in7": "in7: Open Jade/WRT-ZSX-5.txt with Jade, select Zoom from the menu bar",
    "in8": "in8: Open Jade/WRT-ZSX-5.txt with Jade, add two peaks",
    "in9": "in9: Open Jade/XRD1.xrdml with Jade, switch x-axis from 2-theta to d-spacing, add two peaks, then switch back to 2-theta",
    "in10": "in10: Open 'Jade/XRD1.xrdml' with Jade, perform peak finding with default parameters, export the peak report to the desktop as 'WRT_peak.pid'",
    "in11": "in11: Open 'Jade/WRT-ZSX-5.txt' with Jade, perform Whole Pattern Fitting and Rietveld Refinement, save the output file locally as 'WRT_refine.raw'",
    "in12": "in12: Open 'Jade/XRD2.xrdml' with Jade, perform profile fitting, initialize then refine, and print the fitting report to the desktop as 'XRD2.pdf'",
    "in13": "in13: Open 'Jade/WRT-ZSX-5.txt' with Jade, perform peak finding, print the zoom window image to the desktop as 'WRT_window.pdf'",
    "in14": "in14: Open Jade/'XRD1.xrdml' with Jade, perform full-spectrum theta angle correction using internal standard method, print the fitting report to the desktop as 'WRT_theta.pdf'",
    "in15": "in15: Open Jade/WRT-ZSX-5.txt with Jade, calculate d-spacing and Miller indices using Calc, print the report to the desktop as 'WRT_calc.pdf'",
    "in16": "in16: Open 'Jade/WRT-ZSX-5.txt' with Jade, remove background, analyze diffraction peaks and find the best matching phase from the database, export the PDF card to the desktop as 'WRT_PDF1.txt'",
    "in17": "in17: Open 'Jade/WRT-ZSX-5.txt' with Jade, remove background, search for Fe-containing phases (possibly with O element), return the best-matching iron-based oxide or iron-containing phase, save to desktop as 'WRT_Fe.txt'",
    "in18": "in18: Open 'Jade/WRT-ZSX-5.txt' with Jade, perform profile fitting, initialize then refine, print the fitting report to the desktop as 'WRT.pdf'",
    "in19": "in19: Open 'Jade/WRT-ZSX-5.txt' with Jade, apply smoothing once, remove background, find the best 2 matching phases from the database, export PDF cards to desktop as 'PDF1.txt' and 'PDF2.txt'",
    "in20": "in20: Open 'Jade/XRD4.xrdml' with Jade, apply smoothing once, perform profile fitting, initialize then refine, print the fitting report to the desktop as 'XRD4.pdf'",
}

# Operations actually performed in each trajectory (inferred from instructions)
# Now supports main_file (primary file) and other_files (secondary file list)
TRAJECTORY_COMPLETIONS = {
    # Simple tasks
    "in1": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD2.xrdml'],  # If other files were opened during the process, add them here
        "operations": []
    },
    "in2": {
        "main_file": "XRD4.xrdml", 
        "other_files": ['XRD1.xrdml'], 
        "operations": ["peak_finding"]
    },
    "in3": {
        "main_file": "XRD1.xrdml", 
        "other_files": ['XRD3.xrdml'], 
        "operations": ["background_removal"]
    },
    "in4": {
        "main_file": "XRD4.xrdml", 
        "other_files": ['XRD1.xrdml','XRD3.xrdml'], 
        "operations": ["smoothing"]
    },
    "in5": {
        "main_file": "XRD4.xrdml", 
        "other_files": [], 
        "operations": ["smoothing", "background_removal"]
    },
    "in6": {
        "main_file": "XRD1.xrdml", 
        "other_files": [], 
        "operations": ["axis_switch"]
    },
    "in7": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD3.xrdml'], 
        "operations": ["axes_menu"]
    },
    "in8": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD3.xrdml','XRD1.xrdml'], 
        "operations": ["peak_add_two"]
    },
    
    # Medium tasks
    "in9": {
        "main_file": "XRD1.xrdml", 
        "other_files": [],  # Add here if other files were opened during this task
        "operations": ["axis_switch", "peak_add_two"]
    },
    "in10": {
        "main_file": "XRD1.xrdml", 
        "other_files": ['XRD2.xrdml',"WRT-ZSX-5.txt"], 
        "operations": ["peak_finding"], 
        "output": "WRT_peak.pid"
    },
    "in11": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD3.xrdml'], 
        "operations": ["wpf_refinement"], 
        "output": "WRT_refine.raw"
    },
    "in12": {
        "main_file": "XRD2.xrdml", 
        "other_files": ['XRD3.xrdml'], 
        "operations": ["refinement_result"], 
        "output": "XRD2.pdf"
    },
    "in13": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD2.xrdml'], 
        "operations": ["peak_finding"], 
        "output": "WRT_window.pdf"
    },
    "in14": {
        "main_file": "'XRD1.xrdml'", 
        "other_files": ['XRD2.xrdml',"WRT-ZSX-5.txt"], 
        "operations": ["theta_calibration"], 
        "output": "WRT_theta.pdf"
    },
    "in15": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD2.xrdml'], 
        "operations": ["d_spacing_calc"], 
        "output": "WRT_calc.pdf"
    },
    
    # Complex tasks
    "in16": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD2.xrdml'], 
        "operations": ["search_match","background_removal"], 
        "output": "WRT_PDF1.txt"
    },
    "in17": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD2.xrdml'], 
        "operations": ["current_chemistry", "background_removal","search_match"], 
        "output": "WRT_Fe.txt"
    },
    "in18": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD2.xrdml'], 
        "operations": ["refinement_result"], 
        "output": "WRT.pdf"
    },
    "in19": {
        "main_file": "WRT-ZSX-5.txt", 
        "other_files": ['XRD3.xrdml'], 
        "operations": ["smoothing", "background_removal", "search_match"], 
        "output": ["PDF1.txt", "PDF2.txt"]
    },
    "in20": {
        "main_file": "XRD4.xrdml", 
        "other_files": ['XRD2.xrdml',"WRT-ZSX-5.txt"], 
        "operations": ["smoothing", "refinement_result"], 
        "output": "XRD4.pdf"
    },
}


def normalize_filename(filename: str) -> str:
    """
    Normalize filename, remove extension and extra characters
    
    Args:
        filename: original filename
    
    Returns:
        Normalized filename (lowercase, no extension)
    """
    if not filename:
        return ""
    
    # Remove extension
    base = filename
    for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
        if filename.lower().endswith(ext):
            base = filename[:-len(ext)]
            break
    
    # Remove trailing dots and spaces, lowercase
    return base.rstrip('.').strip().lower()


def files_match(expected_file: str, actual_file: str) -> bool:
    """
    判断两个文件名whether matched
    
    Args:
        expected_file: expected filename
        actual_file: actual filename
    
    Returns:
        whether matched
    """
    expected_norm = normalize_filename(expected_file)
    actual_norm = normalize_filename(actual_file)
    
    if not expected_norm or not actual_norm:
        return False
    
    # Substring matching (bidirectional)
    return expected_norm in actual_norm or actual_norm in expected_norm


def calculate_checkpoint_score(check: Dict, traj_data: Dict) -> int:
    """
    Calculate theoretical score for a single checkpoint
    
    Args:
        check: checkpoint configuration
        traj_data: 轨迹数据（包含main_file, other_files和operations）
    
    Returns:
        0 or 1 (whether this checkpoint should score)
    """
    func_name = check['function']
    args = check.get('args', {})
    
    # Get all files for trajectory (primary + secondary)
    main_file = traj_data.get("main_file", "")
    other_files = traj_data.get("other_files", [])
    all_files = [main_file] + other_files if main_file else other_files
    
    traj_ops = traj_data.get("operations", [])
    
    # Checkpoint 1: file open - score if any match found in all_files
    if func_name == 'check_file_opened':
        expected_file = args['expected_filename']
        
        # Check whether matched any file
        for traj_file in all_files:
            if files_match(expected_file, traj_file):
                return 1
        
        return 0
    
    # Checkpoint 2: various operations
    elif func_name == 'check_peak_finding':
        return 1 if 'peak_finding' in traj_ops else 0
    
    elif func_name == 'check_background_removal':
        return 1 if 'background_removal' in traj_ops else 0
    
    elif func_name == 'check_smoothing':
        return 1 if 'smoothing' in traj_ops else 0
    
    elif func_name == 'check_axis_switch':
        return 1 if 'axis_switch' in traj_ops else 0
    
    elif func_name == 'check_axes_menu':
        return 1 if 'axes_menu' in traj_ops else 0
    
    elif func_name == 'check_peak_add_two':
        return 1 if 'peak_add_two' in traj_ops else 0
    
    elif func_name == 'check_wpf_refinement':
        return 1 if 'wpf_refinement' in traj_ops else 0
    
    elif func_name == 'check_refinement_result':
        return 1 if 'refinement_result' in traj_ops else 0
    
    elif func_name == 'check_smoothing_and_background':
        # This is a compound check, full score 2 points
        smooth_score = 1 if 'smoothing' in traj_ops else 0
        background_score = 1 if 'background_removal' in traj_ops else 0
        return smooth_score + background_score
    
    elif func_name == 'check_dialog_title':
        dialog_title = args['title']
        if dialog_title == 'Theta Calibration of Whole Pattern' or \
           dialog_title == 'Theta Calibration Report':
            return 1 if 'theta_calibration' in traj_ops else 0
        elif dialog_title == 'Calculate d-Spacing & Miller Indices':
            return 1 if 'd_spacing_calc' in traj_ops else 0
        elif dialog_title == 'Search/Match Display':
            return 1 if 'search_match' in traj_ops else 0
        elif dialog_title == 'Current Chemistry':
            return 1 if 'current_chemistry' in traj_ops else 0
    
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
    from jade_evaluator import TASK_CONFIGS
    
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
                
                if func_name == 'check_file_opened':
                    check_name = f"open_file:{args['expected_filename']}"
                elif func_name == 'check_dialog_title':
                    check_name = f"dialog:{args['title'][:20]}"
                elif func_name == 'check_smoothing_and_background':
                    check_name = "smooth+bg-subtraction"
                else:
                    # Remove check_ prefix
                    check_name = func_name.replace('check_', '')
                
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
    记录每个检查点的详细结果
    
    Args:
        base_dir: base directory containing in1-in20 subfolders
        output_dir: output directory (optional)
    
    Returns:
        {
            'summary': DataFrame (实际总分矩阵),
            'details': Dict[task_name][trajectory_id] = {
                'checkpoint_results': [check1_result, check2_result, ...],
                'checkpoint_scores': [0/1, 0/1, ...],
                'total_score': int
            }
        }
    """
    
    # Dynamically import JadeEvaluator
    from jade_evaluator import JadeEvaluator, TASK_CONFIGS
    
    base_path = Path(base_dir).resolve()
    if output_dir is None:
        output_dir = base_path.parent / "batch_evaluation_results"
    else:
        output_dir = Path(output_dir).resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"{'='*70}")
    print(f"Jade XRD Batch Evaluation System v3 (检查点级别)")
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
            evaluator = JadeEvaluator(str(traj_folder))
            
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


def generate_checkpoint_comparison_report(theoretical_data: Dict,
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
    
    # ========== 1. Generate checkpoint-level comparison table ==========
    print("\nGenerating checkpoint-level comparison table...")
    
    excel_file = output_path / f"checkpoint_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Sheet 1: Total score comparison (summary)
        summary_df = pd.DataFrame({
            '任务': [],
            '轨迹': [],
            '理论总分': [],
            '实际总分': [],
            '匹配': []
        })
        
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
        for task_name in sorted(theo_details[list(theo_details.keys())[0]].keys()):  # get task list from first trajectory
            rows = []
            
            for traj_id in sorted(theo_details.keys()):
                theo_info = theo_details[traj_id][task_name]
                actual_info = actual_details.get(traj_id, {}).get(task_name, {})
                
                theo_checkpoints = theo_info['checkpoint_scores']
                actual_checkpoints = actual_info.get('checkpoint_scores', [])
                checkpoint_names = theo_info['checkpoint_names']
                
                # Align checkpoint counts (use theoretical as reference)
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
    
    # ========== 2. Generate total score matrix comparison Excel ==========
    excel_summary = output_path / f"summary_matrices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(excel_summary, engine='openpyxl') as writer:
        theo_summary.to_excel(writer, sheet_name='理论总分矩阵')
        actual_summary.to_excel(writer, sheet_name='实际总分矩阵')
        
        diff_matrix = actual_summary - theo_summary
        diff_matrix.to_excel(writer, sheet_name='差异矩阵')
        
        accuracy_matrix = calculate_accuracy_matrix(theo_summary, actual_summary)
        accuracy_matrix.to_excel(writer, sheet_name='准确率(%)')
    
    print(f"✓ 总分矩阵对比已保存: {excel_summary}")
    
    # ========== 3. Print statistics ==========
    print(f"\n{'='*70}")
    print(f"评估统计")
    print(f"{'='*70}")
    stats = calculate_statistics(theo_summary, actual_summary, theo_details, actual_details)
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
    
    parser = argparse.ArgumentParser(description='Jade XRD Batch Evaluation System v3 (检查点级别)')
    parser.add_argument('--base_dir', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\pyautogui\a11y_tree\gpt-5\0\jade',
                       help='包含in1-in20的基础目录')
    parser.add_argument('--output_dir', type=str, default=None,
                       help='输出目录（默认为base_dir的父目录）')
    parser.add_argument('--theoretical_only', action='store_true',
                       help='仅生成理论得分矩阵（不运行实际评估）')
    
    args = parser.parse_args()
    
    # Step 1: Generate theoretical scores (checkpoint level)
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
    # Convert to serializable format
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
    
    # Step 2: Run batch evaluation (checkpoint level)
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
    stats = generate_checkpoint_comparison_report(theoretical_data, actual_data, output_dir)
    
    print("\n✅ All steps complete!")
    print(f"\n输出文件位置: {output_path}")


if __name__ == "__main__":
    main()