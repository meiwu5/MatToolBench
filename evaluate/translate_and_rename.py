"""
Translate all Chinese text to English and rename task keys (简单/中等/复杂 → in1-in20)
in all evaluator and test files under evaluate/
"""
import os
import re
import json
from pathlib import Path

BASE = Path(__file__).parent

# ============================================================
# Task key mappings per tool
# ============================================================
TOOL_TASK_MAPS = {
    # avantage, dm, vesta: 10 simple, 5 medium, 5 complex
    'avantage': {
        **{f'简单-{i}': f'in{i}' for i in range(1, 11)},
        **{f'中等-{i}': f'in{10+i}' for i in range(1, 6)},
        **{f'复杂-{i}': f'in{15+i}' for i in range(1, 6)},
    },
    'dm': {
        **{f'简单-{i}': f'in{i}' for i in range(1, 11)},
        **{f'中等-{i}': f'in{10+i}' for i in range(1, 6)},
        **{f'复杂-{i}': f'in{15+i}' for i in range(1, 6)},
    },
    'vesta': {
        **{f'简单-{i}': f'in{i}' for i in range(1, 11)},
        **{f'中等-{i}': f'in{10+i}' for i in range(1, 6)},
        **{f'复杂-{i}': f'in{15+i}' for i in range(1, 6)},
    },
    # ms: 9 simple, 6 medium, 5 complex
    'ms': {
        **{f'简单-{i}': f'in{i}' for i in range(1, 10)},
        **{f'中等-{i}': f'in{9+i}' for i in range(1, 7)},
        **{f'复杂-{i}': f'in{15+i}' for i in range(1, 6)},
    },
    # jade: 8 simple, 7 medium, 6 complex
    'jade': {
        **{f'简单-{i}': f'in{i}' for i in range(1, 9)},
        **{f'中等-{i}': f'in{8+i}' for i in range(1, 8)},
        **{f'复杂-{i}': f'in{15+i}' for i in range(1, 7)},
    },
}

# ============================================================
# TRAJECTORY_INSTRUCTIONS translations (for test files)
# ============================================================
AVANTAGE_INSTRUCTIONS = {
    "in1": "in1: Open ADVANTAGE software, import Avantage/C1s Scan.VGD",
    "in2": "in2: Open ADVANTAGE software, import four files: Avantage/C1s Scan.VGD, Avantage/O1s Scan.VGD, Avantage/Zn2p Scan.VGD, and Avantage/XPS Survey.VGD",
    "in3": "in3: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, double-click to zoom in the C1s Scan image then double-click to zoom out",
    "in4": "in4: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, select stacked graph mode in Display Modes to show the selected data",
    "in5": "in5: Open ADVANTAGE software, import Avantage/XPS Survey.VGD, copy the spectrum to window B",
    "in6": "in6: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, add background using smart parameters",
    "in7": "in7: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, adjust X-Axis font size to 20",
    "in8": "in8: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, set X-Axis title color to Red",
    "in9": "in9: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, reverse the X-axis energy axis",
    "in10": "in10: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, adjust grid properties to Rows=3, Columns=3",
    "in11": "in11: Open ADVANTAGE software, import Avantage/Zn2p Scan.VGD, perform automatic peak fitting",
    "in12": "in12: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, perform charge correction, shift by amount +0.14 eV",
    "in13": "in13: Open ADVANTAGE software, import Avantage/XPS Survey.VGD, smooth the spectrum, change FWHM to 2.115",
    "in14": "in14: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, smart-add O1s peak, set background average width to 20 eV",
    "in15": "in15: Open ADVANTAGE software, import Avantage/C1s Scan.VGD and Avantage/XPS Survey.VGD, select and arrange these two spectra vertically",
    "in16": "in16: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, add and lock Shirley baseline, perform charge correction by +0.14 eV",
    "in17": "in17: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, smart-add baseline and perform automatic peak fitting",
    "in18": "in18: Open ADVANTAGE software, import Avantage/C1s Scan.VGD, copy to window B, add 3333 to window B values, arrange vertically",
    "in19": "in19: Open ADVANTAGE software, import Avantage/O1s Scan.VGD, add Peak (start 545, end 540 eV), lock and then fit",
    "in20": "in20: Open ADVANTAGE software, import C1s, O1s, and Survey Scan, smart-add peaks for C1s, apply charge shift of +1360 eV to all spectra",
}

