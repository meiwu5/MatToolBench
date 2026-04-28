"""
Material Studio Evaluation System - v2.1 (aligned with v1.0 logic)
Refactored class methods into standalone getter functions accepting env parameter for modular imports

Reference image lookup priority:
  1. env.reference_images dict (key → absolute path)
  2. config['reference_path'] directly specified path
  3. ms_images/<reference_key> auto-lookup in same directory as this file
"""

import os
import re
import json
import glob
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import easyocr
from PIL import Image
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim


# ms_images directory: same level as this file
_MS_IMAGES_DIR = Path(__file__).parent / "ms_images"


# ============ Path Resolution ============

def get_trajectory_dir(env, config: Dict[str, Any]) -> Optional[str]:
    """
    Extract Task ID from env.cache_dir and recursively search for folders containing screenshots under the MS Results directory.
    Falls back to config['trajectory_dir'] if not found.
    """
    cache_path = getattr(env, "cache_dir", "")
    if not cache_path:
        cache_path = config.get("trajectory_dir", "")

    if not cache_path:
        print("[Error] Unable to get path info, please check if env.cache_dir is assigned")
        return None

    task_id = os.path.normpath(cache_path).split(os.sep)[-1]

    if not task_id or task_id == ".":
        print(f"[Error] Unable to parse Task ID, original path: {cache_path}")
        return None

    # results_base: dynamically obtained from env to avoid hardcoding model name/trial_id/action_space etc.
    # Prefer env.result_dir (injected by run.py), fall back to standard container path
    results_base = getattr(env, "result_dir", None) or "/client/results"

    print(f"\n" + "-" * 30)
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
            if glob.glob(os.path.join(candidate, "screenshot-step_*.png")):
                print(f"✅ Successfully matched real path: {candidate}")
                print("-" * 30 + "\n")
                return candidate

    print(f"❌ Search failed: no folder containing {task_id} with screenshots found under {results_base}")
    return None


# ============ Global Helper Functions ============

def _extract_step_number(filename: str) -> int:
    match = re.search(r'step_(\d+)', filename)
    return int(match.group(1)) if match else 0


def _get_ocr_reader() -> easyocr.Reader:
    if not hasattr(_get_ocr_reader, "reader"):
        # gpu=False: Docker has no GPU by default, easyocr will automatically fall back to CPU
        _get_ocr_reader.reader = easyocr.Reader(['en'], gpu=False)
    return _get_ocr_reader.reader


def _load_screenshots(base_folder: Path) -> List[Path]:
    return sorted(
        base_folder.glob("screenshot-step_*.png"),
        key=lambda x: _extract_step_number(x.name)
    )


def _get_cache_folders(base_folder: Path) -> Tuple[Path, Path]:
    task_name = base_folder.name
    evaluate_folder = base_folder.parent / "evaluate"
    ocr_cache = evaluate_folder / "ocr_results" / task_name
    crop_cache = evaluate_folder / "cropped_images" / task_name
    ocr_cache.mkdir(parents=True, exist_ok=True)
    crop_cache.mkdir(parents=True, exist_ok=True)
    return ocr_cache, crop_cache


