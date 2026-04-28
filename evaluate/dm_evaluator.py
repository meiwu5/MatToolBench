"""
DigitalMicrograph Evaluation System - v1.0
For evaluating task completion of DigitalMicrograph software operations
Based on OCR text detection and image analysis
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

class DMEvaluator:
    """DigitalMicrograph Task Evaluator"""
    
    def __init__(self, base_folder: str, label_folder: str = None):
        self.base_folder = Path(base_folder).resolve()
        
        if not self.base_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {self.base_folder}")
        
        self.task_folder_name = self.base_folder.name
        self.screenshots = []
        self.ally_trees = []
        self.ocr_reader = easyocr.Reader(['en'], gpu=True)
        self.current_file = None
        
        # Label folder (for comparing FFT and other operation results)
        if label_folder:
            self.label_folder = Path(label_folder).resolve()
        else:
            self.label_folder = None
        
        # Create evaluation output directory
        dm_folder = self.base_folder.parent
        self.evaluate_folder = dm_folder / "evaluate"
        
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
    def _normalize_ocr_text(self, text: str) -> str:
        """
        Normalize OCR text, only handle clear digit misrecognitions
        Keep letters B, C, d, m etc. as-is
        """
        # Only replace characters clearly misrecognized as digits
        replacements = [
            ('l', '1'),   # lowercase L -> 1
            ('I', '1'),   # uppercase I -> 1
            ('|', '1'),   # pipe -> 1
            ('O', '0'),   # uppercase O -> 0
            ('o', '0'), 
            ('g','9')  # lowercase g -> 9
        ]
        
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        
        # Remove extra spaces
        result = re.sub(r'\s+', ' ', result)
        
        return result

    def _extract_step_number(self, filename: str) -> int:
        """Extract step number from filename"""
        match = re.search(r'step_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
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
        elif region == "top20%":
            img = img.crop((0, 0, width, int(height * 0.2)))
        elif region == "bottom20%":
            img = img.crop((0, int(height * 0.8), width, height))
        elif region == "bottom50%":
            img = img.crop((0, int(height * 0.5), width, height))
        elif region == "center":
            img = img.crop((int(width * 0.2), int(height * 0.2), 
                          int(width * 0.8), int(height * 0.8)))
        elif region == "bottom-right":
            img = img.crop((int(width * 0.7), int(height * 0.7), width, height))
        elif region == "left30%":
            img = img.crop((0, 0, int(width * 0.3), height))
        elif region == "left50%":
            img = img.crop((0, 0, int(width * 0.5), height))
        
        img_array = np.array(img)
        results = self.ocr_reader.readtext(img_array)
        text = "\n".join([result[1] for result in results])
        
        # Cache result
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
    
    def _detect_color_in_region(self, screenshot_path: Path, region: str, 
                               color_name: str) -> bool:
        """
        检测指定区域是否存在特定颜色
        color_name: 'red', 'white', 'black'
        """
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Crop by region
        if region == "center":
            crop_box = (int(width * 0.3), int(height * 0.3), 
                       int(width * 0.7), int(height * 0.7))
        elif region == "top-right":
            crop_box = (int(width * 0.7), 0, width, int(height * 0.3))
        elif region == "full-image":
            crop_box = (0, 0, width, height)
        else:
            crop_box = (0, 0, width, height)
        
        cropped = img.crop(crop_box)
        img_array = np.array(cropped)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        # Define color ranges
        if color_name == 'red':
            # Red has two HSV ranges
            lower1 = np.array([0, 100, 100])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([160, 100, 100])
            upper2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(img_hsv, lower1, upper1)
            mask2 = cv2.inRange(img_hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        elif color_name == 'white':
            lower = np.array([0, 0, 200])
            upper = np.array([180, 30, 255])
            mask = cv2.inRange(img_hsv, lower, upper)
        elif color_name == 'black':
            lower = np.array([0, 0, 0])
            upper = np.array([180, 255, 50])
            mask = cv2.inRange(img_hsv, lower, upper)
        else:
            return False
        
        # Calculate color pixel ratio
        color_pixels = np.sum(mask > 0)
        total_pixels = mask.size
        ratio = color_pixels / total_pixels
        
        # Save debug image
        debug_path = self.crop_cache_folder / f"color_{color_name}_{screenshot_path.stem}.png"
        cv2.imwrite(str(debug_path), mask)
        
        return ratio > 0.01  # 超过1%认为存在该颜色
    
    # ============ Simple task evaluation functions ============
    
    def check_file_import(self, expected_filename: str) -> Dict[str, Any]:
        """
        检查文件是否导入
        DigitalMicrograph top display format: 
        - "@B: dm1" or "@C: dm2" (at the very top of the window)
        
        特别注意：dml 会被OCR识别，需要归一化 l->1
        """
        self._log(f"检查文件导入: {expected_filename}", "INFO")
        
        result = {
            'function': 'check_file_import',
            'expected_file': expected_filename,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'status': 'not_found'}
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        # Extract dm+number part from filename
        filename_match = re.search(r'(dm\d+)', expected_filename, re.IGNORECASE)
        if not filename_match:
            self._log(f"⚠ 无法从 {expected_filename} 提取文件信息", "WARNING")
            return result
        
        base_name = filename_match.group(1).lower()  # dm1
        num_match = re.search(r'dm(\d+)', base_name)
        file_number = num_match.group(1) if num_match else ''
        
        for i, screenshot in enumerate(self.screenshots):
            # Read top region
            text = self._ocr_region(screenshot, "top20%")
            
            # Normalize OCR text
            normalized_text = self._normalize_ocr_text(text)
            
            # Check if pattern @B: dm + number is present
            # Because dml becomes dm1 after normalization
            patterns = [
                # Standard format (after normalization)
                (rf'@[BC]\s*:\s*dm{file_number}\b', 'at_standard'),
                (rf'@[BC]\s*:\s*DM{file_number}\b', 'at_upper'),
                
                # No spaces
                (rf'@[BC]:dm{file_number}\b', 'at_nospace'),
                (rf'@[BC]:DM{file_number}\b', 'at_nospace_upper'),
                
                # No @ symbol
                (rf'[BC]\s*:\s*dm{file_number}\b', 'standard'),
                (rf'[BC]\s*:\s*DM{file_number}\b', 'upper'),
                
                # Direct concatenation
                (rf'@[BC]dm{file_number}\b', 'at_direct'),
                (rf'@[BC]DM{file_number}\b', 'at_direct_upper'),
            ]
            
            matched = False
            matched_pattern = None
            matched_text = None
            
            for pattern, pattern_name in patterns:
                match = re.search(pattern, normalized_text, re.IGNORECASE)
                if match:
                    matched = True
                    matched_pattern = f"{pattern_name}: {pattern}"
                    matched_text = match.group()
                    self._log(f"[调试] ✓ 匹配成功! 模式={pattern_name}, 匹配文本='{matched_text}'", "SUCCESS")
                    break
            
            if matched:
                result['score'] = 1
                result['details']['found_at_step'] = i
                result['details']['status'] = 'imported'
                result['details']['ocr_text_original'] = text.strip()[:150]
                result['details']['ocr_text_normalized'] = normalized_text.strip()[:150]
                result['details']['matched_pattern'] = matched_pattern
                result['details']['matched_text'] = matched_text
                self.current_file = expected_filename
                self._log(f"✓ 文件 {expected_filename} 在步骤 {i} 导入 (匹配文本: {matched_text})", "SUCCESS")
                return result
            else:
                self._log(f"[调试] 步骤{i} 未匹配，期望: dm{file_number}", "WARNING")
        
        self._log(f"✗ 未检测到文件 {expected_filename} 导入", "FAIL")
        return result
        
    def check_text_color(self, text: str, color_name: str, region: str = "full") -> Dict[str, Any]:
        """
        检查特定文本的颜色
        1. First locate text position via OCR
        2. Then detect color at that position to check if matched
        
        Args:
            text: 要查找的文本（如 "20 nm"）
            color_name: 期望的颜色名称 ('red', 'white', 'black', 'green', 'blue')
            region: 搜索区域
        """
        self._log(f"检查文本'{text}'的颜色是否为{color_name}", "INFO")
        
        result = {
            'function': 'check_text_color',
            'text': text,
            'expected_color': color_name,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'text_found': False, 'color_matched': False}
        }
        
        # Define HSV range for colors
        color_ranges = {
            'red': [
                (np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255]))
            ],
            'white': [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
            'black': [(np.array([0, 0, 0]), np.array([180, 255, 50]))],
            'green': [(np.array([40, 40, 40]), np.array([80, 255, 255]))],
            'blue': [(np.array([100, 100, 100]), np.array([130, 255, 255]))],
        }
        
        if color_name.lower() not in color_ranges:
            self._log(f"⚠ 不支持的颜色: {color_name}", "WARNING")
            return result
        
        # Record whether text was ever found (for final summary)
        text_found_in_any_step = False
        
        for i, screenshot in enumerate(self.screenshots):
            self._log(f"[调试] 正在检查步骤{i}/{len(self.screenshots)-1}...", "INFO")
            
            # Load image
            img = Image.open(screenshot)
            width, height = img.size
            
            # Crop by region
            if region == "bottom20%":
                crop_box = (0, int(height * 0.8), width, height)
            elif region == "top20%":
                crop_box = (0, 0, width, int(height * 0.2))
            elif region == "center":
                crop_box = (int(width * 0.2), int(height * 0.2), 
                        int(width * 0.8), int(height * 0.8))
            elif region == "bottom50%":
                crop_box = (0, int(height * 0.5), width, height)
            else:  # full
                crop_box = (0, 0, width, height)
            
            cropped_img = img.crop(crop_box)
            img_array = np.array(cropped_img)
            
            # Use OCR to locate text
            ocr_results = self.ocr_reader.readtext(img_array, detail=1)
            
            # Normalize target text (for matching)
            # For "20 nm", try matching variants like "20nm", "20 nm", "2onm" etc.
            target_variants = [
                self._normalize_ocr_text(text.lower().replace(' ', '')),  # "20nm"
                text.lower().replace(' ', ''),  # "20nm"
                text.lower(),  # "20 nm"
            ]
            
            step_found_text = False
            
            for detection in ocr_results:
                bbox, detected_text, confidence = detection
                
                # Normalize detected text
                normalized_detected = self._normalize_ocr_text(detected_text.lower().replace(' ', ''))
                detected_lower = detected_text.lower().replace(' ', '')
                
                # Check if text matched (try all variants)
                is_match = False
                for variant in target_variants:
                    if variant in normalized_detected or normalized_detected in variant:
                        is_match = True
                        break
                    if variant in detected_lower or detected_lower in variant:
                        is_match = True
                        break
                
                # Extra check: if target is "20 nm", also match patterns with number+unit
                if "nm" in text.lower():
                    # Match patterns like "number + nm"
                    import re
                    if re.search(r'\d+\s*nm', detected_text.lower()):
                        is_match = True
                
                if is_match:
                    step_found_text = True
                    text_found_in_any_step = True
                    result['details']['text_found'] = True
                    result['details']['detected_text'] = detected_text
                    result['details']['confidence'] = confidence
                    
                    self._log(f"[调试] 步骤{i} 找到匹配文本: '{detected_text}' (confidence={confidence:.2f})", "INFO")
                    
                    # Get text bounding box
                    bbox_array = np.array(bbox, dtype=np.int32)
                    x_min = int(bbox_array[:, 0].min())
                    y_min = int(bbox_array[:, 1].min())
                    x_max = int(bbox_array[:, 0].max())
                    y_max = int(bbox_array[:, 1].max())
                    
                    # Expand bounding box to ensure text is included
                    padding = 5
                    x_min = max(0, x_min - padding)
                    y_min = max(0, y_min - padding)
                    x_max = min(img_array.shape[1], x_max + padding)
                    y_max = min(img_array.shape[0], y_max + padding)
                    
                    # Extract text region
                    text_region = img_array[y_min:y_max, x_min:x_max]
                    
                    if text_region.size == 0:
                        self._log(f"[调试] 步骤{i} 文本区域为空，跳过", "WARNING")
                        continue
                    
                    # Save debug image
                    debug_path = self.crop_cache_folder / f"text_color_{text.replace(' ', '_')}_{color_name}_step{i}.png"
                    cv2.imwrite(str(debug_path), cv2.cvtColor(text_region, cv2.COLOR_RGB2BGR))
                    
                    # Convert to HSV color space
                    text_region_bgr = cv2.cvtColor(text_region, cv2.COLOR_RGB2BGR)
                    text_region_hsv = cv2.cvtColor(text_region_bgr, cv2.COLOR_BGR2HSV)
                    
                    # ============= NEW: check all color match ratios =============
                    self._log(f"[颜色分析] 开始分析文本'{detected_text}'的颜色...", "INFO")
                    
                    all_color_ratios = {}
                    for test_color, ranges in color_ranges.items():
                        max_test_ratio = 0.0
                        for lower, upper in ranges:
                            mask = cv2.inRange(text_region_hsv, lower, upper)
                            ratio = np.sum(mask > 0) / mask.size if mask.size > 0 else 0
                            max_test_ratio = max(max_test_ratio, ratio)
                        all_color_ratios[test_color] = max_test_ratio
                    
                    # Print all color match ratios (sorted by ratio, high to low)
                    self._log(f"[颜色分析] 文本'{detected_text}'的颜色分布:", "INFO")
                    for color, ratio in sorted(all_color_ratios.items(), key=lambda x: x[1], reverse=True):
                        percentage = ratio * 100
                        self._log(f"  - {color}: {percentage:.1f}%", "INFO")
                    
                    # Calculate average color
                    mean_color_bgr = np.mean(text_region_bgr.reshape(-1, 3), axis=0)
                    mean_color_hsv = cv2.cvtColor(np.uint8([[mean_color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
                    
                    # Print RGB and HSV values
                    self._log(f"[颜色分析] 平均RGB: (R:{int(mean_color_bgr[2])}, G:{int(mean_color_bgr[1])}, B:{int(mean_color_bgr[0])})", "INFO")
                    self._log(f"[颜色分析] 平均HSV: (H:{mean_color_hsv[0]}, S:{mean_color_hsv[1]}, V:{mean_color_hsv[2]})", "INFO")
                    
                    # Determine the most likely color
                    detected_color_name, detected_color_ratio = max(all_color_ratios.items(), key=lambda x: x[1])
                    self._log(f"[颜色分析] 最可能的颜色: {detected_color_name} ({detected_color_ratio*100:.1f}%)", "INFO")
                    
                    # Save results to details
                    result['details']['color_analysis'] = {
                        'all_colors': all_color_ratios,
                        'detected_color': detected_color_name,
                        'detected_color_ratio': detected_color_ratio,
                        'mean_rgb': (int(mean_color_bgr[2]), int(mean_color_bgr[1]), int(mean_color_bgr[0])),
                        'mean_hsv': (int(mean_color_hsv[0]), int(mean_color_hsv[1]), int(mean_color_hsv[2]))
                    }
                    # ============= Color analysis end =============
                    
                    # Detect target color
                    color_matched = False
                    max_ratio = 0.0
                    
                    for lower, upper in color_ranges[color_name.lower()]:
                        mask = cv2.inRange(text_region_hsv, lower, upper)
                        color_pixels = np.sum(mask > 0)
                        total_pixels = mask.size
                        ratio = color_pixels / total_pixels if total_pixels > 0 else 0
                        max_ratio = max(max_ratio, ratio)
                        
                        # Save color mask debug image
                        mask_debug_path = self.crop_cache_folder / f"text_color_mask_{text.replace(' ', '_')}_{color_name}_step{i}.png"
                        cv2.imwrite(str(mask_debug_path), mask)
                        
                        self._log(f"[调试] 步骤{i} 文本'{detected_text}' {color_name}颜色占比: {ratio:.3f}", "INFO")
                        
                        # If color ratio exceeds threshold, consider match
                        if ratio > 0.15:  # 15% pixel match is sufficient
                            color_matched = True
                            break
                    
                    if color_matched:
                        result['score'] = 1
                        result['details']['found_at_step'] = i
                        result['details']['color_matched'] = True
                        result['details']['bbox'] = bbox_array.tolist()
                        self._log(f"✓ 在步骤 {i} 检测到{color_name}色文本'{text}' (实际识别为'{detected_text}')", "SUCCESS")
                        return result
                    else:
                        self._log(f"[调试] 步骤{i} 找到文本'{detected_text}'但{color_name}颜色占比仅{max_ratio:.3f} (实际为{detected_color_name}色 {detected_color_ratio*100:.1f}%)", "WARNING")
                        # Do not break; continue checking other text detection results in this screenshot
            
            if not step_found_text:
                self._log(f"[调试] 步骤{i} 未找到匹配文本 (继续查找...)", "INFO")
        
        # Summary after traversing all screenshots
        if text_found_in_any_step and not result['details']['color_matched']:
            self._log(f"⚠ 在所有{len(self.screenshots)}个步骤中找到文本'{text}'但颜色都不是{color_name}", "WARNING")
            result['score'] = 0.5  # 找到文本但颜色不对，给一半分
        else:
            self._log(f"✗ 在所有{len(self.screenshots)}个步骤中未检测到{color_name}色文本'{text}'", "FAIL")
        
        return result
    
    def check_ocr_text(self, target_text: List[str], region: str = "full") -> Dict[str, Any]:
        """Check if OCR recognized specific text
        
        Args:
            target_text: 目标文本，可以是单个字符串或字符串列表
            region: 识别区域
        """
        # Convert to list uniformly
        if isinstance(target_text, str):
            target_texts = [target_text]
        else:
            target_texts = target_text
        
        self._log(f"检查OCR文本: {target_texts}", "INFO")
        
        result = {
            'function': 'check_ocr_text',
            'target_text': target_texts,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'matched_texts': []}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, region)
            
            # Flexible matching (ignore case and spaces)
            text_normalized = text.lower().replace(' ', '').replace('\n', '')
            
            # Check whether matched any target text
            matched = []
            for target in target_texts:
                target_normalized = target.lower().replace(' ', '')
                if target_normalized in text_normalized:
                    matched.append(target)
            
            # If at least one target text matched, consider success
            if matched:
                result['score'] = 1
                result['details']['found_at_step'] = i
                result['details']['matched_texts'] = matched
                self._log(f"✓ 在步骤 {i} 检测到文本: {matched}", "SUCCESS")
                return result
        
        self._log(f"✗ 未检测到任何目标文本: {target_texts}", "FAIL")
        return result
    
    def check_drawing_tool(self, tool_name: str) -> Dict[str, Any]:
        """Check if a drawing tool (Box, Oval, Profile, etc.) was used"""
        self._log(f"检查绘图工具: {tool_name}", "INFO")
        
        result = {
            'function': 'check_drawing_tool',
            'tool_name': tool_name,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            if tool_name.lower() in text.lower():
                result['score'] = 1
                result['details']['found_at_step'] = i
                self._log(f"✓ 在步骤 {i} 检测到工具: {tool_name}", "SUCCESS")
                return result
        
        self._log(f"✗ 未检测到工具: {tool_name}", "FAIL")
        return result
    
    def check_border_color(self, box_color: str, corner_color: str = "green", region: str = "full", shape_type: str = "box") -> Dict[str, Any]:
        """
        通过检测角点来判断是否有指定颜色的框
        
        Args:
            box_color: box color (for logging)
            corner_color: corner color (default green)
            region: 搜索区域
            shape_type: 形状类型，'box' 为矩形，'oval' 为椭圆（默认box）
        """
        self._log(f"通过{corner_color}色角点检查{box_color}色{shape_type}在{region}", "INFO")
        
        result = {
            'function': 'check_border_color',
            'box_color': box_color,
            'corner_color': corner_color,
            'region': region,
            'shape_type': shape_type,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'corners_found': []}
        }
        
        # Define HSV range for colors
        color_ranges = {
            'red': [
                (np.array([0, 120, 120]), np.array([10, 255, 255])),
                (np.array([170, 120, 120]), np.array([180, 255, 255]))
            ],
            'green': [(np.array([45, 80, 80]), np.array([75, 255, 255]))],
            'blue': [(np.array([100, 120, 120]), np.array([130, 255, 255]))],
            'yellow': [(np.array([20, 120, 120]), np.array([30, 255, 255]))],
            'white': [(np.array([0, 0, 220]), np.array([180, 25, 255]))],
            'black': [(np.array([0, 0, 0]), np.array([180, 255, 50]))],
        }
        
        # Inner function: check border color match
        def check_border_color_match(img_hsv, x_min, y_min, x_max, y_max, expected_color, color_ranges, border_width=3, shape_type='box'):
            """Check if the border color matches the expected color"""
            h, w = img_hsv.shape[:2]
            x_min_safe = max(0, int(x_min))
            y_min_safe = max(0, int(y_min))
            x_max_safe = min(w, int(x_max))
            y_max_safe = min(h, int(y_max))
            
            # Calculate center and radius
            center_x = (x_min_safe + x_max_safe) / 2
            center_y = (y_min_safe + y_max_safe) / 2
            radius_x = (x_max_safe - x_min_safe) / 2
            radius_y = (y_max_safe - y_min_safe) / 2
            
            borders = []
            
            if shape_type == 'oval':
                # Ellipse: sample pixels near the ellipse edge
                num_samples = 36  # sample 36 points (one every 10 degrees)
                sample_margin = border_width
                
                for angle in np.linspace(0, 2*np.pi, num_samples, endpoint=False):
                    # Points on the ellipse
                    x_outer = int(center_x + radius_x * np.cos(angle))
                    y_outer = int(center_y + radius_y * np.sin(angle))
                    
                    # Point slightly inset from the border
                    x_inner = int(center_x + (radius_x - sample_margin*2) * np.cos(angle))
                    y_inner = int(center_y + (radius_y - sample_margin*2) * np.sin(angle))
                    
                    # Sample pixels between these two points (ellipse border region)
                    if 0 <= x_inner < w and 0 <= y_inner < h and 0 <= x_outer < w and 0 <= y_outer < h:
                        num_points = max(abs(x_outer - x_inner), abs(y_outer - y_inner)) + 1
                        for t in np.linspace(0, 1, int(num_points)):
                            x_sample = int(x_inner + t * (x_outer - x_inner))
                            y_sample = int(y_inner + t * (y_outer - y_inner))
                            if 0 <= y_sample < h and 0 <= x_sample < w:
                                borders.append(img_hsv[y_sample, x_sample])
            else:
                # Rectangle: keep original sampling method
                if y_min_safe + border_width < h:
                    top_border = img_hsv[y_min_safe:y_min_safe+border_width, x_min_safe:x_max_safe]
                    borders.append(top_border.reshape(-1, 3))
                if y_max_safe - border_width > 0:
                    bottom_border = img_hsv[y_max_safe-border_width:y_max_safe, x_min_safe:x_max_safe]
                    borders.append(bottom_border.reshape(-1, 3))
                if x_min_safe + border_width < w:
                    left_border = img_hsv[y_min_safe:y_max_safe, x_min_safe:x_min_safe+border_width]
                    borders.append(left_border.reshape(-1, 3))
                if x_max_safe - border_width > 0:
                    right_border = img_hsv[y_min_safe:y_max_safe, x_max_safe-border_width:x_max_safe]
                    borders.append(right_border.reshape(-1, 3))
            
            if not borders:
                return False, None, None
            
            # Convert to unified format
            if shape_type == 'oval':
                all_border_pixels = np.array(borders)
            else:
                all_border_pixels = np.vstack(borders)
            
            # Calculate median
            median_h = np.median(all_border_pixels[:, 0])
            median_s = np.median(all_border_pixels[:, 1])
            median_v = np.median(all_border_pixels[:, 2])
            
            # Use defined color ranges to count matching pixels for each color
            color_matches = {}
            total_pixels = len(all_border_pixels)
            
            for color_name, ranges in color_ranges.items():
                match_count = 0
                for lower, upper in ranges:
                    mask = cv2.inRange(all_border_pixels.reshape(-1, 1, 3), lower, upper)
                    match_count += np.sum(mask > 0)
                
                match_ratio = match_count / total_pixels if total_pixels > 0 else 0
                color_matches[color_name] = match_ratio
            
            detected_color = max(color_matches, key=color_matches.get)
            max_match_ratio = color_matches[detected_color]
            
            # Lower threshold to 20%
            is_match = (detected_color.lower() == expected_color.lower() and max_match_ratio >= 0.05)
            
            return is_match, detected_color, {
                'median_hsv': (median_h, median_s, median_v),
                'color_matches': color_matches,
                'detected_color': detected_color,
                'max_match_ratio': max_match_ratio
            }
        
        if corner_color.lower() not in color_ranges:
            self._log(f"⚠ 不支持的角点颜色: {corner_color}", "WARNING")
            return result
        
        if shape_type.lower() not in ['box', 'oval']:
            self._log(f"⚠ 不支持的形状类型: {shape_type}，使用默认值'box'", "WARNING")
            shape_type = 'box'
        
        for i, screenshot in enumerate(self.screenshots):
            self._log(f"[调试] 正在检查步骤{i}/{len(self.screenshots)-1}...", "INFO")
            
            # Load image
            img = Image.open(screenshot)
            width, height = img.size
            
            # Crop by region
            if region == "bottom20%" or region == "bottom":
                crop_box = (0, int(height * 0.8), width, height)
            elif region == "top20%" or region == "top":
                crop_box = (0, 0, width, int(height * 0.2))
            elif region == "center":
                crop_box = (int(width * 0.2), int(height * 0.2), 
                        int(width * 0.8), int(height * 0.8))
            elif region == "left":
                crop_box = (0, 0, int(width * 0.3), height)
            elif region == "right":
                crop_box = (int(width * 0.7), 0, width, height)
            else:  # full image
                crop_box = (0, 0, width, height)
            
            cropped_img = img.crop(crop_box)
            img_array = np.array(cropped_img)
            
            # Convert to BGR and HSV color space
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # Detect corner color
            combined_mask = np.zeros(img_hsv.shape[:2], dtype=np.uint8)
            
            for lower, upper in color_ranges[corner_color.lower()]:
                mask = cv2.inRange(img_hsv, lower, upper)
                combined_mask = cv2.bitwise_or(combined_mask, mask)
            
            # Save corner mask debug image
            corner_mask_path = self.crop_cache_folder / f"corner_mask_{corner_color}_step{i}.png"
            cv2.imwrite(str(corner_mask_path), combined_mask)
            
            # Calculate color ratio
            color_pixels = np.sum(combined_mask > 0)
            total_pixels = combined_mask.size
            color_ratio = color_pixels / total_pixels if total_pixels > 0 else 0
            
            self._log(f"[颜色检测] 步骤{i} {corner_color}色像素占比: {color_ratio*100:.3f}%", "INFO")
            
            if color_ratio < 0.0005:
                self._log(f"[调试] 步骤{i} {corner_color}色像素太少 ({color_ratio*100:.3f}%)，跳过", "INFO")
                continue
            
            # Morphological operation: remove noise
            kernel = np.ones((5, 5), np.uint8)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            
            color_pixels_after = np.sum(combined_mask > 0)
            self._log(f"[形态学处理] 步骤{i} 去噪后{corner_color}色像素数: {color_pixels} -> {color_pixels_after}", "INFO")
            
            if color_pixels_after < 100:
                self._log(f"[调试] 步骤{i} 去噪后像素太少，判断为噪点", "INFO")
                continue
            
            # Find contours (corners)
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Collect corner info
            corner_data = []
            min_area = 30
            max_area = 500
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        if cy < img_hsv.shape[0] and cx < img_hsv.shape[1]:
                            pixel_hsv = img_hsv[cy, cx]
                            h, s, v = int(pixel_hsv[0]), int(pixel_hsv[1]), int(pixel_hsv[2])
                            
                            if corner_color.lower() == 'green':
                                if s > 100 and v > 100:
                                    corner_data.append((cx, cy, h, s, v, area))
                                    self._log(f"[角点分析] 找到有效角点 at ({cx},{cy}), 面积={area:.1f}, HSV=({h},{s},{v})", "INFO")
                                else:
                                    self._log(f"[角点过滤] 过滤低饱和度点 at ({cx},{cy}), HSV=({h},{s},{v})", "INFO")
                            else:
                                corner_data.append((cx, cy, h, s, v, area))
            
            self._log(f"[角点检测] 步骤{i} 检测到 {len(corner_data)} 个有效的{corner_color}色角点", "INFO")
            
            if len(corner_data) < 4:
                self._log(f"[调试] 步骤{i} 角点数量不足4个", "INFO")
                continue
            
            # Clustering based on color similarity
            from itertools import combinations
            
            best_rectangle = None
            best_score = 0
            
            # Try all 4 corner combinations
            for combo in combinations(range(len(corner_data)), 4):
                points_data = [corner_data[idx] for idx in combo]
                
                # Extract coordinates and HSV
                points = [(p[0], p[1]) for p in points_data]
                hsv_values = [(p[2], p[3], p[4]) for p in points_data]
                
                # Check if all 4 corner colors are consistent
                h_values = [hsv[0] for hsv in hsv_values]
                s_values = [hsv[1] for hsv in hsv_values]
                v_values = [hsv[2] for hsv in hsv_values]
                
                h_std = np.std(h_values)
                s_std = np.std(s_values)
                v_std = np.std(v_values)
                
                # Color consistency check
                if h_std > 10 or s_std > 50 or v_std > 50:
                    continue
                
                # Geometry check
                points_array = np.array(points)
                x_coords = points_array[:, 0]
                y_coords = points_array[:, 1]

                x_min, x_max = x_coords.min(), x_coords.max()
                y_min, y_max = y_coords.min(), y_coords.max()

                box_width = x_max - x_min
                box_height = y_max - y_min
                
                # Basic size check
                if box_width < 50 or box_height < 50:
                    continue
                
                # Aspect ratio check
                aspect_ratio = max(box_width, box_height) / min(box_width, box_height)
                if aspect_ratio > 5:
                    continue

                # Check if 4 points are close to theoretical corners (rectangle corners)
                corners_theoretical = [
                    (x_min, y_min), (x_max, y_min),
                    (x_min, y_max), (x_max, y_max)
                ]
                
                tolerance = max(box_width, box_height) * 0.15
                matched_corners = 0
                
                for theoretical in corners_theoretical:
                    distances = [np.sqrt((p[0] - theoretical[0])**2 + (p[1] - theoretical[1])**2) 
                            for p in points]
                    if min(distances) < tolerance:
                        matched_corners += 1
                
                if matched_corners < 3:
                    continue
                
                # Border color verification (using input shape_type)
                is_color_match, detected_color, border_info = check_border_color_match(
                    img_hsv, x_min, y_min, x_max, y_max, box_color, color_ranges, 
                    border_width=3, shape_type=shape_type
                )
                
                if border_info:
                    median_h, median_s, median_v = border_info['median_hsv']
                    self._log(f"[框边颜色] 组合{combo} ({shape_type}) - 期望:{box_color}, 检测:{detected_color}, "
                            f"Match ratio:{border_info['max_match_ratio']*100:.1f}%, "
                            f"HSV median:({median_h:.0f},{median_s:.0f},{median_v:.0f})", "INFO")
                    
                    # Print all color match ratios
                    for color_name, ratio in border_info['color_matches'].items():
                        if ratio > 0.1:
                            self._log(f"  {color_name}: {ratio*100:.1f}%", "INFO")
                
                if not is_color_match:
                    self._log(f"[框边颜色] 组合{combo}框边颜色不匹配 (期望:{box_color}, 检测:{detected_color}) (跳过)", "WARNING")
                    continue
                
                self._log(f"[框边颜色] 组合{combo}框边颜色匹配 ✓ ({box_color})", "SUCCESS")
                
                # Calculate score
                score = matched_corners * 10
                score += (10 - h_std)
                score += (50 - s_std) / 5
                score += (50 - v_std) / 5
                score += border_info['max_match_ratio'] * 10
                
                self._log(f"[候选] 组合{combo}: 宽={box_width:.0f}, 高={box_height:.0f}, "
                        f"Matched corners={matched_corners}/4, total score={score:.1f}", "INFO")
                
                if score > best_score:
                    best_score = score
                    best_rectangle = {
                        'points': points,
                        'indices': combo,
                        'bounds': (x_min, y_min, x_max, y_max),
                        'width': box_width,
                        'height': box_height,
                        'matched_corners': matched_corners,
                        'hsv_std': (h_std, s_std, v_std),
                        'score': score,
                        'border_info': border_info
                    }
            
            # Draw debug image
            debug_img = img_bgr.copy()
            
            # Mark all corners (gray)
            for idx, data in enumerate(corner_data):
                cx, cy, h, s, v, area = data
                cv2.circle(debug_img, (cx, cy), 5, (128, 128, 128), 2)
                cv2.putText(debug_img, f"{idx}:{h},{s},{v}", (cx+10, cy), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (128, 128, 128), 1)
            
            # 根据形状类型设置不同的得分阈值
            score_threshold = 8 if shape_type == 'oval' else 30
            
            # If best rectangle found, check if score reaches threshold
            if best_rectangle:
                self._log(f"[得分检查] 形状:{shape_type}, 得分:{best_score:.1f}, 阈值:{score_threshold}", "INFO")
                
                if best_score > score_threshold:
                    points = best_rectangle['points']
                    indices = best_rectangle['indices']
                    x_min, y_min, x_max, y_max = best_rectangle['bounds']
                    border_info = best_rectangle['border_info']
                    
                    # Draw rectangle boundary (yellow)
                    cv2.rectangle(debug_img, (int(x_min), int(y_min)), 
                                (int(x_max), int(y_max)), (0, 255, 255), 3)
                    
                    # Highlight corners of best rectangle (green)
                    for idx in indices:
                        cx, cy = corner_data[idx][0], corner_data[idx][1]
                        cv2.circle(debug_img, (cx, cy), 8, (0, 255, 0), -1)
                        cv2.circle(debug_img, (cx, cy), 10, (0, 255, 255), 2)
                    
                    # Annotate detected border color on the image
                    if border_info:
                        detected_color = border_info['detected_color']
                        match_ratio = border_info['max_match_ratio']
                        label_text = f"{shape_type.upper()}: {detected_color} ({match_ratio*100:.0f}%)"
                        cv2.putText(debug_img, label_text, (int(x_min), int(y_min)-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                    
                    debug_path = self.crop_cache_folder / f"corners_detected_{corner_color}_step{i}.png"
                    cv2.imwrite(str(debug_path), debug_img)
                    
                    # Successfully found
                    result['score'] = 1
                    result['details']['found_at_step'] = i
                    result['details']['corners_found'] = points
                    result['details']['shape_type'] = shape_type
                    result['details']['box_bounds'] = {
                        'x_min': int(x_min),
                        'y_min': int(y_min),
                        'x_max': int(x_max),
                        'y_max': int(y_max),
                        'width': int(best_rectangle['width']),
                        'height': int(best_rectangle['height'])
                    }
                    result['details']['color_consistency'] = {
                        'h_std': float(best_rectangle['hsv_std'][0]),
                        's_std': float(best_rectangle['hsv_std'][1]),
                        'v_std': float(best_rectangle['hsv_std'][2])
                    }
                    result['details']['border_color'] = {
                        'detected': border_info['detected_color'],
                        'expected': box_color,
                        'match': True,
                        'hsv_median': {
                            'h': float(border_info['median_hsv'][0]),
                            's': float(border_info['median_hsv'][1]),
                            'v': float(border_info['median_hsv'][2])
                        },
                        'color_matches': {k: float(v) for k, v in border_info['color_matches'].items()}
                    }
                    
                    self._log(f"=" * 60, "INFO")
                    self._log(f"✓ 在步骤 {i} 通过{len(points)}个{corner_color}色角点检测到{box_color}色{shape_type}", "SUCCESS")
                    self._log(f"  形状类型: {shape_type.upper()}", "SUCCESS")
                    self._log(f"  框的大小: {best_rectangle['width']:.0f}x{best_rectangle['height']:.0f} 像素", "SUCCESS")
                    self._log(f"  角点颜色一致性: H±{best_rectangle['hsv_std'][0]:.1f}, S±{best_rectangle['hsv_std'][1]:.1f}, V±{best_rectangle['hsv_std'][2]:.1f}", "SUCCESS")
                    self._log(f"  框边颜色: {border_info['detected_color']} (匹配度: {border_info['max_match_ratio']*100:.1f}%)", "SUCCESS")
                    self._log(f"  总得分: {best_score:.1f} (阈值: {score_threshold})", "SUCCESS")
                    self._log(f"=" * 60, "INFO")
                    return result
                else:
                    self._log(f"[得分不足] 最高得分{best_score:.1f}未达到{shape_type}的阈值{score_threshold}", "WARNING")
            
            # Save debug image (no match found case)
            debug_path = self.crop_cache_folder / f"corners_detected_{corner_color}_step{i}.png"
            cv2.imwrite(str(debug_path), debug_img)
            self._log(f"[调试] 步骤{i} 未找到符合条件的{shape_type} (最高得分={best_score:.1f})", "WARNING")
        
        self._log(f"✗ 在所有{len(self.screenshots)}个步骤中未通过角点检测到{box_color}色{shape_type}", "FAIL")
        return result
    
    def check_parameter_value(self, param_name: str, expected_value: str) -> Dict[str, Any]:
        """Check if parameter values are set correctly"""
        self._log(f"检查参数 {param_name} = {expected_value}", "INFO")
        
        result = {
            'function': 'check_parameter_value',
            'param_name': param_name,
            'expected_value': expected_value,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "full")
            
            # Find parameter name and value combinations
            # Support multiple formats: "Width: 2000", "Width 2000", "Width=2000"
            patterns = [
                rf'{param_name}\s*[:：]\s*{expected_value}',
                rf'{param_name}\s+{expected_value}',
                rf'{param_name}\s*=\s*{expected_value}'
            ]
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result['score'] = 1
                    result['details']['found_at_step'] = i
                    self._log(f"✓ 在步骤 {i} 检测到 {param_name}={expected_value}", "SUCCESS")
                    return result
        
        self._log(f"✗ 未检测到 {param_name}={expected_value}", "FAIL")
        return result
    
    def check_checkbox_selected(self, checkbox_text: str) -> Dict[str, Any]:
        """Check if a checkbox is selected (via image analysis)"""
        self._log(f"检查复选框选中: {checkbox_text}", "INFO")
        
        result = {
            'function': 'check_checkbox_selected',
            'checkbox_text': checkbox_text,
            'score': 0,
            'max_score': 1,
            'details': {'found_at_step': None, 'text_found': False, 'checkbox_detected': False}
        }
        
        for i, screenshot in enumerate(self.screenshots):
            try:
                # Load image uniformly
                if isinstance(screenshot, (str, Path)):
                    img = cv2.imread(str(screenshot))
                    if img is None:
                        self._log(f"无法读取图像文件: {screenshot}", "WARNING")
                        continue
                elif isinstance(screenshot, np.ndarray):
                    img = screenshot
                else:
                    try:
                        from PIL import Image
                        if hasattr(screenshot, 'convert'):
                            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                        else:
                            self._log(f"不支持的图像类型: {type(screenshot)}", "ERROR")
                            continue
                    except Exception as e:
                        self._log(f"图像转换失败: {e}", "ERROR")
                        continue
                
                if img is None or img.size == 0:
                    self._log(f"步骤 {i}: 图像无效", "WARNING")
                    continue
                
                self._log(f"步骤 {i}: 成功加载图像 shape={img.shape}", "DEBUG")
                
                # Convert to PIL Image
                from PIL import Image
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                
                # Get detailed OCR data
                import pytesseract
                from pytesseract import Output
                
                ocr_data = pytesseract.image_to_data(pil_img, output_type=Output.DICT, lang='eng')
                
                # Find target text
                text_found = False
                text_x, text_y, text_w, text_h = None, None, None, None
                
                target_lower = checkbox_text.lower()
                
                for j in range(len(ocr_data['text'])):
                    word = ocr_data['text'][j].strip()
                    conf = int(ocr_data['conf'][j])
                    
                    if conf <= 0 or not word:
                        continue
                    
                    # Full match (case-insensitive)
                    if target_lower == word.lower():
                        text_found = True
                        result['details']['text_found'] = True
                        
                        text_x = ocr_data['left'][j]
                        text_y = ocr_data['top'][j]
                        text_w = ocr_data['width'][j]
                        text_h = ocr_data['height'][j]
                        
                        self._log(f"找到文本 '{word}' 在位置 ({text_x}, {text_y}, {text_w}, {text_h})", "DEBUG")
                        break
                
                if not text_found:
                    self._log(f"步骤 {i}: 未找到文本 '{checkbox_text}'", "DEBUG")
                    continue
                
                # ✅ Improvement: search for checkbox in a larger range to the left of text
                # Try multiple possible positions and sizes
                search_configs = [
                    # (x_offset, y_offset, width, height)
                    (-30, -5, 25, text_h + 10),   # tight to the left of text
                    (-50, -5, 45, text_h + 10),   # slightly further
                    (-70, -5, 65, text_h + 10),   # even further
                    (-25, -2, 20, text_h + 4),    # slightly smaller region
                ]
                
                best_match = None
                best_score = 0
                
                for x_offset, y_offset, search_w, search_h in search_configs:
                    checkbox_x = max(0, text_x + x_offset)
                    checkbox_y = max(0, text_y + y_offset)
                    
                    # Ensure within image boundaries
                    if checkbox_x + search_w > img.shape[1]:
                        search_w = img.shape[1] - checkbox_x
                    if checkbox_y + search_h > img.shape[0]:
                        search_h = img.shape[0] - checkbox_y
                    
                    if search_w <= 0 or search_h <= 0:
                        continue
                    
                    # Extract region
                    checkbox_region = img[checkbox_y:checkbox_y + search_h,
                                        checkbox_x:checkbox_x + search_w]
                    
                    if checkbox_region.size == 0:
                        continue
                    
                    # Convert to grayscale
                    gray = cv2.cvtColor(checkbox_region, cv2.COLOR_BGR2GRAY)
                    
                    # Detect dark pixels
                    dark_threshold = 100
                    dark_pixels = np.sum(gray < dark_threshold)
                    total_pixels = gray.size
                    dark_ratio = dark_pixels / total_pixels if total_pixels > 0 else 0
                    
                    # Detect edges
                    edges = cv2.Canny(gray, 50, 150)
                    edge_pixels = np.sum(edges > 0)
                    edge_ratio = edge_pixels / total_pixels if total_pixels > 0 else 0
                    
                    # Detect contours
                    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
                    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    significant_contours = [c for c in contours if cv2.contourArea(c) > 5]
                    
                    # Calculate match score
                    score = 0
                    if dark_ratio > 0.10:
                        score += dark_ratio * 100
                    if edge_ratio > 0.05:
                        score += edge_ratio * 50
                    if len(significant_contours) > 0:
                        score += len(significant_contours) * 10
                    
                    self._log(f"  搜索配置 offset=({x_offset},{y_offset}) size=({search_w},{search_h}): "
                            f"dark{dark_ratio:.2%}, edge{edge_ratio:.2%}, contours{len(significant_contours)}, score{score:.1f}", "DEBUG")
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'region': checkbox_region,
                            'x': checkbox_x,
                            'y': checkbox_y,
                            'w': search_w,
                            'h': search_h,
                            'dark_ratio': dark_ratio,
                            'edge_ratio': edge_ratio,
                            'contours': len(significant_contours),
                            'config': (x_offset, y_offset, search_w, search_h)
                        }
                
                # Determine if the best match indicates selection
                if best_match:
                    is_checked = False
                    reason = ""
                    
                    if best_match['dark_ratio'] > 0.10:
                        is_checked = True
                        reason = f"深色像素 {best_match['dark_ratio']:.2%}"
                    elif best_match['edge_ratio'] > 0.05 and best_match['contours'] > 0:
                        is_checked = True
                        reason = f"边缘 {best_match['edge_ratio']:.2%} + {best_match['contours']} 轮廓"
                    elif 1 <= best_match['contours'] <= 3:
                        is_checked = True
                        reason = f"{best_match['contours']} 个勾选笔画"
                    
                    self._log(f"最佳匹配 config={best_match['config']}, 分数={best_score:.1f}, 选中={is_checked}", "DEBUG")
                    
                    if is_checked:
                        result['score'] = 1
                        result['details']['found_at_step'] = i
                        result['details']['checkbox_detected'] = True
                        result['details']['detection_reason'] = reason
                        result['details']['best_score'] = best_score
                        
                        self._log(f"✓ 步骤 {i}: {checkbox_text} 已选中 ({reason})", "SUCCESS")
                        
                        # ✅ Save debug image (optional)
                        debug_path = f"debug_checkbox_{checkbox_text.replace(' ', '_')}_{i}.png"
                        cv2.imwrite(debug_path, best_match['region'])
                        self._log(f"已保存调试图像: {debug_path}", "DEBUG")
                        
                        return result
                    else:
                        self._log(f"步骤 {i}: 文本匹配但未检测到选中标记 (最高分数={best_score:.1f})", "DEBUG")
                else:
                    self._log(f"步骤 {i}: 未找到有效的复选框区域", "WARNING")
                        
            except Exception as e:
                self._log(f"步骤 {i} 检测失败: {e}", "ERROR")
                import traceback
                self._log(traceback.format_exc(), "DEBUG")
                continue
        
        self._log(f"✗ 未检测到 {checkbox_text} 被选中", "FAIL")
        return result
        
    # ============ Medium task evaluation functions ============
    def check_data_bar_by_text(self, min_keywords: int = 2) -> Dict[str, Any]:
        """
        通过识别 Data Bar 的特征文字来判断是否存在 Add Data Bar
        
        Data Bar typical features:
        - Voltage info (e.g. 300 kV)
        - Device name (e.g. OneView)
        - Magnification (e.g. X330000)
        - Pixel info (e.g. 4096 x 4096 pixels)
        - Date/time
        - Exposure time (e.g. 0.1596 s)
        
        Args:
            min_keywords: minimum number of keywords to match (default 2)
        """
        self._log(f"通过文本特征检查 Data Bar (最少匹配 {min_keywords} 个关键词)", "INFO")
        
        result = {
            'function': 'check_data_bar_by_text',
            'score': 0,
            'max_score': 1,
            'details': {
                'data_bar_detected': False,
                'found_at_step': None,
                'matched_keywords': [],
                'ocr_text_sample': None
            }
        }
        
        # Define Data Bar characteristic text patterns
        import re
        
        keyword_patterns = {
            'voltage': r'\d{2,3}\s*kV',                    # e.g. "300 kV", "200kV"
            'magnification': r'[xX]\d{3,7}',               # e.g. "X330000", "x100k"
            'pixels': r'\d{3,5}\s*x\s*\d{3,5}\s*pixels?',  # e.g. "4096 x 4096 pixels"
            'device_oneview': r'OneView',                   # 设备名称
            'device_gatan': r'Gatan',
            'device_ccd': r'CCD',
            'exposure_time': r'\d+\.?\d*\s*[sm]s?(?!\w)',  # e.g. "0.1596 s", "100 ms"
            'date': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',      # e.g. "1/23/2023"
            'time': r'\d{1,2}:\d{2}:\d{2}\s*[AP]M',        # e.g. "10:12:53 AM"
        }
        
        for i, screenshot in enumerate(self.screenshots):
            self._log(f"[步骤 {i}] 检测 Data Bar 文本特征...", "DEBUG")
            
            # Load image
            img = Image.open(screenshot)
            img_array = np.array(img)
            height, width = img_array.shape[:2]
            
            # ✅ Crop region: remove top 15%, bottom 15%, right 50%
            crop_top = int(height * 0.15)      # remove top 15%
            crop_bottom = int(height * 0.85)   # remove bottom 15% (keep up to 85%)
            crop_right = int(width * 0.5)      # keep left 50% only
            
            search_region = img_array[crop_top:crop_bottom, :crop_right]
            search_height, search_width = search_region.shape[:2]
            
            self._log(
                f"  Original size: {height}x{width}, "
                f"Search region: {search_height}x{search_width} "
                f"(top{crop_top}~bottom{crop_bottom}, left0~right{crop_right})",
                "DEBUG"
            )
            
            # OCR recognition
            try:
                ocr_results = self.ocr_reader.readtext(search_region)
                ocr_text = ' '.join([result[1] for result in ocr_results])
                
                self._log(f"  OCR 文本: {ocr_text[:200]}...", "DEBUG")
                result['details']['ocr_text_sample'] = ocr_text[:500]
                
                # Match keywords
                matched = []
                for keyword_name, pattern in keyword_patterns.items():
                    matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                    if matches:
                        matched.append({
                            'keyword': keyword_name,
                            'pattern': pattern,
                            'matches': matches
                        })
                        self._log(f"  ✓ 匹配 {keyword_name}: {matches}", "DEBUG")
                
                # Determine if conditions are met
                if len(matched) >= min_keywords:
                    result['score'] = 1
                    result['details']['data_bar_detected'] = True
                    result['details']['found_at_step'] = i
                    result['details']['matched_keywords'] = matched
                    result['details']['match_count'] = len(matched)
                    
                    keyword_summary = ', '.join([m['keyword'] for m in matched])
                    self._log(
                        f"✓ [Step {i}] Data Bar text features detected: "
                        f"Matched {len(matched)} keywords ({keyword_summary})",
                        "SUCCESS"
                    )
                    return result
                else:
                    self._log(f"  关键词不足: {len(matched)}/{min_keywords}", "DEBUG")
                    
            except Exception as e:
                self._log(f"  OCR 失败: {e}", "ERROR")
                import traceback
                self._log(traceback.format_exc(), "DEBUG")
                continue
        
        self._log(f"✗ 未检测到足够的 Data Bar 文本特征", "FAIL")
        return result

    def check_roi_copy_and_enlarge(self) -> Dict[str, Any]:
        """
        检测 RectangleROI 复制并放大覆盖原始区域
        
        判断逻辑：
        1. First valid ROI detected (4 consistent green corners)
        2. ROI position significantly changed (Y center moved > 30% of original height)
        
        这表示：复制的放大区域覆盖了原始ROI，新ROI框出现在不同位置
        """
        self._log("检查 ROI 复制并放大覆盖（通过位置变化检测）", "INFO")
        
        result = {
            'function': 'check_roi_copy_and_enlarge',
            'score': 0,
            'max_score': 1,
            'details': {
                'first_roi_detected': False,
                'first_roi_step': None,
                'first_roi_center': None,
                'position_changed': False,
                'changed_step': None,
                'new_roi_center': None,
                'displacement': None,
                'roi_history': []
            }
        }
        
        # Define HSV range for green
        green_ranges = [(np.array([45, 80, 80]), np.array([75, 255, 255]))]
        
        roi_history = []
        first_roi_info = None
        
        for i, screenshot in enumerate(self.screenshots):
            self._log(f"[步骤 {i}] 检测 ROI 位置...", "DEBUG")
            
            # Load image
            img = Image.open(screenshot)
            img_array = np.array(img)
            
            # Convert to HSV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # Detect green
            combined_mask = np.zeros(img_hsv.shape[:2], dtype=np.uint8)
            for lower, upper in green_ranges:
                mask = cv2.inRange(img_hsv, lower, upper)
                combined_mask = cv2.bitwise_or(combined_mask, mask)
            
            # Morphological operation
            kernel = np.ones((5, 5), np.uint8)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find corners
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Collect candidate corners
            min_area, max_area = 30, 500
            candidate_corners = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        if cy < img_hsv.shape[0] and cx < img_hsv.shape[1]:
                            pixel_hsv = img_hsv[cy, cx]
                            h, s, v = int(pixel_hsv[0]), int(pixel_hsv[1]), int(pixel_hsv[2])
                            
                            if s > 100 and v > 100:
                                candidate_corners.append({
                                    'x': cx,
                                    'y': cy,
                                    'area': area,
                                    'h': h,
                                    's': s,
                                    'v': v
                                })
            
            # Color consistency check
            valid_roi = None
            
            if len(candidate_corners) >= 4:
                from itertools import combinations
                
                best_combo = None
                min_color_std = float('inf')
                
                for combo in combinations(range(len(candidate_corners)), 4):
                    corners = [candidate_corners[idx] for idx in combo]
                    
                    h_values = [c['h'] for c in corners]
                    s_values = [c['s'] for c in corners]
                    v_values = [c['v'] for c in corners]
                    
                    h_std = np.std(h_values)
                    s_std = np.std(s_values)
                    v_std = np.std(v_values)
                    
                    total_std = h_std + s_std/5 + v_std/5
                    
                    if h_std <= 10 and s_std <= 50 and v_std <= 50:
                        if total_std < min_color_std:
                            min_color_std = total_std
                            best_combo = {
                                'combo': combo,
                                'corners': corners,
                                'h_std': h_std,
                                's_std': s_std,
                                'v_std': v_std
                            }
                
                if best_combo:
                    corners = best_combo['corners']
                    
                    # Calculate ROI center and size
                    x_coords = [c['x'] for c in corners]
                    y_coords = [c['y'] for c in corners]
                    
                    center_x = np.mean(x_coords)
                    center_y = np.mean(y_coords)
                    
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    width = x_max - x_min
                    height = y_max - y_min
                    
                    valid_roi = {
                        'step': i,
                        'center_x': center_x,
                        'center_y': center_y,
                        'x_min': x_min,
                        'y_min': y_min,
                        'x_max': x_max,
                        'y_max': y_max,
                        'width': width,
                        'height': height,
                        'corners': corners,
                        'h_std': best_combo['h_std'],
                        's_std': best_combo['s_std'],
                        'v_std': best_combo['v_std']
                    }
                    
                    self._log(
                        f"  ✓ Valid ROI detected: center=({center_x:.0f}, {center_y:.0f}), "
                        f"Size={width:.0f}x{height:.0f}",
                        "DEBUG"
                    )
            
            roi_history.append({
                'step': i,
                'roi': valid_roi,
                'candidate_count': len(candidate_corners)
            })
            
            # Save debug image
            debug_img = img_bgr.copy()
            
            if valid_roi:
                # Draw ROI box
                cv2.rectangle(
                    debug_img,
                    (int(valid_roi['x_min']), int(valid_roi['y_min'])),
                    (int(valid_roi['x_max']), int(valid_roi['y_max'])),
                    (0, 255, 255), 3
                )
                
                # Mark center
                cv2.circle(debug_img, (int(valid_roi['center_x']), int(valid_roi['center_y'])), 10, (0, 0, 255), -1)
                
                # Mark corners
                for c in valid_roi['corners']:
                    cv2.circle(debug_img, (c['x'], c['y']), 8, (0, 255, 0), -1)
                
                cv2.putText(
                    debug_img,
                    f"Step {i}: ROI Center ({valid_roi['center_x']:.0f}, {valid_roi['center_y']:.0f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                )
            else:
                cv2.putText(
                    debug_img,
                    f"Step {i}: No valid ROI ({len(candidate_corners)} candidates)",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )
            
            debug_path = self.crop_cache_folder / f"roi_position_step{i}.png"
            cv2.imwrite(str(debug_path), debug_img)
            
            # Record first valid ROI
            if valid_roi and first_roi_info is None:
                first_roi_info = valid_roi
                result['details']['first_roi_detected'] = True
                result['details']['first_roi_step'] = i
                result['details']['first_roi_center'] = (center_x, center_y)
                
                self._log(
                    f"✓ Step {i}: First ROI detected, center=({center_x:.0f}, {center_y:.0f})",
                    "SUCCESS"
                )
            
            # Detect position change
            elif valid_roi and first_roi_info:
                # Calculate center displacement
                dx = abs(valid_roi['center_x'] - first_roi_info['center_x'])
                dy = abs(valid_roi['center_y'] - first_roi_info['center_y'])
                
                # Decision criterion: Y displacement > 30% of original ROI height
                threshold_y = first_roi_info['height'] * 0.3
                
                self._log(
                    f"  Displacement: dx={dx:.0f}, dy={dy:.0f}, threshold(30% height)={threshold_y:.0f}",
                    "DEBUG"
                )
                
                if dy > threshold_y:
                    result['details']['position_changed'] = True
                    result['details']['changed_step'] = i
                    result['details']['new_roi_center'] = (valid_roi['center_x'], valid_roi['center_y'])
                    result['details']['displacement'] = {'dx': float(dx), 'dy': float(dy)}
                    result['score'] = 1
                    
                    self._log(
                        f"✓ Step {i}: ROI position changed significantly!\n"
                        f"  Original position: ({first_roi_info['center_x']:.0f}, {first_roi_info['center_y']:.0f})\n"
                        f"  New position: ({valid_roi['center_x']:.0f}, {valid_roi['center_y']:.0f})\n"
                        f"  Y displacement: {dy:.0f} > {threshold_y:.0f} (threshold)",
                        "SUCCESS"
                    )
                    
                    result['details']['roi_history'] = roi_history
                    return result
        
        result['details']['roi_history'] = roi_history
        
        if first_roi_info:
            self._log(
                f"⚠ ROI detected but position did not change significantly\n"
                f"  Zoom-cover operation may not have been performed",
                "WARNING"
            )
        else:
            self._log("✗ 未检测到有效 ROI", "FAIL")
        
        return result
    
    def check_dialog_opened(self, title_keyword: str = "", filename: str = "", 
                   field_checks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        纯 OCR 版本：检测弹窗标题和字段值
        - Title detection: top 5% region
        - Field detection: full region (no longer limited to left 40%)
        
        Args:
            title_keyword: 弹窗标题关键词（如 "Properties"）
            filename: filename (optional, for extra verification)
            field_checks: 需要检查的字段和期望值，格式如 {'Radius': 1.5, 'Stacks': 24}
        
        Example:
            check_dialog_opened('Properties', field_checks={'Radius': 1.5})
        """
        import re
        
        field_msg = f" + field_checks:{field_checks}" if field_checks else ""
        self._log(f"检查弹窗: {title_keyword}{field_msg}", "INFO")
        
        result = {
            'function': 'check_dialog_opened',
            'score': 0,
            'max_score': 1,
            'details': {
                'dialog_detected': False,
                'title_region_text_sample': None,
                'field_region_text_sample': None,
                'target_keyword': title_keyword,
                'field_checks': field_checks or {},
                'field_results': {},
                'detected_at_step': None
            }
        }

        # OCR misrecognition variants of title keywords
        search_keywords = [title_keyword.lower()]
        if title_keyword.lower() == "properties":
            search_keywords.extend(["propertie", "properlie", "propert"])
        elif title_keyword.lower() == "change profile info":
            search_keywords.extend(["change proflle info", "change profi1e info", "change profile lnfo"])

        for i, screenshot in enumerate(self.screenshots):
            # === Step 1: Detect dialog title in top 5% ===
            title_text = self._ocr_region(screenshot, "full")
            title_text_lower = title_text.lower()
            
            # Check if dialog title exists
            found_title = next((k for k in search_keywords if k in title_text_lower), None)

            if not found_title:
                # No title found, skip this frame
                result['details']['title_region_text_sample'] = title_text[:100].replace('\n', ' ')
                continue
            
            # Title found
            result['details']['dialog_detected'] = True
            result['details']['detected_at_step'] = i
            result['details']['title_region_text_sample'] = title_text[:100].replace('\n', ' ')
            
            # If no field check required, return success directly
            if not field_checks:
                result['score'] = 1
                self._log(f"✓ [步骤 {i:02d}] 检测到弹窗标题: '{found_title}'", "SUCCESS")
                return result
            
            # === Step 2: Detect field content in full region ===
            self._log(f"[步骤 {i:02d}] 检测到弹窗标题 '{found_title}'，开始验证字段...", "INFO")
            
            # ✅ Change: read full region instead of partial region
            field_text = self._ocr_region(screenshot, "full")
            field_text_lower = field_text.lower()
            result['details']['field_region_text_sample'] = field_text[:500].replace('\n', ' ')
            
            all_fields_match = True
            for field_name, expected_value in field_checks.items():
                
                # Convert expected value to string (supports int and float)
                if isinstance(expected_value, float):
                    value_str = str(expected_value)
                    # Generate multiple possible OCR recognition forms
                    value_patterns = [
                        value_str,  # 1.5
                        value_str.replace('.', ''),  # 15（OCR 可能漏掉小数点）
                        value_str.rstrip('0').rstrip('.') if '.' in value_str else value_str,  # 1.50 -> 1.5
                        f"{int(float(value_str))}" if '.' in value_str and value_str.endswith('.0') else None  # 1.0 -> 1
                    ]
                    value_patterns = [p for p in value_patterns if p]  # 移除 None
                else:
                    value_str = str(expected_value)
                    value_patterns = [value_str]
                
                # Field name may also have OCR misrecognition
                field_patterns = [field_name.lower()]
                # Added to field matching:
                if field_name.lower() == "integration width":
                    field_patterns.extend([
                        "integratlon width", 
                        "integration wldth", 
                        "lntegration width"
                    ])

                # Added to value matching (for misrecognition of 80):
                if expected_value == 80:
                    value_patterns.extend([
                        "80",
                        "8O",  # O instead of 0
                        "B0",  # B instead of 8
                        "BO",  # both wrong
                        "peq", # actual misrecognition observed
                        "peg",
                        "beg",
                        "80l", # with cursor
                        "801",
                    ])
                
                # Try matching: field name + separator + value
                field_matched = False
                matched_pattern = None
                
                for field_pat in field_patterns:
                    # First try exact matching
                    for value_pat in value_patterns:
                        patterns = [
                            rf'{field_pat}\s*[:：]\s*{re.escape(value_pat)}\b',      # "Integration Width: 80"
                            rf'{field_pat}\s*[:：]\s*{re.escape(value_pat)}\s',      # "Integration Width: 80 "
                            rf'{field_pat}\s+{re.escape(value_pat)}\b',              # "Integration Width 80"
                            rf'{field_pat}\s*[:：]?\s*{re.escape(value_pat)}\b',     # "Integration Width:80"
                            rf'{field_pat}[^\w]*{re.escape(value_pat)}\b',           # 允许中间有任意非字母字符
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, field_text_lower):
                                field_matched = True
                                matched_pattern = f"{field_pat}={value_pat}"
                                break
                        
                        if field_matched:
                            break
                    
                    if field_matched:
                        break
                    
                    # If exact match fails, try fuzzy matching (for floating point + cursor interference)
                    if not field_matched and isinstance(expected_value, (float, int)):
                        for base_val in value_patterns[:1]:  # use base value only
                            # Match "value + optional single noise character"
                            fuzzy_patterns = [
                                rf'{field_pat}\s*[:：]\s*{re.escape(base_val)}[0-9IilL|]?\b',
                                rf'{field_pat}\s*[:：]\s*{re.escape(base_val)}[0-9IilL|]?\s',
                                rf'{field_pat}\s+{re.escape(base_val)}[0-9IilL|]?\b',
                                rf'{field_pat}\s*[:：]?\s*{re.escape(base_val)}[0-9IilL|]?\b',
                            ]
                            
                            for pattern in fuzzy_patterns:
                                match = re.search(pattern, field_text_lower)
                                if match:
                                    field_matched = True
                                    matched_pattern = f"{field_pat}≈{match.group(0).split()[-1]}"
                                    self._log(f"  ℹ 使用模糊匹配: 期望 {base_val}，匹配到 {match.group(0)}", "INFO")
                                    break
                            
                            if field_matched:
                                break
                    
                    if field_matched:
                        break
                
                result['details']['field_results'][field_name] = {
                    'expected': expected_value,
                    'matched': field_matched,
                    'matched_pattern': matched_pattern
                }
                
                if field_matched:
                    self._log(f"  ✓ 字段 '{field_name}' 匹配: {matched_pattern}", "SUCCESS")
                else:
                    self._log(f"  ✗ 字段 '{field_name}' 未找到期望值 {expected_value}", "FAIL")
                    all_fields_match = False
            
            # Step 3: Decide based on field match results
            if all_fields_match:
                result['score'] = 1
                self._log(f"✓ 弹窗标题和所有字段均匹配成功", "SUCCESS")
                return result
            else:
                # Dialog found but fields do not match, give partial score
                matched_count = sum(1 for v in result['details']['field_results'].values() if v['matched'])
                total_count = len(field_checks)
                result['score'] = matched_count / total_count if total_count > 0 else 0
                self._log(
                    f"⚠ Dialog opened but field match incomplete: {matched_count}/{total_count}",
                    "WARNING"
                )
                # Continue checking next frame; later frames may have correct values
            
        # If all screenshots traversed without a complete match
        if result['details']['dialog_detected']:
            self._log(f"✗ 检测到弹窗标题但字段验证失败", "FAIL")
        else:
            self._log(f"✗ 未检测到弹窗标题 '{title_keyword}'", "FAIL")
        
        return result
    
    def check_filled_box_with_corners(self, fill_color: str = "white", corner_color: str = "green") -> Dict[str, Any]:
        """
        检测带绿色角点的填充 Box
        
        判断逻辑：
        1. First detect 4 green corners (locate Box frame)
        2. Then check if box interior is filled with target color
        
        Args:
            fill_color: fill color (default white)
            corner_color: corner color (default green)
        """
        self._log(f"检测带{corner_color}色角点的{fill_color}色填充框", "INFO")
        
        result = {
            'function': 'check_filled_box_with_corners',
            'fill_color': fill_color,
            'corner_color': corner_color,
            'score': 0,
            'max_score': 1,
            'details': {
                'corners_detected': False,
                'filled': False,
                'found_at_step': None,
                'box_info': None
            }
        }
        
        # Color range definitions
        color_ranges = {
            'green': [(np.array([45, 80, 80]), np.array([75, 255, 255]))],
            'white': [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
            'black': [(np.array([0, 0, 0]), np.array([180, 255, 50]))],
            'red': [
                (np.array([0, 120, 120]), np.array([10, 255, 255])),
                (np.array([170, 120, 120]), np.array([180, 255, 255]))
            ],
        }
        
        for i, screenshot in enumerate(self.screenshots):
            self._log(f"[步骤 {i}] 检测填充框...", "DEBUG")
            
            # Load image
            img = Image.open(screenshot)
            img_array = np.array(img)
            
            # Convert to HSV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # === Step 1: Detect green corners ===
            green_mask = np.zeros(img_hsv.shape[:2], dtype=np.uint8)
            for lower, upper in color_ranges[corner_color.lower()]:
                mask = cv2.inRange(img_hsv, lower, upper)
                green_mask = cv2.bitwise_or(green_mask, mask)
            
            # Morphological operation
            kernel = np.ones((5, 5), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find corners
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Collect candidate corners
            min_area, max_area = 30, 500
            candidate_corners = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        if cy < img_hsv.shape[0] and cx < img_hsv.shape[1]:
                            pixel_hsv = img_hsv[cy, cx]
                            h, s, v = int(pixel_hsv[0]), int(pixel_hsv[1]), int(pixel_hsv[2])
                            
                            if s > 100 and v > 100:
                                candidate_corners.append({
                                    'x': cx,
                                    'y': cy,
                                    'h': h,
                                    's': s,
                                    'v': v,
                                    'area': area
                                })
            
            if len(candidate_corners) < 4:
                self._log(f"  角点不足 ({len(candidate_corners)}/4)，跳过", "DEBUG")
                continue
            
            # Color consistency check (find most consistent 4 corners)
            from itertools import combinations
            
            best_box = None
            best_score = 0
            
            for combo in combinations(range(len(candidate_corners)), 4):
                corners = [candidate_corners[idx] for idx in combo]
                
                # Color consistency
                h_values = [c['h'] for c in corners]
                s_values = [c['s'] for c in corners]
                v_values = [c['v'] for c in corners]
                
                h_std = np.std(h_values)
                s_std = np.std(s_values)
                v_std = np.std(v_values)
                
                if h_std > 10 or s_std > 50 or v_std > 50:
                    continue
                
                # Calculate Box boundary
                x_coords = [c['x'] for c in corners]
                y_coords = [c['y'] for c in corners]
                
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                box_width = x_max - x_min
                box_height = y_max - y_min
                
                # Size check
                if box_width < 50 or box_height < 50:
                    continue
                
                # === Step 2: Check if box interior is filled with target color ===
                # Extract box interior region (slightly inset to avoid border interference)
                margin = 10
                inner_x_min = max(0, x_min + margin)
                inner_y_min = max(0, y_min + margin)
                inner_x_max = min(img_hsv.shape[1], x_max - margin)
                inner_y_max = min(img_hsv.shape[0], y_max - margin)
                
                if inner_x_max <= inner_x_min or inner_y_max <= inner_y_min:
                    continue
                
                inner_region = img_hsv[inner_y_min:inner_y_max, inner_x_min:inner_x_max]
                
                # Detect fill color
                fill_mask = np.zeros(inner_region.shape[:2], dtype=np.uint8)
                for lower, upper in color_ranges[fill_color.lower()]:
                    mask = cv2.inRange(inner_region, lower, upper)
                    fill_mask = cv2.bitwise_or(fill_mask, mask)
                
                # Calculate fill ratio
                fill_pixels = np.sum(fill_mask > 0)
                total_inner_pixels = inner_region.shape[0] * inner_region.shape[1]
                fill_ratio = fill_pixels / total_inner_pixels if total_inner_pixels > 0 else 0
                
                self._log(
                    f"  Combination {combo}: Box=({x_min},{y_min},{box_width},{box_height}), "
                    f"Interior {fill_color} fill={fill_ratio*100:.1f}%",
                    "DEBUG"
                )
                
                # Fill threshold: > 80% means filled
                if fill_ratio > 0.8:
                    score = fill_ratio * 100
                    
                    if score > best_score:
                        best_score = score
                        best_box = {
                            'x_min': x_min,
                            'y_min': y_min,
                            'x_max': x_max,
                            'y_max': y_max,
                            'width': box_width,
                            'height': box_height,
                            'fill_ratio': fill_ratio,
                            'corners': corners,
                            'combo': combo
                        }
            
            # Save debug image
            debug_img = img_bgr.copy()
            
            if best_box:
                box = best_box
                
                # Draw Box boundary (yellow)
                cv2.rectangle(
                    debug_img,
                    (box['x_min'], box['y_min']),
                    (box['x_max'], box['y_max']),
                    (0, 255, 255), 3
                )
                
                # Mark corners (green)
                for c in box['corners']:
                    cv2.circle(debug_img, (c['x'], c['y']), 8, (0, 255, 0), -1)
                    cv2.circle(debug_img, (c['x'], c['y']), 10, (0, 255, 255), 2)
                
                # Annotate fill info
                cv2.putText(
                    debug_img,
                    f"Filled {fill_color.upper()} Box",
                    (box['x_min'], box['y_min'] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                )
                
                cv2.putText(
                    debug_img,
                    f"Fill: {box['fill_ratio']*100:.0f}%, Size: {box['width']}x{box['height']}",
                    (box['x_min'], box['y_min'] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2
                )
                
                result['score'] = 1
                result['details']['corners_detected'] = True
                result['details']['filled'] = True
                result['details']['found_at_step'] = i
                result['details']['box_info'] = {
                    'x': box['x_min'],
                    'y': box['y_min'],
                    'width': box['width'],
                    'height': box['height'],
                    'fill_ratio': box['fill_ratio']
                }
                
                self._log(
                    f"✓ [Step {i}] Detected {fill_color}-filled Box:\n"
                    f"  Position: ({box['x_min']}, {box['y_min']})\n"
                    f"  Size: {box['width']}x{box['height']} pixels\n"
                    f"  Interior fill ratio: {box['fill_ratio']*100:.1f}%\n"
                    f"  4 {corner_color} corners",
                    "SUCCESS"
                )
            else:
                cv2.putText(
                    debug_img,
                    f"Step {i}: {len(candidate_corners)} corners, no filled box",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )
            
            debug_path = self.crop_cache_folder / f"filled_box_step{i}.png"
            cv2.imwrite(str(debug_path), debug_img)
            
            if result['score'] > 0:
                return result
        
        self._log(f"✗ 未检测到填充的{fill_color}色 Box（带{corner_color}色角点）", "FAIL")
        return result
    
    # ============ Complex task evaluation functions ============
    def check_text_count_in_dialog(self, dialog_title: str, target_text: str, expected_count: int) -> Dict[str, Any]:
        """
        检测弹窗中某个文本出现的次数
        
        Args:
            dialog_title: dialog title keyword (e.g. "Profile Of 2")
            target_text: 要计数的文本（如 "nm"）
            expected_count: expected occurrence count (e.g. 4)
        """
        import re
        
        self._log(f"检查弹窗 '{dialog_title}' 中 '{target_text}' 出现 {expected_count} 次", "INFO")
        
        result = {
            'function': 'check_text_count_in_dialog',
            'dialog_title': dialog_title,
            'target_text': target_text,
            'expected_count': expected_count,
            'score': 0,
            'max_score': 1,
            'details': {
                'dialog_detected': False,
                'text_count': 0,
                'found_at_step': None
            }
        }
        
        # Title keyword variants
        title_keywords = [dialog_title.lower()]
        if "profile" in dialog_title.lower():
            title_keywords.extend(["proflle", "profi1e", "profile"])
        
        for i, screenshot in enumerate(self.screenshots):
            # === Step 1: Detect dialog title ===
            title_text = self._ocr_region(screenshot, "full")
            title_text_lower = title_text.lower()
            
            # Check if title exists
            found_title = next((k for k in title_keywords if k in title_text_lower), None)
            
            if not found_title:
                continue
            
            result['details']['dialog_detected'] = True
            self._log(f"[步骤 {i}] 检测到弹窗标题 '{dialog_title}'", "DEBUG")
            
            # === Step 2: Count target text occurrences in full region ===
            full_text = self._ocr_region(screenshot, "full")
            
            # Count occurrences (case-insensitive)
            # Use regex to ensure it is an isolated word (avoid matching "nm" inside "anm")
            pattern = rf'\b{re.escape(target_text)}\b'
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            count = len(matches)
            
            result['details']['text_count'] = count
            result['details']['found_at_step'] = i
            
            self._log(
                f"  Detected '{target_text}' {count} times in dialog (expected {expected_count} times)",
                "DEBUG"
            )
            
            # === Step 3: Determine if match ===
            if count == expected_count:
                result['score'] = 1
                self._log(
                    f"✓ [Step {i}] '{target_text}' count matched: {count} == {expected_count}",
                    "SUCCESS"
                )
                return result
            elif count > 0:
                # Partial match (text found but count wrong)
                result['score'] = 0.5
                self._log(
                    f"⚠ [Step {i}] '{target_text}' count mismatch: {count} != {expected_count}",
                    "WARNING"
                )
            else:
                self._log(
                    f"✗ [Step {i}] '{target_text}' not detected in dialog",
                    "FAIL"
                )
        
        if result['details']['dialog_detected']:
            self._log(
                f"✗ Dialog detected but '{target_text}' count incorrect: "
                f"{result['details']['text_count']} != {expected_count}",
                "FAIL"
            )
        else:
            self._log(f"✗ 未检测到弹窗 '{dialog_title}'", "FAIL")
        
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
        
        # Save results
        result_file = self.evaluate_folder / f"{task_name}_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(task_result, f, indent=2, ensure_ascii=False)
        
        return task_result


# ============ TASK CONFIGS ============

TASK_CONFIGS = {
    # Simple tasks
    "in1": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm1.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['5nm'], 'region': '底部30%'}}
    ],
    
    "in2": [
    {'function': 'check_file_import', 'args': {'expected_filename': 'dm2.dm3'}},
    {'function': 'check_ocr_text', 'args': {'target_text': ['Foreground Color'], 'region': 'full'}},
    {'function': 'check_text_color', 'args': {'text': 'nm', 'color_name': 'red', 'region': '底部50%'}}
    ],

    "text_color": [
    {'function': 'check_text_color', 'args': {'text': 'nm', 'color_name': 'red', 'region': '底部50%'}}
    ],

    
    "in3": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm3.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['nm'], 'region': '底部30%'}}
    ],
    
    "in4": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm4.dm3'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'Box'}},
        {'function': 'check_border_color', 'args': {'box_color': 'red', 'region': 'full', 'shape_type':'box'}}
    ],
    
    "border_color": [
        {'function': 'check_border_color', 'args': {'box_color': 'red', 'region': 'full'}}
    ],


    "in5": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm5.dm3'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'Oval'}},
        {'function': 'check_border_color', 'args': {'box_color': 'red', 'region': 'full','shape_type':'oval'}}
    ],
    
    "in6": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm6.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['sobel'], 'region': 'full'}}
    ],
    
    "in7": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm7.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['scale'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['2000','2000']}},
    ],
    
    "in8": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm8.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['rotate'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['p50']}},
    ],
    
    "in9": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm9.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Mean and Std'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Results','Standard Deviation']}},
    ],
    
    "in10": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm10.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Customize'], 'region': 'full'}},
        {'function': 'check_checkbox_selected', 'args': {'checkbox_text': 'Mask'}}
    ],
    
    # Medium tasks
    "in11": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm1.dm3'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'RectangleROI'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Add Data Bar'], 'region': 'full'}},
        {'function': 'check_data_bar_by_text', 'args': {'min_keywords': 2}}
    ],
    
    "in12": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm2.dm3'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'RectangleROI'}},
        {'function': 'check_roi_copy_and_enlarge', 'args': {}}
    ],
    
    "in13": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm4.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Profile Of dm4'], 'region': 'full'}},
        {'function': 'check_dialog_opened', 'args': {
            'title_keyword': 'Change Profile Info',
            'field_checks': {'Integration Width': 80}
        }}
    ],
    
    "in14": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm4.dm4'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['FFT of dm4'], 'region': 'full'}}
    ],
    
   "in15": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm5.dm5'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'Box'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Foreground'], 'region': 'full'}},
        {'function': 'check_filled_box_with_corners', 'args': {
            'fill_color': 'white',
            'corner_color': 'green'
        }}
    ],
    
    # Complex tasks
    "in16": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm1.dm3'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'Box'}},
        {'function': 'check_drawing_tool', 'args': {'tool_name': 'RectangleROI'}},
        {'function': 'check_roi_copy_and_enlarge', 'args': {}},
    ],
    
    "in17": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm2.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['Profile Of'], 'region': 'full'}},
        {'function': 'check_text_count_in_dialog', 'args': {
        'dialog_title': 'Profile Of',
        'target_text': 'nm',
        'expected_count': 5
    }}
    ],
    
    "in18": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm6.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['FFT of'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['IFFT of FFT of'], 'region': 'full'}}
    ],
    
    "in19": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm9.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['FFT of'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['SpotMask'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['IFFT of FFT of'], 'region': 'full'}}
    ],
    
    "in20": [
        {'function': 'check_file_import', 'args': {'expected_filename': 'dm7.dm3'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['FFT of'], 'region': 'full'}},
        {'function': 'check_ocr_text', 'args': {'target_text': ['IFFT of FFT of'], 'region': 'full'}},
        {'function': 'check_dialog_opened', 'args': {
            'title_keyword': 'Image Display Info',
            'field_checks': {'Brightness': 0.3,'Contrast':0.2}
        }}
    ]
}