JADE_INSTRUCTIONS = {
    "in1": "in1: Import 'Jade/WRT-ZSX-5.txt' using Jade",
    "in2": "in2: Open 'Jade/XRD4.xrdml' with Jade, perform peak finding with default parameters",
    "in3": "in3: Open 'Jade/XRD1.xrdml' with Jade, perform background subtraction with default parameters",
    "in4": "in4: Open 'Jade/XRD4.xrdml' with Jade, apply smoothing once",
    "in5": "in5: Open 'Jade/XRD4.xrdml' with Jade, apply smoothing once and background subtraction",
    "in6": "in6: Open Jade/XRD1.xrdml with Jade, switch x-axis from 2-theta to d-spacing, then back to 2-theta",
    "in7": "in7: Open Jade/WRT-ZSX-5.txt with Jade, select Zoom from the menu bar",
    "in8": "in8: Open Jade/WRT-ZSX-5.txt with Jade, add two peaks",
    "in9": "in9: Open Jade/XRD1.xrdml with Jade, switch x-axis from 2-theta to d-spacing, add two peaks, then switch back to 2-theta",
    "in10": "in10: Open 'Jade/XRD1.xrdml' with Jade, perform peak finding with default parameters, export the peak report to the desktop as 'WRT_peak.pid'",
    "in11": "in11: Open 'Jade/WRT-ZSX-5.txt' with Jade, perform Whole Pattern Fitting and Rietveld Refinement, save the output file locally as 'WRT_refine.raw'",
    "in12": "in12: Open 'Jade/XRD2.xrdml' with Jade, perform profile fitting, initialize then refine, and print the fitting report to the desktop as 'XRD2.pdf'",
    "in13": "in13: Open 'Jade/WRT-ZSX-5.txt' with Jade, perform peak finding, print the zoom window image to the desktop as 'WRT_window.pdf'",
    "in14": "in14: Open Jade/'XRD1.xrdml' with Jade, perform full-spectrum theta angle correction using internal standard method, print the fitting report to the desktop as 'WRT_theta.pdf'",
    "in15": "in15: Open Jade/WRT-ZSX-5.txt with Jade, calculate d-spacing and Miller indices using Calc, print the report to the desktop as 'WRT_calc.pdf'",
    "in16": "in16: Open 'Jade/WRT-ZSX-5.txt' with Jade, remove background, analyze diffraction peaks and find the best matching phase from the database, export the PDF card to the desktop as 'WRT_PDF1.txt'",
    "in17": "in17: Open 'Jade/WRT-ZSX-5.txt' with Jade, remove background, search for Fe-containing phases (possibly with O element), return the best-matching iron-based oxide or iron-containing phase, save to desktop as 'WRT_Fe.txt'",
    "in18": "in18: Open 'Jade/WRT-ZSX-5.txt' with Jade, perform profile fitting, initialize then refine, print the fitting report to the desktop as 'WRT.pdf'",
    "in19": "in19: Open 'Jade/WRT-ZSX-5.txt' with Jade, apply smoothing once, remove background, find the best 2 matching phases from the database, export PDF cards to desktop as 'PDF1.txt' and 'PDF2.txt'",
    "in20": "in20: Open 'Jade/XRD4.xrdml' with Jade, apply smoothing once, perform profile fitting, initialize then refine, print the fitting report to the desktop as 'XRD4.pdf'",
}

