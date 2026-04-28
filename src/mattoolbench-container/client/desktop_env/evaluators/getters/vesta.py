"""
VESTA Evaluation System - Full Refactored Version
Main improvement: Refactored class methods into standalone functions accepting env parameter for modular imports

Contains the whole implementation of all 20+ check functions
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

    # results_base: dynamically obtained from env to avoid hardcoding model name/trial_id/action_space etc.
    # Prefer env.result_dir (injected by run.py), fall back to standard container path
    results_base = getattr(env, "result_dir", None) or "/client/results"

    print(f"\n" + "-"*30)
    print(f"📥 Received Cache path: {cache_path}")
    print(f"🎯 Extracted Task ID: {task_id}")
    print(f"🔍 Performing deep search under {results_base}...")

    # Breadth search: does not rely on model name/trial_id subdirectory levels
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
        _get_ocr_reader.reader = easyocr.Reader(['en'], gpu=False)
    return _get_ocr_reader.reader


def _load_screenshots(base_folder: Path) -> List[Path]:
    """Load screenshot files."""
    screenshots = sorted(
        base_folder.glob("screenshot-step_*.png"),
        key=lambda x: _extract_step_number(x.name)
    )
    return screenshots


def _crop_central_region(img_path: Path, save_path: Path, crop_cache_folder: Path) -> Path:
    """Crop the center region of the image (removing Top10%, bottom20%, left 35%)."""
    img = Image.open(img_path)
    width, height = img.size

    left = int(width * 0.35)
    right = width
    top = int(height * 0.1)
    bottom = int(height * 0.8)

    cropped = img.crop((left, top, right, bottom))

    if save_path is None:
        save_path = crop_cache_folder / f"cropped_{img_path.stem}.png"

    cropped.save(save_path)
    return save_path


def _prepare_reference_image(ref_path: Path, output_name: str, crop_cache_folder: Path) -> Optional[Path]:
    """Prepare a cropped version of the reference image."""
    if not ref_path or not ref_path.exists():
        return None

    ref_cropped_path = crop_cache_folder / output_name
    if not ref_cropped_path.exists():
        _crop_central_region(ref_path, ref_cropped_path, crop_cache_folder)

    return ref_cropped_path


def _ocr_region(env, screenshot_path: Path, region: str = "whole", cache_folder: Optional[Path] = None) -> str:
    """Perform OCR on the specified region of a screenshot (with cache)."""
    if cache_folder:
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    img = Image.open(screenshot_path)
    width, height = img.size
    
    # Crop image according to region
    region_map = {
        "Top5%": (0, 0, width, int(height * 0.05)),
        "Top10%": (0, 0, width, int(height * 0.1)),
        "Top20%": (0, 0, width, int(height * 0.2)),
        "Top50%": (0, 0, width, int(height * 0.5)),
        "bottom5%": (0, int(height * 0.95), width, height),
        "bottom10%": (0, int(height * 0.9), width, height),
        "bottom20%": (0, int(height * 0.8), width, height),
        "bottom50%": (0, int(height * 0.5), width, height),
        "Middle50%": (0, int(height * 0.25), width, int(height * 0.75)),
        "Right30%": (int(width * 0.7), 0, width, height),
        "RemoveBottom30%RemoveLeft20%": (int(width * 0.2), int(height * 0.5), width, int(height * 0.7))
    }
    
    if region != "whole" and region in region_map:
        img = img.crop(region_map[region])
    
    img_array = np.array(img)
    reader = _get_ocr_reader()
    results = reader.readtext(img_array)
    text = "\n".join([result[1] for result in results])
    
    # Cache result
    if cache_folder:
        cache_folder.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    return text


def _ocr_region_custom(env, screenshot_path: Path, left_percent: int = 0, right_percent: int = 100,
                    top_percent: int = 0, bottom_percent: int = 100, cache_folder: Optional[Path] = None) -> str:
    """Perform OCR on a custom percentage region of a screenshot."""
    cache_key = f"{screenshot_path.stem}_L{left_percent}R{right_percent}T{top_percent}B{bottom_percent}.txt"
    cache_path = cache_folder / cache_key if cache_folder else None
    
    if cache_path and cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    img = Image.open(screenshot_path)
    width, height = img.size
    
    left = int(width * left_percent / 100)
    right = int(width * right_percent / 100)
    top = int(height * top_percent / 100)
    bottom = int(height * bottom_percent / 100)
    
    img = img.crop((left, top, right, bottom))
    
    img_array = np.array(img)
    reader = _get_ocr_reader()
    results = reader.readtext(img_array)
    text = "\n".join([result[1] for result in results])
    
    if cache_path:
        cache_folder.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    return text


def _calculate_visual_similarity(screenshot_path: Path, reference_cropped: Path, crop_cache_folder: Path) -> Tuple[float, Path]:
    """Calculate visual similarity between screenshot and reference image."""
    if reference_cropped is None:
        return 0.0, None

    screenshot_cropped_path = crop_cache_folder / f"cropped_{screenshot_path.stem}.png"

    if not screenshot_cropped_path.exists():
        screenshot_cropped_path = _crop_central_region(screenshot_path, screenshot_cropped_path, crop_cache_folder)

    try:
        from skimage.metrics import structural_similarity as ssim
        from skimage import io, transform

        img1 = io.imread(reference_cropped)
        img2 = io.imread(screenshot_cropped_path)

        if img1.shape != img2.shape:
            img2 = transform.resize(img2, img1.shape, anti_aliasing=True, preserve_range=True)
            img2 = img2.astype(img1.dtype)

        if len(img1.shape) == 3:
            img1_gray = np.mean(img1, axis=2).astype(np.uint8)
        else:
            img1_gray = img1

        if len(img2.shape) == 3:
            img2_gray = np.mean(img2, axis=2).astype(np.uint8)
        else:
            img2_gray = img2

        similarity = ssim(img1_gray, img2_gray, data_range=255)
        return max(0.0, min(1.0, similarity)), screenshot_cropped_path

    except ImportError:
        # Fallback: MSE-based similarity
        try:
            img1 = Image.open(reference_cropped).convert('L')
            img2 = Image.open(screenshot_cropped_path).convert('L')

            if img1.size != img2.size:
                img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

            arr1 = np.array(img1, dtype=np.float32)
            arr2 = np.array(img2, dtype=np.float32)

            mse = np.mean((arr1 - arr2) ** 2)
            return max(0.0, min(1.0, 1 - (mse / (255 ** 2)))), screenshot_cropped_path
        except Exception:
            return 0.0, screenshot_cropped_path
    except Exception:
        return 0.0, screenshot_cropped_path


def _extract_filename_from_text(text: str) -> Optional[str]:
    """Extract VESTA filename from OCR text."""
    if not text:
        return None
    
    # mp-digit_element.cif
    cif_pattern = r'mp[-_](\d+)[-_]([A-Za-z0-9]+)\.cif'
    match = re.search(cif_pattern, text, re.IGNORECASE)
    if match:
        return f"mp-{match.group(1)}_{match.group(2)}.cif"
    
    # .vesta
    vesta_pattern = r'([A-Za-z0-9_\-]+)\.vesta'
    match = re.search(vesta_pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)
    
    # Without extension
    simple_pattern = r'mp[-_](\d+)[-_]([A-Za-z0-9]+)'
    match = re.search(simple_pattern, text, re.IGNORECASE)
    if match:
        return f"mp-{match.group(1)}_{match.group(2)}"
    
    return None

# ============ Core Check Functions ============

def get_check_file_opened_vesta(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the file has been opened."""
    expected_filename = config.get('expected_filename') or ''
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return {'function': 'check_file_opened', 'expected_file': expected_filename,
                'score': 0, 'max_score': 1, 'details': {'error': 'trajectory dir not found'}}
    base_folder = Path(base_folder).resolve()

    result = {
        'function': 'check_file_opened',
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

    # Identify files in all screenshots
    screenshot_files = []
    for screenshot in screenshots:
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder)
        current_file = _extract_filename_from_text(title_text)
        screenshot_files.append(current_file)

    expected_base = expected_filename.replace('.cif', '').replace('.vesta', '')
    
    found_index = -1
    for i, detected_file in enumerate(screenshot_files):
        if detected_file:
            detected_base = detected_file.replace('.cif', '').replace('.vesta', '')
            
            if expected_base.lower() in detected_base.lower() or \
               detected_base.lower() in expected_base.lower():
                found_index = i
                result['details']['detected_file'] = detected_file
                break
    
    if found_index >= 0:
        result['score'] = 1
        result['details']['found_at_step'] = found_index
        result['details']['status'] = "Initially opened" if found_index == 0 else "Opened during process"
    
    return result