# ============ MAIN FUNCTION ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='DigitalMicrograph 评估系统 v1.0')
    parser.add_argument('folder', type=str, help='Path to screenshot folder')
    parser.add_argument('task', type=str, help='Task name')
    parser.add_argument('--label-folder', type=str, help='标签文件夹路径（用于图像对比）',
                       default=None, dest='label_folder')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"DigitalMicrograph Evaluation System v1.0")
    print(f"{'='*60}\n")
    
    folder_path = Path(args.folder).resolve()
    
    if not folder_path.exists():
        print(f"❌ 错误: 文件夹不存在: {folder_path}")
        return
    
    print(f"✓ 文件夹: {folder_path}")
    print(f"✓ 任务: {args.task}")
    if args.label_folder:
        print(f"✓ 标签文件夹: {args.label_folder}")
    print()
    
    if args.task not in TASK_CONFIGS:
        print(f"❌ 未找到任务 '{args.task}'")
        print(f"\n可用任务:")
        for task_name in sorted(TASK_CONFIGS.keys()):
            print(f"  - {task_name}")
        return
    
    try:
        evaluator = DMEvaluator(str(folder_path), args.label_folder)
        result = evaluator.evaluate_task(args.task, TASK_CONFIGS[args.task])
        
        print(f"\n{'='*60}")
        print(f"评估完成!")
        print(f"{'='*60}")
        print(f"得分: {result['total_score']:.1f}/{result['max_score']} ({result['pass_rate']})")
        print(f"\n详细结果已保存至: {evaluator.evaluate_folder}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()