"""
Material Studio Evaluation System - v1.0
For evaluating task completion of Material Studio software operations
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import easyocr
from PIL import Image
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim

class MSEvaluator:
    """Material Studio Task Evaluator"""
    
    def __init__(self, base_folder: str, reference_images: Dict[str, str] = None):
        """
        Initialize the evaluator
        
        Args:
            base_folder: path to the folder containing screenshots and accessibility tree files
            reference_images: reference image path dict, e.g. {'ball_stick': 'path/to/image.png'}
        """
        self.base_folder = Path(base_folder).resolve()
        
        if not self.base_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {self.base_folder}")
        
        self.task_folder_name = self.base_folder.name
        self.screenshots = []
        self.ally_trees = []
        self.ocr_reader = easyocr.Reader(['en'], gpu=True)
        self.current_file = None
        
        # Set reference image paths
        self.reference_images = reference_images or {}
        
        # Set up evaluation output directory
        ms_folder = self.base_folder.parent
        self.evaluate_folder = ms_folder / "evaluate"
        
        if not self.evaluate_folder.exists():
            self.evaluate_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created evaluation output directory: {self.evaluate_folder}")
        
        # OCR cache directory
        self.ocr_cache_folder = self.evaluate_folder / "ocr_results" / self.task_folder_name
        if not self.ocr_cache_folder.exists():
            self.ocr_cache_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created OCR cache directory: {self.ocr_cache_folder}")
        
        # Cropped image cache directory
        self.crop_cache_folder = self.evaluate_folder / "cropped_images" / self.task_folder_name
        if not self.crop_cache_folder.exists():
            self.crop_cache_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created cropped image cache directory: {self.crop_cache_folder}")
        
        self.log_file = self.evaluate_folder / "evaluation_log.txt"
        
        self._load_files()
        
        # Preprocessing: identify filenames and window titles in screenshots
        self.screenshot_info = self._identify_info_in_screenshots()
    
    def _load_files(self):
        """Load screenshots and accessibility tree files"""
        screenshot_pattern = "screenshot-step_*.png"
        self.screenshots = sorted(
            self.base_folder.glob(screenshot_pattern),
            key=lambda x: self._extract_step_number(x.name)
        )
        
        ally_pattern = "accessibility_tree-step_*.txt"
        self.ally_trees = sorted(
            self.base_folder.glob(ally_pattern),
            key=lambda x: self._extract_step_number(x.name)
        )
        
        print(f"✓ Loaded {len(self.screenshots)} screenshots")
        print(f"✓ Loaded {len(self.ally_trees)} accessibility tree files")
    
    def _extract_step_number(self, filename: str) -> int:
        """Extract step number from filename"""
        match = re.search(r'step_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [{self.task_folder_name}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def _ocr_region(self, screenshot_path: Path, region: str = "full") -> str:
        """Perform OCR on the specified region of a screenshot (with caching)"""
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = self.ocr_cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Crop image by region
        if region == "top5%":
            img = img.crop((0, 0, width, int(height * 0.05)))
        elif region == "top10%":
            img = img.crop((0, 0, width, int(height * 0.1)))
        elif region == "top40%":
            img = img.crop((0, 0, width, int(height * 0.4)))
        elif region == "top50%":
            img = img.crop((0, 0, width, int(height * 0.5)))
        elif region == "bottom5%":
            img = img.crop((0, int(height * 0.95), width, height))
        elif region == "bottom20%":
            img = img.crop((0, int(height * 0.8), width, height))
        elif region == "left30%":
            img = img.crop((0, 0, int(width * 0.3), height))
        elif region == "right30%":
            img = img.crop((int(width * 0.7), 0, width, height))
        elif region == "center-area":
            img = img.crop((int(width * 0.2), int(height * 0.2), 
                          int(width * 0.8), int(height * 0.8)))
        
        img_array = np.array(img)
        results = self.ocr_reader.readtext(img_array)
        text = "\n".join([result[1] for result in results])
        
        # Cache result
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return text
    
    def _identify_info_in_screenshots(self) -> List[Dict]:
        """Preprocessing: identify information in all screenshots (filenames, window titles, etc.)"""
        self._log("开始预处理:识别所有截图信息...", "INFO")
        
        screenshot_info = []
        
        for i, screenshot in enumerate(self.screenshots):
            info = {
                'step': i,
                'top_5_text': self._ocr_region(screenshot, "top5%"),
                'top_40_text': self._ocr_region(screenshot, "top40%"),
                'full_text': None  # 按需加载
            }
            screenshot_info.append(info)
            
        self._log(f"✓ 信息识别完成: 共 {len(screenshot_info)} 帧", "INFO")
        return screenshot_info
    

    # ============ EVALUATION FUNCTIONS ============
    
    def check_file_in_title(self, expected_filename: str, region: str = "top5%") -> Dict[str, Any]:
        """Check if the title bar contains the specified filename"""
        self._log(f"检查标题栏文件名: {expected_filename} (区域: {region})", "INFO")
        
        result = {
            'function': 'check_file_in_title',
            'expected_filename': expected_filename,
            'region': region,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'status': 'not_found'}
        }
        
        expected_base = expected_filename.replace('.stp', '').replace('.xsd', '').lower()
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, region)
            text_lower = text.lower()
            
            if expected_base in text_lower:
                result['score'] = 1
                result['details']['found_at_step'] = i
                result['details']['status'] = 'found'
                result['details']['detected_text'] = text[:100]
                self._log(f"✓ 在步骤 [{i:02d}] 检测到文件名: {expected_filename}", "SUCCESS")
                return result
        
        self._log(f"✗ 未检测到文件名: {expected_filename}", "FAIL")
        return result
    
    def check_dialog_title(self, expected_title: str, region: str = "full", 
                       forbidden_keywords: List[str] = None) -> Dict[str, Any]:
        """Check if a dialog with the specified title appeared"""
        forbidden_keywords = forbidden_keywords or []
        
        log_msg = f"Checking dialog title: {expected_title}"
        if forbidden_keywords:
            log_msg += f" (forbidden: {', '.join(forbidden_keywords)})"
        self._log(log_msg, "INFO")
        
        result = {
            'function': 'check_dialog_title',
            'expected_title': expected_title,
            'forbidden_keywords': forbidden_keywords,
            'score': 0,
            'max_score': 1,
            'details': {
                'found_at_step': None,
                'detected_text': None,
                'forbidden_found': False,
                'forbidden_keyword': None
            }
        }
        
        expected_lower = expected_title.lower()
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, region)
            text_lower = text.lower()
            
            if expected_lower not in text_lower:
                continue
            
            # Check forbidden keywords
            found_forbidden = False
            forbidden_detected = None
            for fb in forbidden_keywords:
                if fb.lower() in text_lower:
                    found_forbidden = True
                    forbidden_detected = fb
                    break
            
            if found_forbidden:
                result['details']['forbidden_found'] = True
                result['details']['forbidden_keyword'] = forbidden_detected
                self._log(f"✗ 步骤 [{i:02d}] 检测到对话框 '{expected_title}' 但出现禁止词 '{forbidden_detected}'", "FAIL")
                continue  # continue to next frame, do not return directly
            
            result['score'] = 1
            result['details']['found_at_step'] = i
            result['details']['detected_text'] = text[:200]
            self._log(f"✓ 在步骤 [{i:02d}] 检测到对话框: {expected_title}", "SUCCESS")
            return result
        
        self._log(f"✗ 未检测到对话框: {expected_title}", "FAIL")
        return result
    
    def check_text_keyword(
        self,
        keyword: str,                           # keyword that must appear
        forbidden_keywords=None,  # list of forbidden keywords (can be None or empty list)
        region: str = "full",
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        检查指定区域是否出现必须关键词，且不出现禁止关键词。
        
        Args:
            keyword: keyword that must appear (string)
            forbidden_keywords: list of forbidden keywords (e.g. ["Import Document"]), can be None
            region: OCR 区域（如 "full"、"top40%" 等）
            case_sensitive: whether case-sensitive (default: no)
        
        Returns:
            结果字典，score=1 表示全部条件满足
        """
        forbidden_keywords = forbidden_keywords or []  # if None, convert to empty list
        
        log_msg = f"Checking keyword: {keyword}"
        if forbidden_keywords:
            log_msg += f" (forbidden: {', '.join(forbidden_keywords)})"
        log_msg += f" (region: {region})"
        self._log(log_msg, "INFO")
        
        result = {
            'function': 'check_text_keyword',
            'keyword': keyword,
            'forbidden_keywords': forbidden_keywords,
            'region': region,
            'score': 0,
            'max_score': 1,
            'details': {
                'found_keyword': False,
                'found_keyword_step': None,
                'forbidden_found': False,
                'forbidden_keyword': None,
                'forbidden_step': None
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, region)
            text_check = text if case_sensitive else text.lower()
            
            # Check required keywords
            keyword_check = keyword if case_sensitive else keyword.lower()
            found_keyword = keyword_check in text_check
            
            # Check all forbidden keywords (any one appearing counts as violation)
            found_forbidden = False
            forbidden_detected = None
            for fb in forbidden_keywords:
                fb_check = fb if case_sensitive else fb.lower()
                if fb_check in text_check:
                    found_forbidden = True
                    forbidden_detected = fb
                    break
            
            # Record details (record even if not passed, for debugging)
            if found_keyword:
                result['details']['found_keyword'] = True
                result['details']['found_keyword_step'] = i
            
            if found_forbidden:
                result['details']['forbidden_found'] = True
                result['details']['forbidden_keyword'] = forbidden_detected
                result['details']['forbidden_step'] = i
            
            # 只有“找到了必须关键词 且 没找到任何禁止关键词”才算通过
            if found_keyword and not found_forbidden:
                result['score'] = 1
                self._log(f"✓ 在步骤 [{i:02d}] 检测到关键词 '{keyword}'，且无禁止词", "SUCCESS")
                return result
        
        # Summary of failure reasons
        if result['details']['found_keyword']:
            reason = f"检测到 '{keyword}'，但出现了禁止词 '{result['details']['forbidden_keyword']}'"
            self._log(f"✗ {reason}", "FAIL")
        else:
            self._log(f"✗ 未检测到必须关键词: {keyword}", "FAIL")
        
        return result
    
    def check_field_value(self, dialog_title: str, field_name: str, 
                         expected_value: Any, tolerance: float = 0.01,
                         alternative_values: List[Any] = None) -> Dict[str, Any]:
            """
            检查对话框中某个字段的值
            
            Args:
                dialog_title: dialog title
                field_name: field name
                expected_value: expected value (primary value)
                tolerance: 数值容差
                alternative_values: optional alternative value list (for OCR misrecognition tolerance)
            """
            # Build all possible expected value lists
            all_expected_values = [expected_value]
            if alternative_values:
                all_expected_values.extend(alternative_values)
            
            self._log(f"检查字段值: {dialog_title} - {field_name} = {expected_value} (可选值: {alternative_values})", "INFO")
            
            result = {
                'function': 'check_field_value',
                'dialog_title': dialog_title,
                'field_name': field_name,
                'expected_value': expected_value,
                'alternative_values': alternative_values,
                'score': 0,
                'max_score': 1,
                'details': {'found': False, 'detected_value': None, 'step': None}
            }
            
            for i, screenshot in enumerate(self.screenshots):
                text = self._ocr_region(screenshot, "full")
                text_lower = text.lower()
                
                if dialog_title.lower() not in text_lower:
                    continue
                
                # Try matching all possible expected values
                for current_expected in all_expected_values:
                    field_patterns = self._generate_field_patterns(field_name, current_expected)
                    
                    for pattern in field_patterns:
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            detected_value = match.group(1) if match.lastindex else current_expected
                            result['score'] = 1
                            result['details']['found'] = True
                            result['details']['detected_value'] = detected_value
                            result['details']['matched_expected'] = current_expected
                            result['details']['step'] = i
                            
                            if current_expected == expected_value:
                                self._log(f"✓ 在步骤 [{i:02d}] 检测到字段值: {field_name} = {detected_value}", "SUCCESS")
                            else:
                                self._log(f"✓ 在步骤 [{i:02d}] 检测到字段值(OCR变体): {field_name} = {detected_value} (匹配到替代值 {current_expected})", "SUCCESS")
                            
                            return result
            
            self._log(f"✗ 未检测到字段值: {field_name} = {expected_value} (或任何替代值)", "FAIL")
            return result
    
    def _generate_field_patterns(self, field_name: str, expected_value: Any) -> List[str]:
        """Generate field matching patterns"""
        patterns = []
        value_str = str(expected_value)
        
        # Handle case where field_name is None
        if field_name is None:
            # If no field name, only match value itself
            return [rf'\b{re.escape(value_str)}\b']
        
        if isinstance(expected_value, (int, float)):
            if isinstance(expected_value, float):
                value_patterns = [
                    value_str,
                    value_str.rstrip('0').rstrip('.'),
                    f"{expected_value:.3f}",
                    f"{int(expected_value)}" if expected_value == int(expected_value) else None
                ]
                value_patterns = [p for p in value_patterns if p]
            else:
                value_patterns = [value_str]
        else:
            value_patterns = [value_str]
        
        field_patterns = [field_name]
        
        if 'α' in field_name or 'alpha' in field_name.lower():
            field_patterns.extend(['alpha', 'α', 'Alpha'])
        if 'β' in field_name or 'beta' in field_name.lower():
            field_patterns.extend(['beta', 'β', 'Beta'])
        
        for field_pat in field_patterns:
            for value_pat in value_patterns:
                patterns.extend([
                    rf'{re.escape(field_pat)}\s*[:：=]\s*{re.escape(value_pat)}\b',
                    rf'{re.escape(field_pat)}\s+{re.escape(value_pat)}\b',
                    rf'{re.escape(field_pat)}\s*[:：=]?\s*{re.escape(value_pat)}\b',
                ])
        
        return patterns
    
    def _calculate_visual_similarity(
        self,
        screenshot,
        reference_path: Path,
        step: int,
        crop_region: Optional[Tuple[float, float, float, float]] = None
    ) -> Tuple[float, Optional[Path]]:
        cropped_path = None
        try:
            # Load image
            if isinstance(screenshot, (str, Path)):
                img = cv2.imread(str(screenshot))
            else:
                img = screenshot

            ref = cv2.imread(str(reference_path))

            if img is None or ref is None:
                raise ValueError("图像加载失败")

            print(f"原始尺寸 → 截图: {img.shape[:2]}, 参考图: {ref.shape[:2]}")

            # ── Key change: apply the same crop ratio to the reference image ──
            img_cropped = img
            ref_cropped = ref   # 先默认全图

            if crop_region:
                # Crop current screenshot
                h_img, w_img = img.shape[:2]
                l, t, r, b = [int(x * d) for x, d in zip(crop_region, [w_img, h_img, w_img, h_img])]
                img_cropped = img[t:b, l:r]

                # Crop reference image with same ratio (assuming similar proportions)
                h_ref, w_ref = ref.shape[:2]
                l_ref, t_ref, r_ref, b_ref = [int(x * d) for x, d in zip(crop_region, [w_ref, h_ref, w_ref, h_ref])]
                ref_cropped = ref[t_ref:b_ref, l_ref:r_ref]

            # Unify size: resize reference crop to match current screenshot crop size (or vice versa)
            target_h, target_w = img_cropped.shape[:2]
            if ref_cropped.shape[:2] != (target_h, target_w):
                ref_cropped = cv2.resize(ref_cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)
                print(f"resize 后参考裁剪图尺寸: {ref_cropped.shape[:2]}")

            # Calculate SSIM
            gray_img = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
            gray_ref = cv2.cvtColor(ref_cropped, cv2.COLOR_BGR2GRAY)

            score = ssim(
                gray_img,
                gray_ref,
                data_range=gray_ref.max() - gray_ref.min()
            )

            # Save: saving the crop of the current screenshot (reference image crop is for calculation only, not saved)
            if self.crop_cache_folder:
                save_dir = Path(self.crop_cache_folder)
                save_dir.mkdir(parents=True, exist_ok=True)

                step_str = f"{step:02d}" if step is not None else "unknown"
                filename = f"cropped_{reference_path.stem}_step_{step_str}.png"
                save_path = save_dir / filename

                if cv2.imwrite(str(save_path), img_cropped):
                    cropped_path = save_path
                    print(f"裁剪图保存成功: {save_path}")
                else:
                    print(f"保存失败: {save_path}")

            return float(score), cropped_path

        except Exception as e:
            print(f"相似度计算/保存异常: {str(e)}")
            return 0.0, None

    def check_visual_similarity(
        self,
        reference_key: str,
        similarity_threshold: float = 0.85,
        crop_region: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict[str, Any]:
        """Check visual similarity between screenshot and reference image (with cropped image saving)"""
        self._log(f"检查视觉相似度: {reference_key} (阈值: {similarity_threshold})", "INFO")

        result = {
            'function': 'check_visual_similarity',
            'reference_key': reference_key,
            'score': 0,
            'max_score': 1,
            'details': {
                'max_similarity': 0.0,
                'max_similarity_step': None,
                'threshold': similarity_threshold,
                'all_similarities': [],
                'similarity_scores': [],
                'cropped_images_folder': str(self.crop_cache_folder),
                'detection_method': 'visual_similarity'
            }
        }

        if reference_key not in self.reference_images:
            result['details']['error'] = f"参考图片 '{reference_key}' 未配置"
            self._log(f"✗ 参考图片未配置: {reference_key}", "FAIL")
            return result

        reference_path = Path(self.reference_images[reference_key])
        if not reference_path.exists():
            result['details']['error'] = f"参考图片不存在: {reference_path}"
            self._log(f"✗ 参考图片不存在: {reference_path}", "FAIL")
            return result

        print(f"\n开始逐帧计算相似度:")

        max_sim = 0.0
        max_step = None

        for i, screenshot in enumerate(self.screenshots):
            similarity, cropped_path = self._calculate_visual_similarity(
                screenshot, reference_path, step=i, crop_region=crop_region
            )

            print(f"  Step [{i:02d}] | Similarity: {similarity:.4f} | Crop: {cropped_path.name if cropped_path else 'N/A'}")

            result['details']['similarity_scores'].append({
                'step': i,
                'similarity': round(similarity, 4),
                'cropped_image': str(cropped_path) if cropped_path else None
            })

            result['details']['all_similarities'].append({
                'step': i,
                'similarity': round(similarity, 4)
            })

            if similarity > max_sim:
                max_sim = similarity
                max_step = i

        result['details']['max_similarity'] = round(max_sim, 4)
        result['details']['max_similarity_step'] = max_step

        print()

        max_sim_rounded = result['details']['max_similarity']

        if max_sim_rounded >= similarity_threshold:
            result['score'] = 1
            self._log(f"✓ 视觉相似度达标: {max_sim_rounded:.4f} >= {similarity_threshold}", "SUCCESS")
        else:
            self._log(f"✗ 视觉相似度不足: {max_sim_rounded:.4f} < {similarity_threshold}", "FAIL")

        self._log(f"\n✓ 所有裁剪后的图片已保存至: {self.crop_cache_folder}", "INFO")
        self._log(f"  - 参考图片: {reference_path.name}", "INFO")
        self._log(f"  - 截图裁剪示例: cropped_{reference_path.stem}_step_*.png", "INFO")

        return result
    
    def check_multiple_fields(self, dialog_title: str, 
                             field_checks: Dict[str, Any]) -> Dict[str, Any]:
        """Check multiple field values in a dialog"""
        self._log(f"检查多个字段: {dialog_title} - {field_checks}", "INFO")
        
        result = {
            'function': 'check_multiple_fields',
            'dialog_title': dialog_title,
            'field_checks': field_checks,
            'score': 0,
            'max_score': 1,
            'details': {
                'field_results': {},
                'all_matched': False,
                'step': None
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            text_lower = text.lower()
            
            if dialog_title.lower() not in text_lower:
                continue
            
            all_matched = True
            for field_name, expected_value in field_checks.items():
                patterns = self._generate_field_patterns(field_name, expected_value)
                
                field_matched = False
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        field_matched = True
                        break
                
                result['details']['field_results'][field_name] = field_matched
                
                if not field_matched:
                    all_matched = False
            
            if all_matched:
                result['score'] = 1
                result['details']['all_matched'] = True
                result['details']['step'] = i
                self._log(f"✓ 在步骤 [{i:02d}] 所有字段均匹配", "SUCCESS")
                return result
        
        matched_count = sum(1 for v in result['details']['field_results'].values() if v)
        total_count = len(field_checks)
        
        if matched_count > 0:
            result['score'] = matched_count / total_count
            self._log(f"⚠ 部分字段匹配: {matched_count}/{total_count}", "WARNING")
        else:
            self._log(f"✗ 未检测到任何匹配字段", "FAIL")
        
        return result
    
    # ============ MAIN TASK EVALUATION FUNCTION ============
    
    def evaluate_task(self, task_name: str, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate task"""
        self._log(f"\n{'='*50}", "INFO")
        self._log(f"Starting evaluation: {task_name}", "INFO")
        self._log(f"{'='*50}", "INFO")
        
        task_result = {
            'task_name': task_name,
            'total_score': 0,
            'max_score': 0,
            'checks': []
        }
        
        for check in checks:
            func_name = check['function']
            args = check.get('args', {})
            
            if hasattr(self, func_name):
                func = getattr(self, func_name)
                check_result = func(**args)
                
                task_result['checks'].append(check_result)
                task_result['total_score'] += check_result['score']
                task_result['max_score'] += check_result['max_score']
        
        if task_result['max_score'] > 0:
            pass_rate = (task_result['total_score'] / task_result['max_score']) * 100
            task_result['pass_rate'] = f"{pass_rate:.1f}%"
        else:
            task_result['pass_rate'] = "N/A"
        
        self._log(f"\n评估完成: {task_result['total_score']}/{task_result['max_score']} ({task_result['pass_rate']})", "INFO")
        
        result_file = self.evaluate_folder / f"{task_name}_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(task_result, f, indent=2, ensure_ascii=False)
        
        return task_result

# ============ TASK CONFIGS ============

TASK_CONFIGS = {
    # Simple tasks
    "in1": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'task 1', 'region': '顶部5%'}}
    ],
    
    "in2": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic',  'forbidden_keywords':["Import Document"],'region': '顶部40%'}}
    ],
    
    "in3": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'urea', 'forbidden_keywords':["Import Document"],'region': '顶部40%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Display Style','forbidden_keywords':['Hide','Display Options']}},
        {'function': 'check_visual_similarity', 'args': {
            'reference_key': 'ball_stick',
            'similarity_threshold': 0.99,
            'crop_region': (0.2, 0.15, 0.7, 0.7)
        }}
    ],
    
    "in4": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Fe','forbidden_keywords':["Import Document"], 'region': '顶部40%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Display Options','forbidden_keywords':['Hide','Display Style']}}
    ],
    
    "in5": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'LiF','forbidden_keywords':["Import Document"], 'region': '顶部40%'}},
        {'function': 'check_visual_similarity', 'args': {
            'reference_key': 'lif_deleted',
            'similarity_threshold': 0.99,
            'crop_region': (0.2, 0.15, 0.7, 0.7)
        }}
    ],
    
    "in6": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic',  'forbidden_keywords':["Import Document"],'region': '顶部40%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Homopolymer','forbidden_keywords': ['Add Atoms']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': None,
            'expected_value': 'ethylene'
        }},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': 'Chain length',
            'expected_value': 20
        }}
    ],
    
    "in7": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic',  'forbidden_keywords':["Import Document"],'region': '顶部40%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Build Crystal', 'forbidden_keywords': ['Unbuild Crystal']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Build Crystal',
            'field_name':None,
            'expected_value': 4910
        }},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Build Crystal',
            'field_name':None,
            'expected_value': 70
        }}
    ],
    
    "in8": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic',  'forbidden_keywords':["Import Document"],'region': '顶部40%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Add Atoms','forbidden_keywords':["Crystal",'Surfaces']}}
    ],
    
    "in9": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Al2O3', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Hide','forbidden_keywords':["Display Style,Display Options"]}},
        {'function': 'check_visual_similarity', 'args': {
            'reference_key': 'al2o3_hidden',
            'similarity_threshold': 0.99
        }}
    ],
    
    # Medium tasks
    "in10": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Build Crystal', 'forbidden_keywords': ['Unbuild Crystal','Add Atoms']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Build Crystal',
            'field_name': None,
            'expected_value': 'P3221'
        }}
    ],
    
    "in11": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic','forbidden_keywords':["Import Document"], 'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Build Crystal', 'forbidden_keywords': ['Unbuild Crystal','SuperCell']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Build Crystal',
            'field_name': None,
            'expected_value': 'P1'
        }}
    ],
    
    "in12": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'urea', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Label'},'forbidden_keywords':["Display Style,Display Options",'Hide']},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Helvetica'}}
    ],
    
    "in13": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Novolac4', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Build Surface','forbidden_keywords': ['Cleave Surface']}}
    ],
    
    "in14": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'SuperSi','forbidden_keywords':["Import Document"], 'region': '顶部50%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'supercell range','forbidden_keywords': ['Unbuild Crystal','Add Atoms','Make P1']}},
    ],
    
    "in15": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Fe','forbidden_keywords':["Import Document"], 'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Cleave Surface','forbidden_keywords': ['Build Surface']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Cleave Surface',
            'field_name': None,
            'expected_value': '5 5 5'
        }}
    ],
    
    # Complex tasks
    "in16": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': '3D Atomistic', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Add Atoms','forbidden_keywords':["Crystal",'Surfaces']}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Display Style','forbidden_keywords':['Hide','Display Options']}},
        {'function': 'check_visual_similarity', 'args': {
            'reference_key': 'H2O',
            'similarity_threshold': 0.98
        }}
    ],
    
    "in17": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'TMOS', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Add Atoms','forbidden_keywords':["Crystal",'Surfaces']}},
        {'function': 'check_multiple_fields', 'args': {
            'dialog_title': 'Add Atoms',
            'field_checks': {'Element': 'H', 'x': 2.0}
        }},
        {'function': 'check_text_keyword', 'args': {
            'keyword': 'Calculate Close Contacts',
            'region': '底部10%'
        }}
    ],
    
    "in18": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Homopolymer'},'forbidden_keywords':["Crystal",'Surfaces']},
         {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': None,
            'expected_value': 'propylene'
        }},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': 'Chain length',
            'expected_value': 40,
            'alternative_values': [140, '|40', '4|0', 'I40', '40I']
        }},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Homopolymer','forbidden_keywords':["Crystal",'Surfaces']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Build Crystal',
            'field_name': None,
            'expected_value': '5 C2'
        }},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Build Crystal',
            'field_name': None,
            'expected_value': 15
        }}
    ],
    
    "in19": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Homopolymer','forbidden_keywords':["Crystal",'Surfaces']}},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': 'Library',
            'expected_value': 'acrylates'
        }},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': 'Tacticity',
            'expected_value': 'Isotactic'
        }},
        {'function': 'check_field_value', 'args': {
            'dialog_title': 'Homopolymer',
            'field_name': 'Chain length',
            'expected_value': 40,
            'alternative_values': [140, '|40', '4|0', 'I40', '40I']
        }}
    ],
    
    "in20": [
        {'function': 'check_file_in_title', 'args': {'expected_filename': 'untitled', 'region': '顶部5%'}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'urea', 'forbidden_keywords':["Import Document"],'region': '顶部50%'}},
        {'function': 'check_dialog_title', 'args': {'expected_title': 'Charges','forbidden_keywords':["Crystal",'Surfaces']}},
        {'function': 'check_text_keyword', 'args': {'keyword': 'Divide-and-conquer'}}
    ]
}


# ============ MAIN FUNCTION ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Material Studio 评估系统 v1.0')
    parser.add_argument('--folder', type=str, help='截图文件夹路径')
    parser.add_argument('--task', type=str, help='任务名称')
    parser.add_argument('--reference-images', type=str, help='参考图片配置JSON文件路径',
                       default=None)
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Material Studio 评估系统 v1.0")
    print(f"{'='*60}\n")
    
    folder_path = Path(args.folder).resolve()
    
    if not folder_path.exists():
        print(f"❌ 错误: 文件夹不存在: {folder_path}")
        return
    
    # Load reference image configuration
    reference_images = {}
    if args.reference_images:
        ref_path = Path(args.reference_images)
        if ref_path.exists():
            with open(ref_path, 'r', encoding='utf-8') as f:
                reference_images = json.load(f)
            print(f"✓ 加载参考图片配置: {len(reference_images)} 个")
    
    print(f"✓ 文件夹: {folder_path}")
    print(f"✓ 任务: {args.task}")
    print()
    
    if args.task not in TASK_CONFIGS:
        print(f"❌ 未找到任务 '{args.task}'")
        print(f"\n可用任务:")
        for task_name in TASK_CONFIGS.keys():
            print(f"  - {task_name}")
        return
    
    try:
        evaluator = MSEvaluator(str(folder_path), reference_images)
        result = evaluator.evaluate_task(args.task, TASK_CONFIGS[args.task])
        
        print(f"\n{'='*60}")
        print(f"评估完成!")
        print(f"{'='*60}")
        print(f"得分: {result['total_score']}/{result['max_score']} ({result['pass_rate']})")
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()