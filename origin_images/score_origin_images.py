#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量调用 https://api.xi-ai.cn/v1 的视觉大模型，对 origin_images 下的图像进行三维度评分。

功能：
1. 对四张拼接图（*_grid.png）按规则网格切分后，对每个小图分别评分
2. 对 origin_images/XRD, XPS, roman, FTIR 下的图1-图4分别评分
3. 使用 base64 发送图片
4. 输出 JSON / CSV

安装依赖：
    pip install requests pillow pandas

运行示例：
    python score_origin_images.py \
      --model Qwen/Qwen3-VL-235B-A22B-Thinking \
      --api-key "你的key"

可选：
    python score_origin_images.py --help
"""

from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import mimetypes
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from PIL import Image


SYSTEM_PROMPT = """You are an expert scientific figure evaluator. You WILL be shown a chart or plot produced by OriginPro along with a textual description of what the figure should look like.

You MUST reply with EXACTLY this one line and NOTHING ELSE — no explanations, no "none", no extra text, no apologies, no refusal:

C:<score> A:<score> T:<score>

Score each dimension on a 1.0–5.0 scale with one decimal place (e.g. 4.3, 3.7, 2.8). Use decimals to maximize distinction. Never output integers only.

Dimension 1 — Visual Correctness (C):
  5.0 – Plot type exactly matches; all axes labeled with units; data accurate; scale/range correct.
  4.0–4.9 – Fundamentally correct, only minor deviations.
  3.0–3.9 – Correct type but noticeable errors in data or labeling.
  2.0–2.9 – Partial match with significant errors.
  1.0–1.9 – Wrong plot type or completely incorrect data.

Dimension 2 — Aesthetic Quality (A):
  5.0 – Publication-ready: professional colors, legible fonts, proper spacing, well-placed legend, no clutter.
  4.0–4.9 – Generally clean, minor cosmetic issues only.
  3.0–3.9 – Adequate but unprofessional (default colors, crowded).
  2.0–2.9 – Significant issues impairing readability.
  1.0–1.9 – Very poor visual quality.

Dimension 3 — Task Completeness (T):
  5.0 – All required elements present exactly as specified (insets, annotations, panels, markers, color bars, etc.).
  4.0–4.9 – Most elements present, at most one minor omission.
  3.0–3.9 – Core met but secondary elements missing.
  2.0–2.9 – Significant required elements absent or wrong.
  1.0–1.9 – Most required elements missing.