# ============================================================
# Comprehensive Chinese → English string replacements
# Applied as exact string substitutions throughout files
# ============================================================
COMMON_REPLACEMENTS = [
    # ---- Module-level docstrings ----
    ('Avantage XPS 评估系统', 'Avantage XPS Evaluation System'),
    ('主要功能：评估 Avantage XPS 软件操作任务的完成情况', 'Main function: evaluate task completion for Avantage XPS software operations'),
    ('DigitalMicrograph 评估系统 - v1.0', 'DigitalMicrograph Evaluation System - v1.0'),
    ('用于评估DigitalMicrograph软件的操作任务完成情况', 'For evaluating task completion of DigitalMicrograph software operations'),
    ('基于OCR文本检测和图像分析', 'Based on OCR text detection and image analysis'),
    ('Jade XRD 评估系统 - 改进版 v2', 'Jade XRD Evaluation System - Improved v2'),
    ('主要改进：增强对 XRDAxrdml 等连写格式的识别', 'Main improvement: enhanced recognition of concatenated formats like XRDAxrdml'),
    ('Jade XRD 批量评估系统 v3', 'Jade XRD Batch Evaluation System v3'),
    ('Material Studio 评估系统 - v1.0', 'Material Studio Evaluation System - v1.0'),
    ('用于评估Material Studio软件的操作任务完成情况', 'For evaluating task completion of Material Studio software operations'),
    ('Material Studio 批量评估系统 (修复版)', 'Material Studio Batch Evaluation System (Fixed)'),
    ('VESTA 评估系统 - v1.2 修复版', 'VESTA Evaluation System - v1.2 Fixed'),
    ('用于评估VESTA晶体结构可视化软件的操作任务完成情况', 'For evaluating task completion of VESTA crystal structure visualization software'),
    ('Avantage XPS 批量评估系统', 'Avantage XPS Batch Evaluation System'),
    ('DigitalMicrograph 批量评估系统', 'DigitalMicrograph Batch Evaluation System'),
    ('用于批量运行 20×20=400 个评估实验并生成对比报告', 'For running 400 (20×20) evaluation experiments in batch and generating comparison reports'),
    # ---- Class docstrings ----
    ('Avantage XPS 任务评估器', 'Avantage XPS Task Evaluator'),
    ('DigitalMicrograph 任务评估器', 'DigitalMicrograph Task Evaluator'),
    ('Jade XRD 任务评估器', 'Jade XRD Task Evaluator'),
    ('Material Studio 任务评估器', 'Material Studio Task Evaluator'),
    ('VESTA 晶体结构可视化任务评估器', 'VESTA Crystal Structure Visualization Task Evaluator'),
    # ---- __init__ docstring params ----
    ('初始化评估器', 'Initialize the evaluator'),
    ('base_folder: 包含截图和accessibility tree文件的文件夹路径',
     'base_folder: path to the folder containing screenshots and accessibility tree files'),
    ("reference_images: 参考图片路径字典,格式如 {'ball_stick': 'path/to/image.png'}",
     "reference_images: reference image path dict, e.g. {'ball_stick': 'path/to/image.png'}"),
    # ---- FileNotFoundError ----
    ('"输入文件夹不存在: {self.base_folder}"', '"Input folder does not exist: {self.base_folder}"'),
    ('"输入文件夹不存在: {base_folder}"', '"Input folder does not exist: {base_folder}"'),
    # ---- Setup comments ----
    ('# 设置评估输出目录', '# Set up evaluation output directory'),
    ('# 创建评估输出目录', '# Create evaluation output directory'),
    ('# OCR缓存目录', '# OCR cache directory'),
    ('# 裁剪图片缓存目录', '# Cropped image cache directory'),
    ('# 裁剪图片缓存目录（用于视觉相似度比较）', '# Cropped image cache directory (for visual similarity comparison)'),
    ('# 标签文件夹（用于对比FFT等操作结果）', '# Label folder (for comparing FFT and other operation results)'),
    ('# 预处理：识别所有截图中的文件名', '# Preprocessing: identify filenames in screenshots'),
    ('# 预处理:识别所有截图中的文件名和窗口标题', '# Preprocessing: identify filenames and window titles in screenshots'),
    ('# 设置标准取向参考图片路径', '# Set reference image path for standard orientation'),
    ('# 设置旋转90度参考图片路径', '# Set reference image path for 90-degree rotation'),
    ('#设置平移400参考图片路径', '# Set reference image path for translation-400'),
    ('#设置放大100参考图片路径', '# Set reference image path for zoom-100'),
    ('# 设置参考图片路径', '# Set reference image paths'),
    ('# 准备参考图片的裁剪版本', '# Prepare cropped version of reference image'),
    ('# 准备旋转90度参考图片的裁剪版本', '# Prepare cropped version of 90-degree rotation reference image'),
    ('# 准备平移400裁剪版本', '# Prepare cropped version of translation-400 reference image'),
    ('# 准备放大100裁剪版本', '# Prepare cropped version of zoom-100 reference image'),
    # ---- print messages ----
    ('"✓ 创建评估输出目录: {self.evaluate_folder}"', '"✓ Created evaluation output directory: {self.evaluate_folder}"'),
    ('"✓ 创建OCR缓存目录: {self.ocr_cache_folder}"', '"✓ Created OCR cache directory: {self.ocr_cache_folder}"'),
    ('"✓ 创建裁剪图片缓存目录: {self.crop_cache_folder}"', '"✓ Created cropped image cache directory: {self.crop_cache_folder}"'),
    ('"✓ 加载了 {len(self.screenshots)} 张截图"', '"✓ Loaded {len(self.screenshots)} screenshots"'),
    ('"✓ 加载了 {len(self.ally_trees)} 个accessibility tree文件"', '"✓ Loaded {len(self.ally_trees)} accessibility tree files"'),
    # ---- _load_files docstring ----
    ('"""加载截图和accessibility tree文件"""', '"""Load screenshots and accessibility tree files"""'),
    # ---- _extract_step_number docstring ----
    ('"""从文件名中提取步骤编号"""', '"""Extract step number from filename"""'),
    # ---- _ocr_region ----
    ('def _ocr_region(self, screenshot_path: Path, region: str = "完整") -> str:',
     'def _ocr_region(self, screenshot_path: Path, region: str = "full") -> str:'),
    ('对图片的指定区域进行OCR识别（带缓存）', 'Perform OCR on the specified region of an image (with caching)'),
    ('"""对截图的指定区域进行OCR识别（带缓存）"""', '"""Perform OCR on the specified region of a screenshot (with caching)"""'),
    ('"""对截图的指定区域进行OCR识别(带缓存)"""', '"""Perform OCR on the specified region of a screenshot (with caching)"""'),
    ('screenshot_path: 截图路径', 'screenshot_path: path to the screenshot'),
    ('region: 区域名称（完整/顶部5%/顶部10%/底部5%/底部10%/左侧10%/右侧10%）',
     'region: region name (full/top5%/top10%/bottom5%/bottom10%/left10%/right10%)'),
    ('识别出的文本', 'recognized text'),
    ('# 检查缓存', '# Check cache'),
    ('# 加载图片并裁剪', '# Load and crop image'),
    ('# 根据区域裁剪图像', '# Crop image by region'),
    ('# 完整区域不需要裁剪', '# Full region: no cropping needed'),
    ('# 中心50%：从25%到75%的位置（上下左右各留25%）',
     '# center50%: from 25% to 75% (25% margin on each side)'),
    ('# OCR识别', '# OCR recognition'),
    ('# 保存到缓存', '# Save to cache'),
    # ---- Region names in if/elif ----
    ('if region == "顶部5%":', 'if region == "top5%":'),
    ('elif region == "顶部5%":', 'elif region == "top5%":'),
    ('if region == "顶部10%":', 'if region == "top10%":'),
    ('elif region == "顶部10%":', 'elif region == "top10%":'),
    ('if region == "顶部20%":', 'if region == "top20%":'),
    ('elif region == "顶部20%":', 'elif region == "top20%":'),
    ('if region == "顶部40%":', 'if region == "top40%":'),
    ('elif region == "顶部40%":', 'elif region == "top40%":'),
    ('if region == "顶部50%":', 'if region == "top50%":'),
    ('elif region == "顶部50%":', 'elif region == "top50%":'),
    ('if region == "底部5%":', 'if region == "bottom5%":'),
    ('elif region == "底部5%":', 'elif region == "bottom5%":'),
    ('if region == "底部10%":', 'if region == "bottom10%":'),
    ('elif region == "底部10%":', 'elif region == "bottom10%":'),
    ('if region == "底部20%":', 'if region == "bottom20%":'),
    ('elif region == "底部20%":', 'elif region == "bottom20%":'),
    ('if region == "底部30%":', 'if region == "bottom30%":'),
    ('elif region == "底部30%":', 'elif region == "bottom30%":'),
    ('if region == "左侧10%":', 'if region == "left10%":'),
    ('elif region == "左侧10%":', 'elif region == "left10%":'),
    ('if region == "左侧20%":', 'if region == "left20%":'),
    ('elif region == "左侧20%":', 'elif region == "left20%":'),
    ('if region == "左侧40%":', 'if region == "left40%":'),
    ('elif region == "左侧40%":', 'elif region == "left40%":'),
    ('if region == "右侧10%":', 'if region == "right10%":'),
    ('elif region == "右侧10%":', 'elif region == "right10%":'),
    ('if region == "中心50%":', 'if region == "center50%":'),
    ('elif region == "中心50%":', 'elif region == "center50%":'),
    # Region names as string literals in calls
    ('"完整"', '"full"'),
    ('"顶部5%"', '"top5%"'),
    ('"顶部10%"', '"top10%"'),
    ('"顶部20%"', '"top20%"'),
    ('"顶部40%"', '"top40%"'),
    ('"顶部50%"', '"top50%"'),
    ('"底部5%"', '"bottom5%"'),
    ('"底部10%"', '"bottom10%"'),
    ('"底部20%"', '"bottom20%"'),
    ('"底部30%"', '"bottom30%"'),
    ('"左侧10%"', '"left10%"'),
    ('"左侧20%"', '"left20%"'),
    ('"左侧40%"', '"left40%"'),
    ('"右侧10%"', '"right10%"'),
    ('"中心50%"', '"center50%"'),
    # ---- _log method ----
    ('def _log(self, message: str, level: str = "信息"):', 'def _log(self, message: str, level: str = "INFO"):'),
    ('"""记录日志"""', '"""Log a message"""'),
    ('"信息"', '"INFO"'),
    ('"调试"', '"DEBUG"'),
    ('"警告"', '"WARNING"'),
    ('"错误"', '"ERROR"'),
    # ---- _identify_files_in_screenshots ----
    ('"""预处理：识别所有截图中的文件名', '"""Preprocessing: identify filenames in all screenshots'),
    ('判定标准：同时出现文件名和 "Binding Energy"', 'Criterion: both filename and "Binding Energy" appear simultaneously'),
    ('同时存储规范化的文本用于后续的模糊匹配', 'Also stores normalized text for subsequent fuzzy matching'),
    ('self._log("开始预处理：识别所有截图中的文件名...", "信息")',
     'self._log("Starting preprocessing: identifying filenames in all screenshots...", "INFO")'),
    ('# OCR识别中心区域', '# OCR the center region'),
    ('# 规范化文本', '# Normalize text'),
    ('# 检查是否有 Binding Energy', '# Check for Binding Energy'),
    ('# 尝试提取所有文件名', '# Try to extract all filenames'),
    ('all_detected_files = set()  # 记录所有检测到的文件', 'all_detected_files = set()  # Record all detected files'),
    ('# 提取每个文件匹配到的实际规范化文本', '# Extract the matched normalized text for each file'),
    ('# 如果识别到多个文件，记录为列表', '# If multiple files detected, store as list'),
    ('# 多个文件', '# Multiple files'),
    # ---- debug log messages ----
    ('"  第 [{i:02d}] 帧: 无法识别文件名 | has_BE: {has_binding_energy} | OCR预览: {preview}"',
     '"  Frame [{i:02d}]: Unable to identify filename | has_BE: {has_binding_energy} | OCR preview: {preview}"'),
    ('"  第 [{i:02d}] 帧: ✓ 识别到文件: {current_files[0]} (规范化: {current_normalized_list[0]}) | OCR预览: {preview}"',
     '"  Frame [{i:02d}]: ✓ Identified file: {current_files[0]} (normalized: {current_normalized_list[0]}) | OCR preview: {preview}"'),
    ('"  第 [{i:02d}] 帧: 无法识别 | OCR: {preview}"',
     '"  Frame [{i:02d}]: Unable to identify | OCR: {preview}"'),
    ('"  第 [{i:02d}] 帧: ✓ {current_file} (XRDA→XRD4)"',
     '"  Frame [{i:02d}]: ✓ {current_file} (XRDA→XRD4)"'),
    ('"  第 [{i:02d}] 帧: ✓ {current_file}"', '"  Frame [{i:02d}]: ✓ {current_file}"'),
    ('"✓ 文件识别完成: 共 {len(screenshot_files)} 帧"',
     '"✓ File identification complete: {len(screenshot_files)} frames total"'),
    ('"  识别到的文件: {\', \'.join(sorted(unique_files))}"',
     '"  Identified files: {\', \'.join(sorted(unique_files))}"'),
    ('"  ⚠️ 警告: 未识别出任何文件名！"', '"  ⚠️ Warning: No filenames identified!"'),
    # ---- Normalization comments ----
    ('归一化OCR文本，只处理明确的数字误识别', 'Normalize OCR text, only handle clear digit misrecognitions'),
    ('保留字母B、C、d、m等原样', 'Keep letters B, C, d, m etc. as-is'),
    ('# 只替换明确会被误识别为数字的字符', '# Only replace characters clearly misrecognized as digits'),
    ("('l', '1'),   # 小写L -> 1", "('l', '1'),   # lowercase L -> 1"),
    ("('I', '1'),   # 大写i -> 1", "('I', '1'),   # uppercase I -> 1"),
    ("('|', '1'),   # 竖线 -> 1", "('|', '1'),   # pipe -> 1"),
    ("('O', '0'),   # 大写o -> 0", "('O', '0'),   # uppercase O -> 0"),
    ("('g','9')  # 小写o -> 0", "('g','9')  # lowercase g -> 9"),
    ('# 移除多余空格', '# Remove extra spaces'),
    # ---- extract filename docstring ----
    ('"""从OCR文本中提取文件名 - 增强版（优先从方括号提取）"""',
     '"""Extract filename from OCR text - enhanced (prefer bracket extraction)"""'),
    ('# ===== 策略-1: 方括号提取（最高优先级）=====',
     '# ===== Strategy-1: Bracket extraction (highest priority) ====='),
    # ---- XRD correction comments ----
    ('# XRD系列误认修正', '# XRD series misrecognition correction'),
    ('# WRT系列误认修正', '# WRT series misrecognition correction'),
    # ---- TASK_CONFIGS section header ----
    ('# ==================== 任务配置 ====================', '# ==================== TASK CONFIGS ===================='),
    ('# 基础难度（10个任务）', '# Basic difficulty (10 tasks)'),
    ('# 简单评估函数', '# Simple evaluation functions'),
    ('# ============ 简单任务评估函数 ============', '# ============ Simple task evaluation functions ============'),
    ('# ============ 中等任务评估函数 ============', '# ============ Medium task evaluation functions ============'),
    ('# ============ 复杂任务评估函数 ============', '# ============ Complex task evaluation functions ============'),
    ('# 简单任务', '# Simple tasks'),
    ('# 中等任务', '# Medium tasks'),
    ('# 复杂任务', '# Complex tasks'),
    ('# 中等难度（5个任务）', '# Medium difficulty (5 tasks)'),
    ('# 复杂难度（5个任务）', '# Complex difficulty (5 tasks)'),
    ('# ---------- 简单任务轨迹 ----------', '# ---------- Simple task trajectories ----------'),
    ('# ---------- 中等任务轨迹 ----------', '# ---------- Medium task trajectories ----------'),
    ('# ---------- 复杂任务轨迹 ----------', '# ---------- Complex task trajectories ----------'),
    # ---- dm_evaluate_test.py specific ----
    ('对应任务结构：', 'Task structure:'),
    (f'  - 简单-1  ~ 简单-10  (10个)', '  - in1  ~ in10  (10 tasks)'),
    (f'  - 中等-1  ~ 中等-5   (5个)', '  - in11 ~ in15  (5 tasks)'),
    (f'  - 复杂-1  ~ 复杂-5   (5个)', '  - in16 ~ in20  (5 tasks)'),
    ('  合计 20 个任务', '  Total: 20 tasks'),
    ('轨迹定义（in1 ~ in20）：每条轨迹对应一个任务被正确完成时的操作记录',
     'Trajectory definitions (in1 ~ in20): each trajectory records the operations when a task is completed correctly'),
    ('# ============ 轨迹完成度定义 ============', '# ============ TRAJECTORY COMPLETION DEFINITIONS ============'),
    ('# 文件已导入', '# File imported'),
    ('# 标注 5nm 标尺', '# Add 5nm scale bar'),
    ('# 执行了添加标尺操作（从无到有）', '# Performed scale bar addition (from none)'),
    ('# 使用 Box 工具', '# Use Box tool'),
    ('# 绘制红色矩形框', '# Draw red rectangle'),
    ('# 使用 Oval 工具', '# Use Oval tool'),
    ('# 绘制红色椭圆框', '# Draw red oval'),
    ('# 应用 Sobel 滤波', '# Apply Sobel filter'),
    ('# 打开 Scale 对话框', '# Open Scale dialog'),
    ('# 设置尺寸 2000', '# Set size to 2000'),
    ('# 旋转操作', '# Rotation operation'),
    ('# 旋转角度 p50', '# Rotation angle p50'),
    ('# 均值与标准差分析', '# Mean and standard deviation analysis'),
    ('# 结果显示（含 Standard Deviation）', '# Results shown (contains Standard Deviation)'),
    ('# 打开 Customize 对话框', '# Open Customize dialog'),
    ('# 勾选 Mask 复选框', '# Check the Mask checkbox'),
    ('# 绘制 RectangleROI', '# Draw RectangleROI'),
    ('# 点击 Add Data Bar', '# Click Add Data Bar'),
    ('# Data Bar 文字信息可见', '# Data Bar text info visible'),
    ('# 复制并放大 ROI 覆盖原区域', '# Copy and enlarge ROI to cover original area'),
    ('# 生成 Profile of dm4', '# Generate Profile of dm4'),
    ('# 打开 Change Profile Info 对话框', '# Open Change Profile Info dialog'),
    ('# 设置 Integration Width = 80', '# Set Integration Width = 80'),
    ('# 执行 FFT，生成 FFT of dm4 图像', '# Perform FFT, generate FFT of dm4 image'),
    ('# 打开前景色设置', '# Open foreground color setting'),
    ('# Box 内部填充白色', '# Fill Box interior with white'),
    ('# 复制放大 ROI', '# Copy and enlarge ROI'),
    ('# 生成 Profile of dm2', '# Generate Profile of dm2'),
    ('# Profile 弹窗中 nm 出现 5 次', '# nm appears 5 times in Profile popup'),
    ('# 执行 FFT', '# Perform FFT'),
    ('# 执行 IFFT（生成 IFFT of FFT of ...）', '# Perform IFFT (generates IFFT of FFT of ...)'),
    ('# 添加 SpotMask', '# Add SpotMask'),
    # ---- avantage_evaluate_test.py comments ----
    ('# 导入原有的AvantageEvaluator', '# Import the AvantageEvaluator'),
    ('# 导入原有的JadeEvaluator', '# Import the JadeEvaluator'),
    ('# ============ 理论得分定义 ============', '# ============ THEORETICAL SCORE DEFINITIONS ============'),
    ('# 轨迹ID与指令的对应关系', '# Mapping of trajectory IDs to instructions'),
    ('# 轨迹实际完成的操作（根据指令推断）', '# Operations actually performed in each trajectory (inferred from instructions)'),
    ('# 说明：', '# Notes:'),
    ('# - imported_files: 主要操作的文件（指令中明确要求导入的）',
     '# - imported_files: files primarily operated on (explicitly required by the instruction)'),
    ('# - other_files: 过程中可能打开但非主要操作对象的文件',
     '# - other_files: files that may be opened during the process but are not the primary target'),
    ('# - operations: 执行的具体操作', '# - operations: specific operations performed'),
    ('# 过程中未打开其他文件', '# No other files opened during the process'),
    ('# 过程中可能重复打开', '# May be opened repeatedly during the process'),
    ('# 过程中打开其他文件', '# Other files opened during the process'),
    ('# 放大缩小', '# Zoom in and out'),
    ('# 堆叠图', '# Stacked graph'),
    ('# 复制后有2个', '# 2 copies after duplication'),
    ('# Smart背景', '# Smart background'),
    ('# 简单任务 (in1-in10)', '# Simple tasks (in1-in10)'),
    ('# 中等任务 (in11-in15)', '# Medium tasks (in11-in15)'),
    ('# 复杂任务 (in16-in20)', '# Complex tasks (in16-in20)'),
    ('# 简单任务', '# Simple tasks'),
    ('# 中等任务', '# Medium tasks'),
    ('# 复杂任务', '# Complex tasks'),
    # ---- ms_evaluate_test.py ----
    ('# ============ 轨迹ID映射 ============', '# ============ TRAJECTORY ID MAPPING ============'),
    ('# ============ 轨迹完成度定义 (修复版) ============', '# ============ TRAJECTORY COMPLETION DEFINITIONS (Fixed) ============'),
    ('# 修复内容: 补充缺失的 document_3d_atomistic 等关键operations',
     '# Fix: added missing operations such as document_3d_atomistic'),
    ('修复内容:', 'Fix:'),
    ('1. check_field_value 理论计算逻辑 - 修复 field_name=None 时的匹配问题',
     '1. check_field_value theoretical logic - fix matching when field_name=None'),
    ('2. check_text_keyword 理论计算逻辑 - 增强opened_file的匹配',
     '2. check_text_keyword theoretical logic - enhanced opened_file matching'),
    ('3. TRAJECTORY_COMPLETIONS - 补充缺失的operations',
     '3. TRAJECTORY_COMPLETIONS - added missing operations'),
    # ---- vesta_evaluator.py ----
    ('修复内容：', 'Fixes:'),
    ('1. check_standard_orientation 使用视觉相似度比较 + 实时打印',
     '1. check_standard_orientation uses visual similarity comparison + real-time print'),
    ('2. check_rotation_90_up 使用视觉相似度比较 + 实时打印',
     '2. check_rotation_90_up uses visual similarity comparison + real-time print'),
    ('3. check_translation 使用视觉相似度比较 + 实时打印',
     '3. check_translation uses visual similarity comparison + real-time print'),
    ('裁剪图片的中心区域：', 'Crop the central region of the image:'),
    ('- 高度：中间70% (去掉顶部10%，底部20%)', '- Height: middle 70% (remove top 10%, bottom 20%)'),
    ('- 宽度：去掉左边35%', '- Width: remove left 35%'),
    ('# 计算裁剪区域', '# Calculate crop region'),
    ('left = int(width * 0.35)  # 去掉左边35%', 'left = int(width * 0.35)  # Remove left 35%'),
    ('"""简单的像素差异相似度计算"""', '"""Simple pixel-difference similarity calculation"""'),
    # ---- Jade test file comments ----
    ('# 轨迹实际完成的操作（根据指令推断）', '# Operations performed in each trajectory (inferred from instructions)'),
    ('# 现在支持 main_file（主要文件）和 other_files（次要文件列表）',
     '# Now supports main_file (primary file) and other_files (secondary file list)'),
    ('# 如果过程中打开了其他文件，在这里添加', '# If other files were opened during the process, add them here'),
    # ---- batch evaluation comments ----
    ('功能：', 'Features:'),
    ('1. 定义每条轨迹的理论得分', '1. Define theoretical scores for each trajectory'),
    ('2. 批量运行 20×20=400 个评估实验', '2. Run 400 (20×20) evaluation experiments in batch'),
    ('3. 生成Excel对比报告', '3. Generate Excel comparison report'),
    ('1. 生成理论得分矩阵（20条轨迹 × 20个任务）- 检查点级别',
     '1. Generate theoretical score matrix (20 trajectories × 20 tasks) - checkpoint level'),
    ('2. 自动运行400个评估实验 - 记录每个检查点',
     '2. Automatically run 400 evaluation experiments - record each checkpoint'),
    ('3. 输出Excel对比报告 - 检查点级别对比',
     '3. Output Excel comparison report - checkpoint-level comparison'),
    # ---- simplicity comment in vesta_evaluator ----
    (f'self._log(f"简单相似度计算错误: {{str(e)}}", "错误")',
     f'self._log(f"Simple similarity calculation error: {{str(e)}}", "ERROR")'),
    # tasks        = list(task_configs.keys())              # 简单-1 ~ 复杂-5
    ('tasks        = list(task_configs.keys())              # 简单-1 ~ 复杂-5',
     'tasks        = list(task_configs.keys())              # in1 ~ in20'),
]

