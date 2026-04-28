"""
Avantage XPS Evaluation System
Main function: evaluate task completion for Avantage XPS software operations
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import easyocr
from PIL import Image
import numpy as np


class AvantageEvaluator:
    """Avantage XPS Task Evaluator"""
    
    def __init__(self, base_folder: str):
        self.base_folder = Path(base_folder).resolve()
        
        if not self.base_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {self.base_folder}")
        
        self.task_folder_name = self.base_folder.name
        self.screenshots = []
        self.ally_trees = []
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)
        self.current_file = None
        
        # Set up evaluation output directory
        avantage_folder = self.base_folder.parent
        self.evaluate_folder = avantage_folder / "evaluate"
        
        if not self.evaluate_folder.exists():
            self.evaluate_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created evaluation output directory: {self.evaluate_folder}")
        
        # OCR cache directory
        self.ocr_cache_folder = self.evaluate_folder / "ocr_results" / self.task_folder_name
        if not self.ocr_cache_folder.exists():
            self.ocr_cache_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created OCR cache directory: {self.ocr_cache_folder}")
        
        self.log_file = self.evaluate_folder / "evaluation_log.txt"
        self.desktop_path = Path.home() / "Desktop"
        
        self._load_files()
        
        # Preprocessing: identify filenames in screenshots
        self.screenshot_files = self._identify_files_in_screenshots()
    
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
    
    def _ocr_region(self, screenshot_path: Path, region: str = "full") -> str:
        """
        Perform OCR on the specified region of an image (with caching)
        
        Args:
            screenshot_path: path to the screenshot
            region: region name (full/top5%/top10%/bottom5%/bottom10%/left10%/right10%)
        
        Returns:
            recognized text
        """
        # Check cache
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = self.ocr_cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Load and crop image
        img = Image.open(screenshot_path)
        width, height = img.size
        
        if region == "top5%":
            img = img.crop((0, 0, width, int(height * 0.05)))
        elif region == "top10%":
            img = img.crop((0, 0, width, int(height * 0.1)))
        elif region == "top20%":
            img = img.crop((0, 0, width, int(height * 0.2)))
        elif region == "bottom5%":
            img = img.crop((0, int(height * 0.95), width, height))
        elif region == "bottom10%":
            img = img.crop((0, int(height * 0.9), width, height))
        elif region == "bottom30%":
            img = img.crop((0, int(height * 0.7), width, height))
        elif region == "left20%":
            img = img.crop((0, 0, int(width * 0.2), height))
        elif region == "left40%":
            img = img.crop((0, 0, int(width * 0.4), height))
        elif region == "right10%":
            img = img.crop((int(width * 0.9), 0, width, height))
        elif region == "center50%":
        # center50%: from 25% to 75% (25% margin on each side)
            left = int(width * 0.25)
            top = int(height * 0.25)
            right = int(width * 0.75)
            bottom = int(height * 0.75)
            img = img.crop((left, top, right, bottom))
        # Full region: no cropping needed
        
        # OCR recognition
        img_array = np.array(img)
        results = self.ocr_reader.readtext(img_array)
        text = "\n".join([result[1] for result in results])
        
        # Save to cache
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return text
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [{self.task_folder_name}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def _identify_files_in_screenshots(self) -> list:
        """
        预处理：识别所有截图中的文件名
        
        Criterion: both filename and "Binding Energy" appear simultaneously
        Also stores normalized text for subsequent fuzzy matching
        """
        self._log("Starting preprocessing: identifying filenames in all screenshots...", "INFO")
        
        screenshot_files = []
        screenshot_files_normalized = []
        all_detected_files = set()  # Record all detected files
        
        for i, screenshot in enumerate(self.screenshots):
            # OCR recognition: center region
            center_text = self._ocr_region(screenshot, "center50%")
            
            # Normalize text
            normalized_text = self._normalize_ocr_text(center_text)
            
            # Check for Binding Energy
            has_binding_energy = self._check_binding_energy(normalized_text)
            
            # Try to extract all filenames
            current_files = []
            current_normalized_list = []
            
            if has_binding_energy:
                current_files = self._extract_all_filenames_from_text(center_text, normalized_text)
                for file in current_files:
                    # Extract the matched normalized text for each file
                    variant = self._extract_matched_variant(normalized_text, file)
                    current_normalized_list.append(variant)
                    all_detected_files.add(file)
            
            if not current_files:
                preview = center_text.replace('\n', ' ')[:200]
                self._log(f"  Frame [{i:02d}]: Unable to identify filename | has_BE: {has_binding_energy} | OCR preview: {preview}", "DEBUG")
                screenshot_files.append(None)
                screenshot_files_normalized.append(None)
            else:
                # If multiple files detected, store as list
                if len(current_files) == 1:
                    screenshot_files.append(current_files[0])
                    screenshot_files_normalized.append(current_normalized_list[0])
                    preview = center_text.replace('\n', ' ')[:200]
                    self._log(f"  Frame [{i:02d}]: ✓ Identified file: {current_files[0]} (normalized: {current_normalized_list[0]}) | OCR preview: {preview}", "DEBUG")
                else:
                    # Multiple files
                    screenshot_files.append(current_files)
                    screenshot_files_normalized.append(current_normalized_list)
                    preview = center_text.replace('\n', ' ')[:200]
                    files_str = ', '.join(current_files)
                    normalized_str = ', '.join(current_normalized_list)
                    self._log(f"  第 [{i:02d}] 帧: ✓ 识别到 {len(current_files)} 个文件: {files_str} (规范化: {normalized_str}) | OCR预览: {preview}", "DEBUG")
        
        self._log(f"✓ File identification complete: {len(screenshot_files)} frames total", "INFO")
        
        # Count identified unique files
        if all_detected_files:
            self._log(f"  Identified files: {', '.join(sorted(all_detected_files))}", "INFO")
        else:
            self._log(f"  ⚠️ Warning: No filenames identified!", "WARNING")
        
        # Store normalized text to instance variable
        self.screenshot_files_normalized = screenshot_files_normalized
        
        # Debug: confirm normalized list is set correctly
        self._log(f"  Normalized list set, length: {len(self.screenshot_files_normalized)}", "DEBUG")
        non_none_normalized = []
        for n in screenshot_files_normalized:
            if n:
                if isinstance(n, list):
                    non_none_normalized.extend(n)
                else:
                    non_none_normalized.append(n)
        if non_none_normalized:
            self._log(f"  Non-null normalized variant sample: {non_none_normalized[:10]}", "DEBUG")
        
        return screenshot_files

    def _check_binding_energy(self, normalized_text: str) -> bool:
        """
        检查是否包含 "Binding Energy"
        
        考虑OCR可能的错误：
        - Binding → Bincling, Bindins, Binging
        - Energy → Enersy, Enerty, Fnerey
        """
        binding_variants = [
            'bindingenergy',
            'binding energy',
            'bindingenergy',
            'bindingenersy',
            'bindingenerty',
            'binclingenergy',
            'bindingfnergy',
        ]
        
        for variant in binding_variants:
            if variant in normalized_text:
                return True
        
        # If strict matching fails, try looser matching
        # Must contain core parts "binding" and "energ"
        if 'binding' in normalized_text and 'energ' in normalized_text:
            return True
        
        return False
    def _normalize_ocr_text(self, text: str) -> str:
        """
        规范化OCR文本，修正常见的OCR识别错误
        
        常见错误：
        - C1s → CIS, C1S, Cls
        - O1s → O1S, OIS, Ols
        - Zn2p → Zn2P, ZnZp
        - 1 → l, I, |
        - 0 → O, o
        """
        if not text:
            return ""
        
        normalized = text
        
        # Remove all spaces for easier matching
        normalized_nospace = normalized.replace(' ', '').replace('\n', '').lower()
        
        return normalized_nospace


    def _extract_all_filenames_from_text(self, text: str, normalized_text: str) -> list:
        """
        从OCR文本中提取所有文件名
        
        Args:
            text: original OCR text
            normalized_text: normalized text (lowercase, no spaces)
        
        Returns:
            list of identified filenames
        """
        # Define all possible filenames and their variants
        # KEY: normalized standard filename -> VALUE: [possible OCR variants]
        # Return value is the corresponding standard filename (original format)
        scan_variants = {
            'c1sscan': {
                'standard_name': 'C1s Scan',
                'variants': ['c1sscan', 'c1scan', 'clsscan', 'cisscan', 'clsscan',
                            'cisscan', 'c1sscan', 'clscan', 'c1s', 'cls', 'cis']
            },
            'o1sscan': {
                'standard_name': 'O1s Scan',
                'variants': ['o1sscan', 'o1scan', 'olsscan', 'oisscan', 'olsscan',
                            'oisscan', 'o1sscan', 'olscan', 'o1s', 'ols', 'ois']
            },
            'zn2pscan': {
                'standard_name': 'Zn2p Scan',
                'variants': ['zn2pscan', 'zn2scan', 'znzpscan', 'zn2pscan',
                            'znzpscan', 'zn2p', 'znzp']
            },
            'xpssurvey': {
                'standard_name': 'XPS Survey',
                'variants': ['xpssurvey', 'xpssurvey', 'xps', 'survey']
            },
            'surveyscan': {
                'standard_name': 'Survey Scan',
                'variants': ['surveyscan', 'surveyscan', 'survey']
            }
        }
        
        found_files = []
        
        # Try matching each filename
        for normalized_key, info in scan_variants.items():
            for variant in info['variants']:
                if variant in normalized_text:
                    if info['standard_name'] not in found_files:
                        found_files.append(info['standard_name'])
                    break
        
        return found_files
    
    def _extract_matched_variant(self, normalized_text: str, standard_filename: str) -> str:
        """
        提取实际匹配到的规范化变体
        
        Args:
            normalized_text: normalized OCR text
            standard_filename: standard filename (e.g. 'C1s Scan')
        
        Returns:
            matched normalized variant (e.g. 'cisscan')
        """
        # Define variant mapping
        variants_for_standard = {
            'C1s Scan': {
                'normalized_key': 'c1sscan',
                'variants': ['c1sscan', 'c1scan', 'clsscan', 'cisscan', 'c1s', 'cls', 'cis']
            },
            'O1s Scan': {
                'normalized_key': 'o1sscan',
                'variants': ['o1sscan', 'o1scan', 'olsscan', 'oisscan', 'o1s', 'ols', 'ois']
            },
            'Zn2p Scan': {
                'normalized_key': 'zn2pscan',
                'variants': ['zn2pscan', 'zn2scan', 'znzpscan', 'zn2p', 'znzp']
            },
            'XPS Survey': {
                'normalized_key': 'xpssurvey',
                'variants': ['xpssurvey', 'xps', 'survey']
            },
            'Survey Scan': {
                'normalized_key': 'surveyscan',
                'variants': ['surveyscan', 'survey']
            }
        }
        
        if standard_filename in variants_for_standard:
            info = variants_for_standard[standard_filename]
            # Find which variant is contained in normalized_text
            for variant in info['variants']:
                if variant in normalized_text:
                    return variant
            # If not found, return normalized key
            return info['normalized_key']
        
        # Default: return normalized standard filename
        return standard_filename.lower().replace(' ', '')
    
    def _is_filename_variant(self, expected_normalized: str, detected_normalized: str) -> bool:
        """
        判断检测到的规范化文件名是否是期望文件名的变体
        
        Args:
            expected_normalized: expected normalized filename (e.g. 'c1sscan')
            detected_normalized: detected normalized filename (e.g. 'cisscan')
        
        Returns:
            whether matched
        """
        # Define variant mapping
        variants_map = {
            'c1sscan': ['c1sscan', 'c1scan', 'clsscan', 'cisscan', 'c1s', 'cls', 'cis'],
            'o1sscan': ['o1sscan', 'o1scan', 'olsscan', 'oisscan', 'o1s', 'ols', 'ois'],
            'zn2pscan': ['zn2pscan', 'zn2scan', 'znzpscan', 'zn2p', 'znzp'],
            'xpssurvey': ['xpssurvey', 'xps', 'survey'],
            'surveyscan': ['surveyscan', 'survey']
        }
        
        # Get variant list for expected filename
        if expected_normalized in variants_map:
            variants = variants_map[expected_normalized]
            return detected_normalized in variants
        
        # If no predefined variants, use exact matching
        return expected_normalized == detected_normalized
    
    def debug_print_all_detected_files(self):
        """
        调试方法：打印所有预处理阶段识别的文件
        """
        self._log(f"\n{'='*60}", "DEBUG")
        self._log(f"Debug: all files identified in preprocessing", "DEBUG")
        self._log(f"{'='*60}", "DEBUG")
        self._log(f"Total {len(self.screenshot_files)} screenshot frames", "DEBUG")
        
        unique_files = {}
        for i, detected_file in enumerate(self.screenshot_files):
            if detected_file:
                # Handle single or multiple files
                files = detected_file if isinstance(detected_file, list) else [detected_file]
                for f in files:
                    if f not in unique_files:
                        unique_files[f] = []
                    unique_files[f].append(i)
        
        self._log(f"Identified {len(unique_files)} distinct files:", "DEBUG")
        for filename, steps in unique_files.items():
            self._log(f"  - '{filename}' appears in steps: {steps}", "DEBUG")
        
        self._log(f"{'='*60}\n", "DEBUG")
    
    # ==================== EVALUATION FUNCTIONS ====================
    # Simple evaluation functions
    def check_multiple_files_imported(self, expected_files: List[str]) -> Dict[str, Any]:
        """
        检测多个文件是否都成功导入（单帧满足原则）
        
        要求在 **同一个步骤（同一张截图）** 中：
        1. Identified file list contains all expected files
        2. "Binding Energy" label count in screenshot equals expected file count
        
        Args:
            expected_files: list of expected filenames to import
            
        Returns:
            evaluation result dict
        """
        self._log(f"Checking multi-file import (all in one frame): {', '.join(expected_files)}", "INFO")
        
        result = {
            'function': 'check_multiple_files_imported',
            'score': 0,
            'max_score': 1,
            'details': {
                'expected_files': expected_files,
                'status': 'failed',
                'best_step_match': None,  # Record the best match for debugging
                'error': None
            }
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        # 1. Prepare normalized mapping for expected files
        expected_normalized_map = {
            expected.lower().replace(' ', ''): expected 
            for expected in expected_files
        }
        expected_count = len(expected_files)
        
        # For recording best match (even on failure, shows closest attempt to success)
        max_files_found = 0
        best_step_details = {}

        # 2. Iterate over every frame (every step)
        for i, (detected_file_data, detected_normalized_data) in enumerate(zip(self.screenshot_files, self.screenshot_files_normalized)):
            
            # --- A. Check file match for current frame ---
            if not detected_file_data:
                continue

            # Ensure converted to list for processing
            current_frame_normalized_list = detected_normalized_data if isinstance(detected_normalized_data, list) else [detected_normalized_data]
            
            # Count how many expected files matched in current frame
            matched_expectations = set()
            
            for detected_norm in current_frame_normalized_list:
                for expected_key, expected_original in expected_normalized_map.items():
                    # Check whether matched, and file not yet recorded in current frame
                    if expected_original not in matched_expectations:
                        if self._is_filename_variant(expected_key, detected_norm):
                            matched_expectations.add(expected_original)
            
            current_match_count = len(matched_expectations)
            
            # 如果当前帧匹配的文件数量比之前的记录多，更新“最佳记录”以便调试
            if current_match_count > max_files_found:
                max_files_found = current_match_count
                best_step_details = {
                    'step': i,
                    'found_files': list(matched_expectations),
                    'missing': list(set(expected_files) - matched_expectations)
                }

            # If current frame did not find all files, skip and move to next frame
            if current_match_count < expected_count:
                continue
            
            # --- B. All files matched! Now check Binding Energy in current frame ---
            self._log(f"  Step [{i:02d}]: Files matched {list(matched_expectations)}, starting OCR check for Binding Energy...", "DEBUG")
            
            current_screenshot = self.screenshots[i]
            ocr_text = self._ocr_region(current_screenshot, "full")
            
            # Count Binding Energy
            binding_energy_count = 0
            binding_energy_variants = [
                'bindingenergy', 'binding energy', 'bindingenersy', 
                'bindingenerty', 'binclingenergy', 'bindingfnergy'
            ]
            
            lines = ocr_text.lower().split('\n')
            for line in lines:
                line_normalized = line.replace(' ', '')
                for variant in binding_energy_variants:
                    if variant in line_normalized:
                        binding_energy_count += 1
                        break 
            
            self._log(f"  Step [{i:02d}]: Binding Energy count: {binding_energy_count} (expected: {expected_count})", "DEBUG")
            
            # --- C. Final decision ---
            # Files all matched AND energy label count also matched (>= to handle OCR over-reading, == is strict)
            if binding_energy_count == expected_count:
                result['score'] = 1
                result['details']['status'] = 'success'
                result['details']['success_step'] = i
                result['details']['found_files'] = list(matched_expectations)
                result['details']['binding_energy_count'] = binding_energy_count
                
                self._log(f"✓ Success: all files detected and Binding Energy count matched at step {i}", "SUCCESS")
                return result
            else:
                # Files matched but Binding Energy count wrong, record this case
                self._log(f"  Step [{i:02d}]: Files matched but Binding Energy count insufficient/excessive", "DEBUG")

        # --- 3. If loop completes without returning, it is a failure ---
        result['details']['best_attempt'] = best_step_details
        if best_step_details:
             self._log(f"✗ Fail: no frame fully satisfies conditions. Best match at step {best_step_details.get('step')}, found {len(best_step_details.get('found_files'))}/{expected_count} files.", "FAIL")
        else:
             self._log("✗ 失败: 未能匹配到任何期望文件。", "FAIL")
             
        return result
    
    def check_image_zoom(self, target_value: str) -> Dict[str, Any]:
        """
        图像放大缩小：检测坐标轴是否出现特定数值后又消失（用于判断图像放大再缩小）
        
        Args:
            target_value: target value (e.g. '282')
            
        Returns:
            evaluation result dict
        """
        self._log(f"Checking image zoom (target value: {target_value})", "INFO")
        
        result = {
            'function': 'check_image_zoom',
            'score': 0,
            'max_score': 1,
            'details': {
                'target_value': target_value,
                'appeared': False,
                'disappeared': False,
                'appeared_at': None,
                'disappeared_at': None
            }
        }
        
        appeared = False
        
        for i, screenshot in enumerate(self.screenshots):
            # Keep region logic as-is (bottom 30% usually corresponds to axis)
            text = self._ocr_region(screenshot, "bottom30%")
            
            if target_value in text:
                if not appeared:
                    appeared = True
                    result['details']['appeared'] = True
                    result['details']['appeared_at'] = i
                    self._log(f"  Step [{i:02d}]: Axis value {target_value} appeared (image zoomed in)", "DEBUG")
            elif appeared and target_value not in text:
                result['details']['disappeared'] = True
                result['details']['disappeared_at'] = i
                result['score'] = 1
                self._log(f"✓ 图像放大缩小完成: 放大({result['details']['appeared_at']}) → 缩小恢复({i})", "SUCCESS")
                break
        
        if result['score'] == 0:
            if appeared:
                self._log(f"✗ Image not restored after zoom: value '{target_value}' did not disappear", "FAIL")
            else:
                self._log(f"✗ Image zoom not performed: value '{target_value}' not detected", "FAIL")
        
        return result
    
    def check_stacked_graph(self, small_values: List[str] = ['2', '4', '6', '8'], normal_markers: List[str] = None) -> Dict[str, Any]:
        """
        堆叠图检测（兼容版）：解决 TypeError 错误，同时支持 C1s 大整数与 O1s 科学计数法。
        
        Args:
            small_values: tick marks in stacked graph mode (e.g. ['2','4','6'])
            normal_markers: legacy parameter passed in (kept for compatibility, combined with regex internally)
        """
        self._log("开始检测堆叠图：正则兼容模式", "INFO")
        
        result = {
            'function': 'check_stacked_graph',
            'score': 0,
            'max_score': 1,
            'details': {
                'has_seen_normal': False,
                'success_step': None,
                'detected_normal_type': None,
                'found_small_values': []
            }
        }

        # 1. Define match patterns
        # Match scientific notation (e.g. 1.20e5)
        pattern_scientific = re.compile(r'\d\.\d+e\d+|0\.00e') 
        # Match 4+ digit large integers (e.g. 40000, 10000, 2000)
        pattern_large_int = re.compile(r'\d{4,}') 

        has_seen_normal = False
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "center50%").lower()
            
            # --- A. Normal mode detection (Normal State) ---
            # Check: regex match OR user-provided normal_markers match
            is_sci = bool(pattern_scientific.search(text))
            is_int = bool(pattern_large_int.search(text))
            is_custom = any(m in text for m in normal_markers) if normal_markers else False
            
            if is_sci or is_int or is_custom:
                has_seen_normal = True
                result['details']['has_seen_normal'] = True
                if is_sci: result['details']['detected_normal_type'] = "scientific"
                elif is_int: result['details']['detected_normal_type'] = "large_int"
                else: result['details']['detected_normal_type'] = "custom_marker"
                continue # Current frame has large values; skip and look for the frame after disappearance

            # --- B. Stacked mode detection (Stacked State) ---
            if has_seen_normal:
                # Check if small ticks appeared
                detected_smalls = [v for v in small_values if v in text]
                
                # Success condition:
                # 1. No large-value features at all (sci, int, custom all False)
                # 2. At least 2 small tick numbers identified
                if not (is_sci or is_int or is_custom) and len(detected_smalls) >= 2:
                    result['score'] = 1
                    result['details']['success_step'] = i
                    result['details']['found_small_values'] = detected_smalls
                    
                    self._log(f"✓ Stacked graph switched successfully (step {i})", "SUCCESS")
                    return result

        # Error feedback
        if not has_seen_normal:
            self._log("✗ 失败：未检测到初始大数值状态（C1s 整数或 O1s 科学计数法）", "FAIL")
        else:
            self._log(f"✗ Fail: large value disappeared but could not identify at least two small ticks {small_values} in same frame", "FAIL")
            
        return result

    def check_duplicate_files_imported(self, expected_files: List[str]) -> Dict[str, Any]:
        """
        检测重复文件导入/复制谱图（单帧严格匹配原则）
        
        要求在同一个步骤中：
        1. Title count fully matched (supports same-name files)
        2. "Binding Energy" axis label count must strictly equal expected total file count
        """
        self._log(f"Checking spectrum copy (strict match): {', '.join(expected_files)}", "INFO")
        
        result = {
            'function': 'check_duplicate_files_imported',
            'score': 0,
            'max_score': 1,
            'details': {
                'expected_files': expected_files,
                'status': 'failed',
                'best_step_match': None,
                'error': None
            }
        }
        
        if not self.screenshots:
            result['details']['error'] = "No screenshots available"
            return result
        
        expected_total_count = len(expected_files)
        norm_expected_list = [f.lower().replace(' ', '') for f in expected_files]
        
        max_total_matched = 0
        best_step_details = {}

        for i, (detected_file_data, detected_normalized_data) in enumerate(zip(self.screenshot_files, self.screenshot_files_normalized)):
            if not detected_file_data:
                continue

            # --- A. Title matching logic (supports duplicates) ---
            current_frame_detected_norm = detected_normalized_data if isinstance(detected_normalized_data, list) else [detected_normalized_data]
            temp_norm_expected = norm_expected_list.copy()
            matched_count = 0
            
            for detected_norm in current_frame_detected_norm:
                for j, target_norm in enumerate(temp_norm_expected):
                    if self._is_filename_variant(target_norm, detected_norm):
                        matched_count += 1
                        temp_norm_expected.pop(j)
                        break
            
            # Update best record for debugging
            if matched_count > max_total_matched:
                max_total_matched = matched_count
                best_step_details = {'step': i, 'matched_count': matched_count}

            # Only do axis OCR deep check when title count is fully met
            if matched_count == expected_total_count:
                self._log(f"  Step [{i:02d}]: Title count reached ({matched_count}), verifying axis...", "DEBUG")
                
                current_screenshot = self.screenshots[i]
                ocr_text = self._ocr_region(current_screenshot, "full")
                
                # --- B. Strict axis label count ---
                binding_energy_count = 0
                binding_energy_variants = [
                    'bindingenergy', 'binding energy', 'bindingenersy', 
                    'bindingenerty', 'binclingenergy', 'bindingfnergy', 'binding'
                ]
                
                lines = ocr_text.lower().split('\n')
                for line in lines:
                    line_normalized = line.replace(' ', '')
                    # Each OCR text line counted at most once as axis label, prevent duplicate counting
                    for variant in binding_energy_variants:
                        if variant in line_normalized:
                            binding_energy_count += 1
                            break 
                
                self._log(f"  Step [{i:02d}]: Axis count = {binding_energy_count}, expected = {expected_total_count}", "DEBUG")
                
                # --- C. Final decision: must be strictly equal ---
                if binding_energy_count == expected_total_count:
                    result['score'] = 1
                    result['details'].update({
                        'status': 'success',
                        'success_step': i,
                        'binding_energy_count': binding_energy_count
                    })
                    self._log(f"✓ Success: title and axis counts strictly matched at step {i} ({expected_total_count})", "SUCCESS")
                    return result
                else:
                    self._log(f"  Step [{i:02d}]: Count mismatch (title:{matched_count} vs axis:{binding_energy_count})", "DEBUG")

        # Failure summary output
        result['details']['best_attempt'] = best_step_details
        self._log(f"✗ Fail: no screenshot found with both title and axis count equal to {expected_total_count}", "FAIL")
             
        return result

    def check_background_added_successfully(self, title: str, bg_type: str = 'Smart') -> Dict[str, Any]:
        """
        证明背景已增加：检测对话框打开、内部出现指定背景类型文本、最后对话框关闭。
        """
        self._log(f"Starting deep background operation detection: {title} -> {bg_type}", "INFO")
        
        result = {
            'function': 'check_background_added_successfully',
            'score': 0,
            'max_score': 1,
            'details': {
                'dialog_appeared': False,
                'bg_text_detected': False,
                'dialog_closed': False
            }
        }

        has_seen_bg_text = False
        dialog_appeared_step = -1

        for i, screenshot in enumerate(self.screenshots):
            # Get full image text with normalization
            text = self._ocr_region(screenshot, "full").lower()
            norm_text = text.replace(' ', '')
            norm_title = title.lower().replace(' ', '')
            norm_bg = bg_type.lower()

            # Determine if dialog is in current frame
            is_dialog_open = norm_title in norm_text

            if is_dialog_open:
                if not result['details']['dialog_appeared']:
                    result['details']['dialog_appeared'] = True
                    self._log(f"  Step [{i:02d}]: Dialog found '{title}'", "DEBUG")
                
                dialog_appeared_step = i
                
                # Core proof: whether 'smart' text appears inside the dialog
                # Note: we usually detect in the background list area on the left side of the dialog
                if norm_bg in text:
                    has_seen_bg_text = True
                    result['details']['bg_text_detected'] = True
                    self._log(f"  Step [{i:02d}]: ✓ Successfully identified background type text '{bg_type}'", "DEBUG")
                continue

            # If dialog was seen before and now disappeared
            if result['details']['dialog_appeared'] and not is_dialog_open:
                if i > dialog_appeared_step:
                    result['details']['dialog_closed'] = True
                    # Only full score when: dialog appeared, Smart text recognized, and dialog closed
                    if has_seen_bg_text:
                        result['score'] = 1
                        self._log(f"✓ Success: full background addition trajectory detected (open - identified {bg_type} - close)", "SUCCESS")
                        return result

        # Failure diagnosis
        if not result['details']['dialog_appeared']:
            self._log(f"✗ Fail: dialog '{title}' not detected", "FAIL")
        elif not has_seen_bg_text:
            self._log(f"✗ Fail: dialog opened but '{bg_type}' not identified in list (Add not clicked or default param not applied)", "FAIL")
        else:
            self._log(f"✗ Fail: background identified but dialog close action not detected", "FAIL")

        return result

        """
        检测特定元素（如文件名）的出现次数是否增加到期望值
        用于检测复制操作（如复制到窗口B）
        
        Args:
            element_name: element name
            expected_count: expected occurrence count
            
        Returns:
            evaluation result dict
        """
        self._log(f"Checking element count increase: {element_name} -> {expected_count}", "INFO")
        
        result = {
            'function': 'check_element_count_increased',
            'score': 0,
            'max_score': 1,
            'details': {
                'element': element_name,
                'expected_count': expected_count,
                'max_count': 0,
                'found_at': None
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            count = text.count(element_name)
            
            if count > result['details']['max_count']:
                result['details']['max_count'] = count
            
            if count >= expected_count:
                result['score'] = 1
                result['details']['found_at'] = i
                self._log(f"✓ Element '{element_name}' appears {count} times (screenshot {i})", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log(
                f"✗ Element '{element_name}' appeared at most {result['details']['max_count']} times, "
                f"expected {expected_count} times",
                "FAIL"
            )
        
        return result
    
        """
        检测弹窗标题是否出现
        
        Args:
            title: dialog title
            
        Returns:
            evaluation result dict
        """
        self._log(f"Checking dialog title: {title}", "INFO")
        
        result = {
            'function': 'check_dialog_title',
            'score': 0,
            'max_score': 1,
            'details': {'title': title}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            if title in text:
                result['score'] = 1
                result['details']['found_at'] = i
                self._log(f"✓ Dialog title found: {title} (screenshot {i})", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log(f"✗ Dialog title not found: {title}", "FAIL")
        
        return result
    
        """
        检测弹窗是否出现后又消失
        
        Args:
            title: dialog title
            
        Returns:
            evaluation result dict
        """
        self._log(f"Checking dialog appears and closes: {title}", "INFO")
        
        result = {
            'function': 'check_dialog_appeared_and_closed',
            'score': 0,
            'max_score': 1,
            'details': {
                'title': title,
                'appeared': False,
                'closed': False,
                'appeared_at': None,
                'closed_at': None
            }
        }
        
        appeared = False
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            if title in text:
                if not appeared:
                    appeared = True
                    result['details']['appeared'] = True
                    result['details']['appeared_at'] = i
                    self._log(f"  Step [{i:02d}]: Dialog appeared", "DEBUG")
            elif appeared and title not in text:
                result['details']['closed'] = True
                result['details']['closed_at'] = i
                result['score'] = 1
                self._log(f"✓ Dialog appeared and closed: appeared({result['details']['appeared_at']}) → closed({i})", "SUCCESS")
                break
        
        if result['score'] == 0:
            if appeared:
                self._log(f"✗ Dialog '{title}' appeared but not closed", "FAIL")
            else:
                self._log(f"✗ Dialog '{title}' did not appear", "FAIL")
        
        return result

    def _get_parameter_variants(self, parameter_name: str) -> list:
        """
        获取参数名的常见OCR变体
        
        Args:
            parameter_name: original parameter name
            
        Returns:
            variant list
        """
        # OCR variant mapping for common parameter names
        common_variants = {
            'font': ['font', 'Font', 'FONT', 'fon', 'fonl'],
            'color': ['color', 'Color', 'COLOR', 'colour', 'Colour', 'coIor'],
            'eV': ['eV', 'ev', 'EV', 'e V', 'e\/', 'e\\\\/'],
            'FWHM': ['FWHM', 'fwhm', 'FW HM', 'FVVHM'],
            'amount': ['amount', 'Amount', 'AMOUNT', 'amoun', 'arnount'],
            'Rows': ['Rows', 'rows', 'ROWS', 'Row', 'Rovvs'],
            'Columns': ['Columns', 'columns', 'COLUMNS', 'Column', 'Colurnns']
        }
        
        if parameter_name in common_variants:
            return common_variants[parameter_name]
        
        # If no predefined, generate basic variants
        return [
            parameter_name,
            parameter_name.lower(),
            parameter_name.upper(),
            parameter_name.capitalize()
        ]

    def _get_value_variants(self, expected_value: str) -> list:
        """
        获取期望值的常见OCR变体
        
        Args:
            expected_value: original expected value
            
        Returns:
            variant list
        """
        variants = [expected_value]
        
        # Common OCR errors for digits
        # 0 ↔ O, 1 ↔ l/I, 5 ↔ S, 8 ↔ B
        if expected_value.isdigit():
            # Add variants for pure numbers
            variant = expected_value
            variant = variant.replace('0', 'O')
            if variant != expected_value:
                variants.append(variant)
            
            variant = expected_value.replace('1', 'l')
            if variant != expected_value:
                variants.append(variant)
            
            variant = expected_value.replace('1', 'I')
            if variant != expected_value:
                variants.append(variant)
        
        # Decimal point variants
        if '.' in expected_value:
            variants.append(expected_value.replace('.', ','))  # 逗号
            variants.append(expected_value.replace('.', ''))   # 无小数点
        
        # Color name variants
        color_variants = {
            'Red': ['Red', 'red', 'RED', 'Rcd', 'Rc'],
            'Blue': ['Blue', 'blue', 'BLUE', 'Bluc', 'Bl'],
            'Green': ['Green', 'green', 'GREEN', 'Grccn', 'Gr'],
            'Black': ['Black', 'black', 'BLACK', 'Blac'],
            'White': ['White', 'white', 'WHITE', 'Whitc']
        }
        
        if expected_value in color_variants:
            return color_variants[expected_value]
        
        # Add case variants
        if expected_value != expected_value.lower():
            variants.append(expected_value.lower())
        if expected_value != expected_value.upper():
            variants.append(expected_value.upper())
        
        return list(set(variants))  # 去重

    def check_dialog_parameter(self, dialog_title: str, parameter_name, 
                           expected_value=None, region: str = "full") -> Dict[str, Any]:
        """
        检测弹窗中特定参数的值，支持单个或多个参数检查
        
        Args:
            dialog_title: dialog title
            parameter_name: parameter name, can be string or list
            expected_value: expected value, can be string, list, or None (None means only check parameter name exists)
            region: detection region, default "full"
            
        Returns:
            evaluation result dict
        """
        # Convert to list format uniformly
        if isinstance(parameter_name, str):
            parameter_name = [parameter_name]
        
        # Process expected_value
        check_value = True  # whether to check value
        if expected_value is None or expected_value == []:
            # If expected_value not provided, only check that parameter name exists
            check_value = False
            expected_value = [None] * len(parameter_name)
        elif isinstance(expected_value, str):
            expected_value = [expected_value]
        
        # Verify parameter count matches value count (only when value check is needed)
        if check_value and len(parameter_name) != len(expected_value):
            return {
                'function': 'check_dialog_parameter',
                'score': 0,
                'max_score': len(parameter_name),
                'error': 'Mismatch between parameter names and expected values count'
            }
        
        num_params = len(parameter_name)
        
        if check_value:
            self._log(
                f"Checking dialog params: {dialog_title} - {dict(zip(parameter_name, expected_value))} (region: {region})",
                "INFO"
            )
        else:
            self._log(
                f"Checking dialog param name exists: {dialog_title} - {parameter_name} (region: {region})",
                "INFO"
            )
        
        result = {
            'function': 'check_dialog_parameter',
            'score': 0,
            'max_score': num_params,
            'details': {
                'dialog_title': dialog_title,
                'parameters': parameter_name if not check_value else dict(zip(parameter_name, expected_value)),
                'region': region,
                'check_value': check_value,
                'found_params': {}
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, region)
            
            # Check if dialog title exists
            if dialog_title not in text:
                continue
            
            self._log(f"  Step [{i:02d}]: Dialog '{dialog_title}' found in region {region}", "DEBUG")
            
            # Normalize text for looser matching
            normalized_text = text.lower().replace(' ', '').replace('\n', '')
            
            # Check each parameter
            for idx, param_name in enumerate(parameter_name):
                # If this parameter was already found, skip
                if param_name in result['details']['found_params']:
                    continue
                
                expect_val = expected_value[idx] if check_value else None
                
                # Define common OCR variants of parameter names
                param_variants = self._get_parameter_variants(param_name)
                param_variants = self._normalize_ocr_text(param_name)
                
                
                matched = False
                matched_info = None
                
                if not check_value:
                    # Only check if parameter name exists
                    for param_var in param_variants:
                        # Strategy 1: exact match
                        if param_var in text:
                            matched = True
                            matched_info = {
                                'pattern': 'exact_match',
                                'param_variant': param_var,
                                'region': region,
                                'screenshot': i
                            }
                            break
                        
                        # Strategy 2: case-insensitive
                        if param_var.lower() in text.lower():
                            matched = True
                            matched_info = {
                                'pattern': 'case_insensitive',
                                'param_variant': param_var,
                                'region': region,
                                'screenshot': i
                            }
                            break
                        
                        # Strategy 3: normalized matching
                        param_norm = param_var.lower().replace(' ', '')
                        if param_norm in normalized_text:
                            matched = True
                            matched_info = {
                                'pattern': 'normalized',
                                'param_variant': param_var,
                                'region': region,
                                'screenshot': i
                            }
                            break
                    
                    if matched:
                        result['score'] += 1
                        result['details']['found_params'][param_name] = matched_info
                        self._log(
                            f"✓ Found param name: {param_name} (screenshot {i}, {region})",
                            "SUCCESS"
                        )
                
                else:
                    # Check parameter name and value (original logic)
                    value_variants = self._get_value_variants(expect_val)
                    
                    # Strategy 1: exact pattern match
                    for param_var in param_variants:
                        for value_var in value_variants:
                            patterns = [
                                rf'{re.escape(param_var)}\s*[:\-=]?\s*{re.escape(value_var)}',
                                rf'{re.escape(param_var)}.*?{re.escape(value_var)}',
                                rf'{re.escape(value_var)}.*?{re.escape(param_var)}'
                            ]
                            
                            for pattern in patterns:
                                if re.search(pattern, text, re.IGNORECASE):
                                    matched = True
                                    matched_info = {
                                        'pattern': pattern,
                                        'param_variant': param_var,
                                        'value_variant': value_var,
                                        'region': region,
                                        'screenshot': i
                                    }
                                    break
                            if matched:
                                break
                        if matched:
                            break
                    
                    # ... (other strategies omitted, keep original logic)
                    
                    if matched:
                        result['score'] += 1
                        result['details']['found_params'][param_name] = matched_info
                        self._log(
                            f"✓ Found args: {param_name}={expect_val} (screenshot {i}, {region})",
                            "SUCCESS"
                        )
            
            # If all parameters found, return early
            if result['score'] == num_params:
                return result
        
        # Print unfound parameters
        missing_params = [p for p in parameter_name if p not in result['details']['found_params']]
        if missing_params:
            self._log(f"✗ Parameters not found: {missing_params}", "FAIL")
        
        return result
    
    def check_dialog_exists(self, dialog_title: str, region: str = "full") -> Dict[str, Any]:
        """
        检测弹窗是否出现
        
        Args:
            dialog_title: dialog title
            region: detection region, default "full"
            
        Returns:
            evaluation result dict
        """
        self._log(
            f"Checking dialog exists: {dialog_title} (region: {region})",
            "INFO"
        )
        
        result = {
            'function': 'check_dialog_exists',
            'score': 0,
            'max_score': 1,
            'details': {
                'dialog_title': dialog_title,
                'region': region,
                'found_at': None
            }
        }
        
        # Define common OCR variants of dialog titles
        title_variants = self._get_value_variants(dialog_title)
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, region)
            
            # Try matching various dialog title variants
            matched = False
            matched_variant = None
            
            for variant in title_variants:
                # Strategy 1: exact match
                if variant in text:
                    matched = True
                    matched_variant = variant
                    break
                
                # Strategy 2: case-insensitive
                if variant.lower() in text.lower():
                    matched = True
                    matched_variant = variant
                    break
                
                # Strategy 3: match after removing spaces
                text_normalized = text.replace(' ', '').replace('\n', '')
                variant_normalized = variant.replace(' ', '')
                if variant_normalized.lower() in text_normalized.lower():
                    matched = True
                    matched_variant = variant
                    break
            
            if matched:
                result['score'] = 1
                result['details']['found_at'] = i
                result['details']['matched_variant'] = matched_variant
                
                # Print OCR text preview for debugging
                preview = text.replace('\n', ' ')[:200]
                self._log(f"  OCR preview: {preview}", "DEBUG")
                
                self._log(
                    f"✓ Found dialog: {dialog_title} (screenshot {i}, {region})",
                    "SUCCESS"
                )
                return result
        
        # Dialog not found
        self._log(f"✗ Dialog not found: {dialog_title}", "FAIL")
        self._log(f"  Attempted title variants: {title_variants}", "DEBUG")
        
        return result
    
    def check_grid_layout(self, rows: int = 3, columns: int = 3) -> Dict[str, Any]:
        """
        检测网格布局是否设置正确
        
        Args:
            rows: number of rows
            columns: number of columns
            
        Returns:
            evaluation result dict
        """
        self._log(f"Checking grid layout: {rows} rows x {columns} columns", "INFO")
        
        result = {
            'function': 'check_grid_layout',
            'score': 0,
            'max_score': 1,
            'details': {
                'rows': rows,
                'columns': columns
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            # Find Rows and Columns settings
            rows_match = re.search(rf'Rows?\s*[:\-=]?\s*{rows}', text, re.IGNORECASE)
            columns_match = re.search(rf'Columns?\s*[:\-=]?\s*{columns}', text, re.IGNORECASE)
            
            if rows_match and columns_match:
                result['score'] = 1
                result['details']['found_at'] = i
                self._log(f"✓ Grid layout found: {rows}x{columns} (screenshot {i})", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log(f"✗ Grid layout not found: {rows}x{columns}", "FAIL")
        
        return result
    
    def check_energy_axis_reversed(self) -> Dict[str, Any]:
        """
        检测能量轴是否反向
        通过检测 "Reverse Energy Axis" 弹窗或选项
        
        Returns:
            evaluation result dict
        """
        self._log("Checking energy axis reversal", "INFO")
        
        result = {
            'function': 'check_energy_axis_reversed',
            'score': 0,
            'max_score': 1,
            'details': {}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            if "Reverse Energy Axis" in text:
                result['score'] = 1
                result['details']['found_at'] = i
                self._log(f"✓ Energy axis reversal option found (screenshot {i})", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log("✗ 未发现能量轴反向选项", "FAIL")
        
        return result
    
    def _get_filename_variants(self, standard_filename: str) -> List[str]:
        """
        获取文件名的所有可能变体
        
        Args:
            standard_filename: standard filename (e.g. 'C1s Scan')
        
        Returns:
            list of all possible variants
        """
        # Define variant mapping
        variants_map = {
            'C1s Scan': ['c1sscan', 'c1scan', 'clsscan', 'cisscan', 'C1s Scan', 'CIs Scan'],
            'O1s Scan': ['o1sscan', 'o1scan', 'olsscan', 'oisscan',  'O1s Scan', 'O1s', 'o1s scan'],
            'Zn2p Scan': ['zn2pscan', 'zn2scan', 'znzpscan', 'zn2p', 'znzp', 'Zn2p Scan', 'Zn2p', 'zn2p scan'],
            'XPS Survey': ['xpssurvey', 'xps', 'survey', 'XPS Survey', 'XPS', 'xps survey'],
            'Survey Scan': ['surveyscan', 'survey', 'Survey Scan', 'survey scan']
        }
        
        if standard_filename in variants_map:
            return variants_map[standard_filename]
        
        # If not in mapping, return basic variant
        return [
            standard_filename,
            standard_filename.lower(),
            standard_filename.lower().replace(' ', ''),
            standard_filename.replace(' ', '')
        ]

    def check_file_duplicated(self, original_file: str, expected_copies: int = 2) -> Dict[str, Any]:
        """
        检测文件是否被复制了指定次数（直接统计OCR文本）
        """
        self._log(
            f"Checking file copy: {original_file} should appear {expected_copies} times", 
            "INFO"
        )
        
        result = {
            'function': 'check_file_duplicated',
            'score': 0,
            'max_score': 1,
            'details': {
                'original_file': original_file,
                'expected_copies': expected_copies,
                'status': 'failed'
            }
        }
        
        # Get all possible variants of a filename
        original_variants = self._get_filename_variants(original_file)
        
        for i, screenshot in enumerate(self.screenshots):
            # Directly OCR the full screenshot
            ocr_text = self._ocr_region(screenshot, "full")
            lines = ocr_text.split('\n')
            
            # Count variant occurrences (by line, avoid substring issues)
            max_count = 0
            matched_variant = None
            
            for variant in original_variants:
                count = 0
                variant_lower = variant.lower()
                
                # Check line by line, count each line at most once
                for line in lines:
                    line_lower = line.strip().lower()
                    # Exact match or contains match
                    if line_lower == variant_lower or variant_lower in line_lower:
                        count += 1
                
                if count > max_count:
                    max_count = count
                    matched_variant = variant
            
            self._log(
                f"  Step [{i:02d}]: Found {max_count} lines containing '{matched_variant}' in OCR (expected {expected_copies})", 
                "DEBUG"
            )
            
            if max_count >= expected_copies:
                # Count Binding Energy
                binding_energy_count = 0
                for line in lines:
                    line_lower = line.strip().lower()
                    if 'binding' in line_lower and 'energy' in line_lower:
                        binding_energy_count += 1
                
                self._log(
                    f"  Step [{i:02d}]: Binding Energy count: {binding_energy_count} (expected: {expected_copies})",
                    "DEBUG"
                )
                
                if binding_energy_count >= expected_copies:
                    result['score'] = 1
                    result['details']['status'] = 'success'
                    result['details']['found_at'] = i
                    result['details']['actual_copies'] = max_count
                    result['details']['matched_variant'] = matched_variant
                    result['details']['binding_energy_count'] = binding_energy_count
                    
                    self._log(
                        f"✓ Success: detected {max_count} copies of {original_file} at step {i}", 
                        "SUCCESS"
                    )
                    return result
        
        self._log(f"✗ Fail: insufficient file copies detected", "FAIL")
        return result


    def evaluate_task(self, task_name: str, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估单个任务
        
        Args:
            task_name: task name
            checks: list of check items
            
        Returns:
            evaluation result
        """
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
            else:
                self._log(f"⚠️ Evaluation function not found: {func_name}", "WARNING")
        
        if task_result['max_score'] > 0:
            pass_rate = (task_result['total_score'] / task_result['max_score']) * 100
            task_result['pass_rate'] = f"{pass_rate:.1f}%"
        else:
            task_result['pass_rate'] = "N/A"
        
        self._log(
            f"\nEvaluation complete: {task_result['total_score']}/{task_result['max_score']} "
            f"({task_result['pass_rate']})",
            "INFO"
        )
        
        # Save results
        result_file = self.evaluate_folder / f"{task_name}_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(task_result, f, indent=2, ensure_ascii=False)
        
        return task_result