def _ocr_region(screenshot_path: Path, region: str = "whole",
                cache_folder: Optional[Path] = None) -> str:
    """Perform OCR on the specified region of a screenshot (with disk cache)."""
    if cache_folder:
        cache_key = f"{screenshot_path.stem}_{region}.txt"
        cache_path = cache_folder / cache_key
        if cache_path.exists():
            return cache_path.read_text(encoding='utf-8')

    img = Image.open(screenshot_path)
    width, height = img.size

    region_map = {
        "Top5%":  (0, 0, width, int(height * 0.05)),
        "Top10%": (0, 0, width, int(height * 0.10)),
        "Top40%": (0, 0, width, int(height * 0.40)),
        "Top50%": (0, 0, width, int(height * 0.50)),
        "bottom5%":  (0, int(height * 0.95), width, height),
        "bottom20%": (0, int(height * 0.80), width, height),
        "Left30%": (0, 0, int(width * 0.30), height),
        "Right30%": (int(width * 0.70), 0, width, height),
        "CenterRegion": (int(width * 0.2), int(height * 0.2),
                    int(width * 0.8), int(height * 0.8)),
    }

    if region in region_map:
        img = img.crop(region_map[region])

    reader = _get_ocr_reader()
    results = reader.readtext(np.array(img))
    text = "\n".join([r[1] for r in results])

    if cache_folder:
        cache_folder.mkdir(parents=True, exist_ok=True)
        (cache_folder / f"{screenshot_path.stem}_{region}.txt").write_text(
            text, encoding='utf-8')

    return text


def _generate_field_patterns(field_name: Optional[str],
                              expected_value: Any) -> List[str]:
    """Generate regex pattern list for field values (aligned with v1.0)."""
    value_str = str(expected_value)

    if field_name is None:
        return [rf'\b{re.escape(value_str)}\b']

    # ── Aligned with v1.0: handle int and float separately ──
    if isinstance(expected_value, (int, float)):
        if isinstance(expected_value, float):
            value_patterns = list(filter(None, [
                value_str,
                value_str.rstrip('0').rstrip('.'),
                f"{expected_value:.3f}",
                f"{int(expected_value)}" if expected_value == int(expected_value) else None
            ]))
        else:
            # int uses original value only
            value_patterns = [value_str]
    else:
        value_patterns = [value_str]

    field_variants = [field_name]
    if 'α' in field_name or 'alpha' in field_name.lower():
        field_variants += ['alpha', 'α', 'Alpha']
    if 'β' in field_name or 'beta' in field_name.lower():
        field_variants += ['beta', 'β', 'Beta']

    patterns = []
    for fp in field_variants:
        for vp in value_patterns:
            patterns += [
                rf'{re.escape(fp)}\s*[:：=]\s*{re.escape(vp)}\b',
                rf'{re.escape(fp)}\s+{re.escape(vp)}\b',
                rf'{re.escape(fp)}\s*[:：=]?\s*{re.escape(vp)}\b',
            ]
    return patterns


def _resolve_reference_path(env, config: Dict[str, Any],
                             reference_key: str) -> Optional[Path]:
    """
    Three-level reference image path lookup (aligned with v1.0 dict-priority, added ms_images auto fallback):
      1. env.reference_images dict key → absolute path
      2. config['reference_path'] directly specified
      3. <this file directory>/ms_images/<reference_key>
    """
    # 1. env dict
    reference_images: Dict[str, str] = getattr(env, 'reference_images', {})
    path_str = reference_images.get(reference_key)
    if path_str:
        return Path(path_str)

    # 2. config directly specified
    path_str = config.get('reference_path')
    if path_str:
        return Path(path_str)

    # 3. ms_images directory auto-lookup (supports with or without extension)
    auto_path = _MS_IMAGES_DIR / reference_key
    if auto_path.exists():
        return auto_path

    # Try common image extensions
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        auto_path_ext = _MS_IMAGES_DIR / (reference_key + ext)
        if auto_path_ext.exists():
            return auto_path_ext

    print(f"[Warning] '{reference_key}' and its common extension variants not found under {_MS_IMAGES_DIR}")
    return None


