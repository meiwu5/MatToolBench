"""
DigitalMicrograph Evaluation System - Full Refactored Version
Main improvement: Refactored class methods into standalone functions accepting env parameter for modular imports

Contains the whole implementation of all evaluation functions
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
import glob

# ============ Core Path Functions ============

def get_trajectory_dir(env, config):
    """
    Core function: Extract ID from Cache path and automatically redirect to the deep directory in Results
    """
    # 1. Get Cache path (from env object or config dict)
    cache_path = getattr(env, "cache_dir", "")
    if not cache_path:
        cache_path = config.get("trajectory_dir", "")

    if not cache_path:
        print("[Error] Unable to get path info, please check if env.cache_dir is assigned")
        return None

    # 2. Extract Task ID
    task_id = os.path.normpath(cache_path).split(os.sep)[-1]
    
    if not task_id or task_id == ".":
        print(f"[Error] Unable to parse Task ID, original path: {cache_path}")
        return None

    # 3. Define Results search root directory
    # Dynamically obtained from env to avoid hardcoding model name/trial_id etc.
    results_base = getattr(env, "result_dir", None) or "/client/results"
    
    print(f"\n" + "-"*30)
    print(f"📥 Received Cache path: {cache_path}")
    print(f"🎯 Extracted Task ID: {task_id}")
    print(f"🔍 Performing deep search under {results_base}...")

    # 4. Deep recursive search
    search_pattern = os.path.join(results_base, "**", f"*{task_id}*")
    found_dirs = glob.glob(search_pattern, recursive=True)
    
    valid_dirs = [d for d in found_dirs if os.path.isdir(d)]
    
    if valid_dirs:
        valid_dirs.sort(key=os.path.getmtime, reverse=True)
        for candidate in valid_dirs:
            if glob.glob(os.path.join(candidate, "screenshot*.png")):
                print(f"✅ Successfully matched real path: {candidate}")
                print("-"*30 + "\n")
                return candidate

    print(f"❌ Search failed: no folder containing {task_id} with screenshots found under {results_base}")
    return None

# ============ Global Helper Functions ============

def _extract_step_number(filename: str) -> int:
    """Extract step number from filename."""
    match = re.search(r'step_(\d+)', filename)
    return int(match.group(1)) if match else 0


def _get_ocr_reader():
    """Get OCR reader singleton."""
    if not hasattr(_get_ocr_reader, 'reader'):
        _get_ocr_reader.reader = easyocr.Reader(['en'], gpu=True)
    return _get_ocr_reader.reader


def _load_screenshots(base_folder: Path) -> List[Path]:
    """Load screenshot files."""
    screenshots = sorted(
        base_folder.glob("screenshot-step_*.png"),
        key=lambda x: _extract_step_number(x.name)
    )
    return screenshots


def _normalize_ocr_text(text: str) -> str:
    """Normalize OCR text."""
    replacements = [
        ('l', '1'), ('I', '1'), ('|', '1'),
        ('O', '0'), ('o', '0'), ('g', '9')
    ]
    
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    
    result = re.sub(r'\s+', ' ', result)
    return result


def _ocr_region(env, screenshot_path: Path, region: str = "whole", 
                cache_folder: Optional[Path] = None) -> str:
    """Perform OCR on the specified region of a screenshot (with cache)."""
    if cache_folder:
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    img = Image.open(screenshot_path)
    width, height = img.size
    
    region_map = {
        "Top5%": (0, 0, width, int(height * 0.05)),
        "Top10%": (0, 0, width, int(height * 0.1)),
        "Top20%": (0, 0, width, int(height * 0.2)),
        "bottom20%": (0, int(height * 0.8), width, height),
        "bottom50%": (0, int(height * 0.5), width, height),
        "Center": (int(width * 0.2), int(height * 0.2), 
                 int(width * 0.8), int(height * 0.8)),
    }
    
    if region != "whole" and region in region_map:
        img = img.crop(region_map[region])
    
    img_array = np.array(img)
    reader = _get_ocr_reader()
    results = reader.readtext(img_array)
    text = "\n".join([result[1] for result in results])
    
    if cache_folder:
        cache_folder.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    return text

# ============ Simple Task Evaluation Functions ============

def get_check_file_import(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the file has been imported."""
    expected_filename = config.get('expected_filename')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_file_import',
            'expected_file': expected_filename,
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_file_import',
        'expected_file': expected_filename,
        'score': 0, 'max_score': 1,
        'details': {'found_at_step': None, 'status': 'not_found'}
    }
    
    screenshots = _load_screenshots(base_folder)
    if len(screenshots) < 1:
        result['details']['error'] = "Insufficient number of screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    cache_folder.mkdir(parents=True, exist_ok=True)
    
    filename_match = re.search(r'(dm\d+)', expected_filename, re.IGNORECASE)
    if not filename_match:
        result['details']['error'] = f"Unable to extract file information from {expected_filename}"
        return result
    
    base_name = filename_match.group(1).lower()
    num_match = re.search(r'dm(\d+)', base_name)
    file_number = num_match.group(1) if num_match else ''
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "Top20%", cache_folder)
        normalized_text = _normalize_ocr_text(text)
        
        patterns = [
            (rf'@[BC]\s*:\s*dm{file_number}\b', 'at_standard'),
            (rf'@[BC]\s*:\s*DM{file_number}\b', 'at_upper'),
            (rf'@[BC]:dm{file_number}\b', 'at_nospace'),
            (rf'[BC]\s*:\s*dm{file_number}\b', 'standard'),
        ]
        
        for pattern, pattern_name in patterns:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                result['score'] = 1
                result['details']['found_at_step'] = i
                result['details']['status'] = 'imported'
                result['details']['matched_text'] = match.group()
                return result
    
    return result


