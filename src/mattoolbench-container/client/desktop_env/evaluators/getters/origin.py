import io
import os
import base64
import logging
import time

from PIL import Image
import openai

logger = logging.getLogger("desktopenv.getters.origin")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIME = {
    "png":  "image/png",
    "jpeg": "image/jpeg",
    "jpg":  "image/jpeg",
    "gif":  "image/gif",
    "webp": "image/webp",
}

# ---------------------------------------------------------------------------
# Prompts for validate_file_with_model
# ---------------------------------------------------------------------------

_FILE_VALIDATE_SYSTEM = """\
You are an expert validator for scientific structure and data files used in materials science \
(e.g. VESTA, XSD, CIF, POSCAR, XYZ formats).

Given the text content of a file and a task description, decide whether the file \
satisfies ALL criteria stated in the description.

Evaluation checklist:
1. Is the file a syntactically valid instance of the expected format?
2. Does it contain the expected atomic species / elements?
3. Do structural parameters (space group, lattice constants, boundary settings, \
   atom counts, coordinate values, etc.) match the description?
4. Are any specific sections, keywords, or numeric values mentioned in the description present?

Reply with exactly one word on its own line: YES if every criterion is satisfied, NO otherwise.
Do NOT explain your reasoning — just YES or NO."""

_FILE_VALIDATE_USER = """\
Task description (what the file should contain):
{description}

File path: {file_path}
File content ({length} chars shown):
---
{content}
---

Does this file satisfy the description? Reply YES or NO."""

# Maximum characters of file text forwarded to the model (~1 500 tokens).
_MAX_FILE_CHARS = 6000

# ---------------------------------------------------------------------------
# Prompts for the existing Origin image evaluator
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert scientific figure evaluator. You will be shown a chart or plot produced by OriginPro and a description of what the figure should look like.

Score the figure on THREE dimensions, each on a 1.0–5.0 scale **with one decimal place allowed** to enable strict and fine-grained differentiation (e.g. 4.3, 3.7, 2.8). Do not round to integers — use decimals wherever appropriate to maximize distinction between similar figures.

Dimension 1 — Visual Correctness (C):
  5.0 – Plot type exactly matches the requirement; all axes correctly labeled with units; data accurately represented; scale and range appropriate.
  4.0–4.9 – Fundamentally correct with only minor deviations (e.g. missing units on one axis, slightly off range).
  3.0–3.9 – Correct plot type but noticeable errors in data representation or labeling.
  2.0–2.9 – Plot type partially matches but significant errors in data or axes.
  1.0–1.9 – Plot type wrong or data completely incorrect.

Dimension 2 — Aesthetic Quality (A):
  5.0 – Publication-ready: professional color scheme, clear legible fonts, proper spacing, legend well-placed, no clutter.
  4.0–4.9 – Generally clean with minor cosmetic issues.
  3.0–3.9 – Adequate but noticeably unprofessional (e.g. default colors, crowded elements).
  2.0–2.9 – Significant aesthetic issues that impair readability.
  1.0–1.9 – Very poor visual quality, hard to interpret.

Dimension 3 — Task Completeness (T):
  5.0 – All required elements present (e.g. insets, annotations, multiple panels, specific markers, color bars) exactly as specified.
  4.0–4.9 – Most required elements present; at most one minor omission.
  3.0–3.9 – Core requirement met but one or more secondary requirements missing.
  2.0–2.9 – Significant required elements absent or incorrect.
  1.0–1.9 – Most required elements absent or completely wrong.