# ==================== TASK CONFIGS ====================

TASK_CONFIGS = {
    # Basic difficulty (10 tasks)
    "in1": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['C1s Scan']}}
    ],
    
    "in2": [
        {'function': 'check_multiple_files_imported', 'args': {
            'expected_files': ['C1s Scan', 'O1s Scan', 'Zn2p Scan', 'XPS Survey']
        }}
    ],
    
    "in3": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['C1s Scan']}},
        {'function': 'check_image_zoom', 'args': {'target_value': '282'}}
    ],
    
    "in4": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['O1s Scan']}},
        {'function': 'check_stacked_graph', 'args': {
            'small_values': ['2', '4', '6', '8'],
            'normal_markers': ['e4', 'e5', '00e']
        }}
    ],
    
    "in5": [
        {"function": "check_multiple_files_imported", "args": {"expected_files": ["XPS Survey"]}},
        {
            "function": "check_duplicate_files_imported", 
            "args": {
                "expected_files": ["XPS Survey", "XPS Survey"] 
            }
        }
    ],
    
    "in6": [
        {
            'function': 'check_multiple_files_imported', 
            'args': {'expected_files': ['Zn2p Scan']}
        },
        {
            'function': 'check_background_added_successfully', 
            'args': {
                'title': 'User Backgrounds',
                'bg_type': 'Smart'
            }
        }
    ],
    
    "in7": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['Zn2p Scan']}},
         {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Chart',
            'region': 'full'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Chart',
            'parameter_name': 'Title Font',
            'expected_value': '20pt',
            'region':'full'
        }}
    ],
    
    "in8": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['Zn2p Scan']}},
         {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Chart',
            'region': 'full'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Chart',
            'parameter_name': 'Title colour',
            'expected_value': 'Transparent',
            'region':'full'
        }}
    ],
    
    "in9": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['Zn2p Scan']}},
        {'function': 'check_energy_axis_reversed', 'args': {}}
    ],
    
    "in10": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['C1s Scan']}},
         {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Grid Properties',
            'region': 'center50%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Grid Properties',
            'parameter_name': ['Rows','Columns'],
            'expected_value': ['3','3'],
            'region':'center50%'
        }}
    ],
    
    # Medium difficulty (5 tasks)
    "in11": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['Zn2p Scan']}},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Fitting',
            'region': 'left20%'
        }}
    ],
    
    "in12": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['O1s Scan']}},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Charge Shift',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Charge Shift',
            'parameter_name': ['Shift By'],
            'expected_value': ['0.14'],
            'region':'left40%'
        }}
    ],
    
    "in13": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['XPS Survey']}},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Smoothing',
            'region': 'center50%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Smoothing',
            'parameter_name': ['FWHM (eV)'],
            'expected_value': ['2.115'],
            'region':'center50%'
        }}
    ],
    
    "in14": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['O1s Scan']}},
        
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Peak Add',
            'parameter_name': 'eV',
            'expected_value': '20',
            'region':'left20%'
        }}
    ],
    
    "in15": [
        {'function': 'check_multiple_files_imported', 'args': {
            'expected_files': ['C1s Scan', 'XPS Survey']
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'LightBox',
            'region': 'left20%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'LightBox',
            'parameter_name': ['C1s Scan','XPS Survey'],
            'expected_value': [],
            'region':'left20%'
        }}
    ],
    
    # Complex difficulty (5 tasks)
    "in16": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['C1s Scan']}},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Add',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Peak Add',
            'parameter_name': ['Iterations'],
            'expected_value': [],
            'region':'left40%'
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Charge Shift',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Charge Shift',
            'parameter_name': ['Shift By'],
            'expected_value': ['19.00'],
            'region':'left40%'
        }}
    ],
    
    "in17": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['O1s Scan']}},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Add',
            'region': 'left20%'
        }},
         {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Fitting',
            'region': 'left20%'
        }}
    ],
    
    "in18": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['C1s Scan']}},
        {'function': 'check_file_duplicated', 'args': {
            'original_file': 'C1s Scan',
            'expected_copies': 2 
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Add Constant',
            'region': 'center50%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Add Constant',
            'parameter_name': ['Constant'],
            'expected_value': ['3333'],
            'region':'center50%'
        }},
         {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'LightBox',
            'region': 'left20%'
        }},
         {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'LightBox',
            'parameter_name': ['C1s Scan','C1s Scan_01'],
            'expected_value': [],
            'region':'left20%'
        }}
    ],
    
    "in19": [
        {'function': 'check_multiple_files_imported', 'args': {'expected_files': ['O1s Scan']}},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Add',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Peak Add',
            'parameter_name': ['Start (eV)','End (eV)'],
            'expected_value': ['545','540'],
            'region':'left40%'
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Fitting',
            'region': 'left20%'
        }}
    ],
    
    "in20": [
        {'function': 'check_multiple_files_imported', 'args': {
            'expected_files': ['C1s Scan', 'O1s Scan', 'Survey Scan']
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Add',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Peak Fitting',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_exists', 'args': {
            'dialog_title': 'Charge Shift',
            'region': 'left40%'
        }},
        {'function': 'check_dialog_parameter', 'args': {
            'dialog_title': 'Charge Shift',
            'parameter_name': ['Shift By'],
            'expected_value': ['360'],
            'region':'left40%'
        }}
    ]
}


# ==================== MAIN FUNCTION ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Avantage XPS Evaluation System')
    parser.add_argument('folder', type=str, help='Path to screenshot folder')
    parser.add_argument('task', type=str, help='Task name')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Avantage XPS Evaluation System")
    print(f"{'='*60}\n")
    
    folder_path = Path(args.folder).resolve()
    
    if not folder_path.exists():
        print(f"❌ 错误: 文件夹不存在: {folder_path}")
        return
    
    print(f"✓ 文件夹: {folder_path}")
    print(f"✓ 任务: {args.task}\n")
    
    if args.task not in TASK_CONFIGS:
        print(f"❌ 未找到任务 '{args.task}'")
        print(f"\n可用任务:")
        for task_name in TASK_CONFIGS.keys():
            print(f"  - {task_name}")
        return
    
    try:
        evaluator = AvantageEvaluator(str(folder_path))
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