def get_check_standard_orientation(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if rotated to standard crystallographic orientation (text detection + visual similarity)."""
    similarity_threshold = config.get('similarity_threshold', 0.9)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    reference_image_path = None  # use vesta_images/ fallback below

    result = {
        'function': 'check_standard_orientation',
        'score': 0,
        'max_score': 1,
        'details': {
            'text_detected': False,
            'similarity_scores': [],
            'max_similarity': 0.0,
            'threshold': similarity_threshold,
            'detection_method': None
        }
    }

    screenshots = _load_screenshots(base_folder)
    if len(screenshots) < 1:
        result['details']['error'] = "Insufficient number of screenshots"
        return result

    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name

    # Step 1: Text detection
    target_text = "Standard orientation of crystal shape"
    for i, screenshot in enumerate(screenshots):
        full_text = _ocr_region(env, screenshot, "Top10%", cache_folder)
        if target_text.lower() in full_text.lower():
            result['score'] = 1
            result['details']['text_detected'] = True
            result['details']['text_detection_step'] = i
            result['details']['detection_method'] = 'text_detection'
            return result

    # Step 2: Visual similarity
    if not reference_image_path:
        default_ref = Path(__file__).parent / "vesta_images" / "orientation.png"
        reference_image_path = default_ref if default_ref.exists() else None
    
    if reference_image_path:
        crop_cache_folder = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
        crop_cache_folder.mkdir(parents=True, exist_ok=True)
        
        reference_cropped = _prepare_reference_image(
            Path(reference_image_path), "reference_cropped.png", crop_cache_folder
        )
        
        if reference_cropped:
            result['details']['detection_method'] = 'visual_similarity'
            
            for i, screenshot in enumerate(screenshots):
                similarity, cropped_path = _calculate_visual_similarity(screenshot, reference_cropped, crop_cache_folder)
                
                result['details']['similarity_scores'].append({
                    'step': i,
                    'similarity': round(similarity, 4),
                    'cropped_image': str(cropped_path) if cropped_path else None
                })
                
                if similarity > result['details']['max_similarity']:
                    result['details']['max_similarity'] = round(similarity, 4)
                    result['details']['max_similarity_step'] = i
            
            if result['details']['similarity_scores']:
                result['details']['initial_similarity'] = result['details']['similarity_scores'][0]['similarity']
                result['details']['final_similarity'] = result['details']['similarity_scores'][-1]['similarity']
            
            if result['details']['max_similarity'] >= similarity_threshold:
                result['score'] = 1
    
    return result


def get_check_rotation_90_up(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check upward rotation by 90 degrees."""
    similarity_threshold = config.get('similarity_threshold', 0.9)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    rotation_90_reference = None  # use vesta_images/ fallback below
    
    result = {
        'function': 'check_rotation_90_up',
        'score': 0,
        'max_score': 1,
        'details': {
            'text_detected': False,
            'similarity_scores': [],
            'max_similarity': 0.0,
            'detection_method': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Text detection
    keyword1 = "rotate around the y axis"
    keyword2 = "90"
    
    for i, screenshot in enumerate(screenshots):
        full_text = _ocr_region(env, screenshot, "Top10%", cache_folder).lower()
        if keyword1 in full_text and keyword2 in full_text:
            result['score'] = 1
            result['details']['text_detected'] = True
            result['details']['detection_method'] = 'text_detection'
            return result
    
    # Visual similarity
    if not rotation_90_reference:
        default_rot = Path(__file__).parent / "vesta_images" / "rotate.png"
        rotation_90_reference = default_rot if default_rot.exists() else None
    
    if rotation_90_reference:
        crop_cache_folder = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
        crop_cache_folder.mkdir(parents=True, exist_ok=True)
        
        rotation_90_cropped = _prepare_reference_image(
            Path(rotation_90_reference), "rotation_90_cropped.png", crop_cache_folder
        )
        
        if rotation_90_cropped:
            result['details']['detection_method'] = 'visual_similarity'
            
            for i, screenshot in enumerate(screenshots):
                similarity, _ = _calculate_visual_similarity(screenshot, rotation_90_cropped, crop_cache_folder)
                
                result['details']['similarity_scores'].append({
                    'step': i,
                    'similarity': round(similarity, 4)
                })
                
                if similarity > result['details']['max_similarity']:
                    result['details']['max_similarity'] = round(similarity, 4)
            
            if result['details']['max_similarity'] >= similarity_threshold:
                result['score'] = 1
    
    return result


def get_check_translation(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check translation operation."""
    direction = config.get('direction', 'right')
    units = config.get('units', 400)
    similarity_threshold = config.get('similarity_threshold', 0.9)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    translation_reference = None  # use vesta_images/ fallback below
    
    result = {
        'function': 'check_translation',
        'direction': direction,
        'units': units,
        'score': 0,
        'max_score': 1,
        'details': {
            'text_detected': False,
            'similarity_scores': [],
            'max_similarity': 0.0,
            'detection_method': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Text detection
    direction_map = {'right': 'rightward', 'left': 'leftward', 'up': 'upward', 'down': 'downward'}
    direction_text = direction_map.get(direction, direction)
    
    keyword1 = f"translate {direction_text}"
    keyword2 = str(units)
    
    for i, screenshot in enumerate(screenshots):
        full_text = _ocr_region(env, screenshot, "Top10%", cache_folder).lower()
        if keyword1 in full_text and keyword2 in full_text:
            result['score'] = 1
            result['details']['text_detected'] = True
            result['details']['detection_method'] = 'text_detection'
            return result
    
    # Visual similarity
    if not translation_reference:
        default_ref = Path(__file__).parent / "vesta_images" / "translate.png"
        translation_reference = default_ref if default_ref.exists() else None
    
    if translation_reference:
        crop_cache_folder = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
        crop_cache_folder.mkdir(parents=True, exist_ok=True)
        
        translation_cropped = _prepare_reference_image(
            Path(translation_reference), "translation_400_cropped.png", crop_cache_folder
        )
        
        if translation_cropped:
            result['details']['detection_method'] = 'visual_similarity'
            
            for i, screenshot in enumerate(screenshots):
                similarity, _ = _calculate_visual_similarity(screenshot, translation_cropped, crop_cache_folder)
                
                result['details']['similarity_scores'].append({
                    'step': i,
                    'similarity': round(similarity, 4)
                })
                
                if similarity > result['details']['max_similarity']:
                    result['details']['max_similarity'] = round(similarity, 4)
            
            if result['details']['max_similarity'] >= similarity_threshold:
                result['score'] = 1
    
    return result


def get_check_style_change(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check style modification (simplified: OCR detection only)."""
    target_style = config.get('target_style')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_style_change',
        'target_style': target_style,
        'score': 0,
        'max_score': 1,
        'details': {
            'style_detected': False,
            'detected_at_step': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Detect if the left panel or whole region has text of the target style
    for i, screenshot in enumerate(screenshots):
        # Check multiple regions
        for region in ["whole", "Top50%"]:
            text = _ocr_region(env, screenshot, region, cache_folder).lower()
            
            if target_style.lower() in text:
                result['score'] = 1
                result['details']['style_detected'] = True
                result['details']['detected_at_step'] = i
                return result
    
    return result


def get_check_atom_info_dialog(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check atom information dialog."""
    atom_type = config.get('atom_type')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_atom_info_dialog',
        'atom_type': atom_type,
        'score': 0,
        'max_score': 1,
        'details': {
            'dialog_detected': False,
            'detected_at_step': None,
            'matched_text': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Match pattern: Ga0, Ga1, N2, N3, etc.
    pattern = rf'\b{atom_type}\d+\b'
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom20%", cache_folder)
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            result['score'] = 1
            result['details']['dialog_detected'] = True
            result['details']['detected_at_step'] = i
            result['details']['matched_text'] = matches[0]
            result['details']['all_matches'] = matches
            break
    
    return result


def get_check_atom_deletion(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check atom deletion operation."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_atom_deletion',
        'score': 0,
        'max_score': 1,
        'details': {
            'deletion_detected': False,
            'delete_keywords': []
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    delete_keywords = ['delete', 'Del']
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom20%", cache_folder)
        text_lower = text.lower()
        
        for keyword in delete_keywords:
            if keyword.lower() in text_lower:
                result['details']['deletion_detected'] = True
                result['details']['delete_keywords'].append({
                    'step': i,
                    'keyword': keyword
                })
    
    if result['details']['deletion_detected']:
        result['score'] = 1
    
    return result


def get_check_bond_display(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check bond connection structure display."""
    atom_a = config.get('atom_a')
    atom_b = config.get('atom_b')
    possible_pairs = config.get('possible_pairs')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    def normalize_label(label: str) -> str:
        """Normalize atom label (handle OCR misrecognition)."""
        if not label:
            return ""
        label = re.sub(r'([A-Z][a-z]?)[Oo](\b|_|-|\s|$)', r'\g<1>0\g<2>', label)
        label = re.sub(r'([A-Z][a-z]?)[Iil](\b|_|-|\s|$)', r'\g<1>1\g<2>', label)
        return label
    
    result = {
        'function': 'check_bond_display',
        'score': 0,
        'max_score': 1,
        'details': {
            'bond_info_detected': False,
            'target_bond_found': False,
            'all_bonds_raw': [],
            'all_bonds_normalized': []
        }
    }
    
    # Build target bonds
    target_bonds = []
    if atom_a and atom_b:
        target_bonds.append((normalize_label(atom_a), normalize_label(atom_b)))
    if possible_pairs:
        for p in possible_pairs:
            if len(p) >= 2:
                target_bonds.append((normalize_label(p[0]), normalize_label(p[1])))
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Match hyphenated structure [atom]-[atom]
    bond_pattern = r'\b([A-Z][a-z]?\w*)\s*-\s*([A-Z][a-z]?\w*)\b'
    
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "bottom20%", cache_folder)
        bond_matches = re.findall(bond_pattern, text)
        
        if bond_matches:
            result['details']['bond_info_detected'] = True
            
            for raw_a, raw_b in bond_matches:
                norm_a = normalize_label(raw_a)
                norm_b = normalize_label(raw_b)
                
                raw_pair = f"{raw_a}-{raw_b}"
                norm_pair = f"{norm_a}-{norm_b}"
                
                result['details']['all_bonds_raw'].append(raw_pair)
                result['details']['all_bonds_normalized'].append(norm_pair)
                
                if target_bonds:
                    for t_a, t_b in target_bonds:
                        if (norm_a == t_a and norm_b == t_b) or (norm_a == t_b and norm_b == t_a):
                            result['details']['target_bond_found'] = True
                            result['details']['matched_target'] = f"{t_a}-{t_b}"
                            result['details']['bond_pattern'] = norm_pair
                            result['score'] = 1
                            return result
                else:
                    # No target specified, any bond found passes
                    result['details']['bond_pattern'] = norm_pair
                    result['score'] = 1
                    return result
    
    return result


def get_check_zoom(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check model zoom state (Zoom In 100%)."""
    similarity_threshold = config.get('similarity_threshold', 0.9)
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    zoom_100_reference = None  # use vesta_images/ fallback below
    
    result = {
        'function': 'check_zoom',
        'score': 0,
        'max_score': 1,
        'details': {
            'text_detected': False,
            'has_zoom_in_text': False,
            'step_value': None,
            'max_similarity': 0.0,
            'detection_method': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Step 1: Text detection (match both Zoom In and Step value)
    for i, screenshot in enumerate(screenshots):
        full_text = _ocr_region(env, screenshot, "Top10%", cache_folder).lower()
        
        has_zoom_in = "zoom in" in full_text
        step_match = re.search(r'step\s*\(?\s*%\s*\)?\s*[:：]?\s*(\d+)', full_text)
        current_step = int(step_match.group(1)) if step_match else None
        
        if has_zoom_in:
            result['details']['has_zoom_in_text'] = True
            
        if current_step is not None:
            result['details']['step_value'] = current_step
        
        # Must see both "zoom in" and Step = 100
        if has_zoom_in and current_step == 100:
            result['score'] = 1
            result['details']['text_detected'] = True
            result['details']['detection_method'] = 'text_ocr'
            return result
    
    # Step 2: Visual similarity comparison (fallback)
    if not zoom_100_reference:
        default_ref = Path(__file__).parent / "vesta_images" / "zoom.png"
        zoom_100_reference = default_ref if default_ref.exists() else None
    
    if zoom_100_reference:
        crop_cache_folder = base_folder.parent / "evaluate" / "cropped_images" / base_folder.name
        crop_cache_folder.mkdir(parents=True, exist_ok=True)
        
        zoom_100_cropped = _prepare_reference_image(
            Path(zoom_100_reference), "zoom_100_cropped.png", crop_cache_folder
        )
        
        if zoom_100_cropped:
            result['details']['detection_method'] = 'visual_similarity'
            
            for i, screenshot in enumerate(screenshots):
                similarity, _ = _calculate_visual_similarity(screenshot, zoom_100_cropped, crop_cache_folder)
                
                if similarity > result['details']['max_similarity']:
                    result['details']['max_similarity'] = round(similarity, 4)
                    result['details']['max_similarity_step'] = i
            
            if result['details']['max_similarity'] >= similarity_threshold:
                result['score'] = 1
    
    return result


def get_check_axes_toggle(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if axis display state has been toggled (simplified: text change detection only)."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_axes_toggle',
        'score': 0,
        'max_score': 1,
        'details': {
            'initial_state': None,
            'final_state': None,
            'state_changed': False
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    
    if len(screenshots) < 2:
        result['details']['error'] = "Insufficient number of screenshots"
        return result
    
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Check axis labels in the first and last frames
    def has_axes(screenshot):
        text = _ocr_region(env, screenshot, "bottom20%", cache_folder).lower()
        # Detect a, b, c axis labels
        return bool(re.search(r'\ba\b', text) or re.search(r'\bb\b', text) or re.search(r'\bc\b', text))
    
    initial_on = has_axes(screenshots[0])
    final_on = has_axes(screenshots[-1])
    
    result['details']['initial_state'] = "ON" if initial_on else "OFF"
    result['details']['final_state'] = "ON" if final_on else "OFF"
    
    if initial_on != final_on:
        result['score'] = 1
        result['details']['state_changed'] = True
    
    return result


def get_check_dialog_opened_vesta(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect dialog title and field values (pure OCR version)."""
    title_keyword = config.get('title_keyword', 'Properties')
    field_checks = config.get('field_checks')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_dialog_opened',
        'score': 0,
        'max_score': 1,
        'details': {
            'dialog_detected': False,
            'target_keyword': title_keyword,
            'field_checks': field_checks or {},
            'field_results': {},
            'detected_at_step': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # OCR variants of title keywords
    search_keywords = [title_keyword.lower()]
    if title_keyword.lower() == "properties":
        search_keywords.extend(["propertie", "properlie", "propert"])
    
    for i, screenshot in enumerate(screenshots):
        # Step 1: Detect dialog title in Top5%
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder).lower()
        
        found_title = next((k for k in search_keywords if k in title_text), None)
        
        if not found_title:
            continue
        
        result['details']['dialog_detected'] = True
        result['details']['detected_at_step'] = i
        
        # If no field check required, return success directly
        if not field_checks:
            result['score'] = 1
            return result
        
        # Step 2: Detect field content in left 40%, top 60% region
        field_text = _ocr_region_custom(
            env, screenshot, 
            left_percent=0, right_percent=40, 
            top_percent=5, bottom_percent=65, 
            cache_folder=cache_folder
        )
        field_text_lower = field_text.lower()
        
        all_fields_match = True
        for field_name, expected_value in field_checks.items():
            # Convert expected value to string
            if isinstance(expected_value, float):
                value_str = str(expected_value)
                value_patterns = [
                    value_str,
                    value_str.replace('.', ''),
                    value_str.rstrip('0').rstrip('.') if '.' in value_str else value_str
                ]
            else:
                value_str = str(expected_value)
                value_patterns = [value_str]
            
            # Field name variants
            field_patterns = [field_name.lower()]
            if field_name.lower() == "radius":
                field_patterns.extend(["radlus", "raidus"])
            elif field_name.lower() == "stacks":
                field_patterns.extend(["stack", "slacks"])
            
            # Try matching
            field_matched = False
            matched_pattern = None
            
            for field_pat in field_patterns:
                for value_pat in value_patterns:
                    patterns = [
                        rf'{field_pat}\s*[:：]\s*{re.escape(value_pat)}\b',
                        rf'{field_pat}\s+{re.escape(value_pat)}\b',
                        rf'{field_pat}\s*[:：]?\s*{re.escape(value_pat)}\b'
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
            
            result['details']['field_results'][field_name] = {
                'expected': expected_value,
                'matched': field_matched,
                'matched_pattern': matched_pattern
            }
            
            if not field_matched:
                all_fields_match = False
        
        # Determine result based on field matching
        if all_fields_match:
            result['score'] = 1
            return result
        else:
            matched_count = sum(1 for v in result['details']['field_results'].values() if v['matched'])
            total_count = len(field_checks)
            result['score'] = matched_count / total_count if total_count > 0 else 0
    
    return result


def get_check_polyhedral_style(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if Polyhedral style is set to the specified style number (simplified: OCR detection)."""
    style_number = config.get('style_number')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_polyhedral_style',
        'style_number': style_number,
        'score': 0,
        'max_score': 1,
        'details': {
            'polyhedral_detected': False,
            'selected_style': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Simplified: detect Properties dialog and Polyhedral keyword
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder).lower()
        
        if "properties" in text and "polyhedral" in text:
            result['details']['polyhedral_detected'] = True
            result['score'] = 1  # Simplified: detected means passed
            return result
    
    return result


def get_check_orientation_vector(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check Upward vector in Orientation dialog (simplified)."""
    expected_values = config.get('expected_values')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_orientation_vector',
        'expected_values': expected_values,
        'score': 0,
        'max_score': 1,
        'details': {
            'detected_values': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Simplified: detect Orientation dialog and expected value
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        if "orientation" in text.lower():
            # Check if expected value is included
            all_found = all(str(val) in text for val in expected_values)
            if all_found:
                result['details']['detected_values'] = expected_values
                result['score'] = 1
                return result
    
    return result


def get_check_lattice_plane(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a plane with the specified hkl has been added in Lattice Planes dialog."""
    expected_hkl = config.get('expected_hkl')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_lattice_plane',
        'expected_hkl': expected_hkl,
        'score': 0,
        'max_score': 1,
        'details': {
            'detected_planes': []
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Simplified: detect Lattice Planes dialog and expected value
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder)
        
        if "lattice" in text.lower() and "plane" in text.lower():
            # Check if expected value is included
            all_found = all(str(val) in text for val in expected_hkl)
            if all_found:
                result['details']['detected_planes'].append(expected_hkl)
                result['score'] = 1
                return result
    
    return result


def get_check_boundary_settings(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check Boundary settings (fractional coordinate ranges)."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_boundary_settings',
        'expected_settings': {k: v for k, v in config.items() if k != 'base_folder'},
        'score': 0,
        'max_score': 1,
        'details': {
            'boundary_detected': False,
            'settings_matched': {},
            'detected_values': {}
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    # Check Boundary dialog and settings
    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(env, screenshot, "whole", cache_folder).lower()
        
        if "boundary" in text or "fractional" in text:
            result['details']['boundary_detected'] = True
            
            # Simplified: check if expected value is included
            all_matched = True
            for key, expected_value in config.items():
                if key in ('base_folder', 'type'):
                    continue
                
                # Check if value is included
                if str(expected_value) in text:
                    result['details']['settings_matched'][key] = True
                    result['details']['detected_values'][key] = expected_value
                else:
                    all_matched = False
            
            if all_matched and result['details']['boundary_detected']:
                result['score'] = 1
                return result
    
    return result


def get_check_bonds_cleared(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the Bonds table has been cleared."""
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_bonds_cleared',
        'score': 0,
        'max_score': 1,
        'details': {
            'initial_bonds_found': False,
            'bonds_cleared': False
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    characteristic_value = '3.39412'
    initial_step_with_bonds = None
    initial_count = 0
    
    for i, screenshot in enumerate(screenshots):
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder)
        if 'bonds' not in title_text.lower():
            continue
        
        table_text = _ocr_region(env, screenshot, "Top50%", cache_folder)
        
        # Count occurrences of characteristic values
        count = table_text.count(characteristic_value)
        
        # Fault-tolerant matching
        if count == 0:
            pattern = r'3\.3941[0-9]'
            matches = re.findall(pattern, table_text)
            count = len(matches)
        
        if count >= 2:
            # Has bonds state
            if initial_step_with_bonds is None:
                initial_step_with_bonds = i
                initial_count = count
                result['details']['initial_bonds_found'] = True
                result['details']['initial_step'] = i
                result['details']['initial_value_count'] = count
        
        elif initial_step_with_bonds is not None and count == 1:
            # Cleared state (input fields only)
            result['details']['bonds_cleared'] = True
            result['details']['cleared_step'] = i
            result['details']['final_value_count'] = count
            result['score'] = 1
            return result
    
    return result


def get_check_atom_coordinates_in_edit_data(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check atom coordinates in Edit Data."""
    atom_label = config.get('atom_label')
    expected_coords = config.get('expected_coords')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_atom_coordinates_in_edit_data',
        'atom_label': atom_label,
        'expected_coords': expected_coords,
        'score': 0,
        'max_score': 1,
        'details': {
            'edit_data_detected': False,
            'coordinates_detected': False,
            'detected_coords': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder)
        if 'edit data' not in title_text.lower():
            continue
        
        result['details']['edit_data_detected'] = True
        
        table_text = _ocr_region(env, screenshot, "Top50%", cache_folder)
        table_text_cleaned = table_text.replace('o', '0').replace('O', '0')
        
        lines_cleaned = table_text_cleaned.split('\n')
        
        # Simplified: find atom label and subsequent coordinate values
        for idx, line in enumerate(lines_cleaned):
            line_stripped = line.strip()
            
            if line_stripped == atom_label:
                # Collect values going forward
                coords_found = []
                for offset in range(1, min(15, len(lines_cleaned) - idx)):
                    next_line = lines_cleaned[idx + offset].strip()
                    
                    coord_match = re.match(r'^([01]\.\d{6})$', next_line)
                    if coord_match:
                        coords_found.append(coord_match.group(1))
                        if len(coords_found) >= 3:
                            break
                
                if len(coords_found) >= 3:
                    try:
                        detected_coords = [float(coords_found[0]), float(coords_found[1]), float(coords_found[2])]
                        result['details']['detected_coords'] = detected_coords
                        result['details']['coordinates_detected'] = True
                        
                        # Compare coordinates
                        coords_match = all(
                            abs(detected - expected) < 0.000001
                            for detected, expected in zip(detected_coords, expected_coords)
                        )
                        
                        if coords_match:
                            result['score'] = 1
                            return result
                    except (ValueError, IndexError):
                        continue
    
    return result


def get_check_multiple_lattice_planes(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check the number of lattice planes added in the Lattice Planes dialog."""
    expected_count = config.get('expected_count')
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_multiple_lattice_planes',
        'expected_count': expected_count,
        'score': 0,
        'max_score': 1,
        'details': {
            'lattice_planes_detected': False,
            'detected_count': 0,
            'row_numbers': []
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder)
        if 'lattice' not in title_text.lower() and 'plane' not in title_text.lower():
            continue
        
        result['details']['lattice_planes_detected'] = True
        
        table_text = _ocr_region(env, screenshot, "Top50%", cache_folder)
        table_text_cleaned = table_text.replace('o', '0').replace('O', '0')
        
        lines = table_text_cleaned.split('\n')
        row_numbers = []
        
        found_table_header = False
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            if 'no.' in line_lower or ('h' in line_lower and 'k' in line_lower and 'l' in line_lower):
                found_table_header = True
                continue
            
            if found_table_header:
                match = re.match(r'^(\d+)\s+', line_stripped)
                if match:
                    row_num = int(match.group(1))
                    if row_num >= 1 and row_num <= 100:
                        if row_num not in row_numbers:
                            row_numbers.append(row_num)
        
        if len(row_numbers) > 0:
            result['details']['detected_count'] = len(row_numbers)
            result['details']['row_numbers'] = sorted(row_numbers)
            result['details']['detected_at_step'] = i
            
            if len(row_numbers) == expected_count:
                result['score'] = 1
                return result
    
    return result

def get_check_properties_field(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check the value of a field in the Properties dialog."""
    field_name = config.get('field_name', '')
    expected_value = config.get('expected_value')
    tolerance = config.get('tolerance', 0.05)
    
    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    
    result = {
        'function': 'check_properties_field',
        'field_name': field_name,
        'expected_value': expected_value,
        'score': 0,
        'max_score': 1,
        'details': {
            'detected_value': None,
            'matched': False,
            'detected_at_step': None
        }
    }
    
    screenshots = _load_screenshots(base_folder)
    cache_folder = base_folder.parent / "evaluate" / "ocr_results" / base_folder.name
    
    for i, screenshot in enumerate(screenshots):
        # Check if it is the Properties dialog
        title_text = _ocr_region(env, screenshot, "Top5%", cache_folder)
        if 'properties' not in title_text.lower():
            continue
        
        # OCR recognize dialog content
        dialog_text = _ocr_region(env, screenshot, "TopLeft45%", cache_folder)
        dialog_text_cleaned = dialog_text.replace('o', '0').replace('O', '0').replace('l', '1').replace('I', '1')
        
        # Find pattern "FieldName ... number"
        pattern = rf'{field_name}\s*[:\s]\s*(-?\d+(?:\.\d+)?)'
        match = re.search(pattern, dialog_text_cleaned, re.IGNORECASE)
        
        if match:
            detected_value = float(match.group(1))
            result['details']['detected_value'] = detected_value
            result['details']['detected_at_step'] = i
            
            if abs(detected_value - expected_value) <= tolerance:
                result['score'] = 1
                result['details']['matched'] = True
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
#         'check_file_opened': check_file_opened,
#         'check_standard_orientation': check_standard_orientation,
#         'check_rotation_90_up': check_rotation_90_up,
#         'check_translation': check_translation,
#         'check_style_change': check_style_change,
#         'check_atom_info_dialog': check_atom_info_dialog,
#         'check_atom_deletion': check_atom_deletion,
#         'check_bond_display': check_bond_display,
#         'check_zoom': check_zoom,
#         'check_axes_toggle': check_axes_toggle,
#         'check_dialog_opened': check_dialog_opened,
#         'check_polyhedral_style': check_polyhedral_style,
#         'check_orientation_vector': check_orientation_vector,
#         'check_lattice_plane': check_lattice_plane,
#         'check_boundary_settings': check_boundary_settings,
#         'check_bonds_cleared': check_bonds_cleared,
#         'check_atom_coordinates_in_edit_data': check_atom_coordinates_in_edit_data,
#         'check_multiple_lattice_planes': check_multiple_lattice_planes,
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