# ============================================================
# Helper: apply task key replacements
# ============================================================
def replace_task_keys(text: str, key_map: dict) -> str:
    """Replace task dict keys like "简单-1" → "in1" in Python source."""
    # Sort by length descending to avoid partial matches (e.g. 简单-10 before 简单-1)
    for zh, en in sorted(key_map.items(), key=lambda x: -len(x[0])):
        # Replace as quoted dict keys
        text = text.replace(f'"{zh}"', f'"{en}"')
        # Also replace in task_name field of JSON-like strings
        text = text.replace(f'"task_name": "{zh}"', f'"task_name": "{en}"')
        # Replace in comments like # 简单-1 ~ 复杂-5
        text = text.replace(zh, en)
    return text


def apply_common_replacements(text: str) -> str:
    for zh, en in COMMON_REPLACEMENTS:
        text = text.replace(zh, en)
    return text


# ============================================================
# Process avantage_evaluator.py
# ============================================================
def process_evaluator(filepath: Path, tool: str) -> None:
    key_map = TOOL_TASK_MAPS[tool]
    text = filepath.read_text(encoding='utf-8')
    text = replace_task_keys(text, key_map)
    text = apply_common_replacements(text)
    filepath.write_text(text, encoding='utf-8')
    print(f"✓ Updated {filepath.name}")


