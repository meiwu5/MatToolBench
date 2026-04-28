"""
VESTA Evaluation System - v1.2 Fixed
For evaluating task completion of VESTA crystal structure visualization software
Fixes:
1. check_standard_orientation uses visual similarity comparison + real-time print
2. check_rotation_90_up uses visual similarity comparison + real-time print
3. check_translation uses visual similarity comparison + real-time print
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

class VESTAEvaluator:
    """VESTA Crystal Structure Visualization Task Evaluator"""
    
    def __init__(self, base_folder: str, reference_image_path: str = None, rotation_90_reference: str = None, translation_reference: str = None, zoom_100_reference: str=None):
        self.base_folder = Path(base_folder).resolve()
        
        if not self.base_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {self.base_folder}")
        
        self.task_folder_name = self.base_folder.name
        self.screenshots = []
        self.ally_trees = []
        self.ocr_reader = easyocr.Reader(['en'], gpu=True)
        self.current_file = None
        
        # Set reference image path for standard orientation
        if reference_image_path:
            self.reference_image_path = Path(reference_image_path)
        else:
            default_ref = Path(__file__).parent / "orientation.png"
            self.reference_image_path = default_ref if default_ref.exists() else None
        
        # Set reference image path for 90-degree rotation
        if rotation_90_reference:
            self.rotation_90_reference_path = Path(rotation_90_reference)
        else:
            default_rot = Path(__file__).parent / "rotation_90.png"
            self.rotation_90_reference_path = default_rot if default_rot.exists() else None

        # Set reference image path for translation-400
        if translation_reference:
            self.translation_reference_path = Path(translation_reference)
        else:
            default_rot = Path(__file__).parent / "translation_400.png"
            self.translation_reference_path = default_rot if default_rot.exists() else None

        # Set reference image path for zoom-100
        if zoom_100_reference:
            self.zoom_100_reference_path = Path(zoom_100_reference)
        else:
            default_rot = Path(__file__).parent / "zoom_100.png"
            self.zoom_100_reference_path = default_rot if default_rot.exists() else None
        
        vesta_folder = self.base_folder.parent
        self.evaluate_folder = vesta_folder / "evaluate"
        
        if not self.evaluate_folder.exists():
            self.evaluate_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created evaluation output directory: {self.evaluate_folder}")
        
        self.ocr_cache_folder = self.evaluate_folder / "ocr_results" / self.task_folder_name
        if not self.ocr_cache_folder.exists():
            self.ocr_cache_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created OCR cache directory: {self.ocr_cache_folder}")
        
        # Create cropped image cache directory (for visual similarity comparison)
        self.crop_cache_folder = self.evaluate_folder / "cropped_images" / self.task_folder_name
        if not self.crop_cache_folder.exists():
            self.crop_cache_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created cropped image cache directory: {self.crop_cache_folder}")
        
        self.log_file = self.evaluate_folder / "evaluation_log.txt"
        
        self._load_files()
        
        # Preprocessing: identify filenames in screenshots
        self.screenshot_files = self._identify_files_in_screenshots()
        
        # Prepare cropped version of reference image
        self.reference_cropped = None
        if self.reference_image_path and self.reference_image_path.exists():
            self.reference_cropped = self._prepare_reference_image(
                self.reference_image_path, 
                "reference_cropped.png"
            )
        
        # Prepare cropped version of 90-degree rotation reference image
        self.rotation_90_cropped = None
        if self.rotation_90_reference_path and self.rotation_90_reference_path.exists():
            self.rotation_90_cropped = self._prepare_reference_image(
                self.rotation_90_reference_path,
                "rotation_90_cropped.png"
            )
        # Prepare cropped version of translation-400 reference image
        self.translation_400_cropped = None
        if self.translation_reference_path and self.translation_reference_path.exists():
            self.translation_400_cropped = self._prepare_reference_image(
                self.translation_reference_path,
                "translation_400_cropped.png"
            )
        # Prepare cropped version of zoom-100 reference image
        self.zoom_100_cropped = None
        if self.zoom_100_reference_path and self.zoom_100_reference_path.exists():
            self.zoom_100_cropped = self._prepare_reference_image(
                self.zoom_100_reference_path,
                "zoom_100_cropped.png"
            )
    
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

    def _crop_central_region(self, img_path: Path, save_path: Path = None) -> Path:
        """
        Crop the central region of the image:
        - Height: middle 70% (remove top 10%, bottom 20%)
        - Width: remove left 35%
        """
        img = Image.open(img_path)
        width, height = img.size
        
        # Calculate crop region
        left = int(width * 0.35)  # Remove left 35%
        right = width
        top = int(height * 0.1)  # Remove top 10%
        bottom = int(height * 0.8)  # Remove bottom 20%
        
        cropped = img.crop((left, top, right, bottom))
        
        if save_path is None:
            save_path = self.crop_cache_folder / f"cropped_{img_path.stem}.png"
        
        cropped.save(save_path)
        return save_path
    
    def _prepare_reference_image(self, ref_path: Path, output_name: str) -> Path:
        """Prepare cropped version of reference image"""
        if not ref_path.exists():
            self._log(f"Warning: reference image not found: {ref_path}", "WARNING")
            return None
        
        ref_cropped_path = self.crop_cache_folder / output_name
        if not ref_cropped_path.exists():
            self._log(f"正在裁剪参考图片: {ref_path.name}...", "INFO")
            self._crop_central_region(ref_path, ref_cropped_path)
            self._log(f"✓ 参考图片已裁剪并保存: {ref_cropped_path}", "INFO")
        else:
            self._log(f"✓ 使用已缓存的参考图片: {ref_cropped_path}", "INFO")
        
        return ref_cropped_path
    
    def _detect_selected_style(self, screenshot_path: Path) -> Tuple[Optional[str], Dict[str, str]]:
        """
        检测左侧面板当前选中的Style
        通过分析蓝色圆圈的位置来判断
        最终修复版：
        1. 移除过短关键词（避免'etr'误匹配'wireframe'）
        2. Correctly handle dialog occlusion (has_style_text check)
        3. 精确匹配优先（避免'stick'误匹配'ball-stick'）
        """
        import cv2
        import traceback
        
        debug_paths = {
            'left_panel': None,
            'blue_mask': None,
            'marked': None,
            'debug_txt': None
        }
        
        debug_file = self.crop_cache_folder / f"debug_{screenshot_path.stem}.txt"
        debug_paths['debug_txt'] = str(debug_file)
        
        try:
            # Step 1: Crop left panel
            img = Image.open(screenshot_path)
            width, height = img.size
            left_panel = img.crop((0, int(height * 0.1), int(width * 0.3), int(height * 0.4)))
            
            # Save left panel
            left_panel_save_path = self.crop_cache_folder / f"left_panel_{screenshot_path.stem}.png"
            left_panel.save(left_panel_save_path)
            debug_paths['left_panel'] = str(left_panel_save_path)
            
            # Step 2: OCR recognition
            img_array = np.array(left_panel)
            results = self.ocr_reader.readtext(img_array, detail=1)
            
            all_texts = [text for _, text, _ in results]
            
            # Write to debug file
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=== OCR Results ===\n")
                for bbox, text, conf in results:
                    f.write(f"  '{text}' (conf: {conf:.2f})\n")
            
            # Step 3: Check dialog
            dialog_keywords = ['ok', 'cancel', 'apply', 'orientation', 'boundary', 'properties','show polyhedra']
            all_text_lower = ' '.join(all_texts).lower()
            has_dialog = any(kw in all_text_lower for kw in dialog_keywords)
            
            if has_dialog:
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write("\n!!! DIALOG DETECTED !!!\n")
            
            # Step 3.5: Check if "Style" text is visible
            has_style_text = False
            style_text_y = None
            for bbox, text, conf in results:
                text_clean = text.strip()
                if text_clean.lower() == 'style':
                    has_style_text = True
                    style_text_y = (bbox[0][1] + bbox[2][1]) / 2
                    with open(debug_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n=== Found 'Style' text at y={style_text_y:.1f} ===\n")
                    break
            
            if not has_style_text:
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n!!! NO 'Style' TEXT FOUND - Likely covered by dialog !!!\n")
            
            # Step 4: Match Style keywords (final fix)
            # Key improvement: reorder to check shorter, easily mismatched items first
            style_keywords_ordered = [
                # Priority 1: short and independent keywords (avoid substring match by long keywords)
                ('Stick', [
                    'stick', 'etick', 'stiok'
                ]),
                # Priority 2: long keywords containing short keywords
                ('Ball & Stick', [
                    'ball-and-stick', 'ball and stick', 'ballandstick', 
                    'ball-stick', 'ballstick'
                ]),
                # Priority 3: other keywords
                ('Space-filling', [
                    'space-filling', 'space filling', 'spacefilling', 
                    'space-fil', 'spacefil',
                    'epace-filling', 'epacefilling', 'epacezing', 
                    'epacezfilling'
                ]),
                ('Polyhedral', [
                    'polyhedral', 'polyhedr', 'polyhed', 'polyhec'
                ]),
                ('Wireframe', [
                    'wireframe', 'wire frame', 'wirefrane', 'wirefram', 
                    'wire-frame', 'wiretramg', 'wiretram'
                ])
            ]
            
            detected_styles = []
            for bbox, text, conf in results:
                text_lower = text.lower().strip()
                # Raise minimum length requirement to 4 characters
                if len(text_lower) < 4:
                    continue
                
                # First try exact matching (fully equal)
                matched_style = None
                for style_name, keywords in style_keywords_ordered:
                    for kw in keywords:
                        if text_lower == kw:
                            matched_style = style_name
                            with open(debug_file, 'a', encoding='utf-8') as f:
                                f.write(f"  [EXACT MATCH] '{text}' -> {style_name}\n")
                            break
                    if matched_style:
                        break
                
                # If exact match fails, try partial matching
                if not matched_style:
                    for style_name, keywords in style_keywords_ordered:
                        for kw in keywords:
                            # Only allow partial matching when keyword length >= 7
                            # Raise threshold to avoid 'stick' in 'ball-stick'
                            if len(kw) >= 7:
                                # Method 1: keyword in text
                                if kw in text_lower:
                                    matched_style = style_name
                                    with open(debug_file, 'a', encoding='utf-8') as f:
                                        f.write(f"  [PARTIAL MATCH] '{text}' -> {style_name} (kw in text)\n")
                                    break
                                # Method 2: text in keyword
                                if len(text_lower) >= 7 and text_lower in kw:
                                    matched_style = style_name
                                    with open(debug_file, 'a', encoding='utf-8') as f:
                                        f.write(f"  [PARTIAL MATCH] '{text}' -> {style_name} (text in kw)\n")
                                    break
                        if matched_style:
                            break
                
                if matched_style:
                    y_center = (bbox[0][1] + bbox[2][1]) / 2
                    detected_styles.append({
                        'text': text,
                        'style': matched_style,
                        'y': y_center,
                        'conf': conf
                    })
            
            # Step 4.5: Fallback mechanism
            if len(detected_styles) < 5 and not has_dialog and has_style_text:
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== Using Fallback: Fixed Y Positions ===\n")
                    f.write(f"  Detected {len(detected_styles)} styles, adding fallback positions\n")
                    f.write(f"  Reason: 'Style' text found, but OCR incomplete\n")
                
                panel_height = left_panel.size[1]
                expected_styles = [
                    ('Ball & Stick', 0.25),
                    ('Space-filling', 0.40),
                    ('Polyhedral', 0.55),
                    ('Wireframe', 0.70),
                    ('Stick', 0.85)
                ]
                
                detected_style_names = set(s['style'] for s in detected_styles)
                
                for style_name, y_ratio in expected_styles:
                    if style_name not in detected_style_names:
                        y_pos = panel_height * y_ratio
                        detected_styles.append({
                            'text': f'[Fallback]',
                            'style': style_name,
                            'y': y_pos,
                            'conf': 0.5
                        })
                        with open(debug_file, 'a', encoding='utf-8') as f:
                            f.write(f"  Added fallback: {style_name} at y={y_pos:.1f}\n")
            
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Detected Styles ===\n")
                if detected_styles:
                    for s in sorted(detected_styles, key=lambda x: x['y']):
                        f.write(f"  {s['text']} -> {s['style']} (y={s['y']:.1f}, conf={s['conf']:.2f})\n")
                else:
                    f.write("  None\n")
            
            # Step 5: If no styles detected, return None directly
            if len(detected_styles) == 0:
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== Early Return: No Styles Detected ===\n")
                    if not has_style_text:
                        f.write(f"  Reason: No 'Style' text found (likely covered by dialog)\n")
                    else:
                        f.write(f"  Reason: OCR failed to recognize any styles\n")
                return None, debug_paths
            
            # Step 6: Blue detection
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Blue Circle Detection ===\n")
            
            panel_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            panel_hsv = cv2.cvtColor(panel_bgr, cv2.COLOR_BGR2HSV)
            
            lower_blue = np.array([100, 150, 150])
            upper_blue = np.array([130, 255, 255])
            blue_mask = cv2.inRange(panel_hsv, lower_blue, upper_blue)
            
            blue_mask_path = self.crop_cache_folder / f"blue_mask_{screenshot_path.stem}.png"
            
            try:
                from PIL import Image as PILImage
                blue_mask_pil = PILImage.fromarray(blue_mask)
                blue_mask_pil.save(str(blue_mask_path))
            except Exception as e:
                try:
                    is_success, buffer = cv2.imencode(".png", blue_mask)
                    if is_success:
                        with open(str(blue_mask_path), 'wb') as f:
                            f.write(buffer)
                except Exception as e2:
                    pass
            debug_paths['blue_mask'] = str(blue_mask_path)
            
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"  Blue mask saved to: {blue_mask_path.name}\n")
            
            # Step 7: Find contours
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"  Total contours found: {len(contours)}\n")
            
            valid_contours = []
            if style_text_y is not None:
                for contour in contours:
                    area = cv2.contourArea(contour)
                    M = cv2.moments(contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        distance_from_style = cy - style_text_y
                        if 10 < distance_from_style < 200:
                            valid_contours.append(contour)
                            with open(debug_file, 'a', encoding='utf-8') as f:
                                f.write(f"  Valid contour at ({cx}, {cy}), area={area:.1f}, distance from Style={distance_from_style:.1f}\n")
                        else:
                            with open(debug_file, 'a', encoding='utf-8') as f:
                                f.write(f"  Skipped contour at ({cx}, {cy}), distance from Style={distance_from_style:.1f} (out of range)\n")
            else:
                valid_contours = contours
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"  No 'Style' text found, using all contours\n")
            
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"  Valid contours after filtering: {len(valid_contours)}\n")
            
            # Step 8: Create annotation image
            panel_marked = img_array.copy()
            
            if valid_contours:
                largest = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    cv2.circle(panel_marked, (cx, cy), 10, (255, 0, 0), 2)
                    
                    for s in detected_styles:
                        y = int(s['y'])
                        cv2.circle(panel_marked, (40, y), 5, (0, 255, 0), -1)
                    
                    with open(debug_file, 'a', encoding='utf-8') as f:
                        f.write(f"  Blue circle at: ({cx}, {cy})\n")
                    
                    if detected_styles:
                        closest = min(detected_styles, key=lambda s: abs(s['y'] - cy))
                        
                        with open(debug_file, 'a', encoding='utf-8') as f:
                            f.write(f"  Closest style: {closest['style']} (distance={abs(closest['y'] - cy):.1f})\n")
                        
                        marked_path = self.crop_cache_folder / f"marked_{screenshot_path.stem}.png"
                        
                        try:
                            from PIL import Image as PILImage
                            marked_pil = PILImage.fromarray(panel_marked)
                            marked_pil.save(str(marked_path))
                        except Exception as e:
                            try:
                                panel_marked_bgr = cv2.cvtColor(panel_marked, cv2.COLOR_RGB2BGR)
                                is_success, buffer = cv2.imencode(".png", panel_marked_bgr)
                                if is_success:
                                    with open(str(marked_path), 'wb') as f:
                                        f.write(buffer)
                            except Exception as e2:
                                pass
                        
                        debug_paths['marked'] = str(marked_path)
                        
                        if has_dialog:
                            return None, debug_paths
                        
                        return closest['style'], debug_paths
            
            marked_path = self.crop_cache_folder / f"marked_{screenshot_path.stem}.png"
            
            try:
                from PIL import Image as PILImage
                marked_pil = PILImage.fromarray(panel_marked)
                marked_pil.save(str(marked_path))
            except Exception as e:
                try:
                    panel_marked_bgr = cv2.cvtColor(panel_marked, cv2.COLOR_RGB2BGR)
                    is_success, buffer = cv2.imencode(".png", panel_marked_bgr)
                    if is_success:
                        with open(str(marked_path), 'wb') as f:
                            f.write(buffer)
                except Exception as e2:
                    pass
            
            debug_paths['marked'] = str(marked_path)
            
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Result ===\n")
                f.write(f"  Returning: None\n")
                if has_dialog:
                    f.write(f"  Reason: Dialog detected\n")
                elif not contours:
                    f.write(f"  Reason: No blue circle\n")
                elif not detected_styles:
                    f.write(f"  Reason: No styles detected\n")
            
            return None, debug_paths
            
        except Exception as e:
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n!!! EXCEPTION !!!\n")
                f.write(f"{traceback.format_exc()}\n")
            self._log(f"检测失败: {str(e)}", "ERROR")
            return None, debug_paths

    def _calculate_visual_similarity(self, screenshot_path: Path, reference_cropped: Path) -> Tuple[float, Path]:
        """
        计算截图与参考图片的视觉相似度
        Returns: (similarity score, path to cropped screenshot)
        """
        if reference_cropped is None:
            self._log("参考图片未准备好，跳过视觉相似度计算", "WARNING")
            return 0.0, None
        
        # Generate path for cropped screenshot
        screenshot_cropped_path = self.crop_cache_folder / f"cropped_{screenshot_path.stem}.png"
        
        # If not yet cropped, crop now
        if not screenshot_cropped_path.exists():
            screenshot_cropped_path = self._crop_central_region(screenshot_path, screenshot_cropped_path)
        
        # Calculate similarity
        try:
            from skimage.metrics import structural_similarity as ssim
            from skimage import io, transform
            
            # Read image
            img1 = io.imread(reference_cropped)
            img2 = io.imread(screenshot_cropped_path)
            
            # Resize for consistency
            if img1.shape != img2.shape:
                img2 = transform.resize(img2, img1.shape, anti_aliasing=True, preserve_range=True)
                img2 = img2.astype(img1.dtype)
            
            # Convert to grayscale
            if len(img1.shape) == 3:
                img1_gray = np.mean(img1, axis=2).astype(np.uint8)
            else:
                img1_gray = img1
                
            if len(img2.shape) == 3:
                img2_gray = np.mean(img2, axis=2).astype(np.uint8)
            else:
                img2_gray = img2
            
            # Calculate SSIM
            similarity = ssim(img1_gray, img2_gray, data_range=255)
            
            return max(0.0, min(1.0, similarity)), screenshot_cropped_path
            
        except ImportError:
            self._log("警告: scikit-image未安装，使用像素差异作为替代方法", "WARNING")
            similarity = self._simple_similarity(screenshot_cropped_path, reference_cropped)
            return similarity, screenshot_cropped_path
        except Exception as e:
            self._log(f"相似度计算错误: {str(e)}", "ERROR")
            return 0.0, screenshot_cropped_path
    
    def _simple_similarity(self, screenshot_cropped: Path, reference_cropped: Path) -> float:
        """Simple pixel-difference similarity calculation"""
        try:
            img1 = Image.open(reference_cropped).convert('L')
            img2 = Image.open(screenshot_cropped).convert('L')
            
            # Resize
            if img1.size != img2.size:
                img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
            
            arr1 = np.array(img1, dtype=np.float32)
            arr2 = np.array(img2, dtype=np.float32)
            
            # Calculate normalized mean squared error
            mse = np.mean((arr1 - arr2) ** 2)
            max_mse = 255 ** 2  # maximum possible MSE
            
            # Convert to similarity (0-1)
            similarity = 1 - (mse / max_mse)
            
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            self._log(f"简单相似度计算错误: {str(e)}", "ERROR")
            return 0.0

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
        if region == "top20%":
            img = img.crop((0, 0, width, int(height * 0.2)))
        elif region == "bottom20%":
            img = img.crop((0, int(height * 0.8), width, height))
        elif region == "top5%":
            img = img.crop((0, 0, width, int(height * 0.05)))
        elif region == "top10%":
            img = img.crop((0, 0, width, int(height * 0.1)))
        elif region == "no-bottom30%-no-left20%":  # remove bottom 30% and left 20%
            img = img.crop((int(width * 0.2), int(height * 0.5), width, int(height * 0.7)))
        elif region == "bottom5%":
            img = img.crop((0, int(height * 0.95), width, height))
        elif region == "bottom50%":
            img = img.crop((0, int(height * 0.5), width, height))
        elif region == "middle50%":
            img = img.crop((0, int(height * 0.25), width, int(height * 0.75)))
        elif region == "right30%":
            img = img.crop((int(width * 0.7), 0, width, height))
        
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
    
    def _read_ally_tree(self, index: int) -> str:
        """Read accessibility tree file"""
        if 0 <= index < len(self.ally_trees):
            with open(self.ally_trees[index], 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _identify_files_in_screenshots(self) -> List[str]:
        """Preprocessing: identify filenames in all screenshots"""
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
                self._log(f"  Frame [{i:02d}]: ✓ {current_file}", "DEBUG")
            
            screenshot_files.append(current_file)
        
        self._log(f"✓ File identification complete: {len(screenshot_files)} frames total", "INFO")
        
        unique_files = set([f for f in screenshot_files if f])
        if unique_files:
            self._log(f"  Identified files: {', '.join(sorted(unique_files))}", "INFO")
        else:
            self._log(f"  ⚠️ Warning: No filenames identified!", "WARNING")
        
        return screenshot_files
    
    def _extract_filename_from_text(self, text: str) -> Optional[str]:
        """Extract VESTA filename from OCR text"""
        if not text:
            return None
        
        # Strategy 1: match mp-number_element.cif format
        cif_pattern = r'mp[-_](\d+)[-_]([A-Za-z0-9]+)\.cif'
        match = re.search(cif_pattern, text, re.IGNORECASE)
        if match:
            return f"mp-{match.group(1)}_{match.group(2)}.cif"
        
        # Strategy 2: match .vesta files
        vesta_pattern = r'([A-Za-z0-9_\-]+)\.vesta'
        match = re.search(vesta_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # Strategy 3: match files without extension
        simple_pattern = r'mp[-_](\d+)[-_]([A-Za-z0-9]+)'
        match = re.search(simple_pattern, text, re.IGNORECASE)
        if match:
            return f"mp-{match.group(1)}_{match.group(2)}"
        
        return None

    # ============ EVALUATION FUNCTIONS ============

    def check_file_opened(self, expected_filename: str) -> Dict[str, Any]:
        """Check if a file has been opened"""
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
        
        expected_base = expected_filename.replace('.cif', '').replace('.vesta', '')
        
        found_index = -1
        for i, detected_file in enumerate(self.screenshot_files):
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

    def check_standard_orientation(self, similarity_threshold: float = 0.9) -> Dict[str, Any]:
        """
        改进版：检查是否旋转到标准晶体学取向
        优先检测文本，如果没有检测到则使用视觉相似度比较
        """
        self._log("检查标准晶体学取向（文本检测 + 视觉相似度）", "INFO")
        
        result = {
            'function': 'check_standard_orientation',
            'score': 0,
            'max_score': 1,
            'details': {
                'text_detected': False,
                'text_detection_step': None,
                'similarity_scores': [],
                'max_similarity': 0.0,
                'max_similarity_step': None,
                'threshold': similarity_threshold,
                'initial_similarity': None,
                'final_similarity': None,
                'cropped_images_folder': str(self.crop_cache_folder),
                'detection_method': None
            }
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        # Step 1: Prioritize text detection
        self._log("步骤1: 检测文本 'Standard orientation of crystal shape'", "INFO")
        target_text = "Standard orientation of crystal shape"
        
        for i, screenshot in enumerate(self.screenshots):
            full_text = self._ocr_region(screenshot, "top10%")
            
            if target_text.lower() in full_text.lower():
                result['score'] = 1
                result['details']['text_detected'] = True
                result['details']['text_detection_step'] = i
                result['details']['detection_method'] = 'text_detection'
                self._log(f"✓ 在步骤 [{i:02d}] 检测到文本: '{target_text}'", "SUCCESS")
                self._log(f"✓ 通过文本检测判断任务完成", "SUCCESS")
                return result
        
        self._log("未检测到目标文本，切换到视觉相似度比较", "INFO")
        
        # Step 2: Visual similarity
        if self.reference_cropped is None:
            self._log("参考图片未准备好，无法进行视觉相似度比较", "WARNING")
            result['details']['error'] = "参考图片未准备好且未检测到文本"
            return result
        
        self._log(f"步骤2: 使用视觉相似度比较", "INFO")
        self._log(f"参考图片（裁剪后）: {self.reference_cropped}", "INFO")
        self._log(f"裁剪图片保存目录: {self.crop_cache_folder}", "INFO")
        print(f"\n开始逐帧计算相似度:")
        
        result['details']['detection_method'] = 'visual_similarity'
        
        # Calculate similarity for each frame
        for i, screenshot in enumerate(self.screenshots):
            similarity, cropped_path = self._calculate_visual_similarity(screenshot, self.reference_cropped)
            
            # Real-time print
            print(f"  Step [{i:02d}] | Similarity: {similarity:.4f} | Crop: {cropped_path.name if cropped_path else 'N/A'}")
            
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
        
        max_sim = result['details']['max_similarity']
        initial_sim = result['details']['initial_similarity']
        final_sim = result['details']['final_similarity']
        
        print()  # blank line separator
        
        if max_sim >= similarity_threshold:
            result['score'] = 1
            self._log(
                f"✓ Standard orientation achieved: max similarity {max_sim:.4f} (step {result['details']['max_similarity_step']:02d})",
                "SUCCESS"
            )
        elif final_sim > initial_sim and final_sim >= similarity_threshold * 0.8:
            result['score'] = 0.5
            self._log(
                f"⚠ Partially complete: final similarity {final_sim:.4f} improved but below threshold {similarity_threshold}",
                "WARNING"
            )
        else:
            self._log(
                f"✗ Standard orientation not achieved: max similarity {max_sim:.4f} < threshold {similarity_threshold}",
                "FAIL"
            )
        
        self._log(f"\n✓ 所有裁剪后的图片已保存至: {self.crop_cache_folder}", "INFO")
        self._log(f"  - 参考图片: reference_cropped.png", "INFO")
        self._log(f"  - 截图: cropped_screenshot-step_*.png", "INFO")
        
        return result

    def check_rotation_90_up(self, similarity_threshold: float = 0.9) -> Dict[str, Any]:
        """
        改进版：检查向上旋转90度
        优先检测文本，如果没有检测到则使用视觉相似度比较
        """
        self._log("检查向上旋转90度（文本检测 + 视觉相似度）", "INFO")
        
        result = {
            'function': 'check_rotation_90_up',
            'score': 0,
            'max_score': 1,
            'details': {
                'text_detected': False,
                'text_detection_step': None,
                'similarity_scores': [],
                'max_similarity': 0.0,
                'max_similarity_step': None,
                'threshold': similarity_threshold,
                'initial_similarity': None,
                'final_similarity': None,
                'cropped_images_folder': str(self.crop_cache_folder),
                'detection_method': None
            }
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        # Step 1: Prioritize text detection
        self._log("步骤1: 检测文本 '90' + 'Rotate around the y axis'", "INFO")
        keyword1 = "rotate around the y axis"
        keyword2 = "90"
        
        for i, screenshot in enumerate(self.screenshots):
            full_text = self._ocr_region(screenshot, "top10%")
            full_text_lower = full_text.lower()
            
            has_rotate = keyword1 in full_text_lower
            has_90 = keyword2 in full_text_lower
            
            if has_rotate and has_90:
                result['score'] = 1
                result['details']['text_detected'] = True
                result['details']['text_detection_step'] = i
                result['details']['detection_method'] = 'text_detection'
                result['details']['detected_keywords'] = [keyword1, keyword2]
                self._log(f"✓ 在步骤 [{i:02d}] 检测到关键词: '{keyword1}' + '{keyword2}'", "SUCCESS")
                self._log(f"✓ 通过文本检测判断任务完成", "SUCCESS")
                return result
        
        self._log("未检测到目标文本，切换到视觉相似度比较", "INFO")
        
        # Step 2: Visual similarity
        if self.rotation_90_cropped is None:
            self._log("旋转90度参考图片未准备好，无法进行视觉相似度比较", "WARNING")
            result['details']['error'] = "旋转90度参考图片未准备好且未检测到文本"
            return result
        
        self._log(f"步骤2: 使用视觉相似度比较", "INFO")
        self._log(f"旋转90度参考图片（裁剪后）: {self.rotation_90_cropped}", "INFO")
        self._log(f"裁剪图片保存目录: {self.crop_cache_folder}", "INFO")
        print(f"\n开始逐帧计算相似度:")
        
        result['details']['detection_method'] = 'visual_similarity'
        
        # Calculate similarity for each frame
        for i, screenshot in enumerate(self.screenshots):
            similarity, cropped_path = self._calculate_visual_similarity(screenshot, self.rotation_90_cropped)
            
            # Real-time print
            print(f"  Step [{i:02d}] | Similarity: {similarity:.4f} | Crop: {cropped_path.name if cropped_path else 'N/A'}")
            
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
        
        max_sim = result['details']['max_similarity']
        initial_sim = result['details']['initial_similarity']
        final_sim = result['details']['final_similarity']
        
        print()  # blank line separator
        
        if max_sim >= similarity_threshold:
            result['score'] = 1
            self._log(
                f"✓ 90-degree rotation completed: max similarity {max_sim:.4f} (step {result['details']['max_similarity_step']:02d})",
                "SUCCESS"
            )
        elif final_sim > initial_sim and final_sim >= similarity_threshold * 0.8:
            result['score'] = 0.5
            self._log(
                f"⚠ Partially complete: final similarity {final_sim:.4f} improved but below threshold {similarity_threshold}",
                "WARNING"
            )
        else:
            self._log(
                f"✗ 90-degree rotation not achieved: max similarity {max_sim:.4f} < threshold {similarity_threshold}",
                "FAIL"
            )
        
        self._log(f"\n✓ 所有裁剪后的图片已保存至: {self.crop_cache_folder}", "INFO")
        self._log(f"  - 旋转90度参考图片: rotation_90_cropped.png", "INFO")
        self._log(f"  - 截图: cropped_screenshot-step_*.png", "INFO")
        
        return result

    def check_translation(self, direction: str = "right", units: int = 400, 
                        similarity_threshold: float = 0.9) -> Dict[str, Any]:
        """
        改进版：检查平移操作
        优先检测文本，如果没有检测到则使用视觉相似度比较
        """
        self._log(f"检查平移操作: {direction} {units}单位（文本检测 + 视觉相似度）", "INFO")
        
        result = {
            'function': 'check_translation',
            'direction': direction,
            'units': units,
            'score': 0,
            'max_score': 1,
            'details': {
                'text_detected': False,
                'text_detection_step': None,
                'similarity_scores': [],
                'max_similarity': 0.0,
                'max_similarity_step': None,
                'max_similarity_path': None,
                'threshold': similarity_threshold,
                'initial_similarity': None,
                'final_similarity': None,
                'cropped_images_folder': str(self.crop_cache_folder),
                'detection_method': None
            }
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        # Step 1: Prioritize text detection
        direction_map = {
            'right': 'rightward',
            'left': 'leftward', 
            'up': 'upward',
            'down': 'downward'
        }
        direction_text = direction_map.get(direction, direction)
        
        self._log(f"步骤1: 检测文本 '{units}' + 'Translate {direction_text}'", "INFO")
        keyword1 = f"translate {direction_text}"
        keyword2 = str(units)
        
        for i, screenshot in enumerate(self.screenshots):
            full_text = self._ocr_region(screenshot, "top10%")
            full_text_lower = full_text.lower()
            
            has_translate = keyword1 in full_text_lower
            has_units = keyword2 in full_text_lower
            
            if has_translate and has_units:
                result['score'] = 1
                result['details']['text_detected'] = True
                result['details']['text_detection_step'] = i
                result['details']['detection_method'] = 'text_detection'
                result['details']['detected_keywords'] = [keyword1, keyword2]
                self._log(f"✓ 在步骤 [{i:02d}] 检测到关键词: '{keyword1}' + '{keyword2}'", "SUCCESS")
                self._log(f"✓ 通过文本检测判断任务完成", "SUCCESS")
                return result
        
        self._log("未检测到目标文本，切换到视觉相似度比较", "INFO")
        
        # Step 2: Visual similarity comparison
        if self.translation_400_cropped is None:
            self._log("平移参考图片未准备好，无法进行视觉相似度比较", "WARNING")
            result['details']['error'] = "平移参考图片未准备好且未检测到文本"
            return result
        
        self._log(f"步骤2: 使用视觉相似度比较", "INFO")
        self._log(f"平移参考图片（裁剪后）: {self.translation_400_cropped}", "INFO")
        self._log(f"裁剪图片保存目录: {self.crop_cache_folder}", "INFO")
        print(f"\n开始逐帧计算相似度:")
        
        result['details']['detection_method'] = 'visual_similarity'
        
        # Calculate similarity for each frame
        for i, screenshot in enumerate(self.screenshots):
            similarity, cropped_path = self._calculate_visual_similarity(screenshot, self.translation_400_cropped)
            
            # Real-time print
            print(f"  Step [{i:02d}] | Similarity: {similarity:.4f} | Crop: {cropped_path.name if cropped_path else 'N/A'}")
            
            result['details']['similarity_scores'].append({
                'step': i,
                'similarity': round(similarity, 4),
                'cropped_image': str(cropped_path) if cropped_path else None
            })
            
            if similarity > result['details']['max_similarity']:
                result['details']['max_similarity'] = round(similarity, 4)
                result['details']['max_similarity_step'] = i
                result['details']['max_similarity_path'] = str(cropped_path) if cropped_path else None
        
        if result['details']['similarity_scores']:
            result['details']['initial_similarity'] = result['details']['similarity_scores'][0]['similarity']
            result['details']['final_similarity'] = result['details']['similarity_scores'][-1]['similarity']
        
        max_sim = result['details']['max_similarity']
        initial_sim = result['details']['initial_similarity']
        final_sim = result['details']['final_similarity']
        
        print()  # blank line separator
        
        if max_sim >= similarity_threshold:
            result['score'] = 1
            self._log(
                f"✓ Translation completed: max similarity {max_sim:.4f} (step {result['details']['max_similarity_step']:02d})",
                "SUCCESS"
            )
        elif final_sim > initial_sim and final_sim >= similarity_threshold * 0.8:
            result['score'] = 0.5
            self._log(
                f"⚠ Partially complete: final similarity {final_sim:.4f} improved but below threshold {similarity_threshold:.4f}",
                "WARNING"
            )
        else:
            self._log(
                f"✗ Translation not completed: max similarity {max_sim:.4f} < threshold {similarity_threshold:.4f}",
                "FAIL"
            )
        
        self._log(f"\n✓ 所有裁剪后的图片已保存至: {self.crop_cache_folder}", "INFO")
        self._log(f"  - 平移参考图片: translation_400_cropped.png", "INFO")
        if result['details'].get('max_similarity_path'):
            max_sim_filename = Path(result['details']['max_similarity_path']).name
            self._log(f"  - 最相似截图: {max_sim_filename}", "INFO")
        self._log(f"  - 截图序列: cropped_screenshot-step_*.png", "INFO")
        
        return result

    def check_style_change(self, target_style: str) -> Dict[str, Any]:
        """
        检查风格修改（如Wireframe、Ball & Stick等）
        只检测是否在任何一步达到了目标Style
        """
        self._log(f"检查风格修改为: {target_style}", "INFO")
        
        result = {
            'function': 'check_style_change',
            'target_style': target_style,
            'score': 0,
            'max_score': 1,
            'details': {
                'style_detected': False,
                'detected_at_step': None,
                'all_detected_styles': []  # 记录所有步骤检测到的style
            }
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result
        
        self._log(f"检测左侧面板选中状态（目标: {target_style}）", "INFO")
        self._log(f"左侧面板裁剪图像保存目录: {self.crop_cache_folder}", "INFO")
        print(f"\n逐帧检测选中的Style:")
        
        target_detected = False
        first_detection_step = None
        
        for i, screenshot in enumerate(self.screenshots):
            detected_style, debug_paths = self._detect_selected_style(screenshot)
            
            result['details']['all_detected_styles'].append({
                'step': i,
                'style': detected_style,
                'debug_paths': debug_paths
            })
            
            # Real-time print - includes cropped image path
            style_text = detected_style if detected_style else '无法识别'
            left_panel_path = Path(debug_paths['left_panel']).name if debug_paths.get('left_panel') else 'N/A'
            marked_path = Path(debug_paths['marked']).name if debug_paths.get('marked') else 'N/A'
            
            print(f"  Step [{i:02d}] | Style: {style_text:15s} | Left panel: {left_panel_path:40s} | Marked: {marked_path}")
            
            # Check whether matched target style
            if detected_style and target_style.lower() in detected_style.lower():
                if not target_detected:
                    target_detected = True
                    first_detection_step = i
                    result['score'] = 1
                    result['details']['style_detected'] = True
                    result['details']['detected_at_step'] = i
                    self._log(f"✓ 在步骤 [{i:02d}] 检测到目标风格 {target_style}", "SUCCESS")
        
        print()  # blank line separator
        
        if target_detected:
            if first_detection_step == 0:
                self._log(f"✓ 初始状态已是目标风格 {target_style}", "SUCCESS")
            else:
                self._log(f"✓ 在步骤 [{first_detection_step}] 成功切换到目标风格 {target_style}", "SUCCESS")
        else:
            self._log(f"✗ 未检测到目标风格 {target_style}", "FAIL")
        
        self._log(f"\n✓ 左侧面板裁剪图像已保存至: {self.crop_cache_folder}", "INFO")
        self._log(f"  - 左侧面板: left_panel_screenshot-step_*.png", "INFO")
        self._log(f"  - 蓝色掩码: blue_mask_screenshot-step_*.png", "INFO")
        self._log(f"  - 标记位置: marked_screenshot-step_*.png (红圈=蓝色检测位置, 绿点=Style选项位置)", "INFO")
        self._log(f"  - 调试信息: debug_screenshot-step_*.txt", "INFO")
        
        return result

    def check_atom_info_dialog(self, atom_type: str) -> Dict[str, Any]:
        """
        检查原子信息弹窗 - 最宽松版本
        只需要匹配原子标签: Ga0, Ga1, N2, N3 等
        
        输入 'Ga' -> 匹配 Ga0, Ga1, Ga2, Ga10 等
        输入 'N'  -> 匹配 N1, N2, N3, N10 等
        
        适应OCR识别不完整的情况（括号可能丢失）
        """
        self._log(f"检查{atom_type}原子信息弹窗", "INFO")
        
        result = {
            'function': 'check_atom_info_dialog',
            'atom_type': atom_type,
            'score': 0,
            'max_score': 1,
            'details': {
                'dialog_detected': False,
                'detected_at_step': None,
                'matched_text': None,
                'all_matches': []
            }
        }
        
        import re
        
        # Detection region
        regions_to_check = [
            "bottom20%"
        ]
        
        for i, screenshot in enumerate(self.screenshots):
            for region_key in regions_to_check:
                text = self._ocr_region(screenshot, region_key)
                
                # Match pattern: Ga0, Ga1, N2, N3 etc.
                # Format: element symbol + number
                # Use word boundaries to ensure exact matching
                pattern = rf'\b{atom_type}\d+\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                if matches:
                    result['score'] = 1
                    result['details']['dialog_detected'] = True
                    result['details']['detected_at_step'] = i
                    result['details']['matched_text'] = matches[0]
                    result['details']['all_matches'] = matches
                    
                    self._log(
                        f"✓ {atom_type} atom info dialog detected (step {i}, {region_name})",
                        "SUCCESS"
                    )
                    self._log(f"  匹配文本: {matches[0]}", "SUCCESS")
                    if len(matches) > 1:
                        self._log(f"  其他匹配: {matches[1:]}", "INFO")
                    
                    return result
        
        self._log(f"✗ 未检测到{atom_type}原子信息弹窗", "FAIL")
        return result

    def check_atom_deletion(self) -> Dict[str, Any]:
        """Check atom deletion operation"""
        self._log("检查原子删除操作", "INFO")
        
        result = {
            'function': 'check_atom_deletion',
            'score': 0,
            'max_score': 1,
            'details': {
                'deletion_detected': False,
                'delete_keywords': []
            }
        }
        
        delete_keywords = ['delete', 'Del']
        
        for i, screenshot in enumerate(self.screenshots):
            text = self._ocr_region(screenshot, "bottom20%")
            text_lower = text.lower()
            
            for keyword in delete_keywords:
                if keyword in text_lower:
                    result['details']['deletion_detected'] = True
                    result['details']['delete_keywords'].append({
                        'step': i,
                        'keyword': keyword
                    })
        
        if result['details']['deletion_detected']:
            result['score'] = 1
            self._log(f"✓ 检测到原子删除操作", "SUCCESS")
        else:
            self._log(f"✗ 未检测到原子删除操作", "FAIL")
        
        return result

    def check_bond_display(self, 
                       atom_a: Optional[str] = None, 
                       atom_b: Optional[str] = None,
                       possible_pairs: Optional[List[List[str]]] = None) -> Dict[str, Any]:
        """
        检查键连接结构显示 (集成 OCR 容错逻辑)
        """
        import re
        
        # --- Internal normalization helper function ---
        def normalize_label(label: str) -> str:
            if not label: return ""
            label = re.sub(r'([A-Z][a-z]?)[Oo](\b|_|-|\s|$)', r'\g<1>0\g<2>', label)
            label = re.sub(r'([A-Z][a-z]?)[Iil](\b|_|-|\s|$)', r'\g<1>1\g<2>', label)
            return label

        # 1. Build and normalize all target sets for detection
        target_bonds = []
        if atom_a and atom_b:
            target_bonds.append((normalize_label(atom_a), normalize_label(atom_b)))
        if possible_pairs:
            for p in possible_pairs:
                if len(p) >= 2:
                    target_bonds.append((normalize_label(p[0]), normalize_label(p[1])))
        
        target_msg = f" (目标: {target_bonds})" if target_bonds else " (任意键)"
        self._log(f"检查键连接结构显示{target_msg}", "INFO")
        
        result = {
            'function': 'check_bond_display',
            'score': 0,
            'max_score': 1,
            'details': {
                'bond_info_detected': False,
                'target_bond_found': False,
                'matched_target': None,
                'detected_at_step': None,
                'bond_pattern': None,
                'all_bonds_raw': [],
                'all_bonds_normalized': []
            }
        }
        
        regions_to_check = ["bottom20%"]
        
        for i, screenshot in enumerate(self.screenshots):
            for region_key in regions_to_check:
                text = self._ocr_region(screenshot, region_key)
                
                # 2. Core regex: match hyphenated structure [atom]-[atom]
                # Use \w* to allow matching misrecognized letters, e.g. FeO-Feo
                bond_pattern = r'\b([A-Z][a-z]?\w*)\s*-\s*([A-Z][a-z]?\w*)\b'
                bond_matches = re.findall(bond_pattern, text)
                
                if bond_matches:
                    result['details']['bond_info_detected'] = True
                    is_success = False
                    
                    for raw_a, raw_b in bond_matches:
                        # 3. Normalize the raw OCR-recognized text
                        norm_a = normalize_label(raw_a)
                        norm_b = normalize_label(raw_b)
                        
                        raw_pair = f"{raw_a}-{raw_b}"
                        norm_pair = f"{norm_a}-{norm_b}"
                        
                        result['details']['all_bonds_raw'].append(raw_pair)
                        result['details']['all_bonds_normalized'].append(norm_pair)
                        
                        # 4. Logic decision
                        if target_bonds:
                            for t_a, t_b in target_bonds:
                                # Check bidirectional match (A-B or B-A)
                                if (norm_a == t_a and norm_b == t_b) or (norm_a == t_b and norm_b == t_a):
                                    result['details']['target_bond_found'] = True
                                    result['details']['matched_target'] = f"{t_a}-{t_b}"
                                    result['details']['bond_pattern'] = norm_pair
                                    is_success = True
                                    self._log(f"✓ 检测到目标键: {norm_pair} (原始OCR: {raw_pair})", "SUCCESS")
                                    break
                        else:
                            # If no target specified, pass as long as any correctly-formatted key is found
                            result['details']['bond_pattern'] = norm_pair
                            is_success = True
                            self._log(f"✓ 检测到键连接: {norm_pair}", "SUCCESS")
                        
                        if is_success: break

                    if is_success:
                        result['details']['detected_at_step'] = i
                        result['score'] = 1
                        return result
                    else:
                        self._log(f"⚠ 发现键 {result['details']['all_bonds_raw']}，但未匹配目标 {target_bonds}", "WARNING")

                # === Fallback logic: only applies when no specific target is specified ===
                elif not target_bonds:
                    has_bond_keyword = bool(re.search(r'bond|连接|distance', text, re.IGNORECASE))
                    has_distance = bool(re.search(r'\d+\.\d+\s*[Åå]', text))
                    if has_bond_keyword or has_distance:
                        result['details']['bond_info_detected'] = True
                        result['score'] = 1
                        self._log(f"✓ 检测到键连接信息 (传统模式)", "SUCCESS")
                        return result
        
        self._log(f"✗ 未检测到目标键连接", "FAIL")
        return result

        def check_zoom(self, percentage: int) -> Dict[str, Any]:
            """Check zoom operation (detect zoom-related text or values)"""
            self._log(f"检查缩放操作: {percentage}%", "INFO")
            
            result = {
                'function': 'check_zoom',
                'percentage': percentage,
                'score': 0,
                'max_score': 1,
                'details': {
                    'zoom_detected': False,
                    'detected_values': []
                }
            }
            
            for i, screenshot in enumerate(self.screenshots):
                text = self._ocr_region(screenshot, "full")
                
                # Check zoom keywords
                if "zoom" in text.lower():
                    result['details']['zoom_detected'] = True
                    
                    # Try to extract zoom value
                    zoom_match = re.search(r'zoom\s*in\s*(\d+)', text, re.IGNORECASE)
                    if zoom_match:
                        detected_val = int(zoom_match.group(1))
                        result['details']['detected_values'].append({
                            'step': i,
                            'value': detected_val
                        })
                        
                        # Check whether matched expected value (allow multiples of 5)
                        if detected_val == percentage or abs(detected_val - percentage) % 5 == 0:
                            result['score'] = 1
                            self._log(f"✓ 检测到缩放操作 {detected_val}% (步骤 {i})", "SUCCESS")
                            return result
            
            if result['details']['zoom_detected']:
                result['score'] = 0.5
                self._log(f"⚠ 检测到zoom操作但数值不匹配", "WARNING")
            else:
                self._log(f"✗ 未检测到缩放操作", "FAIL")
            
            return result
    def check_zoom(self, similarity_threshold: float = 0.9) -> Dict[str, Any]:
        """
        检查模型缩放状态 (Zoom In 100%)
        逻辑：
        1. OCR detection: must simultaneously detect "zoom in" text and "Step(%) = 100"
        2. Visual comparison: if text detection fails, compare with 100% scaled reference image
        """
        import re
        self._log("检查模型放大 100%（文本检测 + 视觉相似度）", "INFO")
        
        result = {
            'function': 'check_zoom',
            'score': 0,
            'max_score': 1,
            'details': {
                'text_detected': False,
                'has_zoom_in_text': False,
                'step_value': None,
                'max_similarity': 0.0,
                'detection_method': None,
                'all_similarities': []
            }
        }
        
        if len(self.screenshots) < 1:
            result['details']['error'] = "Insufficient screenshots"
            return result

        # --- Step 1: Text detection (match both Zoom In and Step value) ---
        self._log("步骤1: 检测关键词 'zoom in' 和 'Step(%)' 数值", "INFO")
        
        for i, screenshot in enumerate(self.screenshots):
            # Expand OCR range to top and bottom, as "zoom in" may appear in status bar
            full_text = self._ocr_region(screenshot, "top10%").lower()
            
            # 1. Detect "zoom in"
            has_zoom_in = "zoom in" in full_text
            
            # 2. Detect Step value (e.g. Step (%): 100)
            step_match = re.search(r'step\s*\(?\s*%\s*\)?\s*[:：]?\s*(\d+)', full_text)
            current_step = int(step_match.group(1)) if step_match else None
            
            if has_zoom_in:
                result['details']['has_zoom_in_text'] = True
                
            if current_step is not None:
                result['details']['step_value'] = current_step

            # Decision condition: must have seen "zoom in" and current step value is 100
            if has_zoom_in and current_step == 100:
                result['score'] = 1
                result['details']['text_detected'] = True
                result['details']['detection_method'] = 'text_ocr'
                self._log(f"✓ 步骤 [{i:02d}]: 同时检测到 'zoom in' 且 Step 为 100", "SUCCESS")
                return result
            elif has_zoom_in or (current_step is not None):
                # Record intermediate state, do not return success directly
                self._log(f"帧 [{i:02d}] 状态: ZoomIn={has_zoom_in}, Step={current_step}", "INFO")

        # --- Step 2: Visual similarity comparison (fallback) ---
        self._log("文本检测未完全达标，进入视觉相似度比对", "INFO")
        print('self.zoom_100_cropped',self.zoom_100_cropped)
        if not hasattr(self, 'zoom_100_cropped') or self.zoom_100_cropped is None:
            self._log("缺失 100% 放大参考图，无法进行视觉校验", "WARNING")
        else:
            result['details']['detection_method'] = 'visual_similarity'
            for i, screenshot in enumerate(self.screenshots):
                similarity, cropped_path = self._calculate_visual_similarity(screenshot, self.zoom_100_cropped)
                print(f"  Step [{i:02d}] | Similarity: {similarity:.4f} | Path: {cropped_path.name if cropped_path else 'N/A'}")
                result['details']['all_similarities'].append(round(similarity, 4))
                
                if similarity > result['details']['max_similarity']:
                    result['details']['max_similarity'] = round(similarity, 4)
                    result['details']['max_similarity_step'] = i

            max_sim = result['details']['max_similarity']
            if max_sim >= similarity_threshold:
                result['score'] = 1
                self._log(f"✓ 视觉特征匹配成功 (相似度 {max_sim})", "SUCCESS")
                return result
            elif max_sim >= similarity_threshold * 0.7:
                result['score'] = 0.5
                self._log(f"⚠ 模型有明显放大迹象，相似度 {max_sim}", "WARNING")

        if result['score'] == 0:
            self._log("✗ 未检测到缩放至 100% 的状态", "FAIL")
        
        return result

    def check_axes_toggle(self) -> Dict[str, Any]:
        """
        检查坐标轴显示状态是否发生了切换(由开变关,或由关变开)
        检测区域: 左下20% (坐标轴a, b, c所在位置)
        起点: 检测到文件名后的第一帧
        """
        
        self._log("检查坐标轴(a, b, c)状态切换", "INFO")
        
        result = {
            'function': 'check_axes_toggle',
            'score': 0,
            'max_score': 1,
            'details': {
                'initial_state': None,
                'final_state': None,
                'initial_axes': [],
                'final_axes': [],
                'state_changed': False,
                'initial_frame': None,
                'final_frame': None,
                'saved_crops': []
            }
        }
        
        if len(self.screenshots) < 2:
            result['details']['error'] = "截图数量不足,无法比对前后状态"
            return result
        
        # === Step 1: Find the first frame where a filename is detected ===
        file_detected_frame = None
        for i, screenshot in enumerate(self.screenshots):
            # Detect if top region has a .cif filename
            text = self._ocr_region(screenshot, "top10%")
            if '.cif' in text.lower():
                file_detected_frame = i
                self._log(f"检测到文件名于第{i}帧", "INFO")
                break
        
        # If no filename detected, use the first frame
        if file_detected_frame is None:
            file_detected_frame = 0
            self._log("未检测到文件名，使用第0帧作为起点", "INFO")
        
        # === Helper: detect if a,b,c labels exist in bottom-left 20% region ===
        def get_axes_state(screenshot_path, suffix, frame_idx):
            img = Image.open(screenshot_path)
            width, height = img.size
            
            # Bottom-left 20% region
            # left=0, top=80%h, right=20%w, bottom=100%h
            crop_box = (0, int(height * 0.8), int(width * 0.2), height)
            cropped_img = img.crop(crop_box)
            
            # Save cropped image
            save_name = f"axes_crop_{suffix}_frame{frame_idx}.png"
            save_path = os.path.join(self.crop_cache_folder, save_name)
            cropped_img.save(save_path)
            result['details']['saved_crops'].append(save_path)
            
            # OCR recognition
            import numpy as np
            img_array = np.array(cropped_img)
            ocr_results = self.ocr_reader.readtext(img_array, detail=1)
            
            # Extract all text
            all_text = ' '.join([text for _, text, _ in ocr_results])
            
            # Record OCR results to debug file
            debug_file = os.path.join(self.crop_cache_folder, f"axes_ocr_{suffix}_frame{frame_idx}.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"=== OCR Results for {suffix} (Frame {frame_idx}) ===\n")
                f.write(f"Crop box: {crop_box}\n")
                f.write(f"Crop size: {cropped_img.size}\n\n")
                for bbox, text, conf in ocr_results:
                    f.write(f"'{text}' (conf: {conf:.2f})\n")
                f.write(f"\n=== All Text ===\n{all_text}\n")
            
            # Detect a, b, c
            found = []
            for label in ['a', 'b', 'c']:
                # Use looser matching: case-insensitive, allow any surrounding characters
                if re.search(rf'\b{label}\b', all_text, re.IGNORECASE):
                    found.append(label)
            
            has_axes = len(found) > 0
            self._log(f"  Frame {frame_idx} ({suffix}): {'找到' if has_axes else '未找到'} 坐标轴 {found}", "INFO")
            
            return has_axes, found
        
        # === Step 2: Check initial state (first frame after file open) ===
        initial_on, initial_list = get_axes_state(
            self.screenshots[file_detected_frame], 
            "initial", 
            file_detected_frame
        )
        result['details']['initial_state'] = "ON" if initial_on else "OFF"
        result['details']['initial_axes'] = initial_list
        result['details']['initial_frame'] = file_detected_frame
        
        # === Step 3: Check final state (last frame) ===
        final_frame = len(self.screenshots) - 1
        final_on, final_list = get_axes_state(
            self.screenshots[final_frame], 
            "final", 
            final_frame
        )
        result['details']['final_state'] = "ON" if final_on else "OFF"
        result['details']['final_axes'] = final_list
        result['details']['final_frame'] = final_frame
        
        # === Step 4: Decision logic ===
        if initial_on != final_on:
            result['score'] = 1
            result['details']['state_changed'] = True
            self._log(
                f"✓ Axis switched successfully: {result['details']['initial_state']} → {result['details']['final_state']} "
                f"(Frame {file_detected_frame} → {final_frame})", 
                "SUCCESS"
            )
        else:
            result['score'] = 0
            self._log(
                f"✗ State unchanged: {result['details']['initial_state']} "
                f"(Frame {file_detected_frame} → {final_frame})", 
                "FAIL"
            )
        
        self._log(f"裁剪图像已保存至: {self.crop_cache_folder}", "INFO")
        return result

    def check_dialog_opened(self, title_keyword: str = "Properties", filename: str = "", 
                       field_checks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        纯 OCR 版本：检测弹窗标题和字段值
        - Title detection: top 5% region
        - Field detection: left 40%, top 60% region (main dialog content area)
        
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

        for i, screenshot in enumerate(self.screenshots):
            # === Step 1: Detect dialog title in top 5% ===
            title_text = self._ocr_region(screenshot, "top5%")
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
            
            # === Step 2: Detect field content in left 40%, top 60% region ===
            self._log(f"[步骤 {i:02d}] 检测到弹窗标题 '{found_title}'，开始验证字段...", "INFO")
            
            # Read field region (left 40%, top 5%-65%)
            field_text = self._ocr_region_custom(screenshot, left_percent=0, right_percent=40, 
                                                top_percent=5, bottom_percent=65)
            field_text_lower = field_text.lower()
            result['details']['field_region_text_sample'] = field_text[:200].replace('\n', ' ')
            
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
                if field_name.lower() == "radius":
                    field_patterns.extend(["radlus", "raidus", "radıus", "radiüs"])
                elif field_name.lower() == "stacks":
                    field_patterns.extend(["stack", "slacks"])
                
                # Try matching: field name + separator + value
                field_matched = False
                matched_pattern = None
                
                for field_pat in field_patterns:
                    # First try exact matching
                    for value_pat in value_patterns:
                        patterns = [
                            rf'{field_pat}\s*[:：]\s*{re.escape(value_pat)}\b',      # "Radius: 1.5"
                            rf'{field_pat}\s*[:：]\s*{re.escape(value_pat)}\s',      # "Radius: 1.5 "
                            rf'{field_pat}\s+{re.escape(value_pat)}\b',              # "Radius 1.5"
                            rf'{field_pat}\s*[:：]?\s*{re.escape(value_pat)}\b',     # "Radius1.5" 或 "Radius :1.5"
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
                    if not field_matched and isinstance(expected_value, float):
                        for base_val in value_patterns[:1]:  # use base value only
                            # Match "value + optional single noise character"
                            # e.g.: 1.5, 1.51, 1.5I, 1.5l, 1.5|, 1.5i, 1.56 etc.
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

    def check_polyhedral_style(self, style_number: int) -> Dict[str, Any]:
        """
        检查 Polyhedral style 是否设置为指定的样式编号
        
        Args:
            style_number: 期望的样式编号（1-6）
        """
        import cv2
        import numpy as np
        
        self._log(f"检查 Polyhedral style 是否为第 {style_number} 个", "INFO")
        
        result = {
            'function': 'check_polyhedral_style',
            'style_number': style_number,
            'score': 0,
            'max_score': 1,
            'details': {
                'polyhedral_detected': False,
                'selected_style': None,
                'detection_method': None,
                'debug_images': []
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            result['details']['detection_method'] = 'opencv_yellow_detection'
            
            # Read screenshot
            img = Image.open(screenshot)
            width, height = img.size
            
            # Crop the left region containing Properties dialog
            dialog_region = img.crop((
                0,                      # left
                int(height * 0.05),     # top (remove top title bar)
                int(width * 0.35),      # right (dialog occupies ~35% width)
                int(height * 0.95)      # bottom
            ))
            
            dialog_width, dialog_height = dialog_region.size
            
            # Crop Polyhedral style region inside the dialog
            poly_region = dialog_region.crop((
                int(dialog_width * 0.05),   # left
                int(dialog_height * 0.12),  # top (below Material)
                int(dialog_width * 0.95),   # right
                int(dialog_height * 0.28)   # bottom (above Planes)
            ))
            
            # Save cropped region for debugging
            debug_path = self.crop_cache_folder / f"polyhedral_region_step{i}.png"
            poly_region.save(debug_path)
            result['details']['debug_images'].append(str(debug_path))
            
            # Convert to OpenCV format
            img_array = np.array(poly_region)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # Detect yellow region (HSV)
            lower_yellow = np.array([20, 100, 100])
            upper_yellow = np.array([35, 255, 255])
            yellow_mask = cv2.inRange(img_hsv, lower_yellow, upper_yellow)
            
            # Morphological operation: remove noise
            kernel = np.ones((3, 3), np.uint8)
            yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
            yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
            
            # Save yellow mask
            mask_path = self.crop_cache_folder / f"yellow_mask_step{i}.png"
            cv2.imwrite(str(mask_path), yellow_mask)
            result['details']['debug_images'].append(str(mask_path))
            
            # Find contours of yellow regions
            contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                self._log(f"  [步骤 {i}] 未检测到黄色高亮区域", "DEBUG")
                continue
            
            # Find the largest yellow region (should be the selected style)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # Filter out too-small regions (may be noise)
            if area < 100:  # minimum area threshold
                self._log(f"  [步骤 {i}] 黄色区域太小，可能是噪点 (area={area})", "DEBUG")
                continue
            
            # Calculate center point of yellow region
            M = cv2.moments(largest_contour)
            if M["m00"] == 0:
                continue
            
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # Mark center point and contour on debug image
            debug_img = img_array.copy()
            cv2.circle(debug_img, (cx, cy), 8, (255, 0, 0), -1)  # blue dot
            cv2.drawContours(debug_img, [largest_contour], -1, (0, 255, 0), 2)  # green contour
            
            # Draw separator line (help determine index)
            region_width = poly_region.size[0]
            for j in range(1, 6):
                x = int(region_width * j / 6)
                cv2.line(debug_img, (x, 0), (x, poly_region.size[1]), (255, 255, 0), 1)
            
            marked_path = self.crop_cache_folder / f"polyhedral_marked_step{i}.png"
            cv2.imwrite(str(marked_path), cv2.cvtColor(debug_img, cv2.COLOR_RGB2BGR))
            result['details']['debug_images'].append(str(marked_path))
            
            # Determine style index based on x coordinate
            style_width = region_width / 6
            detected_style = int(cx / style_width) + 1
            detected_style = max(1, min(6, detected_style))  # clamp to range 1-6
            
            result['details']['selected_style'] = detected_style
            
            self._log(
                f"  [Step {i}] OpenCV detection: style #{detected_style} (center x={cx}, area={area:.0f})",
                "INFO"
            )
            
            if detected_style == style_number:
                result['score'] = 1
                self._log(f"✓ [步骤 {i}] 第 {style_number} 个样式已选中", "SUCCESS")
                return result
        
        # After traversing all steps
        if not result['details']['polyhedral_detected']:
            self._log(f"✗ 所有步骤中均未检测到 Polyhedral 相关弹窗", "FAIL")
        elif result['details']['selected_style']:
            self._log(
                f"✗ Detected style #{result['details']['selected_style']}, but expected style #{style_number}",
                "FAIL"
            )
        else:
            self._log(f"✗ 检测到 Polyhedral 弹窗，但无法确定选中的样式", "FAIL")
        
        if result['details']['debug_images']:
            self._log(f"调试图片已保存至: {self.crop_cache_folder}", "INFO")
        
        return result

    def _ocr_region_custom(self, screenshot_path: Path, left_percent: int = 0, right_percent: int = 100,
                        top_percent: int = 0, bottom_percent: int = 100) -> str:
        """
        对截图的自定义百分比区域进行 OCR 识别（带缓存）
        
        Args:
            left_percent: left boundary percentage (0-100)
            right_percent: 右边界百分比 (0-100)
            top_percent: 上边界百分比 (0-100)
            bottom_percent: lower boundary percentage (0-100)
        """
        cache_key = f"{screenshot_path.stem}_L{left_percent}R{right_percent}T{top_percent}B{bottom_percent}.txt"
        cache_path = self.ocr_cache_folder / cache_key
        
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Calculate crop region
        left = int(width * left_percent / 100)
        right = int(width * right_percent / 100)
        top = int(height * top_percent / 100)
        bottom = int(height * bottom_percent / 100)
        
        # Crop image
        img = img.crop((left, top, right, bottom))
        
        img_array = np.array(img)
        results = self.ocr_reader.readtext(img_array)
        text = "\n".join([result[1] for result in results])
        
        # Cache result
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return text

    def check_orientation_vector(self, expected_values: list) -> Dict[str, Any]:
        """
        检查 Orientation 对话框中的 Upward vector 是否设置为指定值
        
        Args:
            expected_values: expected vector value list [h, k, l], e.g. [2, 2, 2]
        """
        
        self._log(f"检查 Upward vector 是否为 {expected_values}", "INFO")
        
        result = {
            'function': 'check_orientation_vector',
            'expected_values': expected_values,
            'score': 0,
            'max_score': 1,
            'details': {
                'detected_values': None,
                'detection_method': 'ocr',
                'debug_images': []
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            # Read screenshot
            img = Image.open(screenshot)
            width, height = img.size
            
            # Crop Orientation dialog region (top-left)
            dialog_region = img.crop((
                0,                          # left
                0,                          # top
                int(width * 0.23),         # right
                int(height * 0.50)         # bottom
            ))
            
            dialog_width, dialog_height = dialog_region.size
            
            upward_region = dialog_region.crop((
                int(dialog_width * 0.5),    # left (skip h: k: l: labels)
                int(dialog_height * 0.52),  # top
                int(dialog_width * 0.92),   # right
                int(dialog_height * 0.8)    # bottom
            ))
            
            # Save cropped region for debugging
            debug_path = self.crop_cache_folder / f"upward_vector_region_step{i}.png"
            upward_region.save(debug_path)
            result['details']['debug_images'].append(str(debug_path))
            
            # Image preprocessing
            img_array = np.array(upward_region)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Enlarge image
            scale_factor = 3
            enlarged = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            
            # Binarization
            _, binary = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save preprocessed image
            processed_path = self.crop_cache_folder / f"upward_vector_processed_step{i}.png"
            cv2.imwrite(str(processed_path), binary)
            result['details']['debug_images'].append(str(processed_path))
            
            # Use pytesseract for OCR
            try:
                import pytesseract
                
                # OCR config: allow digits, minus sign, and letter O
                ocr_text = pytesseract.image_to_string(
                    binary,
                    config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789-oOhklvectrupwad: '
                )
                
                self._log(f"  [步骤 {i}] OCR 原始结果:\n{ocr_text}", "DEBUG")
                
                # Analyze row by row
                lines = ocr_text.split('\n')
                detected_numbers = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Skip lines containing headers
                    line_lower = line.lower()
                    if 'vector' in line_lower or 'upward' in line_lower:
                        self._log(f"  [步骤 {i}]   跳过标题行: '{line}'", "DEBUG")
                        continue
                    
                    # Replace o and O with 0
                    line_cleaned = line.replace('o', '0').replace('O', '0')
                    
                    # Extract numbers from this line
                    numbers_in_line = re.findall(r'-?\d+', line_cleaned)
                    
                    # Take only the first number from each line
                    if numbers_in_line:
                        detected_numbers.append(int(numbers_in_line[0]))
                        self._log(f"  [步骤 {i}]   提取: '{line}' -> {numbers_in_line[0]}", "DEBUG")
                
                self._log(f"  [步骤 {i}] 最终提取到的数字: {detected_numbers}", "DEBUG")
                
                # Need exactly 3 numbers
                if len(detected_numbers) >= 3:
                    # Take first three numbers as h, k, l
                    detected_values = detected_numbers[:3]
                    result['details']['detected_values'] = detected_values
                    
                    self._log(
                        f"  [Step {i}] Extracted Upward vector: h={detected_values[0]}, k={detected_values[1]}, l={detected_values[2]}",
                        "INFO"
                    )
                    
                    if detected_values == expected_values:
                        result['score'] = 1
                        self._log(f"✓ [步骤 {i}] Upward vector 设置正确: {detected_values}", "SUCCESS")
                        return result
                    else:
                        self._log(
                            f"  [Step {i}] Upward vector mismatch: expected {expected_values}, actual {detected_values}",
                            "DEBUG"
                        )
                else:
                    self._log(f"  [步骤 {i}] 提取的数字不足 3 个（需要 h, k, l），只有 {len(detected_numbers)} 个", "DEBUG")
                    
            except ImportError:
                self._log(f"  [步骤 {i}] pytesseract 未安装", "WARNING")
                break
            except Exception as e:
                self._log(f"  [步骤 {i}] OCR 出错: {str(e)}", "WARNING")
        
        # Final result
        if result['details']['detected_values']:
            self._log(
                f"✗ Upward vector error: expected {expected_values}, actual {result['details']['detected_values']}",
                "FAIL"
            )
        else:
            self._log(f"✗ 无法提取 Upward vector 值", "FAIL")
        
        if result['details']['debug_images']:
            self._log(f"调试图片: {self.crop_cache_folder}", "INFO")
        
        return result

    def check_lattice_plane(self, expected_hkl: list) -> Dict[str, Any]:
        """
        检查 Lattice Planes 对话框中是否添加了指定 hkl 的平面
        
        Args:
            expected_hkl: expected Miller indices [h, k, l], e.g. [1, 0, 0]
        """
        import re
        import cv2
        import numpy as np
        from PIL import Image
        
        self._log(f"检查是否添加了 hkl={expected_hkl} 的 Lattice Plane", "INFO")
        
        result = {
            'function': 'check_lattice_plane',
            'expected_hkl': expected_hkl,
            'score': 0,
            'max_score': 1,
            'details': {
                'detected_planes': [],
                'detection_method': 'ocr',
                'debug_images': []
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            # Read screenshot
            img = Image.open(screenshot)
            width, height = img.size
            
            # Crop Lattice Planes dialog region (top-left)
            dialog_region = img.crop((
                0,                          # left
                0,                          # top
                int(width * 0.31),         # right (dialog occupies ~31% width)
                int(height * 0.50)         # bottom
            ))
            
            dialog_width, dialog_height = dialog_region.size
            
            # Crop table region
            # Table is below the "Calculate the best plane" button
            # 根据截图：
            # - Horizontal: 3% from left to 90% from left of dialog (excluding right button area)
            # - Vertical: 62% to 78% of dialog height (table header and data rows)
            table_region = dialog_region.crop((
                int(dialog_width * 0.03),   # left
                int(dialog_height * 0.62),  # top
                int(dialog_width * 0.90),   # right
                int(dialog_height * 0.78)   # bottom
            ))
            
            # Save cropped region for debugging
            debug_path = self.crop_cache_folder / f"lattice_plane_table_step{i}.png"
            table_region.save(debug_path)
            result['details']['debug_images'].append(str(debug_path))
            
            # Image preprocessing
            img_array = np.array(table_region)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Enlarge image to improve recognition rate
            scale_factor = 3
            enlarged = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            
            # Binarization
            _, binary = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save preprocessed image
            processed_path = self.crop_cache_folder / f"lattice_plane_processed_step{i}.png"
            cv2.imwrite(str(processed_path), binary)
            result['details']['debug_images'].append(str(processed_path))
            
            # Use pytesseract for OCR
            try:
                import pytesseract
                
                # OCR: recognize table content
                ocr_text = pytesseract.image_to_string(
                    binary,
                    config='--psm 6 --oem 3'
                )
                
                self._log(f"  [步骤 {i}] OCR 识别结果:\n{ocr_text}", "DEBUG")
                
                # Analyze table row by row
                lines = ocr_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Skip table header
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ['no.', 'no', 'miller', 'indices']):
                        self._log(f"  [步骤 {i}]   跳过表头: '{line}'", "DEBUG")
                        continue
                    
                    # Replace characters that may be misrecognized
                    line_cleaned = line.replace('o', '0').replace('O', '0').replace('l', '1').replace('I', '1')
                    
                    # Extract all numbers from this line (may include negatives and decimals)
                    # Table format: No. | h | k | l | d | ...
                    numbers = re.findall(r'-?\d+(?:\.\d+)?', line_cleaned)
                    
                    self._log(f"  [步骤 {i}]   行 '{line}' -> 数字: {numbers}", "DEBUG")
                    
                    # At least 4 numbers needed: No, h, k, l
                    if len(numbers) >= 4:
                        try:
                            # Skip first number (row index), take next three as h, k, l
                            h = int(float(numbers[1]))
                            k = int(float(numbers[2]))
                            l_value = int(float(numbers[3]))
                            
                            detected_plane = [h, k, l_value]
                            result['details']['detected_planes'].append(detected_plane)
                            
                            self._log(f"  [步骤 {i}]   检测到平面: h={h}, k={k}, l={l_value}", "INFO")
                            
                            # Check whether matched
                            if detected_plane == expected_hkl:
                                result['score'] = 1
                                self._log(f"✓ [步骤 {i}] 找到匹配的 Lattice Plane: {detected_plane}", "SUCCESS")
                                return result
                        except (ValueError, IndexError) as e:
                            self._log(f"  [步骤 {i}]   解析数字失败: {e}", "DEBUG")
                            continue
                
                if result['details']['detected_planes']:
                    self._log(
                        f"  [Step {i}] Detected {len(result['details']['detected_planes'])} planes, but none matching {expected_hkl}",
                        "DEBUG"
                    )
                else:
                    self._log(f"  [步骤 {i}] 表格为空或无法识别", "DEBUG")
                    
            except ImportError:
                self._log(f"  [步骤 {i}] pytesseract 未安装", "WARNING")
                break
            except Exception as e:
                self._log(f"  [步骤 {i}] OCR 出错: {str(e)}", "WARNING")
        
        # Final result
        if result['details']['detected_planes']:
            self._log(
                f"✗ Plane with hkl={expected_hkl} not found. Detected planes: {result['details']['detected_planes']}",
                "FAIL"
            )
        else:
            self._log(f"✗ 未检测到任何 Lattice Plane", "FAIL")
        
        if result['details']['debug_images']:
            self._log(f"调试图片: {self.crop_cache_folder}", "INFO")
        
        return result

    def check_boundary_settings(self, **kwargs) -> Dict[str, Any]:
        """
        检查Boundary设置（分数坐标范围）
        
        Args:
            **kwargs: settings, e.g. y_max=2, z_max=2
        """
        import re
        import cv2
        import numpy as np
        from PIL import Image
        
        self._log(f"检查Boundary设置: {kwargs}", "INFO")
        
        result = {
            'function': 'check_boundary_settings',
            'expected_settings': kwargs,
            'score': 0,
            'max_score': 1,
            'details': {
                'boundary_detected': False,
                'settings_matched': {},
                'detected_values': {},
                'debug_images': []
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            # Read screenshot
            img = Image.open(screenshot)
            width, height = img.size
            
            # Crop Boundary dialog region (top-left)
            dialog_region = img.crop((
                0,                          # left
                0,                          # top
                int(width * 0.38),         # right
                int(height * 0.65)         # bottom
            ))
            
            dialog_width, dialog_height = dialog_region.size
            
            # Crop "Ranges of fractional coordinates" region
            ranges_region = dialog_region.crop((
                int(dialog_width * 0.03),   # left
                int(dialog_height * 0.08),  # top
                int(dialog_width * 0.97),   # right
                int(dialog_height * 0.32)   # bottom
            ))
            
            # Save cropped region for debugging
            debug_path = self.crop_cache_folder / f"boundary_region_step{i}.png"
            ranges_region.save(debug_path)
            result['details']['debug_images'].append(str(debug_path))
            
            # Image preprocessing
            img_array = np.array(ranges_region)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Enlarge image
            scale_factor = 3
            enlarged = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            
            # Binarization
            _, binary = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save preprocessed image
            processed_path = self.crop_cache_folder / f"boundary_processed_step{i}.png"
            cv2.imwrite(str(processed_path), binary)
            result['details']['debug_images'].append(str(processed_path))
            
            # Use pytesseract for OCR
            try:
                import pytesseract
                
                # OCR recognition
                ocr_text = pytesseract.image_to_string(
                    binary,
                    config='--psm 6 --oem 3'
                )
                
                # Replace common misrecognized characters
                ocr_text = ocr_text.replace('o', '0').replace('O', '0').replace('l', '1').replace('I', '1')
                
                self._log(f"  [步骤 {i}] OCR 识别结果:\n{ocr_text}", "DEBUG")
                
                # Check if this is a Boundary dialog
                if 'range' in ocr_text.lower() or 'fractional' in ocr_text.lower() or 'coordinate' in ocr_text.lower():
                    result['details']['boundary_detected'] = True
                    self._log(f"  [步骤 {i}] 检测到 Boundary 对话框", "DEBUG")
                else:
                    self._log(f"  [步骤 {i}] 未检测到 Boundary 对话框", "DEBUG")
                    continue
                
                # Check each setting item
                all_matched = True
                
                for key, expected_value in kwargs.items():
                    # Parse key, e.g. "y_max" -> coordinate='y', type='max'
                    # Supported formats: x_min, x_max, y_min, y_max, z_min, z_max
                    match = re.match(r'([xyz])_(min|max)', key)
                    if not match:
                        self._log(f"  [步骤 {i}] 无效的参数名: {key}", "WARNING")
                        result['details']['settings_matched'][key] = False
                        all_matched = False
                        continue
                    
                    coordinate = match.group(1)  # x, y, or z
                    min_or_max = match.group(2)  # min or max
                    
                    # Find the corresponding value in OCR text
                    # Match pattern: x(min) = number or xmin = number
                    patterns = [
                        rf'{coordinate}\s*\(\s*{min_or_max}\s*\)\s*=\s*(-?\d+(?:\.\d+)?)',
                        rf'{coordinate}\s*{min_or_max}\s*=\s*(-?\d+(?:\.\d+)?)',
                    ]
                    
                    detected_value = None
                    for pattern in patterns:
                        search_match = re.search(pattern, ocr_text, re.IGNORECASE)
                        if search_match:
                            detected_value = float(search_match.group(1))
                            break
                    
                    if detected_value is not None:
                        result['details']['detected_values'][key] = detected_value
                        
                        # Compare values (consider floating point error)
                        if abs(detected_value - float(expected_value)) < 0.01:
                            result['details']['settings_matched'][key] = True
                            self._log(f"  [步骤 {i}] ✓ {key}: {detected_value} (期望 {expected_value})", "DEBUG")
                        else:
                            result['details']['settings_matched'][key] = False
                            all_matched = False
                            self._log(f"  [步骤 {i}] ✗ {key}: {detected_value} (期望 {expected_value})", "DEBUG")
                    else:
                        result['details']['settings_matched'][key] = False
                        all_matched = False
                        self._log(f"  [步骤 {i}] ✗ {key}: 未检测到", "DEBUG")
                
                # If all settings match
                if all_matched and result['details']['boundary_detected']:
                    result['score'] = 1
                    self._log(f"✓ [步骤 {i}] Boundary 设置完全匹配", "SUCCESS")
                    return result
                
            except ImportError:
                self._log(f"  [步骤 {i}] pytesseract 未安装", "WARNING")
                break
            except Exception as e:
                self._log(f"  [步骤 {i}] OCR 出错: {str(e)}", "WARNING")
        
        # Final result
        if not result['details']['boundary_detected']:
            self._log(f"✗ 未检测到 Boundary 对话框", "FAIL")
        else:
            unmatched = [k for k, v in result['details']['settings_matched'].items() if not v]
            if unmatched:
                self._log(f"✗ Boundary 设置不匹配。未匹配项: {unmatched}", "FAIL")
                self._log(f"  期望值: {kwargs}", "FAIL")
                self._log(f"  检测值: {result['details']['detected_values']}", "FAIL")
            else:
                self._log(f"✗ Boundary 设置检查失败", "FAIL")
        
        if result['details']['debug_images']:
            self._log(f"调试图片: {self.crop_cache_folder}", "INFO")
        
        return result

    def check_bonds_cleared(self) -> Dict[str, Any]:
        import re
        
        self._log("检查 Bonds 表格是否被清空", "INFO")
        
        result = {
            'function': 'check_bonds_cleared',
            'score': 0,
            'max_score': 1,
            'details': {
                'initial_bonds_found': False,
                'bonds_cleared': False,
                'initial_step': None,
                'cleared_step': None,
                'initial_value_count': 0,
                'final_value_count': 0,
                'characteristic_value': '3.39412',
                'detection_method': 'value_occurrence_count'
            }
        }
        
        initial_step_with_bonds = None
        initial_count = 0
        
        for i, screenshot in enumerate(self.screenshots):
            # Step 1: Detect title - confirm dialog exists
            title_text = self._ocr_region(screenshot, "top5%")
            if 'bonds' not in title_text.lower():
                continue
            
            # Step 2: Detect content
            table_text = self._ocr_region(screenshot, "top50%")
            
            # Step 3: Count "3.39412" occurrences
            # Method 1: exact match
            count = table_text.count('3.39412')
            
            # Method 2: if exact match fails, try fault-tolerant matching (allow OCR errors)
            if count == 0:
                pattern = r'3\.3941[0-9]'
                matches = re.findall(pattern, table_text)
                count = len(matches)
            
            self._log(f"  [步骤 {i:02d}] '3.39412' 出现 {count} 次", "DEBUG")
            
            # Step 4: State decision
            if count >= 2:
                # Bond state (input box + table)
                if initial_step_with_bonds is None:
                    initial_step_with_bonds = i
                    initial_count = count
                    result['details']['initial_bonds_found'] = True
                    result['details']['initial_step'] = i
                    result['details']['initial_value_count'] = count
                    self._log(
                        f"  [Step {i:02d}] Bonds table has bonds, '3.39412' appears {count} times", 
                        "INFO"
                    )
            
            elif initial_step_with_bonds is not None and count == 1:
                # Clear state (input box only)
                result['details']['bonds_cleared'] = True
                result['details']['cleared_step'] = i
                result['details']['final_value_count'] = count
                result['score'] = 1
                self._log(
                    f"✓ [Step {i:02d}] Bonds table cleared", 
                    "SUCCESS"
                )
                self._log(f"  '3.39412' 出现次数: {initial_count} → {count}", "INFO")
                self._log(f"  （{count} 次 = 仅在 Max. length 输入框中）", "INFO")
                return result
        
        # Final decision
        if not result['details']['initial_bonds_found']:
            self._log("✗ 未检测到 Bonds 弹窗或表格始终为空", "FAIL")
        else:
            self._log(
                f"✗ Bonds table not cleared ('3.39412' always appears {initial_count} times)", 
                "FAIL"
            )
        
        return result

    def check_atom_coordinates_in_edit_data(self, atom_label: str, expected_coords: List[float]) -> Dict[str, Any]:
        import re
        from PIL import Image
        
        self._log(f"检查 {atom_label} 的坐标是否为 {expected_coords}", "INFO")
        
        result = {
            'function': 'check_atom_coordinates_in_edit_data',
            'atom_label': atom_label,
            'expected_coords': expected_coords,
            'score': 0,
            'max_score': 1,
            'details': {
                'edit_data_detected': False,
                'coordinates_detected': False,
                'detected_coords': None,
                'debug_images': []
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            # Step 1: Detect title
            title_text = self._ocr_region(screenshot, "top5%")
            if 'edit data' not in title_text.lower():
                continue
            
            result['details']['edit_data_detected'] = True
            
            # Step 2: Detect content and clean up OCR misrecognition
            table_text = self._ocr_region(screenshot, "top50%")
            
            # Clean up common misrecognitions
            table_text_cleaned = table_text.replace('o', '0').replace('O', '0')
            # Note: cannot globally replace l → 1, because "Cl" would become "C1"
            
            # Save debug image
            img = Image.open(screenshot)
            width, height = img.size
            table_region = img.crop((0, 0, int(width * 0.60), int(height * 0.70)))
            debug_path = self.crop_cache_folder / f"edit_data_{atom_label}_step{i}.png"
            table_region.save(debug_path)
            result['details']['debug_images'].append(str(debug_path))
            
            # Step 3: Split by line
            lines_original = table_text.split('\n')
            lines_cleaned = table_text_cleaned.split('\n')
            
            # Step 4: Find index of target atom
            atom_indices = []
            for idx, (original_line, cleaned_line) in enumerate(zip(lines_original, lines_cleaned)):
                line_stripped = original_line.strip()
                
                # Skip empty lines
                if not line_stripped:
                    continue
                
                # Skip table header
                if any(kw in line_stripped.lower() for kw in ['atom', 'label', 'charge', 'coordinates', 'occ.', 'uiso', 'no.', 'symbol', 'phase', 'unit cell']):
                    continue
                
                # Check if this is the target atom row
                # Method: must exactly match atom symbol (e.g. "Na" or "Cl"), not labels (Na0, Cl1)
                # Labels may be variants like Na0, NaO, Cl1, Cll etc.
                if line_stripped == atom_label:
                    atom_indices.append(idx)
                    self._log(f"  [步骤 {i:02d}] 找到原子 '{atom_label}' 在行 {idx}", "DEBUG")
            
            # Step 5: For each found atom position, search forward for coordinates
            for atom_idx in atom_indices:
                self._log(f"  [步骤 {i:02d}] 从行 {atom_idx} 开始向后查找坐标", "DEBUG")
                
                # Collect values going forward (using cleaned text)
                coords_found = []
                for offset in range(1, min(15, len(lines_cleaned) - atom_idx)):
                    next_line_cleaned = lines_cleaned[atom_idx + offset].strip()
                    next_line_original = lines_original[atom_idx + offset].strip()
                    
                    # Skip empty lines
                    if not next_line_cleaned:
                        continue
                    
                    # Skip table header and other keywords
                    if any(kw in next_line_original.lower() for kw in ['atom', 'label', 'occ.', 'uiso', 'new', 'delete', 'clear']):
                        continue
                    
                    # Check if this is a coordinate value
                    # Match: 0.000000, 1.000000, 0.500000 etc. (6 decimal places)
                    coord_match = re.match(r'^([01]\.\d{6})$', next_line_cleaned)
                    if coord_match:
                        coords_found.append(coord_match.group(1))
                        self._log(f"  [步骤 {i:02d}]   行 {atom_idx + offset}: '{next_line_original}' → 坐标值 {coord_match.group(1)}", "DEBUG")
                        
                        # Stop after collecting 3 coordinates
                        if len(coords_found) >= 3:
                            break
                    else:
                        # Record non-coordinate lines (for debugging)
                        self._log(f"  [步骤 {i:02d}]   行 {atom_idx + offset}: '{next_line_original}' (非坐标)", "DEBUG")
                        
                        # If some coordinates already found but encounter non-numeric line, likely table separator
                        # Continue searching but not too far
                        if len(coords_found) > 0 and offset > 8:
                            break
                
                self._log(f"  [步骤 {i:02d}] 提取的坐标: {coords_found}", "INFO")
                
                # Step 6: Verify coordinates
                if len(coords_found) >= 3:
                    try:
                        x = float(coords_found[0])
                        y = float(coords_found[1])
                        z = float(coords_found[2])
                        
                        detected_coords = [x, y, z]
                        result['details']['detected_coords'] = detected_coords
                        result['details']['coordinates_detected'] = True
                        
                        self._log(f"  [步骤 {i:02d}] 检测到 {atom_label} 坐标: {detected_coords}", "INFO")
                        
                        # Compare coordinates
                        coords_match = all(
                            abs(detected - expected) < 0.000001
                            for detected, expected in zip(detected_coords, expected_coords)
                        )
                        
                        if coords_match:
                            result['score'] = 1
                            self._log(f"✓ [步骤 {i:02d}] {atom_label} 坐标匹配: {detected_coords}", "SUCCESS")
                            return result
                        else:
                            self._log(
                                f"  [Step {i:02d}] Coordinates mismatch: expected {expected_coords}, actual {detected_coords}",
                                "DEBUG"
                            )
                    except (ValueError, IndexError) as e:
                        self._log(f"  [步骤 {i:02d}] 解析失败: {e}", "DEBUG")
                        continue
        
        # Final result
        if not result['details']['edit_data_detected']:
            self._log(f"✗ 未检测到 Edit Data 弹窗", "FAIL")
        elif not result['details']['coordinates_detected']:
            self._log(f"✗ 未检测到 {atom_label} 的坐标", "FAIL")
        elif result['details']['detected_coords']:
            self._log(
                f"✗ {atom_label} coordinate error: expected {expected_coords}, actual {result['details']['detected_coords']}",
                "FAIL"
            )
        else:
            self._log(f"✗ 无法提取 {atom_label} 的坐标", "FAIL")
        
        if result['details']['debug_images']:
            self._log(f"调试图片: {self.crop_cache_folder}", "INFO")
        
        return result

    def check_multiple_lattice_planes(self, expected_count: int) -> Dict[str, Any]:
        """
        检查 Lattice Planes 弹窗中添加的晶面数量
        
        检测逻辑:
        1. Detect top 5% to confirm Lattice Planes dialog exists
        2. Detect table content in top 50%
        3. Count row numbers under No. column
        
        表格格式:
        No.   h    k    l    d (Å)
        1     1    1    0    2.76169
        2     1    1    0    2.76169
        3     1    1    0    2.76169
        
        Args:
            expected_count: expected crystal plane count
        """
        import re
        
        self._log(f"检查 Lattice Planes 表格中的晶面数量（期望: {expected_count}）", "INFO")
        
        result = {
            'function': 'check_multiple_lattice_planes',
            'expected_count': expected_count,
            'score': 0,
            'max_score': 1,
            'details': {
                'lattice_planes_detected': False,
                'detected_count': 0,
                'detected_at_step': None,
                'row_numbers': []
            }
        }
        
        for i, screenshot in enumerate(self.screenshots):
            # Step 1: Detect title - confirm Lattice Planes dialog exists
            title_text = self._ocr_region(screenshot, "top5%")
            if 'lattice' not in title_text.lower() and 'plane' not in title_text.lower():
                continue
            
            result['details']['lattice_planes_detected'] = True
            
            # Step 2: Detect table content in top 50%
            table_text = self._ocr_region(screenshot, "top50%")
            
            # Clean up OCR misrecognition
            table_text_cleaned = table_text.replace('o', '0').replace('O', '0')
            
            self._log(f"  [步骤 {i:02d}] Lattice Planes 弹窗存在，开始检测表格", "DEBUG")
            
            # Step 3: Find row numbers under No. column
            # Table format:
            # No.   h    k    l    d (Å)
            # 2     1    1    0    2.76169
            # 3     1    1    0    2.76169
            
            lines = table_text_cleaned.split('\n')
            row_numbers = []
            
            found_table_header = False
            for line in lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # Find table header (No. h k l d)
                if 'no.' in line_lower or ('h' in line_lower and 'k' in line_lower and 'l' in line_lower):
                    found_table_header = True
                    self._log(f"  [步骤 {i:02d}] 找到表头: {line_stripped}", "DEBUG")
                    continue
                
                # If header already found, start looking for data rows
                if found_table_header:
                    # Match data rows: starting with a number (row index)
                    # Format: "2     1    1    0    2.76169"
                    # Or: "3     1    1    0    2.76169"
                    match = re.match(r'^(\d+)\s+', line_stripped)
                    if match:
                        row_num = int(match.group(1))
                        # Filter out possible misrecognitions (e.g. 1, 100 or other unreasonable values)
                        # Crystal plane row index usually starts from 2 (1 may be the default)
                        if row_num >= 1 and row_num <= 100:
                            if row_num not in row_numbers:
                                row_numbers.append(row_num)
                                self._log(f"  [步骤 {i:02d}] 找到晶面行: No.{row_num}", "DEBUG")
            
            # Step 4: Count and decide
            if len(row_numbers) > 0:
                result['details']['detected_count'] = len(row_numbers)
                result['details']['row_numbers'] = sorted(row_numbers)
                result['details']['detected_at_step'] = i
                
                self._log(f"  [步骤 {i:02d}] 检测到 {len(row_numbers)} 个晶面: {result['details']['row_numbers']}", "INFO")
                
                # Determine if matched
                if len(row_numbers) == expected_count:
                    result['score'] = 1
                    self._log(f"✓ [步骤 {i:02d}] 晶面数量匹配: {len(row_numbers)} 个", "SUCCESS")
                    return result
                else:
                    self._log(
                        f"  [Step {i:02d}] Count mismatch: expected {expected_count}, actual {len(row_numbers)}",
                        "DEBUG"
                    )
        
        # Final result
        if not result['details']['lattice_planes_detected']:
            self._log("✗ 未检测到 Lattice Planes 弹窗", "FAIL")
        elif result['details']['detected_count'] == 0:
            self._log("✗ 未检测到任何晶面数据行", "FAIL")
        else:
            self._log(
                f"✗ Crystal plane count mismatch: expected {expected_count}, actual {result['details']['detected_count']}",
                "FAIL"
            )
        
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
    "in1": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-13_Fe.cif'}},
        {'function': 'check_standard_orientation', 'args': {'similarity_threshold': 0.9}}
    ],
    
    "in2": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-30_Cu.cif'}},
        {'function': 'check_rotation_90_up', 'args': {'similarity_threshold': 0.95}}
    ],
    
    "in3": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-66_C.cif'}},
        {'function': 'check_translation', 'args': {
            'direction': 'right', 
            'units': 400,
            'similarity_threshold': 0.9
        }}
    ],
    
    "in4": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-81_Au.cif'}},
        {'function': 'check_style_change', 'args': {'target_style': 'Wireframe'}}
    ],
    
    "in5": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-804_GaN.cif'}},
        {'function': 'check_atom_info_dialog', 'args': {'atom_type': 'Ga'}}
    ],
    
    "in6": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-804_GaN.cif'}},
        {'function': 'check_atom_info_dialog', 'args': {'atom_type': 'N'}},
        {'function': 'check_atom_deletion', 'args': {}}
    ],
    
    "in7": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-13_Fe.cif'}},
        {
            'function': 'check_bond_display', 
            'args': {
                'possible_pairs': [
                    ['Fe1', 'Fe1'],
                    ['Fe0', 'Fe0']
                ]
            }
        }
    ],
    
    "in8": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-804_GaN.cif'}},
        {'function': 'check_zoom', 'args': {}}
    ],
    
    "in9": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-149_Si.cif'}},
        {'function': 'check_atom_deletion', 'args': {}}
    ],
    
    "in10": [
    {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-66_C.cif'}},
    {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Properties', 'filename': 'mp-66_C.cif'}},
    {'function': 'check_axes_toggle', 'args': {}}
    ],
    
    "in11": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-2534_GaAs.cif'}},
        {'function': 'check_atom_deletion', 'args': {}}
    ],
    
    # Usage in task config:
    "in12": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-1265_MgO.cif'}},
        {'function': 'check_dialog_opened', 'args': {
            'title_keyword': 'Properties', 
            'field_checks': {'Radius': 1.5}  # 检查 Radius 字段是否为 1.5
        }}
    ],
    
    "in13": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-804_GaN.cif'}},
        {'function': 'check_style_change', 'args': {'target_style': 'Polyhedral'}},
        {'function': 'check_axes_display_off', 'args': {}},
        {'function': 'check_polyhedral_style', 'args': {'style_number': 4}}
    ],
    
    "in14": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-1265_MgO.cif'}},
        {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Orientation'}},
        {'function': 'check_orientation_vector', 'args': {'expected_values': [3, 3, 3]}}
    ],
    
    "in15": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-1265_MgO.cif'}},
        {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Lattice Planes'}},
        {'function': 'check_lattice_plane', 'args': {'expected_hkl': [1, 2, 2]}}
    ],
    
    "in16": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-1143'}},
        {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Boundary'}},
        {'function': 'check_boundary_settings', 'args': {'y_max': 2, 'z_max': 2}}
    ],
    
    "in17": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-804_GaN.cif'}},
        {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Boundary'}},
        {'function': 'check_boundary_settings', 'args': {'y_max': 2}},
        {'function': 'check_style_change', 'args': {'target_style': 'Polyhedral'}},
        {'function': 'check_polyhedral_style', 'args': {'style_number': 3}}
    ],
    
    "in18": [
    {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-22862_NaCl.cif'}},
    {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Bonds'}},
    {'function': 'check_bonds_cleared', 'args': {}},
    {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Edit Data'}},
    {'function': 'check_atom_coordinates_in_edit_data', 'args': {'atom_label': 'Na', 'expected_coords': [1.0, 1.0, 1.0]}},
    {'function': 'check_atom_coordinates_in_edit_data', 'args': {'atom_label': 'Cl', 'expected_coords': [1.0, 0.5, 0.5]}}
    ],
    
    "in19": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-149_Si.cif'}},
        {'function': 'check_boundary_settings', 'args': {'x_max': 2, 'y_max': 2, 'z_max': 2}},
        {'function': 'check_properties_radius', 'args': {'radius_value': 0.8}},
        {'function': 'check_properties_radius', 'args': {'radius_value': 0.15}}
    ],
    
    "in20": [
        {'function': 'check_file_opened', 'args': {'expected_filename': 'mp-2534_GaAs.cif'}},
        {'function': 'check_boundary_settings', 'args': {'x_min': -0.5, 'x_max': 1.5, 'y_min': -0.5, 'y_max': 1.5}},
        {'function': 'check_dialog_opened', 'args': {'title_keyword': 'Lattice Planes'}},
        {'function': 'check_multiple_lattice_planes', 'args': {'expected_count':2}}
    ]
}


# ============ MAIN FUNCTION ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='VESTA 评估系统 v1.2 修复版')
    parser.add_argument('folder', type=str, help='Path to screenshot folder')
    parser.add_argument('task', type=str, help='Task name')
    parser.add_argument('--reference', type=str, help='标准取向参考图片路径',
                       default=None)
    parser.add_argument('--rotation-90-ref', type=str, help='旋转90度参考图片路径',
                       default=None, dest='rotation_90_ref')
    parser.add_argument('--translation_reference', type=str, help='平移400参考图片路径',
                       default=None, dest='translation_reference')
    parser.add_argument('--zomm_100_reference', type=str, help='放大100参考图片路径',
                       default=None, dest='zomm_100_reference')
    
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"VESTA 评估系统 v1.2 修复版")
    print(f"{'='*60}\n")
    
    folder_path = Path(args.folder).resolve()
    
    if not folder_path.exists():
        print(f"❌ 错误: 文件夹不存在: {folder_path}")
        return
    
    print(f"✓ 文件夹: {folder_path}")
    print(f"✓ 任务: {args.task}")
    if args.reference:
        print(f"✓ 标准取向参考图片: {args.reference}")
    if args.rotation_90_ref:
        print(f"✓ 旋转90度参考图片: {args.rotation_90_ref}")
    if args.translation_reference:
        print(f"✓ 平移400参考图片: {args.translation_reference}")
    if args.zomm_100_reference:
        print(f"✓ 平移400参考图片: {args.zomm_100_reference}")
    print()
    
    if args.task not in TASK_CONFIGS:
        print(f"❌ 未找到任务 '{args.task}'")
        print(f"\n可用任务:")
        for task_name in TASK_CONFIGS.keys():
            print(f"  - {task_name}")
        return
    
    try:
        evaluator = VESTAEvaluator(str(folder_path), args.reference, args.rotation_90_ref, args.translation_reference, args.zomm_100_reference)
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