def _calculate_visual_similarity(
    screenshot_path: Path,
    reference_path: Path,
    step: int,
    crop_cache_folder: Path,
    crop_region: Optional[Tuple[float, float, float, float]] = None
) -> Tuple[float, Optional[Path]]:
    """
    Calculate SSIM similarity between screenshot and reference image (aligned with v1.0: both are cropped by the same ratio).
    crop_region: (left%, top%, right%, bottom%) proportional coordinates, None uses the full image.
    """
    cropped_path = None
    try:
        img = cv2.imread(str(screenshot_path))
        ref = cv2.imread(str(reference_path))

        if img is None or ref is None:
            raise ValueError("Image loading failed")

        print(f"Original size → screenshot: {img.shape[:2]}, reference: {ref.shape[:2]}")

        img_cropped = img
        ref_cropped = ref

        if crop_region:
            # ── Aligned with v1.0: both screenshot and reference are cropped by the same ratio ──
            h_img, w_img = img.shape[:2]
            l, t, r, b = [int(x * d) for x, d in zip(crop_region, [w_img, h_img, w_img, h_img])]
            img_cropped = img[t:b, l:r]

            h_ref, w_ref = ref.shape[:2]
            l_r, t_r, r_r, b_r = [int(x * d) for x, d in zip(crop_region, [w_ref, h_ref, w_ref, h_ref])]
            ref_cropped = ref[t_r:b_r, l_r:r_r]

        # Size alignment
        target_h, target_w = img_cropped.shape[:2]
        if ref_cropped.shape[:2] != (target_h, target_w):
            ref_cropped = cv2.resize(ref_cropped, (target_w, target_h),
                                     interpolation=cv2.INTER_AREA)
            print(f"Reference crop size after resize: {ref_cropped.shape[:2]}")

        gray_img = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(ref_cropped, cv2.COLOR_BGR2GRAY)

        score = ssim(gray_img, gray_ref,
                     data_range=gray_ref.max() - gray_ref.min())

        # Save screenshot crop result (reference crop is used only for calculation, not saved)
        crop_cache_folder.mkdir(parents=True, exist_ok=True)
        save_name = f"cropped_{reference_path.stem}_step_{step:02d}.png"
        save_path = crop_cache_folder / save_name
        if cv2.imwrite(str(save_path), img_cropped):
            cropped_path = save_path
            print(f"Cropped image saved successfully: {save_path}")
        else:
            print(f"Save failed: {save_path}")

        return float(score), cropped_path

    except Exception as e:
        print(f"[Similarity calculation error] step={step}: {e}")
        return 0.0, None


# ============ Standalone Getter Check Functions ============