# ============================================================
# Process avantage_evaluate_test.py
# ============================================================
def process_avantage_test(filepath: Path) -> None:
    text = filepath.read_text(encoding='utf-8')
    # Replace TRAJECTORY_INSTRUCTIONS values
    for key, en_val in AVANTAGE_INSTRUCTIONS.items():
        # Match: "inX": "...Chinese...",
        pattern = rf'("{key}":\s*)"[^"]*"'
        replacement = f'\\1"{en_val}"'
        text = re.sub(pattern, replacement, text)
    text = apply_common_replacements(text)
    filepath.write_text(text, encoding='utf-8')
    print(f"✓ Updated {filepath.name}")


# ============================================================
# Process Jade_evaluate_test.py
# ============================================================
def process_jade_test(filepath: Path) -> None:
    text = filepath.read_text(encoding='utf-8')
    for key, en_val in JADE_INSTRUCTIONS.items():
        pattern = rf'("{key}":\s*)"[^"]*"'
        replacement = f'\\1"{en_val}"'
        text = re.sub(pattern, replacement, text)
    text = apply_common_replacements(text)
    filepath.write_text(text, encoding='utf-8')
    print(f"✓ Updated {filepath.name}")


# ============================================================
# Process ms_evaluate_test.py
# ============================================================
def process_ms_test(filepath: Path) -> None:
    text = filepath.read_text(encoding='utf-8')
    key_map = TOOL_TASK_MAPS['ms']
    # 1. Replace TRAJECTORY_ID_MAPPING values: "简单-1" → "in1"
    for zh, en in sorted(key_map.items(), key=lambda x: -len(x[0])):
        text = text.replace(f': "{zh}"', f': "{en}"')
    # 2. Replace TRAJECTORY_COMPLETIONS keys
    for zh, en in sorted(key_map.items(), key=lambda x: -len(x[0])):
        text = text.replace(f'"{zh}": {{', f'"{en}": {{')
    # 3. Replace comments "# 中等任务" etc.
    text = apply_common_replacements(text)
    filepath.write_text(text, encoding='utf-8')
    print(f"✓ Updated {filepath.name}")