Reply with EXACTLY this format and nothing else:
C:<score> A:<score> T:<score>
Example: C:4.3 A:3.7 T:5.0
"""


DEFAULT_BASE_URL = "https://www.dmxapi.cn/v1"
DEFAULT_API_KEY = "sk-IaWQzUX6tmMv6fNhTqz6QCCTLceHw1RHLiaLRlNhmQ87i8xR"
DEFAULT_MODEL = "gemini-3.1-pro-preview"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

GRID_CONFIG = {
    "ftir_grid.png": {"rows": 2, "cols": 3},
    "palette_grid.png": {"rows": 3, "cols": 3},
    "xps_grid.png": {"rows": 2, "cols": 3},
    "xrd_grid.png": {"rows": 2, "cols": 3},
}

FOLDER_CONFIG = {
    "XRD": {"pattern": "图*.png", "limit": 4},
    "XPS": {"pattern": "图*.png", "limit": 4},
    "roman": {"pattern": "图*.png", "limit": 4},
    "FTIR": {"pattern": "图*.png", "limit": 4},
}

DESCRIPTION_MAP = {
    "ftir_grid.png": "This is one candidate subfigure from an FTIR figure comparison grid. Evaluate scientific plotting quality, readability, aesthetics, and whether the FTIR-style figure appears complete and publication-suitable.",
    "palette_grid.png": "This is one candidate scientific chart from a palette comparison grid. Evaluate which subfigure is visually better and scientifically clearer, and score it on correctness, aesthetics, and completeness.",
    "xps_grid.png": "This is one candidate subfigure from an XPS figure comparison grid. Evaluate scientific plotting quality, readability, aesthetics, and whether the XPS-style figure appears complete and publication-suitable.",
    "xrd_grid.png": "This is one candidate subfigure from an XRD figure comparison grid. Evaluate scientific plotting quality, readability, aesthetics, and whether the XRD-style figure appears complete and publication-suitable.",
    "XRD": "This figure should be an XRD-style scientific plot. Evaluate data presentation quality, axis/legend readability, publication aesthetics, and whether the necessary XRD elements appear complete.",
    "XPS": "This figure should be an XPS-style scientific plot. Evaluate data presentation quality, fitted components or peak information if present, publication aesthetics, and completeness.",
    "roman": "This figure should be a Raman-style scientific plot. Evaluate data presentation quality, readability, publication aesthetics, and whether the Raman plot appears complete.",
    "FTIR": "This figure should be an FTIR-style scientific plot. Evaluate data presentation quality, readability, publication aesthetics, and whether the FTIR plot appears complete.",
}


@dataclass
class ScoreResult:
    task_type: str
    group_name: str
    source_file: str
    item_name: str
    prompt_description: str
    c: Optional[float]
    a: Optional[float]
    t: Optional[float]
    parsed_ok: bool
    raw_response: str
    error: str = ""


class XiAIVisionScorer:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 300,
        max_retries: int = 5,
        request_interval: float = 2.0,
        temperature: float = 0.0,
        max_tokens: int = 128,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_interval = request_interval
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def encode_image_to_data_url(self, image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def build_user_prompt(self, description: str, item_name: str) -> str:
        return (
            f"Figure description: {description}\n"
            f"Current figure item: {item_name}\n"
            "Please evaluate this scientific figure candidate on the three required dimensions. "
            "Return exactly one line in the format C:<score> A:<score> T:<score> and nothing else."
        )

    def score_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str,
        description: str,
        item_name: str,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], bool, str, str]:
        data_url = self.encode_image_to_data_url(image_bytes, mime_type)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.build_user_prompt(description, item_name)},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        last_error = ""
        raw_response = ""

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                raw_json = response.json()

                choice = raw_json["choices"][0]
                finish_reason = choice.get("finish_reason", "?")
                raw_response = (choice["message"].get("content") or "").strip()

                # 空响应或内容被过滤，重试
                if not raw_response:
                    last_error = (
                        f"attempt {attempt}/{self.max_retries}: "
                        f"empty response (finish_reason={finish_reason})"
                    )
                    print(f"    [WARN] {last_error}")
                    time.sleep(self.request_interval * attempt)  # 指数退避
                    continue

                c, a, t, ok = self.parse_scores(raw_response)
                if not ok:
                    print(f"    [WARN] parse failed (attempt {attempt}), raw: {repr(raw_response)}")
                    # 解析失败也重试，模型可能输出了非预期格式
                    last_error = f"attempt {attempt}/{self.max_retries}: parse failed"
                    time.sleep(self.request_interval)
                    continue

                # 成功后等待，避免限速
                time.sleep(self.request_interval)
                return c, a, t, ok, raw_response, ""

            except Exception as exc:
                last_error = f"attempt {attempt}/{self.max_retries}: {exc}"
                print(f"    [ERROR] {last_error}")
                if attempt < self.max_retries:
                    time.sleep(self.request_interval * attempt)

        return None, None, None, False, raw_response, last_error

    @staticmethod
    def parse_scores(
        text: str,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], bool]:
        # 1. 剥离 <think>...</think> 块（Thinking 模型的 CoT 输出）
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        # 2. 支持：全角/半角冒号、多位小数、逗号或空格分隔
        pattern = (
            r"C\s*[：:]\s*(\d+(?:\.\d+)?)"
            r"[\s,]+"
            r"A\s*[：:]\s*(\d+(?:\.\d+)?)"
            r"[\s,]+"
            r"T\s*[：:]\s*(\d+(?:\.\d+)?)"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None, None, None, False

        c, a, t = map(float, match.groups())

        # 3. 超出合理范围则拒绝
        if not all(0.0 < v <= 10.0 for v in (c, a, t)):
            return None, None, None, False

        # 4. 如果模型按 10 分制输出，自动折算到 5 分制
        if any(v > 5.0 for v in (c, a, t)):
            print(
                f"    [INFO] scores appear to be on 10-point scale "
                f"(C={c} A={a} T={t}), rescaling to 5-point"
            )
            c, a, t = round(c / 2, 1), round(a / 2, 1), round(t / 2, 1)

        return c, a, t, True


def read_image_bytes(path: Path) -> Tuple[bytes, str]:
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "image/png"
    return path.read_bytes(), mime_type


def crop_grid_image(
    image_path: Path, rows: int, cols: int, min_size: int = 50
) -> List[Tuple[str, bytes, str]]:
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    cell_w = width // cols
    cell_h = height // rows
    print(f"  [INFO] {image_path.name}: {width}x{height}, cell={cell_w}x{cell_h}")
    results: List[Tuple[str, bytes, str]] = []

    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            upper = r * cell_h
            right = (c + 1) * cell_w if c < cols - 1 else width
            lower = (r + 1) * cell_h if r < rows - 1 else height
            cropped = img.crop((left, upper, right, lower))

            if cropped.width < min_size or cropped.height < min_size:
                print(
                    f"  [SKIP] r{r + 1}_c{c + 1} too small "
                    f"({cropped.width}x{cropped.height}), skipping"
                )
                continue

            buffer = io.BytesIO()
            cropped.save(buffer, format="PNG")
            item_name = f"r{r + 1}_c{c + 1}"
            results.append((item_name, buffer.getvalue(), "image/png"))
    return results


def natural_key(path: Path):
    parts = re.split(r"(\d+)", path.stem)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def collect_folder_images(folder: Path, pattern: str, limit: int) -> List[Path]:
    candidates = [p for p in folder.glob(pattern) if p.suffix.lower() in IMAGE_EXTS]
    candidates = sorted(candidates, key=natural_key)
    return candidates[:limit] if limit > 0 else candidates


def score_grid_images(root: Path, scorer: XiAIVisionScorer) -> List[ScoreResult]:
    results: List[ScoreResult] = []
    for filename, cfg in GRID_CONFIG.items():
        path = root / filename
        if not path.exists():
            print(f"[GRID] {filename}: NOT FOUND, skipping")
            results.append(
                ScoreResult(
                    task_type="grid",
                    group_name=filename,
                    source_file=str(path),
                    item_name="<missing>",
                    prompt_description=DESCRIPTION_MAP.get(filename, ""),
                    c=None,
                    a=None,
                    t=None,
                    parsed_ok=False,
                    raw_response="",
                    error="file not found",
                )
            )
            continue

        description = DESCRIPTION_MAP.get(filename, "")
        sub_images = crop_grid_image(path, cfg["rows"], cfg["cols"])
        print(f"[GRID] {filename}: {len(sub_images)} sub-images")

        for item_name, image_bytes, mime_type in sub_images:
            c, a, t, ok, raw, err = scorer.score_image_bytes(
                image_bytes=image_bytes,
                mime_type=mime_type,
                description=description,
                item_name=f"{filename}/{item_name}",
            )
            results.append(
                ScoreResult(
                    task_type="grid",
                    group_name=filename,
                    source_file=str(path),
                    item_name=item_name,
                    prompt_description=description,
                    c=c,
                    a=a,
                    t=t,
                    parsed_ok=ok,
                    raw_response=raw,
                    error=err,
                )
            )
            print(f"  - {item_name}: C={c} A={a} T={t} ok={ok}")
    return results


def score_folder_images(root: Path, scorer: XiAIVisionScorer) -> List[ScoreResult]:
    results: List[ScoreResult] = []
    for folder_name, cfg in FOLDER_CONFIG.items():
        folder = root / folder_name
        description = DESCRIPTION_MAP.get(folder_name, "")
        if not folder.exists():
            print(f"[FOLDER] {folder_name}: NOT FOUND, skipping")
            results.append(
                ScoreResult(
                    task_type="folder",
                    group_name=folder_name,
                    source_file=str(folder),
                    item_name="<missing-folder>",
                    prompt_description=description,
                    c=None,
                    a=None,
                    t=None,
                    parsed_ok=False,
                    raw_response="",
                    error="folder not found",
                )
            )
            continue

        image_paths = collect_folder_images(folder, cfg["pattern"], cfg["limit"])
        print(f"[FOLDER] {folder_name}: {len(image_paths)} images")

        for image_path in image_paths:
            image_bytes, mime_type = read_image_bytes(image_path)
            c, a, t, ok, raw, err = scorer.score_image_bytes(
                image_bytes=image_bytes,
                mime_type=mime_type,
                description=description,
                item_name=f"{folder_name}/{image_path.name}",
            )
            results.append(
                ScoreResult(
                    task_type="folder",
                    group_name=folder_name,
                    source_file=str(image_path),
                    item_name=image_path.name,
                    prompt_description=description,
                    c=c,
                    a=a,
                    t=t,
                    parsed_ok=ok,
                    raw_response=raw,
                    error=err,
                )
            )
            print(f"  - {image_path.name}: C={c} A={a} T={t} ok={ok}")
    return results


def save_json(results: List[ScoreResult], output_path: Path) -> None:
    output_path.write_text(
        json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_csv(results: List[ScoreResult], output_path: Path) -> None:
    fieldnames = list(asdict(results[0]).keys()) if results else [
        "task_type",
        "group_name",
        "source_file",
        "item_name",
        "prompt_description",
        "c",
        "a",
        "t",
        "parsed_ok",
        "raw_response",
        "error",
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def summarize(results: List[ScoreResult]) -> None:
    total = len(results)
    ok_count = sum(1 for r in results if r.parsed_ok)
    fail_count = total - ok_count
    print("\n===== Summary =====")
    print(f"Total:      {total}")
    print(f"Parsed OK:  {ok_count}")
    print(f"Failed:     {fail_count}")
    if ok_count:
        avg_c = sum(r.c for r in results if r.parsed_ok) / ok_count
        avg_a = sum(r.a for r in results if r.parsed_ok) / ok_count
        avg_t = sum(r.t for r in results if r.parsed_ok) / ok_count
        print(f"Avg C/A/T:  {avg_c:.2f} / {avg_a:.2f} / {avg_t:.2f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score OriginPro figures with xi-ai vision model."
    )
    parser.add_argument(
        "--root", type=str, default="origin_images",
        help="Root directory of images."
    )
    parser.add_argument(
        "--output-dir", type=str, default="origin_images/results_llm",
        help="Directory for JSON/CSV outputs."
    )
    parser.add_argument(
        "--base-url", type=str, default=DEFAULT_BASE_URL,
        help="API base URL."
    )
    parser.add_argument(
        "--api-key", type=str, default=DEFAULT_API_KEY,
        help="API key."
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help="Vision model name."
    )
    parser.add_argument(
        "--timeout", type=int, default=300,
        help="Request timeout in seconds."
    )
    parser.add_argument(
        "--max-retries", type=int, default=5,
        help="Retry times for each image (including empty/parse-fail retries)."
    )
    parser.add_argument(
        "--interval", type=float, default=2.0,
        help="Base interval (seconds) between requests to avoid rate limiting."
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0,
        help="Sampling temperature."
    )
    parser.add_argument(
        "--max-tokens", type=int, default=4096,
        help="Max tokens for response."
    )
    parser.add_argument(
        "--only-grid", action="store_true",
        help="Only score grid images."
    )
    parser.add_argument(
        "--only-folder", action="store_true",
        help="Only score folder images."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        print(f"Image root does not exist: {root}", file=sys.stderr)
        return 1

    if args.only_grid and args.only_folder:
        print("--only-grid and --only-folder cannot be used together.", file=sys.stderr)
        return 1

    scorer = XiAIVisionScorer(
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
        max_retries=args.max_retries,
        request_interval=args.interval,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    results: List[ScoreResult] = []

    if not args.only_folder:
        results.extend(score_grid_images(root, scorer))

    if not args.only_grid:
        results.extend(score_folder_images(root, scorer))

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"results_{timestamp}.json"
    csv_path = output_dir / f"results_{timestamp}.csv"
    save_json(results, json_path)
    save_csv(results, csv_path)
    summarize(results)
    print(f"\nJSON saved to: {json_path}")
    print(f"CSV  saved to: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())