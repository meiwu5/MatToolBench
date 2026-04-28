"""
Jade XRD Evaluation System - Improved v2
Main improvement: enhanced recognition of concatenated formats like XRDAxrdml
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import easyocr
from PIL import Image
import numpy as np

class JadeEvaluator:
    """Jade XRD Task Evaluator"""
    
    def __init__(self, base_folder: str):
        self.base_folder = Path(base_folder).resolve()
        
        if not self.base_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {self.base_folder}")
        
        self.task_folder_name = self.base_folder.name
        self.screenshots = []
        self.ally_trees = []
        self.ocr_reader = easyocr.Reader(['en'], gpu=True)
        self.current_file = None
        
        jade_folder = self.base_folder.parent
        self.evaluate_folder = jade_folder / "evaluate"
        
        if not self.evaluate_folder.exists():
            self.evaluate_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created evaluation output directory: {self.evaluate_folder}")
        
        self.ocr_cache_folder = self.evaluate_folder / "ocr_results" / self.task_folder_name
        if not self.ocr_cache_folder.exists():
            self.ocr_cache_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created OCR cache directory: {self.ocr_cache_folder}")
        
        self.log_file = self.evaluate_folder / "evaluation_log.txt"
        
        self._load_files()
        
        # Preprocessing: identify filenames in screenshots
        self.screenshot_files = self._identify_files_in_screenshots()
        
    def _load_files(self):
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
        match = re.search(r'step_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0

    def _ocr_region(self, screenshot_path: Path, region: str = "full") -> str:
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = self.ocr_cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        img = Image.open(screenshot_path)
        width, height = img.size
        
        if region == "top20%":
            img = img.crop((0, 0, width, int(height * 0.2)))
        elif region == "bottom20%":
            img = img.crop((0, int(height * 0.8), width, height))
        elif region == "top5%":
            img = img.crop((0, 0, width, int(height * 0.05)))
        elif region == "top10%":
            img = img.crop((0, 0, width, int(height * 0.1)))
        elif region == "bottom10%":
            img = img.crop((0, int(height * 0.9), width, height))
        elif region == "bottom5%":
            img = img.crop((0, int(height * 0.95), width, height))
        
        img_array = np.array(img)
        results = self.ocr_reader.readtext(img_array)
        text = "\n".join([result[1] for result in results])
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return text
    
    def _log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [{self.task_folder_name}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def _read_ally_tree(self, index: int) -> str:
        if 0 <= index < len(self.ally_trees):
            with open(self.ally_trees[index], 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _identify_files_in_screenshots(self) -> List[str]:
        self._log("Starting preprocessing: identifying filenames in all screenshots...", "INFO")
        
        screenshot_files = []
        last_detected_file = None
        
        for i, screenshot in enumerate(self.screenshots):
            title_text = self._ocr_region(screenshot, "top5%")
            current_file = self._extract_filename_from_text(title_text)
            
            if not current_file:
                current_file = last_detected_file
                preview = title_text.replace('\n', ' ')[:150]
                self._log(f"  Frame [{i:02d}]: Unable to identify | OCR: {preview}", "DEBUG")
            else:
                last_detected_file = current_file
                if 'XRDA' in title_text or 'XRDa' in title_text:
                    self._log(f"  Frame [{i:02d}]: ✓ {current_file} (XRDA→XRD4)", "DEBUG")
                elif 'XRD' in current_file:
                    self._log(f"  Frame [{i:02d}]: ✓ {current_file}", "DEBUG")
                else:
                    self._log(f"  Frame [{i:02d}]: ✓ {current_file}", "DEBUG")
            
            screenshot_files.append(current_file)
        
        self._log(f"✓ File identification complete: {len(screenshot_files)} frames total", "INFO")
        
        unique_files = set([f for f in screenshot_files if f])
        if unique_files:
            self._log(f"  Identified files: {', '.join(sorted(unique_files))}", "INFO")
        else:
            self._log(f"  ⚠️ Warning: No filenames identified!", "WARNING")
        
        return screenshot_files
    
    def _normalize_ocr_text(self, text: str) -> str:
        if not text:
            return ""
        
        normalized = text
        
        # XRD series misrecognition correction
        xrd_replacements = {
            'XRDA': 'XRD4', 'XRDa': 'XRD4',
            'XRDB': 'XRD8', 'XRDb': 'XRD8',
            'XRDI': 'XRD1', 'XRDi': 'XRD1',
            'XRDl': 'XRD1', 'XRDL': 'XRD1',
            'XRDO': 'XRD0', 'XRDo': 'XRD0',
            'XRDS': 'XRD5', 'XRDs': 'XRD5',
            'XRDZ': 'XRD2', 'XRDz': 'XRD2',
        }
        
        for wrong, correct in xrd_replacements.items():
            normalized = normalized.replace(wrong, correct)
        
        # WRT series misrecognition correction
        wrt_replacements = {
            'WRT-Z2X': 'WRT-ZSX',
            'WRT-ZzX': 'WRT-ZSX',
            'WRT-ZSX-S': 'WRT-ZSX-5',
            'WRT-ZSX-s': 'WRT-ZSX-5',
        }
        
        for wrong, correct in wrt_replacements.items():
            normalized = normalized.replace(wrong, correct)
        
        return normalized

    def _extract_filename_from_text(self, text: str) -> str:
        """Extract filename from OCR text - enhanced (prefer bracket extraction)"""
        if not text:
            return None
        
        norm_text = self._normalize_ocr_text(text)
        
        # ===== Strategy-1: Bracket extraction (highest priority) =====
        # Filename is usually in title bar brackets, e.g. [XRD1.xrdml] or [WRT-ZSX-5.txt]
        bracket_patterns = [
            r'\[([^\]]*(?:XRD|xrd)[^\]]*)\]',  # bracket content containing XRD
            r'\[([^\]]*(?:WRT|wrt)[^\]]*)\]',  # bracket content containing WRT
        ]
        
        for pattern in bracket_patterns:
            # First search in normalized text
            match = re.search(pattern, norm_text)
            if match:
                bracket_content = match.group(1).strip()
                filename = self._parse_bracket_content(bracket_content)
                if filename:
                    self._log(f"    方括号提取成功: [{bracket_content}] → {filename}", "DEBUG")
                    return filename
            
            # Then search in original text
            match = re.search(pattern, text)
            if match:
                bracket_content = match.group(1).strip()
                # Normalize first, then parse
                norm_content = self._normalize_ocr_text(bracket_content)
                filename = self._parse_bracket_content(norm_content)
                if filename:
                    self._log(f"    方括号提取成功(规范化): [{bracket_content}] → {filename}", "DEBUG")
                    return filename
        
        # ===== Strategy-0: Concatenated form =====
        # Match: XRDAxrdml, XRD4xrdml, XRD1xrdml etc.
        connected_pattern = r'XRD([1-4AaIilLZz])xrdml'
        
        # First search in normalized text
        match = re.search(connected_pattern, norm_text, re.IGNORECASE)
        if match:
            char = match.group(1).upper()
            char_map = {'A': '4', 'I': '1', 'L': '1', 'Z': '2', '1': '1', '2': '2', '3': '3', '4': '4'}
            if char in char_map:
                return f'XRD{char_map[char]}.xrdml'
        
        # Then search in original text
        match = re.search(connected_pattern, text, re.IGNORECASE)
        if match:
            char = match.group(1).upper()
            char_map = {'A': '4', 'I': '1', 'L': '1', 'Z': '2', '1': '1', '2': '2', '3': '3', '4': '4'}
            if char in char_map:
                return f'XRD{char_map[char]}.xrdml'
        
        # ===== Strategy-1: Standard format (with dots) =====
        ext_patterns = [
            r'\b(XRD[1-4]\.xrdml)\b',
            r'\b(WRT-ZSX-5\.txt)\b',
        ]
        
        for pattern in ext_patterns:
            match = re.search(pattern, norm_text, re.IGNORECASE)
            if match:
                filename = match.group(1)
                if 'xrd' in filename.lower():
                    num = filename[3]
                    return f'XRD{num}.xrdml'
                return filename
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                filename = match.group(1)
                if 'xrd' in filename.lower():
                    num = filename[3]
                    return f'XRD{num}.xrdml'
                return filename
        
        # ===== Strategy-2: Without extension =====
        simple_patterns = [
            r'\b(XRD[1-4])\b',
            r'\b(WRT-ZSX-5)\b',
        ]
        
        for pattern in simple_patterns:
            match = re.search(pattern, norm_text, re.IGNORECASE)
            if match:
                filename = match.group(1).strip()
                if 'xrd' in filename.lower():
                    num = filename[3]
                    return f'XRD{num}'
                return filename
        
        # ===== Strategy-3: Fuzzy matching =====
        fuzzy_pattern = r'\bXRD\s*[1-4AaIilLZz]\b'
        match = re.search(fuzzy_pattern, norm_text, re.IGNORECASE)
        if match:
            xrd_part = match.group(0).replace(' ', '').upper()
            last_char = xrd_part[-1]
            char_map = {'A': '4', 'I': '1', 'L': '1', 'Z': '2', '1': '1', '2': '2', '3': '3', '4': '4'}
            if last_char in char_map:
                return f'XRD{char_map[last_char]}'
        
        return None
    
    def _parse_bracket_content(self, content: str) -> str:
        """
        解析方括号内的内容，提取文件名
        
        Args:
            content: content inside brackets (already normalized)
        
        Returns:
            标准化的文件名，如果无法识别则返回None
        """
        if not content:
            return None
        
        content = content.strip()
        
        # XRD series files - match XRD + digit (1-4)
        xrd_match = re.search(r'XRD\s*([1-4])', content, re.IGNORECASE)
        if xrd_match:
            num = xrd_match.group(1)
            # Check if there is an extension
            if '.xrdml' in content.lower() or 'xrdml' in content.lower():
                return f'XRD{num}.xrdml'
            else:
                return f'XRD{num}'
        
        # WRT series files - match WRT-ZSX-5 or its variants
        wrt_match = re.search(r'WRT[-\s]*ZSX[-\s]*5', content, re.IGNORECASE)
        if wrt_match:
            # Check if there is an extension
            if '.txt' in content.lower():
                return 'WRT-ZSX-5.txt'
            else:
                return 'WRT-ZSX-5'
        
        return None

    def _fuzzy_filename_match(self, filename: str, text: str) -> bool:
        if not text:
            return False

        norm_text = self._normalize_ocr_text(text)
        text_lower = text.lower()
        norm_text_lower = norm_text.lower()

        filename_base = filename
        for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
            if filename_base.lower().endswith(ext):
                filename_base = filename_base[:-len(ext)]
                break
        filename_base = filename_base.rstrip('.').strip()
        
        if not filename_base:
            return False
        
        base_lower = filename_base.lower()

        # Quick match
        if filename in text or filename.lower() in text_lower:
            return True
        if filename_base in text or base_lower in text_lower:
            return True
        if filename in norm_text or filename.lower() in norm_text_lower:
            return True
        if filename_base in norm_text or base_lower in norm_text_lower:
            return True

        # Generate variants
        variants = set([filename_base, base_lower])

        digit_replacements = {
            '0': ['0', 'O', 'o'],
            '1': ['1', 'I', 'i', 'l', 'L', '|'],
            '2': ['2', 'Z', 'z'],
            '4': ['4', 'A', 'a'],
            '5': ['5', 'S', 's'],
            '8': ['8', 'B', 'b'],
        }

        current_variants = list(variants)
        for digit, reps in digit_replacements.items():
            if digit in filename_base:
                new_vars = []
                for var in current_variants:
                    for rep in reps:
                        new_vars.append(var.replace(digit, rep))
                current_variants.extend(new_vars)

        variants.update(current_variants)

        for variant in variants:
            if variant in text or variant in norm_text:
                return True
            if variant in text_lower or variant in norm_text_lower:
                return True

        return False

    def _extract_imax(self, text: str):
        if not text:
            return None
        
        norm_text = text.lower()
        norm_text = re.sub(r'\s+', ' ', norm_text)
        norm_text = norm_text.replace('lmax', 'max').replace('ilmax', 'imax')
        
        patterns = [
            r'(?:i|1|l|!)?\s*max\s*[\)\]~=-]+\s*(\d+)(?=\D|$)',
            r'i\s*\(\s*max\s*\)\s*[=~-]+\s*(\d+)',
            r'imax\s*[=~-]+\s*(\d+)',
            r'max\s*[\)\]~=-]+\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, norm_text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
                
        return None

    # ============ EVALUATION FUNCTIONS ============

    def check_file_opened(self, expected_filename: str) -> Dict[str, Any]:
        self._log(f"检查文件打开: {expected_filename}", "INFO")
        
        result = {
            'function': 'check_file_opened',
            'expected_file': expected_filename,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'status': 'not_found'}
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        expected_base = expected_filename
        for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
            if expected_filename.lower().endswith(ext):
                expected_base = expected_filename[:-len(ext)]
                break
        expected_base = expected_base.rstrip('.').strip()
        
        found_index = -1
        for i, detected_file in enumerate(self.screenshot_files):
            if detected_file:
                detected_base = detected_file
                for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
                    if detected_file.lower().endswith(ext):
                        detected_base = detected_file[:-len(ext)]
                        break
                detected_base = detected_base.rstrip('.').strip()
                
                if expected_base.lower() in detected_base.lower() or \
                   detected_base.lower() in expected_base.lower():
                    found_index = i
                    result['details']['detected_file'] = detected_file
                    break
        
        if found_index >= 0:
            result['score'] = 1
            result['details']['found_at_step'] = found_index
            self.current_file = self.screenshot_files[found_index]
            
            if found_index == 0:
                status = "初始已打开"
                msg = f"✓ File {expected_filename} initially opened (recognized as: {self.current_file})"
            else:
                status = "过程中打开"
                msg = f"✓ File {expected_filename} opened at step {found_index} (recognized as: {self.current_file})"
            
            result['details']['status'] = status
            self._log(msg, "SUCCESS")
        else:
            self.current_file = None
            self._log(f"✗ 未检测到文件 {expected_filename}", "FAIL")
        
        return result
            
    def check_peak_finding(self) -> Dict[str, Any]:
        self._log("检查寻峰操作", "INFO")
        
        result = {
            'function': 'check_peak_finding',
            'score': 0,
            'max_score': 1,
            'details': {}
        }
        
        if len(self.screenshots) < 2:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        first_text = self._ocr_region(self.screenshots[0], "bottom10%")
        last_text = self._ocr_region(self.screenshots[-1], "bottom10%")
        
        has_zero_peaks = "0 Peaks" in first_text or "d=?" in first_text
        peak_match = re.search(r'(\d+)\s*Peaks?', last_text, re.IGNORECASE)
        if peak_match:
            peak_count = int(peak_match.group(1))
        has_peaks = peak_match and int(peak_match.group(1)) > 0
        
        if has_zero_peaks and has_peaks and peak_count != 2:
            result['score'] = 1
            self._log(f"✓ 寻峰成功: 0 → {peak_match.group(1)} Peaks", "SUCCESS")
        else:
            self._log("✗ 寻峰未完成", "FAIL")
        
        return result

    def check_peak_add_two(self) -> Dict[str, Any]:
        """
        检查增加一个峰的操作
        
        检测逻辑：
        - Peak count in bottom 20% changes from X Peaks to X+1 Peaks
        - e.g.: 2 Peaks → 3 Peaks
        
        Returns:
            包含检测结果的字典
        """
        self._log("检查增加一个峰操作", "INFO")
        
        result = {
            'function': 'check_peak_add_one',
            'score': 0,
            'max_score': 1,
            'details': {
                'peak_counts': [],  # 记录所有帧的峰数量
                'initial_peaks': None,
                'final_peaks': None,
                'increase': None
            }
        }
        
        if len(self.screenshots) < 2:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        # Iterate all screenshots, extract peak counts
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "bottom20%")
            
            # Extract peak count
            peak_match = re.search(r'(\d+)\s*Peaks?', text, re.IGNORECASE)
            
            if peak_match:
                peak_count = int(peak_match.group(1))
                result['details']['peak_counts'].append({
                    'step': i,
                    'count': peak_count
                })
                self._log(f"  步骤 [{i:02d}]: 检测到 {peak_count} Peaks", "DEBUG")
        
        # Analyze peak count change
        if len(result['details']['peak_counts']) >= 2:
            # Get initial peak count (first detected value, can be 0)
            initial_peak = result['details']['peak_counts'][0]['count']
            result['details']['initial_peaks'] = initial_peak
            
            # Get final peak count (last value)
            final_peak = result['details']['peak_counts'][-1]['count']
            result['details']['final_peaks'] = final_peak
            
            # Calculate increment
            increase = final_peak - initial_peak
            result['details']['increase'] = increase
            
            # Scoring: exactly 1 peak added
            if increase == 2:
                result['score'] = 1
                self._log(f"✓ 增加两个峰成功: {initial_peak} Peaks → {final_peak} Peaks (+2)", "SUCCESS")
            elif increase > 0 and increase !=2:
                self._log(f"⚠ 峰数量增加了{increase}个: {initial_peak} → {final_peak} (预期+2)", "WARNING")
            elif increase == 0:
                self._log(f"✗ 峰数量未变化: {initial_peak} Peaks", "FAIL")
            else:
                self._log(f"✗ 峰数量减少了: {initial_peak} → {final_peak} ({increase})", "FAIL")
        else:
            self._log("✗ 检测到的峰数量记录不足", "FAIL")
        
        return result

    def check_background_removal(self) -> Dict[str, Any]:
        self._log("检查背景扣除", "INFO")
        
        result = {
            'function': 'check_background_removal',
            'score': 0,
            'max_score': 1,
            'details': {}
        }

        INITIAL_IMAX_MAP = {
            'WRT-ZSX-5.txt': 5792, 'WRT-ZSX-5': 5792,
            'XRD1.xrdml': 454, 'XRD1': 454,
            'XRD2.xrdml': 1757, 'XRD2': 1757,
            'XRD3.xrdml': 456, 'XRD3': 456,
            'XRD4.xrdml': 463, 'XRD4': 463,
        }

        dynamic_baselines = {}

        for i, screenshot in enumerate(self.screenshots):
            current_fname = self.screenshot_files[i]
            
            if not current_fname:
                continue

            data_text = self._ocr_region(screenshot, "top20%")
            imax = self._extract_imax(data_text)
            
            if imax is None:
                continue

            baseline = None
            source = None
            
            fname_base = current_fname
            for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
                if current_fname.lower().endswith(ext):
                    fname_base = current_fname[:-len(ext)]
                    break
            
            for preset_fname, preset_val in INITIAL_IMAX_MAP.items():
                preset_base = preset_fname
                for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
                    if preset_fname.lower().endswith(ext):
                        preset_base = preset_fname[:-len(ext)]
                        break
                
                if fname_base.lower() == preset_base.lower():
                    baseline = preset_val
                    source = f"预设({preset_fname})"
                    break
            
            if baseline is None:
                if current_fname not in dynamic_baselines:
                    dynamic_baselines[current_fname] = imax
                baseline = dynamic_baselines[current_fname]
                source = "动态"

            drop_ratio = (baseline - imax) / baseline if baseline > 0 else 0

            if drop_ratio >= 0.20 and imax > 0:
                result['score'] = 1
                result['details'].update({
                    'file': current_fname,
                    'initial': baseline,
                    'final': imax,
                    'drop': f"{drop_ratio*100:.1f}%",
                    'frame': i
                })
                self._log(f"✓ 背景扣除成功: {baseline} → {imax} (降{drop_ratio*100:.1f}%)", "SUCCESS")
                return result

        self._log("✗ 未发现背景扣除", "FAIL")
        return result
        
    def check_smoothing(self) -> Dict[str, Any]:
        self._log("检查平滑操作", "INFO")
        
        result = {
            'function': 'check_smoothing',
            'score': 0,
            'max_score': 1,
            'details': {'found_at_steps': []}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "top20%")
            
            if "Smooth whole Pattern" in text or "Smooth Whole Pattern" in text:
                result['details']['found_at_steps'].append(i)
        
        if result['details']['found_at_steps']:
            result['score'] = 1
            self._log(f"✓ 平滑操作成功", "SUCCESS")
        else:
            self._log("✗ 未发现平滑操作", "FAIL")
        
        return result
    
    def check_smoothing_and_background(self) -> Dict[str, Any]:
        result = {
            'function': 'check_smoothing_and_background',
            'score': 0,
            'max_score': 2,
            'details': {}
        }
        
        smoothing_result = self.check_smoothing()
        background_result = self.check_background_removal()
        
        result['details']['smoothing'] = smoothing_result
        result['details']['background'] = background_result
        result['score'] = smoothing_result['score'] + background_result['score']
        
        return result
    
    def check_axis_switch(self) -> Dict[str, Any]:
        self._log("检查坐标轴切换", "INFO")
        
        result = {
            'function': 'check_axis_switch',
            'score': 0,
            'max_score': 1,
            'details': {'axis_sequence': []}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "bottom20%")
            
            if "Two-theta" in text or "Two-Theta" in text or "2θ" in text:
                result['details']['axis_sequence'].append(('two-theta', i))
            elif "d-Scale" in text or "d Scale" in text:
                result['details']['axis_sequence'].append(('d-scale', i))
        
        sequence = [axis[0] for axis in result['details']['axis_sequence']]
        
        if len(sequence) >= 3:
            if sequence[0] == 'two-theta' and 'd-scale' in sequence and sequence[-1] == 'two-theta':
                result['score'] = 1
                self._log(f"✓ 坐标轴切换成功", "SUCCESS")
        
        if result['score'] == 0:
            self._log("✗ 坐标轴切换未完成", "FAIL")
        
        return result
    
    def check_axes_menu(self) -> Dict[str, Any]:
        """
        检查是否选择了Zoom菜单（通过检测下拉菜单展开）
        
        检测策略：
        只检测Axes下拉菜单的展开状态（菜单项检测）
        - Must detect Axes-specific menu items (e.g. X-axis options, Y-axis options)
        - Threshold: ≥3 menu items indicates menu is expanded
        
        注意：
        - Seeing "Axes" in menu bar ≠ Axes selected (may be display only)
        - Must detect dropdown menu expansion to count as instruction complete
        
        Returns:
            包含检测结果的字典
        """
        self._log("检查Axes菜单选择操作（检测下拉菜单展开）", "INFO")
        
        result = {
            'function': 'check_axes_menu',
            'score': 0,
            'max_score': 1,
            'details': {
                'menu_expanded_steps': [],
                'menu_items_detected': []
            }
        }
        
        if not self.screenshots:
            result['details']['error'] = "无截图"
            return result
        
        # Iterate all screenshots, look for Axes dropdown menu
        for i, screenshot in enumerate(self.screenshots):
            # OCR recognition: full region (menu may be anywhere)
            full_text = self._ocr_region(screenshot, "full")
            
            # Detect Axes menu dropdown content
            # Options specific to the Axes menu
            axes_menu_items = [
                # X-axis options (specific to Axes menu)
                "Grid OFF",
                "Grid ON (X)",
                "Grid ON (Y)",
                "Auto Scale",
                "Full Range",
                # Y-axis options (specific to Axes menu)
                "Display Range",
                "Vertical Marker",
            ]
            
            menu_items_found = 0
            found_items = []
            for item in axes_menu_items:
                if item in full_text:
                    menu_items_found += 1
                    found_items.append(item)
            
            # Decision: 3+ Axes-specific menu items detected → menu is expanded
            if menu_items_found >= 3:
                result['details']['menu_expanded_steps'].append(i)
                result['details']['menu_items_detected'].append({
                    'step': i,
                    'count': menu_items_found,
                    'items': found_items
                })
                
                # Show first 3 detected items
                items_preview = ', '.join(found_items[:3])
                if len(found_items) > 3:
                    items_preview += '...'
                self._log(f"  步骤 [{i:02d}]: ✓ 检测到Axes下拉菜单展开 (找到{menu_items_found}个菜单项: {items_preview})", "DEBUG")
        
        # Scoring: score if menu expansion detected at least once
        if len(result['details']['menu_expanded_steps']) > 0:
            result['score'] = 1
            first_detection = result['details']['menu_expanded_steps'][0]
            self._log(f"✓ 检测到Axes菜单展开: 首次在步骤 {first_detection}", "SUCCESS")
            self._log(f"  菜单展开步骤: {result['details']['menu_expanded_steps']}", "DEBUG")
        else:
            self._log("✗ 未检测到Axes下拉菜单展开", "FAIL")
            self._log("  提示: 必须检测到Axes特有的菜单项（如X-axis选项）才算选择了菜单", "INFO")
        
        return result

    def check_wpf_refinement(self) -> Dict[str, Any]:
        self._log("检查WPF拟合结果", "INFO")
        
        result = {
            'function': 'check_wpf_refinement',
            'score': 0,
            'max_score': 1,
            'details': {}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "底部5")
            
            # Check if there are no peaks
            peaks_match = re.search(r'peaks?', text, re.IGNORECASE)
            if peaks_match:
                continue  # if peaks found, skip this screenshot
            
            # Check R-value format 1: R-number or R=number
            r_match = re.search(r'R\s*[-=]\s*(\d+\.?\d*)', text)
            if r_match:
                result['details']['r_value'] = r_match.group(1)
                result['score'] = 1
                self._log(f"✓ WPF拟合结果: R={r_match.group(1)}", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log("✗ 未发现WPF拟合结果", "FAIL")
        
        return result

    def check_refinement_result(self) -> Dict[str, Any]:
        self._log("检查拟合结果", "INFO")
        
        result = {
            'function': 'check_refinement_result',
            'score': 0,
            'max_score': 1,
            'details': {}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "底部5")
            
            # Check if there are no peaks
            peaks_match = re.search(r'peaks?', text, re.IGNORECASE)
            if peaks_match:
                continue  # if peaks found, skip this screenshot
            
            # Check profiles
            profile_match = re.search(r'(\d+)\s*profiles?', text, re.IGNORECASE)
            if profile_match:
                result['details']['profiles'] = profile_match.group(1)
                result['score'] = 1
                self._log(f"✓ 拟合结果: {profile_match.group(1)} profiles", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log("✗ 未发现拟合结果", "FAIL")
        
        return result
    
    def check_dialog_title(self, title: str) -> Dict[str, Any]:
        self._log(f"Checking dialog title: {title}", "INFO")
        
        result = {
            'function': 'check_dialog_title',
            'score': 0,
            'max_score': 1,
            'details': {
                'title': title
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            if title in text:
                result['score'] = 1
                self._log(f"✓ 发现弹窗标题: {title}", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log(f"✗ Dialog title not found: {title}", "FAIL")
        
        return result

    def check_search_match_elements(self) -> Dict[str, Any]:
        self._log("检查S/M匹配元素", "INFO")
        
        result = {
            'function': 'check_search_match_elements',
            'score': 0,
            'max_score': 1,
            'details': {
                'element_count': 0
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            # First check if it is a Search/Match Display dialog
            text_full = self._ocr_region(screenshot, "full")
            if "Search/Match Display" not in text_full:
                continue
            
            # Check bottom region
            text_bottom = self._ocr_region(screenshot, "底部5")
            
            # Check if there is a selected row (usually marked with ☑ or checkbox)
            checked_lines = re.findall(r'☑.*', text_bottom)
            
            # Or directly check if Figure of Merit column exists (indicates match results)
            if "Figure Of Merit" in text_bottom or "Chemical Formula" in text_bottom:
                result['score'] = 1
                result['details']['element_count'] = len(checked_lines) if checked_lines else 1
                self._log(f"✓ S/M匹配元素列表存在", "SUCCESS")
                break
        
        if result['score'] == 0:
            self._log("✗ 未发现S/M匹配元素", "FAIL")
        
        return result

        
    def evaluate_task(self, task_name: str, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
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


TASK_CONFIGS = {
    "in1": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}}
    ],
    "in2": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD4.xrdml'}},
        {'function': 'check_peak_finding', 'args': {}}
    ],
    "in3": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD1.xrdml'}},
        {'function': 'check_background_removal', 'args': {}}
    ],
    "in4": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD4.xrdml'}},
        {'function': 'check_smoothing', 'args': {}}
    ],
    "in5": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD4.xrdml'}},
        {'function': 'check_smoothing', 'args': {}},
        {'function': 'check_background_removal', 'args': {}}
    ],
    "in6": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD1.xrdml'}},
        {'function': 'check_axis_switch', 'args': {}}
    ],
    "in7": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_axes_menu', 'args': {}}
    ],
    "in8": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_peak_add_two', 'args': {}}
    ],
    "in9": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD1.xrdml'}},
         {'function': 'check_axis_switch', 'args': {}},
         {'function': 'check_peak_add_two', 'args': {}}
    ],
    "in10": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD1.xrdml'}},
        {'function': 'check_peak_finding', 'args': {}}
    ],
    "in11": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        
        {'function': 'check_wpf_refinement', 'args': {}}
    ],
    "in12": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD2.xrdml'}},
        {'function': 'check_refinement_result', 'args': {}}
    ],
    "in13": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_peak_finding', 'args': {}}
    ],
    "in14": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD1.xrdml'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Theta Calibration of Whole Pattern'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Theta Calibration Report'}}
    ],
    "in15": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Calculate d-Spacing & Miller Indices'}}
    ],
    "in16": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD2.xrdml'}},
        {'function': 'check_background_removal', 'args': {}},
        {'function': 'check_dialog_title', 'args': {'title': 'Search/Match Display'}}
    ],
    "in17": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_background_removal', 'args': {}},
        {'function': 'check_dialog_title', 'args': {'title': 'Current Chemistry'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Search/Match Display'}}
    ],
    "in18": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_refinement_result', 'args': {}}
    ],
    "in19": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'WRT-ZSX-5.txt'}},
        {'function': 'check_smoothing_and_background', 'args': {}},
        {'function': 'check_dialog_title', 'args': {'title': 'Search/Match Display'}}
    ],
    "in20": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD4.xrdml'}},
        {'function': 'check_smoothing', 'args': {}},
        {'function': 'check_refinement_result', 'args': {}}
    ],
    "in21": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'XRD2.xrdml'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Search/Match Display'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Current Chemistry'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Calculate d-Spacing & Miller Indices'}},
        {'function': 'check_dialog_title', 'args': {'title': 'Theta Calibration of Whole Pattern'}},
        {'function': 'check_refinement_result', 'args': {}}
    ]
}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Jade XRD 评估系统 v2')
    parser.add_argument('folder', type=str, help='Path to screenshot folder')
    parser.add_argument('task', type=str, help='Task name')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Jade XRD 评估系统 v2")
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
        evaluator = JadeEvaluator(str(folder_path))
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