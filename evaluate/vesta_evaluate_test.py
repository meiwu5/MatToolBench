"""
VESTA Batch Evaluation System
For running 400 (20×20) evaluation experiments in batch and generating comparison reports
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Import the VESTAEvaluator
sys.path.append(str(Path(__file__).parent))


# ============ TRAJECTORY COMPLETION DEFINITIONS ============

TRAJECTORY_COMPLETIONS = {
    "in1": {
        "opened_file": "mp-13_Fe.cif",
        "operations": ["standard_orientation"]
    },
    
    "in2": {
        "opened_file": "mp-30_Cu.cif",
        "operations": ["rotation_90_up"]
    },
    
    "in3": {
        "opened_file": "mp-66_C.cif",
        "operations": ["translation_right_400"]
    },
    
    "in4": {
        "opened_file": "mp-81_Au.cif",
        "operations": ["style_wireframe"]
    },
    
    "in5": {
        "opened_file": "mp-804_GaN.cif",
        "operations": ["atom_info_Ga"]
    },
    
    "in6": {
        "opened_file": "mp-804_GaN.cif",
        "operations": ["atom_info_N", "atom_deletion"]
    },
    
    "in7": {
        "opened_file": "mp-13_Fe.cif",
        "operations": ["bond_display"]
    },
    
    "in8": {
        "opened_file": "mp-804_GaN.cif",
        "operations": ["zoom_100","atom_info_N"]
    },
    
    "in9": {
        "opened_file": "mp-149_Si.cif",
        "operations": ["atom_deletion"]
    },
    
    "in10": {
        "opened_file": "mp-66_C.cif",
        "operations": ["dialog_properties", "axes_toggle"]
    },
    
    "in11": {
        "opened_file": "mp-2534_GaAs.cif",
        "operations": ["atom_deletion"]
    },
    
    "in12": {
        "opened_file": "mp-1265_MgO.cif",
        "operations": ["dialog_properties", "check_properties_1.5"]
    },
    
    "in13": {
        "opened_file": "mp-804_GaN.cif",
        "operations": ["atom_info_N","style_polyhedral", "dialog_properties","axes_toggle", "polyhedral_style_4"]
    },
    
    "in14": {
        "opened_file": "mp-1265_MgO.cif",
        "operations": ["dialog_orientation", "orientation_vector_3_3_3"]
    },
    
    "in15": {
        "opened_file": "mp-1265_MgO.cif",
        "operations": ["dialog_lattice planes", "lattice_plane_1_2_2"]
    },
    
    "in16": {
        "opened_file": "mp-1143",
        "operations": ["dialog_boundary", "boundary_y_max_2", "boundary_z_max_2"]
    },
    
    "in17": {
        "opened_file": "mp-804_GaN.cif",
        "operations": ["atom_info_N","dialog_boundary", "dialog_properties","boundary_y_max_2", "style_polyhedral", "polyhedral_style_3"]
    },
    
    "in18": {
        "opened_file": "mp-22862_NaCl.cif",
        "operations": [
            "dialog_bonds", 
            "bonds_cleared", 
            "dialog_edit_data",
            "atom_coords_Na_1.0_1.0_1.0",
            "atom_coords_Cl_1.0_0.5_0.5"
        ]
    },
    
    "in19": {
        "opened_file": "mp-149_Si.cif",
        "operations": [
            "dialog_boundary",
            "boundary_x_max_2", 
            "boundary_y_max_2", 
            "boundary_z_max_2",
            "dialog_properties",
            "radius_0.8",
            "radius_0.15"
        ]
    },
    
    "in20": {
        "opened_file": "mp-804_GaN.cif",
        "operations": [
            "atom_info_N",
            "dialog_boundary",
            "boundary_x_min_-0.5",
            "boundary_x_max_1.5",
            "boundary_y_min_-0.5",
            "boundary_y_max_1.5",
            "dialog_lattice planes",
            "lattice_planes_count_2"
        ]
    }
}


# ============ THEORETICAL SCORE CALCULATION ============

def calculate_checkpoint_score(check: Dict, traj_data: Dict) -> int:
    """
    Calculate theoretical score for a single checkpoint
    
    Args:
        check: checkpoint configuration {'function': '...', 'args': {...}}
        traj_data: trajectory data {'opened_file': '...', 'operations': [...]}

    Returns:
        Score this checkpoint should receive
    """
    func_name = check['function']
    args = check.get('args', {})
    
    opened_file = traj_data.get('opened_file', '')
    traj_ops = traj_data.get('operations', [])
    
    # === Checkpoint 1: File open ===
    if func_name == 'check_file_opened':
        expected_file = args.get('expected_filename', '')
        # Remove extension for comparison
        expected_base = expected_file.replace('.cif', '').replace('.vesta', '')
        opened_base = opened_file.replace('.cif', '').replace('.vesta', '')
        
        if expected_base.lower() in opened_base.lower() or opened_base.lower() in expected_base.lower():
            return 1
        return 0
    
    # === Checkpoint 2: Standard orientation ===
    elif func_name == 'check_standard_orientation':
        return 1 if 'standard_orientation' in traj_ops else 0
    
    # === Checkpoint 3: Rotate 90 degrees ===
    elif func_name == 'check_rotation_90_up':
        return 1 if 'rotation_90_up' in traj_ops else 0
    
    # === Checkpoint 4: Translation ===
    elif func_name == 'check_translation':
        direction = args.get('direction', 'right')
        units = args.get('units', 400)
        op_name = f'translation_{direction}_{units}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 5: Style switching ===
    elif func_name == 'check_style_change':
        target_style = args.get('target_style', '').lower()
        op_name = f'style_{target_style}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 6: Atom info dialog ===
    elif func_name == 'check_atom_info_dialog':
        atom_type = args.get('atom_type', '')
        op_name = f'atom_info_{atom_type}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 7: Atom deletion ===
    elif func_name == 'check_atom_deletion':
        return 1 if 'atom_deletion' in traj_ops else 0
    
    # === Checkpoint 8: Bond display ===
    elif func_name == 'check_bond_display':
        return 1 if 'bond_display' in traj_ops else 0
    
    # === Checkpoint 9: Zoom ===
    elif func_name == 'check_zoom':
        return 1 if 'zoom_100' in traj_ops else 0
    
    # === Checkpoint 10: Axis switching ===
    elif func_name == 'check_axes_toggle':
        return 1 if 'axes_toggle' in traj_ops else 0
    
    # === Checkpoint 11: Dialog open ===
    elif func_name == 'check_dialog_opened':
        dialog_title = args.get('title_keyword', '').lower()
        op_name = f'dialog_{dialog_title}'
        
        # Base score: dialog opened
        score = 1 if op_name in traj_ops else 0
        
        # Extra score: field check
        field_checks = args.get('field_checks', {})
        if field_checks and score > 0:
            for field_name, value in field_checks.items():
                field_op = f'{field_name.lower()}_{value}'
                if field_op in traj_ops:
                    score += 1
        
        return score

    elif func_name == 'check_properties_field':
        value  = args.get('expected_value','')
        op_name = f'check_properties_{value}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 12: Polyhedral style ===
    elif func_name == 'check_polyhedral_style':
        style_num = args.get('style_number', 0)
        op_name = f'polyhedral_style_{style_num}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 13: Orientation vector ===
    elif func_name == 'check_orientation_vector':
        expected_values = args.get('expected_values', [])
        vec_str = '_'.join(map(str, expected_values))
        op_name = f'orientation_vector_{vec_str}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 14: Crystal plane ===
    elif func_name == 'check_lattice_plane':
        expected_hkl = args.get('expected_hkl', [])
        hkl_str = '_'.join(map(str, expected_hkl))
        op_name = f'lattice_plane_{hkl_str}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 15: Boundary settings ===
    elif func_name == 'check_boundary_settings':
        score = 0
        for key, value in args.items():
            op_name = f'boundary_{key}_{value}'
            if op_name in traj_ops:
                score += 1
        return score
    
    # === Checkpoint 16: Bonds cleared ===
    elif func_name == 'check_bonds_cleared':
        return 1 if 'bonds_cleared' in traj_ops else 0
    
    # === Checkpoint 17: Atom coordinates ===
    elif func_name == 'check_atom_coordinates_in_edit_data':
        atom_label = args.get('atom_label', '')
        coords = args.get('expected_coords', [])
        coords_str = '_'.join(map(str, coords))
        op_name = f'atom_coords_{atom_label}_{coords_str}'
        return 1 if op_name in traj_ops else 0
    
    # === Checkpoint 18: Multiple crystal planes ===
    elif func_name == 'check_multiple_lattice_planes':
        count = args.get('expected_count', 0)
        op_name = f'lattice_planes_count_{count}'
        return 1 if op_name in traj_ops else 0
    
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
    from vesta_evaluator import TASK_CONFIGS
    
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
                    file = args.get('expected_filename', '')
                    check_name = f"open:{file[:15]}"
                elif func_name == 'check_dialog_opened':
                    check_name = f"dialog:{args.get('title_keyword', '')[:15]}"
                else:
                    # Remove check_ prefix
                    check_name = func_name.replace('check_', '').replace('_', ' ')[:20]
                
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


def run_batch_evaluation(base_dir: str, output_dir: str = None,
                        reference_image: str = None,
                        rotation_90_ref: str = None,
                        translation_ref: str = None,
                        zoom_100_ref: str = None) -> Dict[str, Any]:
    """
    批量运行评估实验（20轨迹 × 20任务 = 400个实验）
    
    Args:
        base_dir: base directory containing in1-in20 subfolders
        output_dir: output directory (optional)
        reference_image: 标准取向参考图片
        rotation_90_ref: 旋转90度参考图片
        translation_ref: 平移参考图片
        zoom_100_ref: 缩放100%参考图片
    
    Returns:
        {
            'summary': DataFrame (实际总分矩阵),
            'details': Dict[task_name][trajectory_id] = {...}
        }
    """
    
    # Import VESTAEvaluator
    from vesta_evaluator import VESTAEvaluator, TASK_CONFIGS
    
    base_path = Path(base_dir).resolve()
    if output_dir is None:
        output_dir = base_path.parent / "batch_evaluation_results"
    else:
        output_dir = Path(output_dir).resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"{'='*70}")
    print(f"VESTA Batch Evaluation System")
    print(f"{'='*70}")
    print(f"基础目录: {base_path}")
    print(f"输出目录: {output_dir}")
    if reference_image:
        print(f"标准取向参考图: {reference_image}")
    if rotation_90_ref:
        print(f"旋转90度参考图: {rotation_90_ref}")
    if translation_ref:
        print(f"平移参考图: {translation_ref}")
    if zoom_100_ref:
        print(f"缩放100%参考图: {zoom_100_ref}")
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
            print(f"  → Initialize the evaluator...")
            
            # Create evaluator
            evaluator = VESTAEvaluator(
                str(traj_folder),
                reference_image_path=reference_image,
                rotation_90_reference=rotation_90_ref,
                translation_reference=translation_ref,
                zoom_100_reference=zoom_100_ref
            )
            
            print(f"  ✓ Evaluator initialized")
            print(f"  ✓ Screenshot count: {len(evaluator.screenshots)}")
            
            # Iterate over all tasks
            for task_idx, (task_name, task_checks) in enumerate(TASK_CONFIGS.items(), 1):
                try:
                    print(f"\n  [{task_idx}/20] 测试任务: {task_name}")
                    print(f"      Checkpoint count: {len(task_checks)}")
                    
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
                    
                    print(f"      ✓ Score: {total_score}/{result['max_score']}")
                    print(f"      ✓ Checkpoint scores: {checkpoint_scores}")
                    
                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")
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
            import traceback
            traceback.print_exc()
            
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
    
    parser = argparse.ArgumentParser(description='VESTA Batch Evaluation System')
    parser.add_argument('--base_dir', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\pyautogui\a11y_tree\gpt-5\0\vesta',
                       help='包含in1-in20的基础目录')
    parser.add_argument('--output_dir', type=str, default=r'D:\ChemLLM\science_agent\results\pyautogui\a11y_tree\gpt-5\0\vesta\test',
                       help='输出目录（默认为base_dir的父目录）')
    parser.add_argument('--theoretical_only', action='store_true',
                       help='仅生成理论得分矩阵（不运行实际评估）')
    parser.add_argument('--reference', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\label\vesta\orientation.png',
                       help='标准取向参考图片路径')
    parser.add_argument('--rotation-90-ref', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\label\vesta\rotate.png',
                       help='旋转90度参考图片路径',
                       dest='rotation_90_ref')
    parser.add_argument('--translation-ref', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\label\vesta\translate.png',
                       help='平移参考图片路径',
                       dest='translation_ref')
    parser.add_argument('--zoom-100-ref', type=str, 
                       default=r'D:\ChemLLM\science_agent\results\label\vesta\zoom.png',
                       help='缩放100%参考图片路径',
                       dest='zoom_100_ref')
    
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
    actual_data = run_batch_evaluation(
        args.base_dir, 
        output_dir,
        reference_image=args.reference,
        rotation_90_ref=args.rotation_90_ref,
        translation_ref=args.translation_ref,
        zoom_100_ref=args.zoom_100_ref
    )
    
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