Reply with EXACTLY this format and nothing else:
C:<score> A:<score> T:<score>
Example: C:4.3 A:3.7 T:5.0"""

_USER_TEMPLATE = (
    "Description of the required figure:\n{description}\n\n"
    "Score the chart above on the three dimensions. "
    "Reply with exactly one line in this format: C:<score> A:<score> T:<score>. "
    "Each score must be a number from 1.0 to 5.0, and decimals are allowed."
)


def _resolve_path(file_path: str) -> str:
    """Convert a relative path to absolute, rooted at the client/output_result/ directory."""
    if os.path.isabs(file_path):
        return file_path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    client_dir  = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    return os.path.join(client_dir, "output_result", file_path)


def _load_image_as_base64(file_path: str):
    """
    Load *file_path* as a PIL image and return {"base64": str, "format": str}.
    Returns None on any failure.
    """
    path = _resolve_path(file_path)
    if not os.path.exists(path):
        logger.warning("Image not found: %s", path)
        return None
    try:
        with Image.open(path) as img:
            img.load()
            fmt = (img.format or "PNG").upper()
            buf = io.BytesIO()
            img.save(buf, format=fmt)
            return {"base64": base64.b64encode(buf.getvalue()).decode(), "format": fmt}
    except Exception as exc:
        logger.error("Failed to load image %s: %s", path, exc)
        return None


def _build_client():
    """
    Build an OpenAI-compatible client for the Origin eval model.

    Priority for each setting (first non-empty wins):
      API key:  ORIGIN_EVAL_API_KEY  → OPENAI_API_KEY  → AZURE_API_KEY
      Base URL: ORIGIN_EVAL_BASE_URL → OPENAI_ENDPOINT → AZURE_ENDPOINT
      Model:    ORIGIN_EVAL_MODEL    → DEFAULT_MODEL   → "gpt-4o"
    """
    api_key = (
        os.getenv("ORIGIN_EVAL_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("AZURE_API_KEY")
    )
    base_url = (
        os.getenv("ORIGIN_EVAL_BASE_URL")
        or os.getenv("OPENAI_ENDPOINT")
        or os.getenv("AZURE_ENDPOINT")
        or "https://api.openai.com/v1"
    )
    model = (
        os.getenv("ORIGIN_EVAL_MODEL")
        or os.getenv("DEFAULT_MODEL")
        or "gpt-4o"
    )
    if not api_key:
        raise EnvironmentError(
            "No API key found. Set ORIGIN_EVAL_API_KEY (or OPENAI_API_KEY / AZURE_API_KEY)."
        )
    return openai.OpenAI(api_key=api_key, base_url=base_url), model


def _call_with_retry(client, model: str, messages: list, retries: int = 3, backoff: float = 2.0) -> str:
    """Call the chat API with exponential-backoff retry. Returns the response text."""
    for attempt in range(1, retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=32,
                temperature=0.0,
            )
            return resp.choices[0].message.content.strip()
        except openai.RateLimitError as exc:
            wait = backoff ** attempt
            logger.warning("Rate limit hit (attempt %d/%d), retrying in %.1fs: %s", attempt, retries, wait, exc)
            time.sleep(wait)
        except openai.APIError as exc:
            wait = backoff ** attempt
            logger.warning("API error (attempt %d/%d), retrying in %.1fs: %s", attempt, retries, wait, exc)
            time.sleep(wait)
    raise RuntimeError(f"Origin eval API call failed after {retries} attempts.")


def _parse_scores(answer: str):
    """
    Parse 'C:<n> A:<n> T:<n>' response into (correctness, aesthetic, completeness).
    Accepts integer or decimal scores and returns (None, None, None) if parsing fails.
    """
    import re
    m = re.search(
        r'C\s*:\s*([1-5](?:\.\d+)?)\s+A\s*:\s*([1-5](?:\.\d+)?)\s+T\s*:\s*([1-5](?:\.\d+)?)',
        answer,
        re.IGNORECASE,
    )
    if m:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    return None, None, None


# ---------------------------------------------------------------------------
# Public getter functions (called by the evaluator framework)
# ---------------------------------------------------------------------------

def get_file_exists_nonempty(env, config) -> bool:
    """Return True if the file exists on the VM AND contains non-zero meaningful content."""
    file_path = config.get("file_path")
    if not file_path:
        logger.warning("get_file_exists_nonempty: 'file_path' not specified.")
        return False
    try:
        content = env.controller.get_file(file_path)
    except Exception as e:
        logger.warning("get_file_exists_nonempty: VM check failed for %s: %s", file_path, e)
        return False
    if content is None:
        logger.warning("File not found on VM: %s", file_path)
        return False
    try:
        text = content.decode("utf-8", errors="ignore").strip()
    except Exception:
        text = ""
    if not text:
        logger.warning("File is empty on VM: %s", file_path)
        return False
    # Reject files whose entire content is just "0" (API returned 0 results)
    if text == "0":
        logger.warning("File contains only '0', treating as no result: %s", file_path)
        return False
    # Reject files indicating 0 retrieved entries (e.g. "retrieved 0 entries")
    text_lower = text.lower()
    zero_patterns = ["retrieved 0 entries", "0 entries retrieved", "retrieved 0 results",
                     "total: 0", "count: 0", "found 0"]
    for pat in zero_patterns:
        if pat in text_lower:
            logger.warning("File indicates 0 results ('%s'): %s", pat, file_path)
            return False
    logger.info("File exists and has content on VM: %s", file_path)
    return True


def get_file_exists(env, config) -> bool:
    """Return True if the file at config['file_path'] exists on the VM."""
    file_path = config.get("file_path")
    if not file_path:
        logger.warning("get_file_exists: 'file_path' not specified.")
        return False
    try:
        content = env.controller.get_file(file_path)
    except Exception as e:
        logger.warning("get_file_exists: VM check failed for %s: %s", file_path, e)
        return False
    exists = content is not None
    if exists:
        logger.info("File exists on VM: %s", file_path)
    else:
        logger.warning("File not found on VM: %s", file_path)
    return exists


def get_origin_aesthetic_score(env, config) -> float:
    """
    Use a vision LLM to score the output figure on three dimensions (C, A, T).

    Returns (C + A + T) / 3 / 5.0 when the LLM produces parseable output, 0.0 otherwise.
    Individual scores (correctness, aesthetic, completeness) are saved to
    {env.cache_dir}/origin_aesthetic.json so they appear in the task result directory.

    Expected config keys:
        file_path   (str)  – path to the output image on the VM
        description (str)  – natural-language description of what the correct figure must show
    """
    file_path   = config.get("file_path")
    description = config.get("description", "").strip()

    if not file_path:
        logger.error("get_origin_aesthetic_score: 'file_path' not specified in config.")
        return 0.0
    if not description:
        logger.error("get_origin_aesthetic_score: 'description' not specified in config.")
        return 0.0

    # Fetch the image bytes from the VM
    try:
        content = env.controller.get_file(file_path)
    except Exception as exc:
        logger.warning("get_origin_aesthetic_score: VM file fetch failed for %s: %s", file_path, exc)
        return 0.0
    if content is None:
        logger.warning("get_origin_aesthetic_score: file not found on VM: %s", file_path)
        return 0.0

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.load()
            fmt = (img.format or "PNG").upper()
            buf = io.BytesIO()
            img.save(buf, format=fmt)
            img_data = {"base64": base64.b64encode(buf.getvalue()).decode(), "format": fmt}
    except Exception as exc:
        logger.error("get_origin_aesthetic_score: failed to decode image from VM: %s", exc)
        return 0.0

    mime     = _MIME.get(img_data["format"].lower(), "image/png")
    data_url = f"data:{mime};base64,{img_data['base64']}"

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                {"type": "text", "text": _USER_TEMPLATE.format(description=description)},
            ],
        },
    ]

    try:
        client, model = _build_client()
        logger.info("Calling vision model '%s' for Origin aesthetic score (file: %s)", model, file_path)
        answer = _call_with_retry(client, model, messages)
        logger.info("Model answer: '%s'", answer)

        c, a, t = _parse_scores(answer)
        if c is None:
            logger.warning(
                "get_origin_aesthetic_score: could not parse scores from '%s'; returning 0.", answer
            )
            return 0.0

        score = (c + a + t) / 3.0 / 5.0
        logger.info(
            "Origin aesthetic scores — C:%.1f  A:%.1f  T:%.1f  avg:%.2f  score:%.4f",
            c, a, t, (c + a + t) / 3.0, score,
        )

        # Persist individual scores to the task result directory
        import json as _json
        scores_path = os.path.join(env.cache_dir, "origin_aesthetic.json")
        try:
            with open(scores_path, "w", encoding="utf-8") as f:
                _json.dump(
                    {
                        "correctness": c,
                        "aesthetic":   a,
                        "completeness": t,
                        "average": round((c + a + t) / 3.0, 4),
                        "score":   round(score, 4),
                        "raw_answer": answer,
                    },
                    f, indent=2,
                )
            logger.info("Origin aesthetic scores saved to %s", scores_path)
        except Exception as exc:
            logger.warning("get_origin_aesthetic_score: failed to save scores to %s: %s", scores_path, exc)

        return score

    except EnvironmentError as exc:
        logger.error("get_origin_aesthetic_score skipped — %s", exc)
        return 0.0
    except Exception as exc:
        logger.error("get_origin_aesthetic_score failed: %s", exc)
        return 0.0


def get_validate_image_with_model(env, config) -> bool:
    """
    Use a vision LLM to check whether the output figure satisfies the task description.

    Expected config keys:
        file_path   (str)  – path to the output image on the VM
        description (str)  – natural-language description of what the correct figure must show

    The model, API key, and endpoint are read from environment variables:
        ORIGIN_EVAL_MODEL    – vision model to use (e.g. "gpt-4o")
        ORIGIN_EVAL_API_KEY  – API key (falls back to OPENAI_API_KEY / AZURE_API_KEY)
        ORIGIN_EVAL_BASE_URL – base URL (falls back to OPENAI_ENDPOINT / AZURE_ENDPOINT)

    Returns True if the model judges the figure correct, False otherwise.
    """
    file_path = config.get("file_path")
    description = config.get("description", "").strip()

    if not file_path:
        logger.error("get_validate_image_with_model: 'file_path' not specified in config.")
        return False
    if not description:
        logger.error("get_validate_image_with_model: 'description' not specified in config.")
        return False

    # Fetch the image bytes from the VM (same as get_file_exists does)
    try:
        content = env.controller.get_file(file_path)
    except Exception as exc:
        logger.warning("get_validate_image_with_model: VM file fetch failed for %s: %s", file_path, exc)
        return False
    if content is None:
        logger.warning("get_validate_image_with_model: file not found on VM: %s", file_path)
        return False

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.load()
            fmt = (img.format or "PNG").upper()
            buf = io.BytesIO()
            img.save(buf, format=fmt)
            img_data = {"base64": base64.b64encode(buf.getvalue()).decode(), "format": fmt}
    except Exception as exc:
        logger.error("get_validate_image_with_model: failed to decode image from VM: %s", exc)
        return False

    mime = _MIME.get(img_data["format"].lower(), "image/png")
    data_url = f"data:{mime};base64,{img_data['base64']}"

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": data_url, "detail": "high"},
                },
                {
                    "type": "text",
                    "text": _USER_TEMPLATE.format(description=description),
                },
            ],
        },
    ]

    try:
        client, model = _build_client()
        logger.info("Calling vision model '%s' for Origin eval (file: %s)", model, file_path)
        answer = _call_with_retry(client, model, messages)
        logger.info("Model answer: '%s'", answer)

        c, a, t = _parse_scores(answer)
        if c is None:
            logger.warning(
                "Could not parse scores from answer '%s'; falling back to False.", answer
            )
            return False

        avg = (c + a + t) / 3.0
        logger.info(
            "Origin eval scores — Correctness:%.1f  Aesthetic:%.1f  Completeness:%.1f  avg:%.2f  pass:%s",
            c, a, t, avg, avg >= 3.0,
        )
        return avg >= 3.0

    except EnvironmentError as exc:
        logger.error("Origin eval skipped — %s", exc)
        return False
    except Exception as exc:
        logger.error("Origin eval failed: %s", exc)
        return False


def get_validate_file_with_model(env, config) -> bool:
    """
    Read a text-based structure file from the VM and ask an LLM whether its
    content satisfies the task description.

    Designed for formats such as VESTA, XSD, CIF, POSCAR, XYZ that are
    human-readable text — the file is decoded and the first ``_MAX_FILE_CHARS``
    characters are forwarded to the model together with a structured prompt.

    Expected config keys:
        file_path   (str)  – absolute path to the file on the VM
        description (str)  – natural-language description of what the file must contain

    Returns True if the model answers YES, False for NO or any failure.
    """
    file_path   = config.get("file_path", "").strip()
    description = config.get("description", "").strip()

    if not file_path:
        logger.error("get_validate_file_with_model: 'file_path' not specified in config.")
        return False
    if not description:
        logger.error("get_validate_file_with_model: 'description' not specified in config.")
        return False

    # ── Fetch file bytes from VM ──────────────────────────────────────────────
    try:
        content_bytes = env.controller.get_file(file_path)
    except Exception as exc:
        logger.warning("get_validate_file_with_model: VM file fetch failed for %s: %s", file_path, exc)
        return False
    if content_bytes is None:
        logger.warning("get_validate_file_with_model: file not found on VM: %s", file_path)
        return False

    # ── Decode to text (replace undecodable bytes) ────────────────────────────
    try:
        file_text = content_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.error("get_validate_file_with_model: failed to decode file %s: %s", file_path, exc)
        return False

    truncated = file_text[:_MAX_FILE_CHARS]
    was_truncated = len(file_text) > _MAX_FILE_CHARS

    user_msg = _FILE_VALIDATE_USER.format(
        description=description,
        file_path=file_path,
        length=f"{len(truncated)}" + (" (truncated)" if was_truncated else ""),
        content=truncated,
    )

    messages = [
        {"role": "system", "content": _FILE_VALIDATE_SYSTEM},
        {"role": "user",   "content": user_msg},
    ]

    try:
        client, model = _build_client()
        logger.info(
            "Calling model '%s' for file validation (file: %s, truncated: %s)",
            model, file_path, was_truncated,
        )
        answer = _call_with_retry(client, model, messages)
        logger.info("Model answer for file validation: '%s'", answer)
        result = answer.strip().upper().startswith("YES")
        logger.info("get_validate_file_with_model: %s → %s", file_path, result)
        return result

    except EnvironmentError as exc:
        logger.error("get_validate_file_with_model skipped — %s", exc)
        return False
    except Exception as exc:
        logger.error("get_validate_file_with_model failed: %s", exc)
        return False


def get_file_contains(env, config) -> bool:
    """
    Return True if the file at ``file_path`` on the VM contains ALL of the
    specified keywords.

    Supports two config formats:
        expected_keywords  (list[str])  – every string in the list must appear in the file
        keyword / expected (str)        – a single string that must appear

    The check is case-sensitive plain-text search (not regex).
    Returns False if the file does not exist or cannot be fetched.
    """
    file_path = config.get("file_path", "").strip()
    if not file_path:
        logger.error("get_file_contains: 'file_path' not specified in config.")
        return False

    # ── Resolve keyword(s) ────────────────────────────────────────────────────
    keywords = config.get("expected_keywords")
    if keywords is None:
        single = config.get("keyword") or config.get("expected", "")
        keywords = [single] if single else []
    if not keywords:
        logger.warning("get_file_contains: no keywords specified; returning False.")
        return False

    # ── Fetch file bytes from VM ──────────────────────────────────────────────
    try:
        content_bytes = env.controller.get_file(file_path)
    except Exception as exc:
        logger.warning("get_file_contains: VM file fetch failed for %s: %s", file_path, exc)
        return False
    if content_bytes is None:
        logger.warning("get_file_contains: file not found on VM: %s", file_path)
        return False

    # Decode once for text search
    try:
        text = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    # ── Check every keyword ───────────────────────────────────────────────────
    missing = [kw for kw in keywords if kw not in text]
    if missing:
        logger.warning("get_file_contains: keywords not found in %s: %s", file_path, missing)
        return False

    logger.info("get_file_contains: all keywords found in %s: %s", file_path, keywords)
    return True
