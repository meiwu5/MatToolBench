"""
Material Studio Batch Evaluation System (Fixed)
Fix:
1. check_field_value theoretical logic - fix matching when field_name=None
2. check_text_keyword theoretical logic - enhanced opened_file matching
3. TRAJECTORY_COMPLETIONS - added missing operations
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# ============ TRAJECTORY ID MAPPING ============

TRAJECTORY_ID_MAPPING = {
    "in1": "in1",
    "in2": "in2",
    "in3": "in3",
    "in4": "in4",
    "in5": "in5",
    "in6": "in6",
    "in7": "in7",
    "in8": "in8",
    "in9": "in9",
    "in10": "in10",
    "in11": "in11",
    "in12": "in12",
    "in13": "in13",
    "in14": "in14",
    "in15": "in15",
    "in16": "in16",
    "in17": "in17",
    "in18": "in18",
    "in19": "in19",
    "in20": "in20"
}

DISPLAY_NAME_TO_ID = {v: k for k, v in TRAJECTORY_ID_MAPPING.items()}

# ============ TRAJECTORY COMPLETION DEFINITIONS (Fixed) ============
# Fix: added missing operations such as document_3d_atomistic

TRAJECTORY_COMPLETIONS = {
    "in1": {
        "opened_file": "task 1",
        "operations": ["file_opened"]
    },
    
    "in2": {
        "opened_file": "untitled",
        "operations": ["untitled_opened", "document_3d_atomistic"]
    },
    
    "in3": {
        "opened_file": "urea",
        "operations": ["file_opened", "untitled_opened", "urea_opened", "display_style_dialog", "display_style_ball_stick"]
    },
    
    "in4": {
        "opened_file": "Fe",
        "operations": ["file_opened", "untitled_opened", "fe_opened", "display_options_dialog"]
    },
    
    "in5": {
        "opened_file": "LiF",
        "operations": ["file_opened", "untitled_opened", "lif_opened", "atoms_deleted"]
    },
    
    "in6": {
        "opened_file": "untitled",
        "operations": [ "untitled_opened","document_3d_atomistic", "homopolymer_dialog", "repeat_unit_ethylene", "chain_length_20","tacticity_isotactic"]
    },
    
    "in7": {
        "opened_file": "untitled",
        "operations": [ "untitled_opened", "document_3d_atomistic", "build_crystal_dialog", "lattice_a_4910", "lattice_alpha_70","space_group_p1"]
    },
    
    "in8": {
        "opened_file": "untitled",
        "operations": [ "untitled_opened", "document_3d_atomistic", "add_atoms_dialog"]
    },
    
    "in9": {
        "opened_file": "Al2O3",
        "operations": [ "untitled_opened", "al2o3_opened", "atoms_hidden"]
    },
    
    # Medium tasks
    "in10": {
        "opened_file": "untitled",
        "operations": [ "untitled_opened", "document_3d_atomistic", "build_crystal_dialog", "space_group_p3221"]
    },
    
    "in11": {
        "opened_file": "untitled",
        "operations": ["untitled_opened", "document_3d_atomistic", "build_crystal_dialog", "space_group_p1"]
    },
    
    "in12": {
        "opened_file": "urea",
        "operations": ["file_opened", "untitled_opened", "urea_opened", "label_dialog", "font_helvetica"]
    },
    
    "in13": {
        "opened_file": "Novolac4",
        "operations": ["file_opened", "untitled_opened", "novolac4_opened", "build_surface_dialog"]
    },
    
    "in14": {
        "opened_file": "Si",
        "operations": ["file_opened", "untitled_opened", "si_opened", "supercell_dialog", "supercell_range"]
    },
    
    "in15": {
        "opened_file": "Fe",
        "operations": ["file_opened", "untitled_opened", "fe_opened", "cleave_surface_dialog", "miller_indices_5_5_5"]
    },
    
    # Complex tasks
    "in16": {
        "opened_file": "untitled",
        "operations": [
            "untitled_opened",
            "document_3d_atomistic",
            "add_atoms_dialog",
            "atom_o_added",
            "atom_h_added",
            "display_style_dialog",
            "display_style_ball_stick"
        ]
    },
    
    "in17": {
        "opened_file": "TMOS",
        "operations": [
            "file_opened",
            "untitled_opened",
            "tmos_opened",
            "add_atoms_dialog",
            "atom_h_x_2.0",
            "calculate_close_contacts"
        ]
    },
    
    "in18": {
        "opened_file": "untitled",
        "operations": [
            "untitled_opened",
            "homopolymer_dialog",
            "repeat_unit_propylene",
            "chain_length_40",
            "build_crystal_dialog",
            "space_group_5_c2",  # Note: "5 C2" is the full name of the space group
            "lattice_a_15",
            "tacticity_isotactic",
            "space_group_p1"
        ]
    },
    
    "in19": {
        "opened_file": "untitled",
        "operations": [
            "untitled_opened",
            "repeat_unit_propylene",
            "homopolymer_dialog",
            "library_acrylates",
            "tacticity_isotactic",
            "chain_length_40"
        ]
    },
    
    "in20": {
        "opened_file": "urea",
        "operations": [
            "file_opened",
            "untitled_opened",
            "urea_opened",
            "charges_dialog",
            "method_divide_and_conquer"
        ]
    }
}


# ============ THEORETICAL SCORE CALCULATION (Fixed) ============

def calculate_checkpoint_score(check: Dict, traj_data: Dict) -> int:
    """
    Calculate theoretical score for a single checkpoint (Fixed)
    
    Fix:
    1. check_field_value: fix numeric matching when field_name=None
    2. check_text_keyword: enhanced matching logic for opened_file
    """
    func_name = check['function']
    args = check.get('args', {})
    
    opened_file = traj_data.get('opened_file', '')
    traj_ops = traj_data.get('operations', [])
    
    # === Checkpoint 1: File open ===
    if func_name == 'check_file_in_title':
        expected_file = args.get('expected_filename', '')
        if opened_file is None:
            return 0
        
        expected_base = expected_file.replace('.stp', '').replace('.xsd', '').lower()
        opened_base = opened_file.lower() if opened_file else ''
        
        if expected_base == opened_base or expected_base in opened_base or opened_base in expected_base:
            return 1
        
        if expected_base == 'untitled':
            if 'untitled_opened' in traj_ops or opened_base == 'untitled':
                return 1
        
        return 0
    
    # === Checkpoint 2: Dialog title ===
    elif func_name == 'check_dialog_title':
        expected_title = args.get('expected_title', '').lower().replace(' ', '_')
        dialog_op = f"{expected_title}_dialog"
        return 1 if dialog_op in traj_ops else 0
    
    # === Checkpoint 3: Keyword check (Fixed) ===
    elif func_name == 'check_text_keyword':
        keyword = args.get('keyword', '').lower().replace(' ', '_').replace('-', '_')
        forbidden = args.get('forbidden_keywords', [])
        
        # Multiple possible keyword matches
        keyword_ops = [
            f"document_{keyword}",
            f"{keyword}_opened",
            f"{keyword}_dialog",
            f"method_{keyword}",  # for method-type keywords
            keyword
        ]
        
        if keyword == 'hide':
            keyword_ops.extend(['atoms_hidden', 'hidden', 'hide'])
        
        # Method 1: full match operations
        found_in_ops = any(op in traj_ops for op in keyword_ops)
        
        # Method 2: substring match operations (handle hyphen variants etc.)
        if not found_in_ops:
            for op in traj_ops:
                op_lower = op.lower().replace('-', '_')
                if keyword in op_lower:
                    found_in_ops = True
                    break
        
        # Method 3: check opened_file (do not add auto-generated content like 3D atomistic)
        found_in_file = False
        if opened_file:
            opened_lower = opened_file.lower().replace(' ', '').replace('_', '').replace('-', '')
            keyword_clean = keyword.replace('_', '').replace('-', '')
            
            # Only match chemical formulas or filenames, not document types
            if keyword_clean not in ['3d', 'atomistic', '3datomistic', 'document']:
                if keyword_clean in opened_lower or opened_lower in keyword_clean:
                    found_in_file = True
        
        found = found_in_ops or found_in_file
        
        # Check forbidden words
        has_forbidden = False
        for fb in forbidden:
            fb_clean = fb.lower().replace(' ', '_').replace('-', '_')
            for op in traj_ops:
                op_clean = op.lower().replace('-', '_')
                if fb_clean in op_clean:
                    has_forbidden = True
                    break
            if has_forbidden:
                break
        
        return 1 if (found and not has_forbidden) else 0
    

    # === Checkpoint 4: Field value check (Fixed) ===
    elif func_name == 'check_field_value':
        dialog_title = args.get('dialog_title', '').lower().replace(' ', '_')
        field_name = args.get('field_name')
        expected_value = args.get('expected_value')
        alternative_values = args.get('alternative_values', [])
        
        traj_ops_lower = [op.lower() for op in traj_ops]
        
        dialog_op = f"{dialog_title}_dialog"
        if dialog_op not in traj_ops_lower:
            return 0
        
        all_values = [expected_value] + (alternative_values if alternative_values else [])
        
        for value in all_values:
            # Keep original value, only lowercase for case-insensitive matching
            value_lower = str(value).lower()
            
            if field_name:
                # Has field name: generate possible operation names
                field_clean = field_name.lower().replace(' ', '_')
                # Try multiple possible formats
                possible_ops = [
                    f"{field_clean}_{value_lower}",
                    f"{field_clean}_{value_lower.replace(' ', '_')}"
                ]
            else:
                # No field name: check value directly
                possible_ops = [
                    value_lower,
                    value_lower.replace(' ', '_')
                ]
            
            # Method 1: full match
            for op_name in possible_ops:
                if op_name in traj_ops_lower:
                    return 1
            
            # # Method 2: substring matching (check if value appears in any operation)
            for op_lower in traj_ops_lower:
                # Directly check if original value_lower is in operation
                if value_lower in op_lower:
                    return 1
                # Also check the version with spaces replaced by underscores
                value_with_underscore = value_lower.replace(' ', '_')
                if value_with_underscore in op_lower:
                    return 1
        
        return 0
    
    # === Checkpoint 5: Visual similarity ===
    elif func_name == 'check_visual_similarity':
        reference_key = args.get('reference_key', '').lower()
        
        # Fix: each visual reference must satisfy multiple conditions simultaneously
        if reference_key == 'ball_stick':
            # Urea ball-and-stick model: requires both display_style_ball_stick and urea
            return 1 if ('display_style_ball_stick' in traj_ops and 
                        'urea_opened' in traj_ops) else 0
        
        elif reference_key == 'h2o':
            # H2O: requires both O and H atoms added and ball-and-stick model set
            return 1 if ('atom_o_added' in traj_ops and 
                        'atom_h_added' in traj_ops and
                        'display_style_ball_stick' in traj_ops) else 0
        
        elif reference_key == 'lif_deleted':
            return 1 if 'atoms_deleted' in traj_ops else 0
        
        elif reference_key == 'al2o3_hidden':
            return 1 if 'atoms_hidden' in traj_ops else 0
        
        return 0
    
    # === Checkpoint 6: Multi-field check ===
    elif func_name == 'check_multiple_fields':
        dialog_title = args.get('dialog_title', '').lower().replace(' ', '_')
        field_checks = args.get('field_checks', {})
        
        traj_ops_lower = [op.lower() for op in traj_ops]
        
        dialog_op = f"{dialog_title}_dialog"
        if dialog_op not in traj_ops_lower:
            return 0
        
        score = 0
        for field_name, expected_value in field_checks.items():
            field_clean = field_name.lower().replace(' ', '_')
            value_str = str(expected_value).lower().replace(' ', '_')
            op_name = f"{field_clean}_{value_str}"
            
            if op_name in traj_ops_lower:
                score += 1
            else:
                # Substring matching
                for op_lower in traj_ops_lower:
                    if value_str in op_lower:
                        score += 1
                        break
        
        total_fields = len(field_checks)
        return 1 if score == total_fields else 0
    
    return 0


def generate_theoretical_scores_detailed(task_configs: Dict) -> Dict[str, Any]:
    """
    生成详细的理论得分矩阵（包含每个检查点的得分）
    """
    
    folder_ids = [f"in{i}" for i in range(1, 21)]
    tasks = list(task_configs.keys())
    
    summary_matrix = pd.DataFrame(0, index=folder_ids, columns=tasks)
    detailed_scores = {}
    
    for folder_id in folder_ids:
        display_name = TRAJECTORY_ID_MAPPING.get(folder_id)
        if not display_name or display_name not in TRAJECTORY_COMPLETIONS:
            continue
            
        traj_data = TRAJECTORY_COMPLETIONS[display_name]
        detailed_scores[folder_id] = {}
        
        for task_name, task_checks in task_configs.items():
            checkpoint_scores = []
            checkpoint_names = []
            
            for check_idx, check in enumerate(task_checks):
                score = calculate_checkpoint_score(check, traj_data)
                checkpoint_scores.append(score)
                
                # Generate checkpoint names
                func_name = check['function']
                args = check.get('args', {})
                
                if func_name == 'check_file_in_title':
                    file = args.get('expected_filename', '')
                    check_name = f"open:{file[:15]}"
                elif func_name == 'check_dialog_title':
                    check_name = f"dialog:{args.get('expected_title', '')[:15]}"
                elif func_name == 'check_text_keyword':
                    check_name = f"keyword:{args.get('keyword', '')[:15]}"
                elif func_name == 'check_field_value':
                    field = args.get('field_name', 'N/A')
                    value = args.get('expected_value', '')
                    check_name = f"field:{field}={value}"[:20]
                elif func_name == 'check_visual_similarity':
                    check_name = f"visual:{args.get('reference_key', '')[:10]}"
                else:
                    check_name = func_name.replace('check_', '').replace('_', ' ')[:20]
                
                checkpoint_names.append(f"CP{check_idx+1}:{check_name}")
            
            detailed_scores[folder_id][task_name] = {
                'checkpoint_scores': checkpoint_scores,
                'checkpoint_names': checkpoint_names,
                'total_score': sum(checkpoint_scores),
                'display_name': display_name
            }
            
            summary_matrix.loc[folder_id, task_name] = sum(checkpoint_scores)
    
    return {
        'summary': summary_matrix,
        'details': detailed_scores
    }


def run_batch_evaluation(base_dir: str, output_dir: str = None,
                        reference_images: Dict[str, str] = None) -> Dict[str, Any]:
    """Run evaluation experiments in batch"""
    
    sys.path.insert(0, str(Path(__file__).parent))
    from ms_evaluator import MSEvaluator, TASK_CONFIGS
    
    base_path = Path(base_dir).resolve()
    if output_dir is None:
        output_dir = base_path.parent / "batch_evaluation_results"
    else:
        output_dir = Path(output_dir).resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"{'='*70}")
    print(f"Material Studio 批量评估系统")
    print(f"{'='*70}")
    print(f"基础目录: {base_path}")
    print(f"输出目录: {output_dir}")
    if reference_images:
        print(f"参考图片数量: {len(reference_images)}")
    print(f"{'='*70}\n")
    
    folder_ids = [f"in{i}" for i in range(1, 21)]
    tasks = list(TASK_CONFIGS.keys())
    
    actual_scores_summary = pd.DataFrame(0.0, index=folder_ids, columns=tasks)
    actual_scores_detailed = {}
    error_log = []
    
    for folder_id in folder_ids:
        traj_folder = base_path / folder_id
        display_name = TRAJECTORY_ID_MAPPING.get(folder_id, folder_id)
        
        if not traj_folder.exists():
            print(f"⚠️  警告: 轨迹文件夹不存在: {traj_folder}")
            error_log.append(f"{folder_id} ({display_name}): folder does not exist")
            
            actual_scores_detailed[folder_id] = {}
            for task_name in tasks:
                actual_scores_detailed[folder_id][task_name] = {
                    'checkpoint_results': [],
                    'checkpoint_scores': [],
                    'checkpoint_names': [],
                    'total_score': 0,
                    'error': '文件夹不存在',
                    'display_name': display_name
                }
            continue
        
        print(f"\n{'='*70}")
        print(f"正在处理: {folder_id} ({display_name})")
        print(f"{'='*70}")
        
        actual_scores_detailed[folder_id] = {}
        
        try:
            print(f"  → Initialize the evaluator...")
            
            evaluator = MSEvaluator(
                str(traj_folder),
                reference_images=reference_images
            )
            
            print(f"  ✓ Evaluator initialized")
            print(f"  ✓ Screenshot count: {len(evaluator.screenshots)}")
            
            for task_idx, (task_name, task_checks) in enumerate(TASK_CONFIGS.items(), 1):
                try:
                    print(f"\n  [{task_idx}/{len(tasks)}] 测试任务: {task_name}")
                    print(f"      Checkpoint count: {len(task_checks)}")
                    
                    result = evaluator.evaluate_task(task_name, task_checks)
                    
                    checkpoint_results = result['checks']
                    checkpoint_scores = [check['score'] for check in checkpoint_results]
                    total_score = sum(checkpoint_scores)
                    
                    actual_scores_detailed[folder_id][task_name] = {
                        'checkpoint_results': checkpoint_results,
                        'checkpoint_scores': checkpoint_scores,
                        'checkpoint_names': [
                            f"CP{i+1}:{check['function'].replace('check_', '')}" 
                            for i, check in enumerate(checkpoint_results)
                        ],
                        'total_score': total_score,
                        'display_name': display_name
                    }
                    
                    actual_scores_summary.loc[folder_id, task_name] = total_score
                    
                    print(f"      ✓ Score: {total_score}/{result['max_score']}")
                    print(f"      ✓ Checkpoint scores: {checkpoint_scores}")
                    
                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")
                    error_log.append(f"{folder_id} ({display_name}) - {task_name}: {str(e)}")
                    
                    actual_scores_detailed[folder_id][task_name] = {
                        'checkpoint_results': [],
                        'checkpoint_scores': [],
                        'checkpoint_names': [],
                        'total_score': 0,
                        'error': str(e),
                        'display_name': display_name
                    }
                    continue
        
        except Exception as e:
            print(f"❌ 轨迹 {folder_id} ({display_name}) 初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            error_log.append(f"{folder_id} ({display_name}): initialization failed - {str(e)}")
            for task_name in tasks:
                actual_scores_detailed[folder_id][task_name] = {
                    'checkpoint_results': [],
                    'checkpoint_scores': [],
                    'checkpoint_names': [],
                    'total_score': 0,
                    'error': f"Trajectory initialization failed: {str(e)}",
                    'display_name': display_name
                }
            continue
    
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
    """Generate checkpoint-level comparison report"""
    
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
            for folder_id in theo_summary.index:
                theo_score = theo_summary.loc[folder_id, task_name]
                actual_score = actual_summary.loc[folder_id, task_name]
                match = '✓' if abs(theo_score - actual_score) < 0.01 else '✗'
                
                display_name = TRAJECTORY_ID_MAPPING.get(folder_id, folder_id)
                
                rows.append({
                    '任务': task_name,
                    '轨迹ID': folder_id,
                    '轨迹名': display_name,
                    '理论总分': theo_score,
                    '实际总分': actual_score,
                    '差异': actual_score - theo_score,
                    '匹配': match
                })
        
        summary_df = pd.DataFrame(rows)
        summary_df.to_excel(writer, sheet_name='总分对比', index=False)
        
        # Sheet 2-N: Checkpoint detail comparison for each task
        for task_name in sorted(theo_details[list(theo_details.keys())[0]].keys()):
            rows = []
            
            for folder_id in sorted(theo_details.keys()):
                theo_info = theo_details[folder_id][task_name]
                actual_info = actual_details.get(folder_id, {}).get(task_name, {})
                
                theo_checkpoints = theo_info['checkpoint_scores']
                actual_checkpoints = actual_info.get('checkpoint_scores', [])
                checkpoint_names = theo_info['checkpoint_names']
                
                display_name = theo_info.get('display_name', TRAJECTORY_ID_MAPPING.get(folder_id, folder_id))
                
                if len(actual_checkpoints) < len(theo_checkpoints):
                    actual_checkpoints.extend([0] * (len(theo_checkpoints) - len(actual_checkpoints)))
                
                for idx, (cp_name, theo_score, actual_score) in enumerate(
                    zip(checkpoint_names, theo_checkpoints, actual_checkpoints)
                ):
                    match = '✓' if abs(theo_score - actual_score) < 0.01 else '✗'
                    
                    rows.append({
                        '轨迹ID': folder_id,
                        '轨迹名': display_name,
                        'checkpoint': f"CP{idx+1}",
                        '检查内容': cp_name,
                        '理论得分': theo_score,
                        '实际得分': actual_score,
                        'whether matched': match,
                        '差异': actual_score - theo_score
                    })
            
            df = pd.DataFrame(rows)
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
                accuracy_matrix.loc[row, col] = 100.0 if abs(actual) < 0.01 else 0.0
            else:
                accuracy_matrix.loc[row, col] = (actual / theoretical) * 100
    
    return accuracy_matrix


def calculate_statistics(theo_summary: pd.DataFrame,
                         actual_summary: pd.DataFrame,
                         theo_details: Dict,
                         actual_details: Dict) -> Dict[str, Any]:
    """Calculate statistics"""
    
    total_tests = len(theo_summary.index) * len(theo_summary.columns)
    diff_matrix = actual_summary - theo_summary
    perfect_matches = (abs(diff_matrix) < 0.01).sum().sum()
    
    total_checkpoints = 0
    checkpoint_matches = 0
    
    for traj_id in theo_details.keys():
        for task_name in theo_details[traj_id].keys():
            theo_info = theo_details[traj_id][task_name]
            actual_info = actual_details.get(traj_id, {}).get(task_name, {})
            
            theo_checkpoints = theo_info['checkpoint_scores']
            actual_checkpoints = actual_info.get('checkpoint_scores', [])
            
            if len(actual_checkpoints) < len(theo_checkpoints):
                actual_checkpoints.extend([0] * (len(theo_checkpoints) - len(actual_checkpoints)))
            
            for theo_score, actual_score in zip(theo_checkpoints, actual_checkpoints):
                total_checkpoints += 1
                if abs(theo_score - actual_score) < 0.01:
                    checkpoint_matches += 1
    
    stats = {
        '总测试数(任务级)': total_tests,
        '完全匹配数(任务级)': int(perfect_matches),
        'task_match_rate(%)': f"{(perfect_matches / total_tests * 100):.1f}",
        '高估数(任务级)': int((diff_matrix > 0.01).sum().sum()),
        '低估数(任务级)': int((diff_matrix < -0.01).sum().sum()),
        '总检查点数': total_checkpoints,
        '检查点匹配数': checkpoint_matches,
        'checkpoint_match_rate(%)': f"{(checkpoint_matches / total_checkpoints * 100):.1f}" if total_checkpoints > 0 else "0.0",
    }
    
    return stats


def main():
    """Main function: generate theoretical scores + run batch evaluation + generate comparison report"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Material Studio Batch Evaluation System (Fixed)')
    parser.add_argument('--base_dir', type=str, 
                       required=True,
                       help='包含任务文件夹的基础目录')
    parser.add_argument('--output_dir', type=str, 
                       default=None,
                       help='输出目录（默认为base_dir/batch_evaluation_results）')
    parser.add_argument('--theoretical_only', action='store_true',
                       help='仅生成理论得分矩阵（不运行实际评估）')
    parser.add_argument('--reference-images', type=str, 
                       default=None,
                       help='参考图片配置JSON文件路径')
    
    args = parser.parse_args()
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    if 'ms_evaluator' in sys.modules:
        del sys.modules['ms_evaluator']
    
    from ms_evaluator import TASK_CONFIGS
    
    print("Step 1: Generating theoretical score matrix (checkpoint level)...")
    theoretical_data = generate_theoretical_scores_detailed(TASK_CONFIGS)
    
    output_dir = args.output_dir or str(Path(args.base_dir) / "batch_evaluation_results_fixed")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    theoretical_file = output_path / "theoretical_scores_summary.xlsx"
    theoretical_data['summary'].to_excel(theoretical_file)
    print(f"✓ 理论总分矩阵已保存: {theoretical_file}")
    
    theoretical_detail_file = output_path / "theoretical_scores_detailed.json"
    serializable_details = {}
    for folder_id, traj_data in theoretical_data['details'].items():
        serializable_details[folder_id] = {}
        for task_name, task_info in traj_data.items():
            serializable_details[folder_id][task_name] = {
                'checkpoint_scores': task_info['checkpoint_scores'],
                'checkpoint_names': task_info['checkpoint_names'],
                'total_score': task_info['total_score'],
                'display_name': task_info.get('display_name', TRAJECTORY_ID_MAPPING.get(folder_id, folder_id))
            }
    
    with open(theoretical_detail_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_details, f, indent=2, ensure_ascii=False)
    print(f"✓ 理论详细得分已保存: {theoretical_detail_file}\n")
    
    if args.theoretical_only:
        print("Only generating theoretical scores, program ends.")
        return
    
    reference_images = {}
    if args.reference_images:
        ref_path = Path(args.reference_images)
        if ref_path.exists():
            with open(ref_path, 'r', encoding='utf-8') as f:
                reference_images = json.load(f)
            print(f"✓ 加载参考图片配置: {len(reference_images)} 个")
    
    print(f"\n步骤2: 运行批量评估（{len(TRAJECTORY_COMPLETIONS)} 轨迹 × {len(TASK_CONFIGS)} 任务）...")
    actual_data = run_batch_evaluation(
        args.base_dir, 
        output_dir,
        reference_images=reference_images
    )
    
    actual_file = output_path / "actual_scores_summary.xlsx"
    actual_data['summary'].to_excel(actual_file)
    print(f"✓ 实际总分矩阵已保存: {actual_file}")
    
    actual_detail_file = output_path / "actual_scores_detailed.json"
    serializable_actual = {}
    for folder_id, traj_data in actual_data['details'].items():
        serializable_actual[folder_id] = {}
        for task_name, task_info in traj_data.items():
            serializable_actual[folder_id][task_name] = {
                'checkpoint_scores': task_info.get('checkpoint_scores', []),
                'checkpoint_names': task_info.get('checkpoint_names', []),
                'total_score': task_info.get('total_score', 0),
                'display_name': task_info.get('display_name', TRAJECTORY_ID_MAPPING.get(folder_id, folder_id)),
                'error': task_info.get('error', None)
            }
    
    with open(actual_detail_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_actual, f, indent=2, ensure_ascii=False)
    print(f"✓ 实际详细得分已保存: {actual_detail_file}\n")
    
    print("\nStep 3: Generating checkpoint-level comparison report...")
    stats = generate_comparison_report(theoretical_data, actual_data, output_dir)
    
    print("\n✅ All steps complete!")
    print(f"\n输出文件位置: {output_path}")


if __name__ == "__main__":
    main()