# ============================================================
# Process dm_evaluate_test.py and vesta_evaluate_test.py
# ============================================================
def process_generic_test(filepath: Path) -> None:
    text = filepath.read_text(encoding='utf-8')
    text = apply_common_replacements(text)
    filepath.write_text(text, encoding='utf-8')
    print(f"✓ Updated {filepath.name}")


# ============================================================
# Rename result JSON files and update task_name inside
# ============================================================
def rename_result_files() -> None:
    results_root = BASE / 'results'
    if not results_root.exists():
        print("No results directory found, skipping.")
        return

    # Map tool folder name → key_map
    tool_folder_map = {
        'avantage': TOOL_TASK_MAPS['avantage'],
        'dm': TOOL_TASK_MAPS['dm'],
        'jade': TOOL_TASK_MAPS['jade'],
        'ms': TOOL_TASK_MAPS['ms'],
        'vesta': TOOL_TASK_MAPS['vesta'],
    }

    renamed = 0
    for tool_name, key_map in tool_folder_map.items():
        # Find all *_result.json files in any subdirectory matching this tool
        for json_file in results_root.rglob('*_result.json'):
            # Check if parent path contains the tool name
            parts = json_file.parts
            if tool_name not in parts:
                continue
            stem = json_file.stem  # e.g. "简单-1_result"
            for zh, en in sorted(key_map.items(), key=lambda x: -len(x[0])):
                old_prefix = f'{zh}_result'
                new_prefix = f'{en}_result'
                if stem == old_prefix:
                    new_name = json_file.with_name(f'{new_prefix}.json')
                    # Update task_name inside the JSON
                    try:
                        data = json.loads(json_file.read_text(encoding='utf-8'))
                        if data.get('task_name') == zh:
                            data['task_name'] = en
                        json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
                    except Exception:
                        pass
                    json_file.rename(new_name)
                    renamed += 1
                    break

    print(f"✓ Renamed {renamed} result JSON files")


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    # Evaluator files
    process_evaluator(BASE / 'avantage_evaluator.py', 'avantage')
    process_evaluator(BASE / 'dm_evaluator.py', 'dm')
    process_evaluator(BASE / 'jade_evaluator.py', 'jade')
    process_evaluator(BASE / 'ms_evaluator.py', 'ms')
    process_evaluator(BASE / 'vesta_evaluator.py', 'vesta')

    # Test files
    process_avantage_test(BASE / 'avantage_evaluate_test.py')
    process_jade_test(BASE / 'Jade_evaluate_test.py')
    process_ms_test(BASE / 'ms_evaluate_test.py')
    process_generic_test(BASE / 'dm_evaluate_test.py')
    process_generic_test(BASE / 'vesta_evaluate_test.py')

    # Result JSON files
    rename_result_files()

    print("\nDone!")
