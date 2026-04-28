"""
Jade XRD Evaluation System - Refactored v3
Main improvement: Refactored class methods into standalone functions accepting env parameter for modular imports
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
import glob

# ============ Global Configuration ============

INITIAL_IMAX_MAP = {
    'WRT-ZSX-5.txt': 5792, 'WRT-ZSX-5': 5792,
    'XRD1.xrdml': 454, 'XRD1': 454,
    'XRD2.xrdml': 1757, 'XRD2': 1757,
    'XRD3.xrdml': 456, 'XRD3': 456,
    'XRD4.xrdml': 463, 'XRD4': 463,
}


# ============ Helper Functions ============
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
    """Normalize OCR text and correct common misrecognitions."""
    if not text:
        return ""
    
    normalized = text
    
    # XRD series misrecognition corrections
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
    
    # WRT series misrecognition corrections
    wrt_replacements = {
        'WRT-Z2X': 'WRT-ZSX',
        'WRT-ZzX': 'WRT-ZSX',
        'WRT-ZSX-S': 'WRT-ZSX-5',
        'WRT-ZSX-s': 'WRT-ZSX-5',
    }
    
    for wrong, correct in wrt_replacements.items():
        normalized = normalized.replace(wrong, correct)
    
    return normalized


def _parse_bracket_content(content: str) -> Optional[str]:
    """Parse content inside brackets to extract filename."""
    if not content:
        return None
    
    content = content.strip()
    
    # XRD series files
    xrd_match = re.search(r'XRD\s*([1-4])', content, re.IGNORECASE)
    if xrd_match:
        num = xrd_match.group(1)
        if '.xrdml' in content.lower() or 'xrdml' in content.lower():
            return f'XRD{num}.xrdml'
        else:
            return f'XRD{num}'
    
    # WRT series files
    wrt_match = re.search(r'WRT[-\s]*ZSX[-\s]*5', content, re.IGNORECASE)
    if wrt_match:
        if '.txt' in content.lower():
            return 'WRT-ZSX-5.txt'
        else:
            return 'WRT-ZSX-5'
    
    return None


def _extract_filename_from_text(text: str) -> Optional[str]:
    """Extract filename from OCR text."""
    if not text:
        return None
    
    norm_text = _normalize_ocr_text(text)
    
    # Strategy 1: Bracket extraction
    bracket_patterns = [
        r'\[([^\]]*(?:XRD|xrd)[^\]]*)\]',
        r'\[([^\]]*(?:WRT|wrt)[^\]]*)\]',
    ]
    
    for pattern in bracket_patterns:
        match = re.search(pattern, norm_text)
        if match:
            bracket_content = match.group(1).strip()
            filename = _parse_bracket_content(bracket_content)
            if filename:
                return filename
        
        match = re.search(pattern, text)
        if match:
            bracket_content = match.group(1).strip()
            norm_content = _normalize_ocr_text(bracket_content)
            filename = _parse_bracket_content(norm_content)
            if filename:
                return filename
    
    # Strategy 2: Concatenated form
    connected_pattern = r'XRD([1-4AaIilLZz])xrdml'
    
    match = re.search(connected_pattern, norm_text, re.IGNORECASE)
    if match:
        char = match.group(1).upper()
        char_map = {'A': '4', 'I': '1', 'L': '1', 'Z': '2', '1': '1', '2': '2', '3': '3', '4': '4'}
        if char in char_map:
            return f'XRD{char_map[char]}.xrdml'
    
    match = re.search(connected_pattern, text, re.IGNORECASE)
    if match:
        char = match.group(1).upper()
        char_map = {'A': '4', 'I': '1', 'L': '1', 'Z': '2', '1': '1', '2': '2', '3': '3', '4': '4'}
        if char in char_map:
            return f'XRD{char_map[char]}.xrdml'
    
    # Strategy 3: Standard format
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
    
    # Strategy 4: Without extension
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
    
    # Strategy 5: Fuzzy matching
    fuzzy_pattern = r'\bXRD\s*[1-4AaIilLZz]\b'
    match = re.search(fuzzy_pattern, norm_text, re.IGNORECASE)
    if match:
        xrd_part = match.group(0).replace(' ', '').upper()
        last_char = xrd_part[-1]
        char_map = {'A': '4', 'I': '1', 'L': '1', 'Z': '2', '1': '1', '2': '2', '3': '3', '4': '4'}
        if last_char in char_map:
            return f'XRD{char_map[last_char]}'
    
    return None


def _extract_imax(text: str) -> Optional[int]:
    """Extract Imax value from text."""
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


# ============ OCR and File Loading Functions ============

def _get_ocr_reader():
    """Get OCR reader singleton."""
    if not hasattr(_get_ocr_reader, 'reader'):
        _get_ocr_reader.reader = easyocr.Reader(['en'], gpu=False)
    return _get_ocr_reader.reader


def _load_screenshots(base_folder) -> List[Path]:  # Optionally keep or remove Path type annotation
    """Load screenshot files."""
    # Unify to Path objects
    if isinstance(base_folder, str):
        base_folder = Path(base_folder)
    elif not isinstance(base_folder, Path):
        base_folder = Path(str(base_folder))  # Guard against unexpected types

    # Ensure the path exists (optional but recommended)
    if not base_folder.is_dir():
        print(f"Warning: Directory does not exist or is not a folder → {base_folder}")
        return []

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
    
    # Read image
    img = Image.open(screenshot_path)
    width, height = img.size
    
    # Crop region
    if region == "Top20%":
        img = img.crop((0, 0, width, int(height * 0.2)))
    elif region == "bottom20%":
        img = img.crop((0, int(height * 0.8), width, height))
    elif region == "Top5%":
        img = img.crop((0, 0, width, int(height * 0.05)))
    elif region == "Top10%":
        img = img.crop((0, 0, width, int(height * 0.1)))
    elif region == "bottom10%":
        img = img.crop((0, int(height * 0.9), width, height))
    elif region == "bottom5%":
        img = img.crop((0, int(height * 0.95), width, height))
    
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


def _identify_files_in_screenshots(env, screenshots: List[Path], cache_folder: Optional[Path] = None) -> List[Optional[str]]:
    """Identify filenames in all screenshots."""
    screenshot_files = []
    last_detected_file = None
    
    for i, screenshot in enumerate(screenshots):
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder)
        current_file = _extract_filename_from_text(title_text)
        
        if not current_file:
            current_file = last_detected_file
        else:
            last_detected_file = current_file
        
        screenshot_files.append(current_file)
    
    return screenshot_files


# ============ Core Check Functions ============

def get_check_file_opened_jade(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the file has been opened."""
    expected_filename = config.get('expected_filename')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_file_opened',
        'expected_file': expected_filename,
        'score': 0,
        'max_score': 1,
        'details': {'found_at_step': None, 'status': 'not_found'}
    }
    
    screenshots = _load_screenshots(base_folder)
    
    if len(screenshots) < 1:
        result['details']['error'] = "Insufficient number of screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    screenshot_files = _identify_files_in_screenshots(env, screenshots, cache_folder)
    
    expected_base = expected_filename
    for ext in ['.xrdml', '.txt', '.raw', '.xy', '.pdf', '.pid']:
        if expected_filename.lower().endswith(ext):
            expected_base = expected_filename[:-len(ext)]
            break
    expected_base = expected_base.rstrip('.').strip()
    
    found_index = -1
    for i, detected_file in enumerate(screenshot_files):
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
        
        if found_index == 0:
            result['details']['status'] = "Initially opened"
        else:
            result['details']['status'] = "Opened during process"
    
    return result