def get_check_file_in_title(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the title bar contains the specified filename."""
    expected_filename = config.get('expected_filename', '')
    region = config.get('region', 'Top5%')

    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    ocr_cache, _ = _get_cache_folders(base_folder)
    screenshots = _load_screenshots(base_folder)

    result = {
        'function': 'check_file_in_title',
        'expected_filename': expected_filename,
        'region': region,
        'score': 0,
        'max_score': 1,
        'details': {'found_at_step': None, 'status': 'not_found'}
    }

    expected_base = expected_filename.replace('.stp', '').replace('.xsd', '').lower()

    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(screenshot, region, ocr_cache).lower()
        if expected_base in text:
            result['score'] = 1
            result['details'].update({
                'found_at_step': i,
                'status': 'found',
                'detected_text': text[:100]
            })
            print(f"✓ [step {i:02d}] Detected filename: {expected_filename}")
            return result

    print(f"✗ Filename not detected: {expected_filename}")
    return result


def get_check_dialog_title_ms(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a dialog with the specified title appeared (supports forbidden keywords)."""
    expected_title = config.get('expected_title', '')
    region = config.get('region', 'whole')
    forbidden_keywords = config.get('forbidden_keywords') or []

    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    ocr_cache, _ = _get_cache_folders(base_folder)
    screenshots = _load_screenshots(base_folder)

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

    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(screenshot, region, ocr_cache)
        text_lower = text.lower()

        if expected_lower not in text_lower:
            continue

        forbidden_hit = next(
            (fb for fb in forbidden_keywords if fb.lower() in text_lower), None)

        if forbidden_hit:
            result['details']['forbidden_found'] = True
            result['details']['forbidden_keyword'] = forbidden_hit
            print(f"✗ [step {i:02d}] Dialog '{expected_title}' contains forbidden word '{forbidden_hit}'")
            continue  # Aligned with v1.0: continue to next frame

        result['score'] = 1
        result['details'].update({
            'found_at_step': i,
            'detected_text': text[:200]
        })
        print(f"✓ [step {i:02d}] Detected dialog: {expected_title}")
        return result

    print(f"✗ Dialog not detected: {expected_title}")
    return result


def get_check_text_keyword(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check that the specified region contains keyword and none of the forbidden_keywords."""
    keyword = config.get('keyword', '')
    forbidden_keywords = config.get('forbidden_keywords') or []
    region = config.get('region', 'whole')
    case_sensitive = config.get('case_sensitive', False)

    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    ocr_cache, _ = _get_cache_folders(base_folder)
    screenshots = _load_screenshots(base_folder)

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

    def _norm(s): return s if case_sensitive else s.lower()
    kw_check = _norm(keyword)

    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(screenshot, region, ocr_cache)
        text_check = _norm(text)

        found_kw = kw_check in text_check
        forbidden_hit = next(
            (fb for fb in forbidden_keywords if _norm(fb) in text_check), None)

        if found_kw:
            result['details']['found_keyword'] = True
            result['details']['found_keyword_step'] = i

        if forbidden_hit:
            result['details']['forbidden_found'] = True
            result['details']['forbidden_keyword'] = forbidden_hit
            result['details']['forbidden_step'] = i

        if found_kw and not forbidden_hit:
            result['score'] = 1
            print(f"✓ [step {i:02d}] Detected keyword '{keyword}' with no forbidden words")
            return result

    if result['details']['found_keyword']:
        print(f"✗ Detected '{keyword}' but forbidden word '{result['details']['forbidden_keyword']}' appeared")
    else:
        print(f"✗ Keyword not detected: {keyword}")

    return result


def get_check_field_value(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check field value in a dialog (supports numeric tolerance and OCR alternate values, aligned with v1.0)."""
    dialog_title = config.get('dialog_title', '')
    field_name = config.get('field_name')
    expected_value = config.get('expected_value')
    alternative_values = config.get('alternative_values') or []
    tolerance = config.get('tolerance', 0.01)  # Aligned with v1.0: keep tolerance parameter

    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    ocr_cache, _ = _get_cache_folders(base_folder)
    screenshots = _load_screenshots(base_folder)

    all_expected = [expected_value] + list(alternative_values)

    result = {
        'function': 'check_field_value',
        'dialog_title': dialog_title,
        'field_name': field_name,
        'expected_value': expected_value,
        'alternative_values': alternative_values,
        'tolerance': tolerance,
        'score': 0,
        'max_score': 1,
        'details': {'found': False, 'detected_value': None, 'step': None}
    }

    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(screenshot, 'whole', ocr_cache)
        if dialog_title.lower() not in text.lower():
            continue

        for cur_expected in all_expected:
            for pattern in _generate_field_patterns(field_name, cur_expected):
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    detected = match.group(1) if match.lastindex else cur_expected
                    result['score'] = 1
                    result['details'].update({
                        'found': True,
                        'detected_value': detected,
                        'matched_expected': cur_expected,
                        'step': i
                    })
                    tag = "" if cur_expected == expected_value else f"(OCR variant {cur_expected})"
                    print(f"✓ [step {i:02d}] {field_name} = {detected} {tag}")
                    return result

    print(f"✗ Field value not detected: {field_name} = {expected_value}")
    return result


def get_check_visual_similarity(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check SSIM visual similarity between screenshot and reference image.

    Reference image path lookup priority:
      1. env.reference_images[reference_key]
      2. config['reference_path']
      3. <this file directory>/ms_images/<reference_key>
    """
    reference_key = config.get('reference_key', '')
    similarity_threshold = config.get('similarity_threshold', 0.85)
    crop_region = config.get('crop_region')

    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    _, crop_cache = _get_cache_folders(base_folder)
    screenshots = _load_screenshots(base_folder)

    result = {
        'function': 'check_visual_similarity',
        'reference_key': reference_key,
        'score': 0,
        'max_score': 1,
        'details': {
            'max_similarity': 0.0,
            'max_similarity_step': None,
            'threshold': similarity_threshold,
            'similarity_scores': [],
            'all_similarities': [],
            'cropped_images_folder': str(crop_cache),
            'detection_method': 'visual_similarity'
        }
    }

    reference_path = _resolve_reference_path(env, config, reference_key)

    if reference_path is None:
        result['details']['error'] = f"Reference image '{reference_key}' not found (not in env.reference_images / config['reference_path'] / ms_images/)"
        print(f"✗ Reference image not found: {reference_key}")
        return result

    if not reference_path.exists():
        result['details']['error'] = f"Reference image does not exist: {reference_path}"
        print(f"✗ Reference image does not exist: {reference_path}")
        return result

    print(f"\nStarting frame-by-frame similarity calculation (reference: {reference_path}):")

    max_sim, max_step = 0.0, None

    for i, screenshot in enumerate(screenshots):
        sim, cropped_path = _calculate_visual_similarity(
            screenshot, reference_path, i, crop_cache, crop_region)

        entry = {
            'step': i,
            'similarity': round(sim, 4),
            'cropped_image': str(cropped_path) if cropped_path else None
        }
        result['details']['similarity_scores'].append(entry)
        result['details']['all_similarities'].append({'step': i, 'similarity': round(sim, 4)})
        print(f"  [step {i:02d}] Similarity: {sim:.4f} | Cropped: {cropped_path.name if cropped_path else 'N/A'}")

        if sim > max_sim:
            max_sim, max_step = sim, i

    result['details']['max_similarity'] = round(max_sim, 4)
    result['details']['max_similarity_step'] = max_step

    if max_sim >= similarity_threshold:
        result['score'] = 1
        print(f"✓ Visual similarity meets threshold: {max_sim:.4f} >= {similarity_threshold}")
    else:
        print(f"✗ Visual similarity insufficient: {max_sim:.4f} < {similarity_threshold}")

    print(f"\n✓ Cropped images saved to: {crop_cache}")
    print(f"  - Reference image: {reference_path.name}")
    print(f"  - Screenshot crop example: cropped_{reference_path.stem}_step_*.png")

    return result


def get_check_multiple_fields(env, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if multiple field values in a dialog all match in the same frame."""
    dialog_title = config.get('dialog_title', '')
    field_checks: Dict[str, Any] = config.get('field_checks', {})

    base_folder = get_trajectory_dir(env, config)
    if base_folder is None:
        return None
    base_folder = Path(base_folder).resolve()
    ocr_cache, _ = _get_cache_folders(base_folder)
    screenshots = _load_screenshots(base_folder)

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

    for i, screenshot in enumerate(screenshots):
        text = _ocr_region(screenshot, 'whole', ocr_cache)
        if dialog_title.lower() not in text.lower():
            continue

        field_results = {}
        for field_name, expected_value in field_checks.items():
            field_results[field_name] = any(
                re.search(p, text, re.IGNORECASE)
                for p in _generate_field_patterns(field_name, expected_value)
            )

        result['details']['field_results'] = field_results

        if all(field_results.values()):
            result['score'] = 1
            result['details']['all_matched'] = True
            result['details']['step'] = i
            print(f"✓ [step {i:02d}] All fields matched")
            return result

    matched_count = sum(1 for v in result['details']['field_results'].values() if v)
    total_count = len(field_checks)

    if matched_count > 0:
        result['score'] = matched_count / total_count
        print(f"⚠ Partial field match: {matched_count}/{total_count}")
    else:
        print(f"✗ No matching fields detected")

    return result