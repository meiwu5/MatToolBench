"""
Avantage XPS Evaluation System - Refactored Version
Main improvement: Refactored class methods into standalone functions accepting env parameter for modular imports
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import easyocr
from PIL import Image
import numpy as np
import glob

# ============ Helper Functions ============
def get_trajectory_dir(env, config):
    """
    Core function: Extract ID from Cache path and automatically redirect to the deep directory in Results
    """
    cache_path = getattr(env, "cache_dir", "")
    if not cache_path:
        cache_path = config.get("trajectory_dir", "")

    if not cache_path:
        print("[Error] Unable to get path info, please check if env.cache_dir is assigned")
        return None

    # 2. Extract Task ID (from "Cache\38103299..." extract "38103299...")
    # Handle Windows path separators and take the last segment
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

    # 4. Deep recursive search for folders containing the ID (using ** to match all levels)
    search_pattern = os.path.join(results_base, "**", f"*{task_id}*")
    found_dirs = glob.glob(search_pattern, recursive=True)
    
    # Filter for actual directories
    valid_dirs = [d for d in found_dirs if os.path.isdir(d)]
    
    if valid_dirs:
        # Sort by modification time, take the newest directory
        valid_dirs.sort(key=os.path.getmtime, reverse=True)
        for candidate in valid_dirs:
            # Verify the directory contains images to ensure it is not empty
            if glob.glob(os.path.join(candidate, "screenshot*.png")):
                print(f"✅ Successfully matched real path: {candidate}")
                print("-"*30 + "\n")
                return candidate

    print(f"❌ Search failed: no folder containing {task_id} with screenshots found under {results_base}")
    return None


def _extract_step_number(filename: str) -> int:
    """Extract step number from filename."""
    match = re.search(r'step_(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0


def _normalize_ocr_text(text: str) -> str:
    """Normalize OCR text and correct common OCR recognition errors."""
    if not text:
        return ""
    
    # Remove all spaces for easier matching
    normalized_nospace = text.replace(' ', '').replace('\n', '').lower()
    
    return normalized_nospace


def _check_binding_energy(normalized_text: str) -> bool:
    """Check if the text contains "Binding Energy"."""
    binding_variants = [
        'bindingenergy',
        'binding energy',
        'bindingenersy',
        'bindingenerty',
        'binclingenergy',
        'bindingfnergy',
    ]
    
    for variant in binding_variants:
        if variant in normalized_text:
            return True
    
    # Loose matching
    if 'binding' in normalized_text and 'energ' in normalized_text:
        return True
    
    return False


def _extract_all_filenames_from_text(text: str, normalized_text: str) -> list:
    """Extract all filenames from OCR text."""
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
    
    for normalized_key, info in scan_variants.items():
        for variant in info['variants']:
            if variant in normalized_text:
                if info['standard_name'] not in found_files:
                    found_files.append(info['standard_name'])
                break
    
    return found_files


def _extract_matched_variant(normalized_text: str, standard_filename: str) -> str:
    """Extract the actually matched normalized variant."""
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
        for variant in info['variants']:
            if variant in normalized_text:
                return variant
        return info['normalized_key']
    
    return standard_filename.lower().replace(' ', '')


def _is_filename_variant(expected_normalized: str, detected_normalized: str) -> bool:
    """Check if the detected normalized filename is a variant of the expected filename."""
    variants_map = {
        'c1sscan': ['c1sscan', 'c1scan', 'clsscan', 'cisscan', 'c1s', 'cls', 'cis'],
        'o1sscan': ['o1sscan', 'o1scan', 'olsscan', 'oisscan', 'o1s', 'ols', 'ois'],
        'zn2pscan': ['zn2pscan', 'zn2scan', 'znzpscan', 'zn2p', 'znzp'],
        'xpssurvey': ['xpssurvey', 'xps', 'survey'],
        'surveyscan': ['surveyscan', 'survey']
    }
    
    if expected_normalized in variants_map:
        variants = variants_map[expected_normalized]
        return detected_normalized in variants
    
    return expected_normalized == detected_normalized


def _get_parameter_variants(parameter_name: str) -> list:
    """Get common OCR variants of a parameter name."""
    common_variants = {
        'font': ['font', 'Font', 'FONT', 'fon', 'fonl'],
        'color': ['color', 'Color', 'COLOR', 'colour', 'Colour', 'coIor'],
        'eV': ['eV', 'ev', 'EV', 'e V', 'e/', 'e\\\\/'],
        'FWHM': ['FWHM', 'fwhm', 'FW HM', 'FVVHM'],
        'amount': ['amount', 'Amount', 'AMOUNT', 'amoun', 'arnount'],
        'Rows': ['Rows', 'rows', 'ROWS', 'Row', 'Rovvs'],
        'Columns': ['Columns', 'columns', 'COLUMNS', 'Column', 'Colurnns']
    }
    
    if parameter_name in common_variants:
        return common_variants[parameter_name]
    
    return [
        parameter_name,
        parameter_name.lower(),
        parameter_name.upper(),
        parameter_name.capitalize()
    ]


def _get_value_variants(expected_value: str) -> list:
    """Get common OCR variants of an expected value."""
    variants = [expected_value]
    
    # Common OCR errors for digits
    if expected_value.isdigit():
        variant = expected_value.replace('0', 'O')
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
        variants.append(expected_value.replace('.', ','))
        variants.append(expected_value.replace('.', ''))
    
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
    
    return list(set(variants))


def _get_filename_variants(standard_filename: str) -> List[str]:
    """Get all possible variants of a filename."""
    variants_map = {
        'C1s Scan': ['c1sscan', 'c1scan', 'clsscan', 'cisscan', 'C1s Scan', 'CIs Scan'],
        'O1s Scan': ['o1sscan', 'o1scan', 'olsscan', 'oisscan',  'O1s Scan', 'O1s', 'o1s scan'],
        'Zn2p Scan': ['zn2pscan', 'zn2scan', 'znzpscan', 'zn2p', 'znzp', 'Zn2p Scan', 'Zn2p', 'zn2p scan'],
        'XPS Survey': ['xpssurvey', 'xps', 'survey', 'XPS Survey', 'XPS', 'xps survey'],
        'Survey Scan': ['surveyscan', 'survey', 'Survey Scan', 'survey scan']
    }
    
    if standard_filename in variants_map:
        return variants_map[standard_filename]
    
    return [
        standard_filename,
        standard_filename.lower(),
        standard_filename.lower().replace(' ', ''),
        standard_filename.replace(' ', '')
    ]


# ============ OCR and File Loading Functions ============

def _get_ocr_reader():
    """Get OCR reader singleton."""
    if not hasattr(_get_ocr_reader, 'reader'):
        _get_ocr_reader.reader = easyocr.Reader(['en'], gpu=False)
    return _get_ocr_reader.reader


def _load_screenshots(base_folder: Path) -> List[Path]:
    """Load screenshot files."""
    screenshot_pattern = "screenshot-step_*.png"
    screenshots = sorted(
        base_folder.glob(screenshot_pattern),
        key=lambda x: _extract_step_number(x.name)
    )
    return screenshots


def _ocr_region(env, screenshot_path: Path, region: str = "whole", cache_folder: Optional[Path] = None) -> str:
    """Perform OCR on the specified region of a screenshot."""
    # Check cache
    if cache_folder:
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    # Load image and crop
    img = Image.open(screenshot_path)
    width, height = img.size
    
    if region == "Top5%":
        img = img.crop((0, 0, width, int(height * 0.05)))
    elif region == "Top10%":
        img = img.crop((0, 0, width, int(height * 0.1)))
    elif region == "Top20%":
        img = img.crop((0, 0, width, int(height * 0.2)))
    elif region == "bottom5%":
        img = img.crop((0, int(height * 0.95), width, height))
    elif region == "bottom10%":
        img = img.crop((0, int(height * 0.9), width, height))
    elif region == "bottom 30%":
        img = img.crop((0, int(height * 0.7), width, height))
    elif region == "20% on the left":
        img = img.crop((0, 0, int(width * 0.2), height))
    elif region == "40% on the left":
        img = img.crop((0, 0, int(width * 0.4), height))
    elif region == "Right10%":
        img = img.crop((int(width * 0.9), 0, width, height))
    elif region == "50% of the center":
        left = int(width * 0.25)
        top = int(height * 0.25)
        right = int(width * 0.75)
        bottom = int(height * 0.75)
        img = img.crop((left, top, right, bottom))
    
    # OCR recognition
    img_array = np.array(img)
    reader = _get_ocr_reader()
    results = reader.readtext(img_array)
    text = "\n".join([result[1] for result in results])
    
    # Save cache
    if cache_folder:
        cache_folder.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    return text


def _identify_files_in_screenshots(env, screenshots: List[Path], cache_folder: Optional[Path] = None) -> tuple:
    """Identify filenames in all screenshots."""
    screenshot_files = []
    screenshot_files_normalized = []
    
    for i, screenshot in enumerate(screenshots):
        center_text = _ocr_region(env, screenshot, "50% of the center", cache_folder)
        normalized_text = _normalize_ocr_text(center_text)
        
        has_binding_energy = _check_binding_energy(normalized_text)
        
        current_files = []
        current_normalized_list = []
        
        if has_binding_energy:
            current_files = _extract_all_filenames_from_text(center_text, normalized_text)
            for file in current_files:
                variant = _extract_matched_variant(normalized_text, file)
                current_normalized_list.append(variant)
        
        if not current_files:
            screenshot_files.append(None)
            screenshot_files_normalized.append(None)
        else:
            if len(current_files) == 1:
                screenshot_files.append(current_files[0])
                screenshot_files_normalized.append(current_normalized_list[0])
            else:
                screenshot_files.append(current_files)
                screenshot_files_normalized.append(current_normalized_list)
    
    return screenshot_files, screenshot_files_normalized


# ============ Core Check Functions ============

def get_check_multiple_files_imported(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if multiple files have all been successfully imported (single-frame satisfaction principle)."""
    expected_files = config.get('expected_files', [])
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_multiple_files_imported',
        'score': 0,
        'max_score': 1,
        'details': {
            'expected_files': expected_files,
            'status': 'failed',
            'best_step_match': None,
            'error': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    
    if len(screenshots) < 1:
        result['details']['error'] = "Insufficient number of screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    screenshot_files, screenshot_files_normalized = _identify_files_in_screenshots(env, screenshots, cache_folder)
    
    expected_normalized_map = {
        expected.lower().replace(' ', ''): expected 
        for expected in expected_files
    }
    expected_count = len(expected_files)
    
    max_files_found = 0
    best_step_details = {}

    for i, (detected_file_data, detected_normalized_data) in enumerate(zip(screenshot_files, screenshot_files_normalized)):
        if not detected_file_data:
            continue

        current_frame_normalized_list = detected_normalized_data if isinstance(detected_normalized_data, list) else [detected_normalized_data]
        
        matched_expectations = set()
        
        for detected_norm in current_frame_normalized_list:
            for expected_key, expected_original in expected_normalized_map.items():
                if expected_original not in matched_expectations:
                    if _is_filename_variant(expected_key, detected_norm):
                        matched_expectations.add(expected_original)
        
        current_match_count = len(matched_expectations)
        
        if current_match_count > max_files_found:
            max_files_found = current_match_count
            best_step_details = {
                'step': i,
                'found_files': list(matched_expectations),
                'missing': list(set(expected_files) - matched_expectations)
            }

        if current_match_count < expected_count:
            continue
        
        current_screenshot = screenshots[i]
        ocr_text = _ocr_region(env, current_screenshot, "whole", cache_folder)
        
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
        
        if binding_energy_count == expected_count:
            result['score'] = 1
            result['details']['status'] = 'success'
            result['details']['success_step'] = i
            result['details']['found_files'] = list(matched_expectations)
            result['details']['binding_energy_count'] = binding_energy_count
            return result

    result['details']['best_attempt'] = best_step_details
    return result


def get_check_image_zoom(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Image zoom in/out: detect if specific values appear on the axis then disappear."""
    target_value = config.get('target_value')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
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
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    appeared = False
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom 30%", cache_folder)
        
        if target_value in text:
            if not appeared:
                appeared = True
                result['details']['appeared'] = True
                result['details']['appeared_at'] = i
        elif appeared and target_value not in text:
            result['details']['disappeared'] = True
            result['details']['disappeared_at'] = i
            result['score'] = 1
            break
    
    return result


def get_check_stacked_graph(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Stacked chart detection (compatible version)."""
    small_values = config.get('small_values', ['2', '4', '6', '8'])
    normal_markers = config.get('normal_markers', None)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
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

    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name

    pattern_scientific = re.compile(r'\d\.\d+e\d+|0\.00e') 
    pattern_large_int = re.compile(r'\d{4,}') 

    has_seen_normal = False
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "50% of the center", cache_folder).lower()
        
        is_sci = bool(pattern_scientific.search(text))
        is_int = bool(pattern_large_int.search(text))
        is_custom = any(m in text for m in normal_markers) if normal_markers else False
        
        if is_sci or is_int or is_custom:
            has_seen_normal = True
            result['details']['has_seen_normal'] = True
            if is_sci: result['details']['detected_normal_type'] = "scientific"
            elif is_int: result['details']['detected_normal_type'] = "large_int"
            else: result['details']['detected_normal_type'] = "custom_marker"
            continue

        if has_seen_normal:
            detected_smalls = [v for v in small_values if v in text]
            
            if not (is_sci or is_int or is_custom) and len(detected_smalls) >= 2:
                result['score'] = 1
                result['details']['success_step'] = i
                result['details']['found_small_values'] = detected_smalls
                return result

    return result


def get_check_duplicate_files_imported(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect duplicate file import/copy spectrum (single-frame strict matching principle)."""
    expected_files = config.get('expected_files', [])
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
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
    
    screenshots = _load_screenshots(base_folder)
    
    if not screenshots:
        result['details']['error'] = "No available screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    screenshot_files, screenshot_files_normalized = _identify_files_in_screenshots(env, screenshots, cache_folder)
    
    expected_total_count = len(expected_files)
    norm_expected_list = [f.lower().replace(' ', '') for f in expected_files]
    
    max_total_matched = 0
    best_step_details = {}

    for i, (detected_file_data, detected_normalized_data) in enumerate(zip(screenshot_files, screenshot_files_normalized)):
        if not detected_file_data:
            continue

        current_frame_detected_norm = detected_normalized_data if isinstance(detected_normalized_data, list) else [detected_normalized_data]
        temp_norm_expected = norm_expected_list.copy()
        matched_count = 0
        
        for detected_norm in current_frame_detected_norm:
            for j, target_norm in enumerate(temp_norm_expected):
                if _is_filename_variant(target_norm, detected_norm):
                    matched_count += 1
                    temp_norm_expected.pop(j)
                    break
        
        if matched_count > max_total_matched:
            max_total_matched = matched_count
            best_step_details = {'step': i, 'matched_count': matched_count}

        if matched_count == expected_total_count:
            current_screenshot = screenshots[i]
            ocr_text = _ocr_region(env, current_screenshot, "whole", cache_folder)
            
            binding_energy_count = 0
            binding_energy_variants = [
                'bindingenergy', 'binding energy', 'bindingenersy', 
                'bindingenerty', 'binclingenergy', 'bindingfnergy', 'binding'
            ]
            
            lines = ocr_text.lower().split('\n')
            for line in lines:
                line_normalized = line.replace(' ', '')
                for variant in binding_energy_variants:
                    if variant in line_normalized:
                        binding_energy_count += 1
                        break 
            
            if binding_energy_count == expected_total_count:
                result['score'] = 1
                result['details'].update({
                    'status': 'success',
                    'success_step': i,
                    'binding_energy_count': binding_energy_count
                })
                return result

    result['details']['best_attempt'] = best_step_details
    return result

def get_check_background_added_successfully(env, config: Dict[str, Any]) -> Dict[str, Any]:
    title = config.get('title')
    bg_type = config.get('bg_type', 'Smart')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    """
    Prove background has been added: detect dialog opened, specified background type text appeared inside, then dialog closed.
    """
    self._log(f"Starting deep detection of background operation: {title} -> {bg_type}", "Info")
    
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
        # Get full-image text with normalization
        text = self._ocr_region(screenshot, "whole").lower()
        norm_text = text.replace(' ', '')
        norm_title = title.lower().replace(' ', '')
        norm_bg = bg_type.lower()

        # Determine if the dialog is present in the current frame
        is_dialog_open = norm_title in norm_text

        if is_dialog_open:
            if not result['details']['dialog_appeared']:
                result['details']['dialog_appeared'] = True
                self._log(f"  Step [{i:02d}]: Found dialog '{title}'", "Debug")
            
            dialog_appeared_step = i
            
            # Core proof: whether 'smart' text appeared inside the dialog
            # Note: we usually detect in the background list area on the left side of the dialog
            if norm_bg in text:
                has_seen_bg_text = True
                result['details']['bg_text_detected'] = True
                self._log(f"  Step [{i:02d}]: ✓ Successfully recognized background type text '{bg_type}'", "Debug")
            continue

        # If the dialog was previously seen but now disappeared
        if result['details']['dialog_appeared'] and not is_dialog_open:
            if i > dialog_appeared_step:
                result['details']['dialog_closed'] = True
                # Only award full score when dialog appeared, Smart text was recognized, and dialog has closed
                if has_seen_bg_text:
                    result['score'] = 1
                    self._log(f"✓ Success: whole detected background addition trajectory (open-recognize {bg_type}-close)", "Success")
                    return result

    # Failure diagnosis
    if not result['details']['dialog_appeared']:
        self._log(f"✗ Failure: dialog '{title}' not detected", "Failure")
    elif not has_seen_bg_text:
        self._log(f"✗ Failure: dialog opened but '{bg_type}' not recognized in its list (possibly Add not clicked or default parameters not applied)", "Failure")
    else:
        self._log(f"✗ Failure: background recognized but dialog close action not detected", "Failure")

    return result

    """
    Detect if the occurrence count of a specific element (e.g., filename) increases to the expected value.
    Used to detect copy operations (e.g., copy to window B).

    Args:
        element_name: element name
        expected_count: expected occurrence count

    Returns:
        evaluation result dict
    """
    self._log(f"Checking element count increase: {element_name} -> {expected_count}", "Info")
    
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
        text = self._ocr_region(screenshot, "whole")
        count = text.count(element_name)
        
        if count > result['details']['max_count']:
            result['details']['max_count'] = count
        
        if count >= expected_count:
            result['score'] = 1
            result['details']['found_at'] = i
            self._log(f"✓ Element '{element_name}' appeared {count} times (screenshot {i})", "Success")
            break
    
    if result['score'] == 0:
        self._log(
            f"✗ Element '{element_name}' appeared at most {result['details']['max_count']} times,"
            f" expected {expected_count} times",
            "Failure"
        )
    
    return result

    """
    Detect if a dialog title has appeared.

    Args:
        title: dialog title

    Returns:
        evaluation result dict
    """
    self._log(f"Checking dialog title: {title}", "Info")
    
    result = {
        'function': 'check_dialog_title',
        'score': 0,
        'max_score': 1,
        'details': {'title': title}
    }
    
    for i, screenshot in enumerate(self.screenshots):
        text = self._ocr_region(screenshot, "whole")
        
        if title in text:
            result['score'] = 1
            result['details']['found_at'] = i
            self._log(f"✓ Found dialog title: {title} (screenshot {i})", "Success")
            break
    
    if result['score'] == 0:
        self._log(f"✗ Dialog title not found: {title}", "Failure")
    
    return result

    """
    Detect if a dialog appeared and then disappeared.

    Args:
        title: dialog title

    Returns:
        evaluation result dict
    """
    self._log(f"Checking dialog appear and close: {title}", "Info")
    
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
        text = self._ocr_region(screenshot, "whole")
        
        if title in text:
            if not appeared:
                appeared = True
                result['details']['appeared'] = True
                result['details']['appeared_at'] = i
                self._log(f"  Step [{i:02d}]: Dialog appeared", "Debug")
        elif appeared and title not in text:
            result['details']['closed'] = True
            result['details']['closed_at'] = i
            result['score'] = 1
            self._log(f"✓ Dialog appeared and closed: appeared({result['details']['appeared_at']}) → closed({i})", "Success")
            break
    
    if result['score'] == 0:
        if appeared:
            self._log(f"✗ Dialog '{title}' appeared but did not close", "Failure")
        else:
            self._log(f"✗ Dialog '{title}' did not appear", "Failure")
    
    return result

def get_check_dialog_parameter(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect specific parameter values in a dialog, supports single or multiple parameter checks."""
    dialog_title = config.get('dialog_title')
    parameter_name = config.get('parameter_name')
    expected_value = config.get('expected_value', None)
    region = config.get('region', 'whole')
    forbidden_parameter = config.get('forbidden_parameter', None)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    if isinstance(parameter_name, str):
        parameter_name = [parameter_name]
    
    check_value = True
    if expected_value is None or expected_value == []:
        check_value = False
        expected_value = [None] * len(parameter_name)
    elif isinstance(expected_value, str):
        expected_value = [expected_value]
    
    if check_value and len(parameter_name) != len(expected_value):
        return {
            'function': 'check_dialog_parameter',
            'score': 0,
            'max_score': len(parameter_name),
            'error': 'Parameter names and expected values count mismatch'
        }
    
    num_params = len(parameter_name)
    
    result = {
        'function': 'check_dialog_parameter',
        'score': 0,
        'max_score': num_params,
        'details': {
            'dialog_title': dialog_title,
            'parameters': parameter_name if not check_value else dict(zip(parameter_name, expected_value)),
            'region': region,
            'check_value': check_value,
            'forbidden_parameter': forbidden_parameter,
            'found_params': {}
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, region, cache_folder)
        
        if dialog_title not in text:
            continue
        
        # Forbidden text present, skip this screenshot
        if forbidden_parameter and forbidden_parameter.lower() in text.lower():
            continue
        
        normalized_text = text.lower().replace(' ', '').replace('\n', '')
        
        for idx, param_name in enumerate(parameter_name):
            if param_name in result['details']['found_params']:
                continue
            
            expect_val = expected_value[idx] if check_value else None
            
            param_variants = _get_parameter_variants(param_name)
            
            matched = False
            matched_info = None
            
            if not check_value:
                for param_var in param_variants:
                    if param_var in text:
                        matched = True
                        matched_info = {'pattern': 'exact_match', 'param_variant': param_var, 'region': region, 'screenshot': i}
                        break
                    if param_var.lower() in text.lower():
                        matched = True
                        matched_info = {'pattern': 'case_insensitive', 'param_variant': param_var, 'region': region, 'screenshot': i}
                        break
                    param_norm = param_var.lower().replace(' ', '')
                    if param_norm in normalized_text:
                        matched = True
                        matched_info = {'pattern': 'normalized', 'param_variant': param_var, 'region': region, 'screenshot': i}
                        break
                
                if matched:
                    result['score'] += 1
                    result['details']['found_params'][param_name] = matched_info
            
            else:
                value_variants = _get_value_variants(expect_val)
                
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
                                matched_info = {'pattern': pattern, 'param_variant': param_var, 'value_variant': value_var, 'region': region, 'screenshot': i}
                                break
                        if matched:
                            break
                    if matched:
                        break
                
                if matched:
                    result['score'] += 1
                    result['details']['found_params'][param_name] = matched_info
        
        if result['score'] == num_params:
            return result
    
    return result


def get_check_dialog_exists(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if a dialog has appeared."""
    dialog_title = config.get('dialog_title')
    region = config.get('region', 'whole')
    forbidden_parameter = config.get('forbidden_parameter', None)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_dialog_exists',
        'score': 0,
        'max_score': 1,
        'details': {
            'dialog_title': dialog_title,
            'region': region,
            'forbidden_parameter': forbidden_parameter,
            'found_at': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    title_variants = _get_value_variants(dialog_title)
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, region, cache_folder)
        
        matched = False
        matched_variant = None
        
        for variant in title_variants:
            if variant in text:
                matched = True
                matched_variant = variant
                break
            
            if variant.lower() in text.lower():
                matched = True
                matched_variant = variant
                break
            
            text_normalized = text.replace(' ', '').replace('\n', '')
            variant_normalized = variant.replace(' ', '')
            if variant_normalized.lower() in text_normalized.lower():
                matched = True
                matched_variant = variant
                break
        
        if matched:
            if forbidden_parameter and forbidden_parameter.lower() in text.lower():
                continue  # Forbidden text present, skip this screenshot
            
            result['score'] = 1
            result['details']['found_at'] = i
            result['details']['matched_variant'] = matched_variant
            return result
    
    return result


def get_check_grid_layout(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if the grid layout is set correctly."""
    rows = config.get('rows', 3)
    columns = config.get('columns', 3)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_grid_layout',
        'score': 0,
        'max_score': 1,
        'details': {
            'rows': rows,
            'columns': columns
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        rows_match = re.search(rf'Rows?\s*[:\-=]?\s*{rows}', text, re.IGNORECASE)
        columns_match = re.search(rf'Columns?\s*[:\-=]?\s*{columns}', text, re.IGNORECASE)
        
        if rows_match and columns_match:
            result['score'] = 1
            result['details']['found_at'] = i
            break
    
    return result


def get_check_energy_axis_reversed(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if the energy axis is reversed."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_energy_axis_reversed',
        'score': 0,
        'max_score': 1,
        'details': {}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        if "Reverse Energy Axis" in text:
            result['score'] = 1
            result['details']['found_at'] = i
            break
    
    return result


def get_check_file_duplicated(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if a file has been copied the specified number of times (directly count OCR text)."""
    original_file = config.get('original_file')
    expected_copies = config.get('expected_copies', 2)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
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
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    original_variants = _get_filename_variants(original_file)
    
    for i, screenshot in enumerate(screenshots):
        ocr_text = _ocr_region(env, screenshot, "whole", cache_folder)
        lines = ocr_text.split('\n')
        
        max_count = 0
        matched_variant = None
        
        for variant in original_variants:
            count = 0
            variant_lower = variant.lower()
            
            for line in lines:
                line_lower = line.strip().lower()
                if line_lower == variant_lower or variant_lower in line_lower:
                    count += 1
            
            if count > max_count:
                max_count = count
                matched_variant = variant
        
        if max_count >= expected_copies:
            binding_energy_count = 0
            for line in lines:
                line_lower = line.strip().lower()
                if 'binding' in line_lower and 'energy' in line_lower:
                    binding_energy_count += 1
            
            if binding_energy_count >= expected_copies:
                result['score'] = 1
                result['details']['status'] = 'success'
                result['details']['found_at'] = i
                result['details']['actual_copies'] = max_count
                result['details']['matched_variant'] = matched_variant
                result['details']['binding_energy_count'] = binding_energy_count
                return result
    
    return result


# # ============ Task Evaluation Functions ============

# def evaluate_task(env, config: Dict[str, Any]) -> Dict[str, Any]:
#     """Evaluate whole task."""
#     task_name = config.get('task_name', 'Unknown Task')
#     checks = config.get('checks', [])
#     base_folder = config.get('base_folder', env.traj_dir)
    
#     task_result = {
#         'task_name': task_name,
#         'total_score': 0,
#         'max_score': 0,
#         'checks': []
#     }
    
#     function_map = {
#         'check_multiple_files_imported': check_multiple_files_imported,
#         'check_image_zoom': check_image_zoom,
#         'check_stacked_graph': check_stacked_graph,
#         'check_duplicate_files_imported': check_duplicate_files_imported,
#         'check_background_added_successfully': check_background_added_successfully,
#         'check_dialog_parameter': check_dialog_parameter,
#         'check_dialog_exists': check_dialog_exists,
#         'check_grid_layout': check_grid_layout,
#         'check_energy_axis_reversed': check_energy_axis_reversed,
#         'check_file_duplicated': check_file_duplicated,
#     }
    
#     for check in checks:
#         func_name = check['function']
#         args = check.get('args', {})
        
#         check_config = {**args, 'base_folder': base_folder}
        
#         if func_name in function_map:
#             func = function_map[func_name]
#             check_result = func(env, check_config)
            
#             task_result['checks'].append(check_result)
#             task_result['total_score'] += check_result['score']
#             task_result['max_score'] += check_result['max_score']
    
#     if task_result['max_score'] > 0:
#         pass_rate = (task_result['total_score'] / task_result['max_score']) * 100
#         task_result['pass_rate'] = f"{pass_rate:.1f}%"
#     else:
#         task_result['pass_rate'] = "N/A"
    
#     return task_result