def get_check_peak_finding(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check peak finding operation."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_peak_finding',
        'score': 0,
        'max_score': 1,
        'details': {}
    }
    
    screenshots = _load_screenshots(base_folder)
    
    if len(screenshots) < 2:
        result['details']['error'] = "Insufficient number of screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    first_text = _ocr_region(env, screenshots[0], "bottom10%", cache_folder)
    last_text = _ocr_region(env, screenshots[-1], "bottom10%", cache_folder)
    
    has_zero_peaks = "0 Peaks" in first_text or "d=?" in first_text
    peak_match = re.search(r'(\d+)\s*Peaks?', last_text, re.IGNORECASE)
    
    if peak_match:
        peak_count = int(peak_match.group(1))
        has_peaks = peak_count > 0
        
        if has_zero_peaks and has_peaks and peak_count != 2:
            result['score'] = 1
            result['details']['peak_count'] = peak_count
    
    return result


def get_check_peak_add_two(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check the operation of adding two peaks."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_peak_add_two',
        'score': 0,
        'max_score': 1,
        'details': {
            'peak_counts': [],
            'initial_peaks': None,
            'final_peaks': None,
            'increase': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    
    if len(screenshots) < 2:
        result['details']['error'] = "Insufficient number of screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom20%", cache_folder)
        
        peak_match = re.search(r'(\d+)\s*Peaks?', text, re.IGNORECASE)
        
        if peak_match:
            peak_count = int(peak_match.group(1))
            result['details']['peak_counts'].append({
                'step': i,
                'count': peak_count
            })
    
    if len(result['details']['peak_counts']) >= 2:
        initial_peak = result['details']['peak_counts'][0]['count']
        result['details']['initial_peaks'] = initial_peak
        
        final_peak = result['details']['peak_counts'][-1]['count']
        result['details']['final_peaks'] = final_peak
        
        increase = final_peak - initial_peak
        result['details']['increase'] = increase
        
        if increase == 2:
            result['score'] = 1
    
    return result


def get_check_background_removal(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check background subtraction."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_background_removal',
        'score': 0,
        'max_score': 1,
        'details': {}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    screenshot_files = _identify_files_in_screenshots(env, screenshots, cache_folder)
    
    dynamic_baselines = {}
    
    for i, screenshot in enumerate(screenshots):
        current_fname = screenshot_files[i]
        
        if not current_fname:
            continue
        
        data_text = _ocr_region(env, screenshot, "Top20%", cache_folder)
        imax = _extract_imax(data_text)
        
        if imax is None:
            continue
        
        baseline = None
        
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
                break
        
        if baseline is None:
            if current_fname not in dynamic_baselines:
                dynamic_baselines[current_fname] = imax
            baseline = dynamic_baselines[current_fname]
        
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
            return result
    
    return result


def get_check_smoothing(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check smoothing operation."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_smoothing',
        'score': 0,
        'max_score': 1,
        'details': {'found_at_steps': []}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "Top20%", cache_folder)
        
        if "Smooth whole Pattern" in text or "Smooth Whole Pattern" in text:
            result['details']['found_at_steps'].append(i)
    
    if result['details']['found_at_steps']:
        result['score'] = 1
    
    return result


def get_check_smoothing_and_background(env, config: Dict[str, Any]) -> Dict[str, Any]:
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    """Check smoothing and background subtraction operations."""
    result = {
        'function': 'get_check_smoothing_and_background',
        'score': 0,
        'max_score': 2,
        'details': {}
    }
    
    smoothing_result = check_smoothing(env, base_folder)
    background_result = check_background_removal(env, base_folder)
    
    result['details']['smoothing'] = smoothing_result
    result['details']['background'] = background_result
    result['score'] = smoothing_result['score'] + background_result['score']
    
    return result


def get_check_axis_switch(env, config: Dict[str, Any]) -> Dict[str, Any]:
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_axis_switch',
        'score': 0,
        'max_score': 1,
        'details': {'axis_sequence': []}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom20%", cache_folder)
        
        if "Two-theta" in text or "Two-Theta" in text or "2θ" in text:
            result['details']['axis_sequence'].append(('two-theta', i))
        elif "d-Scale" in text or "d Scale" in text:
            result['details']['axis_sequence'].append(('d-scale', i))
    
    sequence = [axis[0] for axis in result['details']['axis_sequence']]
    
    if len(sequence) >= 3:
        if sequence[0] == 'two-theta' and 'd-scale' in sequence and sequence[-1] == 'two-theta':
            result['score'] = 1
    
    return result


def get_check_axes_menu(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the Axes menu was selected."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_axes_menu',
        'score': 0,
        'max_score': 1,
        'details': {
            'menu_expanded_steps': [],
            'menu_items_detected': []
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    
    if not screenshots:
        result['details']['error'] = "No screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    axes_menu_items = [
        "Grid OFF",
        "Grid ON (X)",
        "Grid ON (Y)",
        "Auto Scale",
        "Full Range",
        "Display Range",
        "Vertical Marker",
    ]
    
    for i, screenshot in enumerate(screenshots):
        full_text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        menu_items_found = 0
        found_items = []
        for item in axes_menu_items:
            if item in full_text:
                menu_items_found += 1
                found_items.append(item)
        
        if menu_items_found >= 3:
            result['details']['menu_expanded_steps'].append(i)
            result['details']['menu_items_detected'].append({
                'step': i,
                'count': menu_items_found,
                'items': found_items
            })
    
    if len(result['details']['menu_expanded_steps']) > 0:
        result['score'] = 1
    
    return result


def get_check_wpf_refinement(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check WPF refinement result."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_wpf_refinement',
        'score': 0,
        'max_score': 1,
        'details': {}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom5%", cache_folder)
        
        peaks_match = re.search(r'peaks?', text, re.IGNORECASE)
        if peaks_match:
            continue
        
        r_match = re.search(r'R\s*[-=]\s*(\d+\.?\d*)', text)
        if r_match:
            result['details']['r_value'] = r_match.group(1)
            result['score'] = 1
            break
    
    return result


def get_check_refinement_result(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check refinement result."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_refinement_result',
        'score': 0,
        'max_score': 1,
        'details': {}
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom5%", cache_folder)
        
        peaks_match = re.search(r'peaks?', text, re.IGNORECASE)
        if peaks_match:
            continue
        
        profile_match = re.search(r'(\d+)\s*profiles?', text, re.IGNORECASE)
        if profile_match:
            result['details']['profiles'] = profile_match.group(1)
            result['score'] = 1
            break
    
    return result


def get_check_dialog_title_jade(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check dialog title."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    title = config.get('title')
    
    result = {
        'function': 'get_check_dialog_title',
        'score': 0,
        'max_score': 1,
        'details': {
            'title': title
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        if title in text:
            result['score'] = 1
            result['details']['found_at_step'] = i
            break
    
    return result


def get_check_search_match_elements(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check S/M matched elements."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    result = {
        'function': 'get_check_search_match_elements',
        'score': 0,
        'max_score': 1,
        'details': {
            'element_count': 0
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        text_full = _ocr_region(env, screenshot, "whole", cache_folder)
        if "Search/Match Display" not in text_full:
            continue
        
        text_bottom = _ocr_region(env, screenshot, "bottom5%", cache_folder)
        
        checked_lines = re.findall(r'☑.*', text_bottom)
        
        if "Figure Of Merit" in text_bottom or "Chemical Formula" in text_bottom:
            result['score'] = 1
            result['details']['element_count'] = len(checked_lines) if checked_lines else 1
            result['details']['found_at_step'] = i
            break
    
    return result