def get_check_ocr_text(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if OCR detected specific text."""
    target_text = config.get('target_text')
    region = config.get('region', 'whole')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_ocr_text',
            'target_text': target_text,
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    if isinstance(target_text, str):
        target_texts = [target_text]
    else:
        target_texts = target_text
    
    result = {
        'function': 'check_ocr_text',
        'target_text': target_texts,
        'score': 0, 'max_score': 1,
        'details': {'found_at_step': None, 'matched_texts': []}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, region, cache_folder)
        text_normalized = text.lower().replace(' ', '').replace('\n', '')
        
        matched = []
        for target in target_texts:
            target_normalized = target.lower().replace(' ', '')
            if target_normalized in text_normalized:
                matched.append(target)
        
        if matched:
            result['score'] = 1
            result['details']['found_at_step'] = i
            result['details']['matched_texts'] = matched
            return result
    
    return result


def get_check_drawing_tool(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a drawing tool was used."""
    tool_name = config.get('tool_name')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_drawing_tool',
            'tool_name': tool_name,
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_drawing_tool',
        'tool_name': tool_name,
        'score': 0, 'max_score': 1,
        'details': {'found_at_step': None}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        if tool_name.lower() in text.lower():
            result['score'] = 1
            result['details']['found_at_step'] = i
            return result
    
    return result


def get_check_parameter_value(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if parameter value is set correctly."""
    param_name = config.get('param_name')
    expected_value = config.get('expected_value')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_parameter_value',
            'param_name': param_name,
            'expected_value': expected_value,
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_parameter_value',
        'param_name': param_name,
        'expected_value': expected_value,
        'score': 0, 'max_score': 1,
        'details': {'found_at_step': None}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        patterns = [
            rf'{param_name}\s*[:：]\s*{expected_value}',
            rf'{param_name}\s+{expected_value}',
            rf'{param_name}\s*=\s*{expected_value}'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result['score'] = 1
                result['details']['found_at_step'] = i
                return result
    
    return result


def get_check_border_color(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if there is a box of the specified color by detecting corner points."""
    box_color = config.get('box_color')
    corner_color = config.get('corner_color', 'green')
    region = config.get('region', 'whole')
    shape_type = config.get('shape_type', 'box')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_border_color',
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_border_color',
        'box_color': box_color,
        'corner_color': corner_color,
        'score': 0, 'max_score': 1,
        'details': {'found_at_step': None}
    }
    
    color_ranges = {
        'green': [(np.array([45, 80, 80]), np.array([75, 255, 255]))],
        'red': [(np.array([0, 120, 120]), np.array([10, 255, 255]))],
    }
    
    if corner_color.lower() not in color_ranges:
        return result
    
    screenshots = _load_screenshots(base_folder)
    crop_cache = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
    crop_cache.mkdir(parents=True, exist_ok=True)
    
    for i, screenshot in enumerate(screenshots):
        img = Image.open(screenshot)
        img_array = np.array(img)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        # Detect corner colors
        combined_mask = np.zeros(img_hsv.shape[:2], dtype=np.uint8)
        for lower, upper in color_ranges[corner_color.lower()]:
            mask = cv2.inRange(img_hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Morphological operations
        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        corner_data = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 30 < area < 500:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    corner_data.append((cx, cy))
        
        if len(corner_data) >= 4:
            result['score'] = 1
            result['details']['found_at_step'] = i
            return result
    
    return result


def get_check_text_color(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check the color of specific text."""
    text = config.get('text')
    color_name = config.get('color_name')
    region = config.get('region', 'whole')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_text_color',
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_text_color',
        'text': text,
        'expected_color': color_name,
        'score': 0, 'max_score': 1,
        'details': {'text_found': False, 'color_matched': False}
    }
    
    color_ranges = {
        'red': [(np.array([0, 100, 100]), np.array([10, 255, 255]))],
        'white': [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
        'green': [(np.array([40, 40, 40]), np.array([80, 255, 255]))],
    }
    
    if color_name.lower() not in color_ranges:
        return result
    
    screenshots = _load_screenshots(base_folder)
    reader = _get_ocr_reader()
    
    for i, screenshot in enumerate(screenshots):
        img = Image.open(screenshot)
        img_array = np.array(img)
        
        # OCR text localization
        ocr_results = reader.readtext(img_array, detail=1)
        
        for detection in ocr_results:
            bbox, detected_text, confidence = detection
            
            if text.lower() in detected_text.lower():
                result['details']['text_found'] = True
                
                # Extract text region and detect color
                bbox_array = np.array(bbox, dtype=np.int32)
                x_min = max(0, int(bbox_array[:, 0].min()) - 5)
                y_min = max(0, int(bbox_array[:, 1].min()) - 5)
                x_max = min(img_array.shape[1], int(bbox_array[:, 0].max()) + 5)
                y_max = min(img_array.shape[0], int(bbox_array[:, 1].max()) + 5)
                
                text_region = img_array[y_min:y_max, x_min:x_max]
                if text_region.size == 0:
                    continue
                
                text_region_bgr = cv2.cvtColor(text_region, cv2.COLOR_RGB2BGR)
                text_region_hsv = cv2.cvtColor(text_region_bgr, cv2.COLOR_BGR2HSV)
                
                # Detect color
                for lower, upper in color_ranges[color_name.lower()]:
                    mask = cv2.inRange(text_region_hsv, lower, upper)
                    ratio = np.sum(mask > 0) / mask.size if mask.size > 0 else 0
                    
                    if ratio > 0.15:
                        result['score'] = 1
                        result['details']['color_matched'] = True
                        result['details']['found_at_step'] = i
                        return result
    
    return result


def get_check_checkbox_selected(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a checkbox is selected."""
    checkbox_text = config.get('checkbox_text')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_checkbox_selected',
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_checkbox_selected',
        'checkbox_text': checkbox_text,
        'score': 0, 'max_score': 1,
        'details': {'text_found': False, 'checkbox_detected': False}
    }
    
    screenshots = _load_screenshots(base_folder)
    
    try:
        import pytesseract
        from pytesseract import Output
        
        for i, screenshot in enumerate(screenshots):
            img = cv2.imread(str(screenshot))
            if img is None:
                continue
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            ocr_data = pytesseract.image_to_data(pil_img, output_type=Output.DICT, lang='eng')
            
            # Find target text
            for j in range(len(ocr_data['text'])):
                word = ocr_data['text'][j].strip()
                if checkbox_text.lower() == word.lower():
                    result['details']['text_found'] = True
                    
                    text_x = ocr_data['left'][j]
                    text_y = ocr_data['top'][j]
                    text_h = ocr_data['height'][j]
                    
                    # Search for checkbox to the left of text
                    checkbox_x = max(0, text_x - 50)
                    checkbox_y = max(0, text_y - 5)
                    checkbox_w = 45
                    checkbox_h = text_h + 10
                    
                    checkbox_region = img[checkbox_y:checkbox_y + checkbox_h,
                                        checkbox_x:checkbox_x + checkbox_w]
                    
                    if checkbox_region.size > 0:
                        gray = cv2.cvtColor(checkbox_region, cv2.COLOR_BGR2GRAY)
                        dark_ratio = np.sum(gray < 100) / gray.size
                        
                        if dark_ratio > 0.10:
                            result['score'] = 1
                            result['details']['checkbox_detected'] = True
                            result['details']['found_at_step'] = i
                            return result
    except Exception as e:
        result['details']['error'] = str(e)
    
    return result


def get_check_dialog_opened(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect dialog title and field values."""
    title_keyword = config.get('title_keyword', '')
    field_checks = config.get('field_checks')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_dialog_opened',
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_dialog_opened',
        'score': 0, 'max_score': 1,
        'details': {
            'dialog_detected': False,
            'target_keyword': title_keyword,
            'field_results': {}
        }
    }
    
    search_keywords = [title_keyword.lower()]
    if title_keyword.lower() == "properties":
        search_keywords.extend(["propertie", "properlie"])
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        title_text = _ocr_region(env, screenshot, "whole", cache_folder)
        title_text_lower = title_text.lower()
        
        found_title = next((k for k in search_keywords if k in title_text_lower), None)
        
        if not found_title:
            continue
        
        result['details']['dialog_detected'] = True
        result['details']['detected_at_step'] = i
        
        if not field_checks:
            result['score'] = 1
            return result
        
        # Check fields
        field_text = _ocr_region(env, screenshot, "whole", cache_folder)
        field_text_lower = field_text.lower()
        
        all_fields_match = True
        for field_name, expected_value in field_checks.items():
            value_str = str(expected_value)
            field_patterns = [field_name.lower()]
            
            field_matched = False
            for field_pat in field_patterns:
                pattern = rf'{field_pat}\s*[:：]\s*{re.escape(value_str)}\b'
                if re.search(pattern, field_text_lower):
                    field_matched = True
                    break
            
            result['details']['field_results'][field_name] = {
                'expected': expected_value,
                'matched': field_matched
            }
            
            if not field_matched:
                all_fields_match = False
        
        if all_fields_match:
            result['score'] = 1
            return result
    
    return result


def get_check_data_bar_by_text(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect presence of Data Bar by recognizing its characteristic text."""
    min_keywords = config.get('min_keywords', 2)
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_data_bar_by_text',
            'score': 0, 'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_data_bar_by_text',
        'score': 0, 'max_score': 1,
        'details': {'data_bar_detected': False, 'matched_keywords': []}
    }
    
    keyword_patterns = {
        'voltage': r'\d{2,3}\s*kV',
        'magnification': r'[xX]\d{3,7}',
        'pixels': r'\d{3,5}\s*x\s*\d{3,5}\s*pixels?',
        'device': r'(OneView|Gatan|CCD)',
        'exposure_time': r'\d+\.?\d*\s*[sm]s',
    }
    
    screenshots = _load_screenshots(base_folder)
    reader = _get_ocr_reader()
    
    for i, screenshot in enumerate(screenshots):
        img = Image.open(screenshot)
        img_array = np.array(img)
        height, width = img_array.shape[:2]
        
        # Crop search region
        search_region = img_array[int(height*0.15):int(height*0.85), :int(width*0.5)]
        
        try:
            ocr_results = reader.readtext(search_region)
            ocr_text = ' '.join([r[1] for r in ocr_results])
            
            matched = []
            for keyword_name, pattern in keyword_patterns.items():
                if re.findall(pattern, ocr_text, re.IGNORECASE):
                    matched.append(keyword_name)
            
            if len(matched) >= min_keywords:
                result['score'] = 1
                result['details']['data_bar_detected'] = True
                result['details']['found_at_step'] = i
                result['details']['matched_keywords'] = matched
                return result
        except Exception:
            continue
    
    return result


# ============ Advanced Detection Functions ============

def get_check_roi_copy_and_enlarge(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect if RectangleROI is copied and enlarged to cover the original area.

    Logic:
    1. Detect the first valid ROI (4 green corner points with consistent color)
    2. Detect significant ROI position change (Y-center moved > 30% of original height)

    This means: the copied enlarged area covers the original ROI, and the new ROI frame appears at a different position.

    Args:
        env: environment object
        config: configuration dict

    Returns:
        Dict: evaluation result
            - score: 0 or 1
            - details: details including ROI position change
    """
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_roi_copy_and_enlarge',
            'score': 0,
            'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
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
    
    screenshots = _load_screenshots(base_folder)
    crop_cache_folder = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
    crop_cache_folder.mkdir(parents=True, exist_ok=True)
    
    for i, screenshot in enumerate(screenshots):
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
        
        # Morphological operations
        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find corner points
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Collect candidate corner points
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
        
        # Color consistency check (find the 4 most consistent corner points)
        valid_roi = None
        
        if len(candidate_corners) >= 4:
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
        
        roi_history.append({
            'step': i,
            'roi': valid_roi,
            'candidate_count': len(candidate_corners)
        })
        
        # Save debug image
        debug_img = img_bgr.copy()
        
        if valid_roi:
            # Draw ROI frame
            cv2.rectangle(
                debug_img,
                (int(valid_roi['x_min']), int(valid_roi['y_min'])),
                (int(valid_roi['x_max']), int(valid_roi['y_max'])),
                (0, 255, 255), 3
            )
            
            # Mark center
            cv2.circle(debug_img, (int(valid_roi['center_x']), int(valid_roi['center_y'])), 10, (0, 0, 255), -1)
            
            # Mark corner points
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
        
        debug_path = crop_cache_folder / f"roi_position_step{i}.png"
        cv2.imwrite(str(debug_path), debug_img)
        
        # Record the first valid ROI
        if valid_roi and first_roi_info is None:
            first_roi_info = valid_roi
            result['details']['first_roi_detected'] = True
            result['details']['first_roi_step'] = i
            result['details']['first_roi_center'] = (center_x, center_y)
        
        # Detect position change
        elif valid_roi and first_roi_info:
            # Calculate center displacement
            dx = abs(valid_roi['center_x'] - first_roi_info['center_x'])
            dy = abs(valid_roi['center_y'] - first_roi_info['center_y'])
            
            # Criterion: Y displacement > 30% of original ROI height
            threshold_y = first_roi_info['height'] * 0.3
            
            if dy > threshold_y:
                result['details']['position_changed'] = True
                result['details']['changed_step'] = i
                result['details']['new_roi_center'] = (valid_roi['center_x'], valid_roi['center_y'])
                result['details']['displacement'] = {'dx': float(dx), 'dy': float(dy)}
                result['score'] = 1
                
                result['details']['roi_history'] = roi_history
                return result
    
    result['details']['roi_history'] = roi_history
    return result


def get_check_filled_box_with_corners(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect a filled Box with green corner points.

    Logic:
    1. First detect 4 green corner points (locate Box frame)
    2. Then check if the interior of the frame is filled with the target color

    Args:
        env: environment object
        config: configuration dict
            - fill_color: fill color (default white)
            - corner_color: corner color (default green)

    Returns:
        Dict: evaluation result
    """
    fill_color = config.get('fill_color', 'white')
    corner_color = config.get('corner_color', 'green')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_filled_box_with_corners',
            'fill_color': fill_color,
            'corner_color': corner_color,
            'score': 0,
            'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
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
    
    screenshots = _load_screenshots(base_folder)
    crop_cache_folder = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
    crop_cache_folder.mkdir(parents=True, exist_ok=True)
    
    for i, screenshot in enumerate(screenshots):
        # Load image
        img = Image.open(screenshot)
        img_array = np.array(img)
        
        # Convert to HSV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        # Step 1: Detect green corner points
        green_mask = np.zeros(img_hsv.shape[:2], dtype=np.uint8)
        for lower, upper in color_ranges[corner_color.lower()]:
            mask = cv2.inRange(img_hsv, lower, upper)
            green_mask = cv2.bitwise_or(green_mask, mask)
        
        # Morphological operations
        kernel = np.ones((5, 5), np.uint8)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find corner points
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Collect candidate corner points
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
            continue
        
        # Color consistency check (find the 4 most consistent corner points)
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
            
            # Step 2: Check if the interior of the frame is filled with the target color
            # Extract interior region (inset slightly to avoid frame interference)
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
            
            # Mark corner points (green)
            for c in box['corners']:
                cv2.circle(debug_img, (c['x'], c['y']), 8, (0, 255, 0), -1)
                cv2.circle(debug_img, (c['x'], c['y']), 10, (0, 255, 255), 2)
            
            # Annotate fill information
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
        
        debug_path = crop_cache_folder / f"filled_box_step{i}.png"
        cv2.imwrite(str(debug_path), debug_img)
        
        if result['score'] > 0:
            return result
    
    return result


def get_check_text_count_in_dialog(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect the number of occurrences of specific text in a dialog.

    Args:
        env: environment object
        config: configuration dict
            - dialog_title: dialog title keyword (e.g. "Profile Of 2")
            - target_text: text to count (e.g. "nm")
            - expected_count: expected occurrence count (e.g. 4)

    Returns:
        Dict: evaluation result
    """
    dialog_title = config.get('dialog_title')
    target_text = config.get('target_text')
    expected_count = config.get('expected_count')
    base_folder = get_trajectory_dir(env, config)
    
    if not base_folder:
        return {
            'function': 'check_text_count_in_dialog',
            'dialog_title': dialog_title,
            'target_text': target_text,
            'expected_count': expected_count,
            'score': 0,
            'max_score': 1,
            'details': {'error': 'Unable to get trajectory directory'}
        }
    
    base_folder = Path(base_folder).resolve()
    
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
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        # Step 1: Detect dialog title
        title_text = _ocr_region(env, screenshot, "whole", cache_folder)
        title_text_lower = title_text.lower()
        
        # Check if title exists
        found_title = next((k for k in title_keywords if k in title_text_lower), None)
        
        if not found_title:
            continue
        
        result['details']['dialog_detected'] = True
        
        # Step 2: Count target text occurrences in the whole region
        full_text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        # Count occurrences (case-insensitive)
        # Use regex to ensure whole-word matching (avoid matching "nm" inside "anm")
        pattern = rf'\b{re.escape(target_text)}\b'
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        count = len(matches)
        
        result['details']['text_count'] = count
        result['details']['found_at_step'] = i
        
        # Step 3: Determine if it matches
        if count == expected_count:
            result['score'] = 1
            return result
        elif count > 0:
            # Partial match (text found but count wrong)
            result['score'] = 0.5
    
    return result
