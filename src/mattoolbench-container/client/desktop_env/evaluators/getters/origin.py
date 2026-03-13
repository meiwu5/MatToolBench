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

_SYSTEM_PROMPT = (
    "You are a scientific figure evaluator. "
    "You will be shown a chart or plot produced by OriginPro and a description of what the figure should look like. "
    "Assess ONLY whether the figure satisfies every requirement stated in the description. "
    "Reply with exactly one word: 'true' if all requirements are met, 'false' otherwise. "
    "Do not add any explanation."
)

_USER_TEMPLATE = (
    "Description of the required figure:\n{description}\n\n"
    "Does the chart above satisfy ALL of the above requirements? Reply true or false."
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
                max_tokens=16,
                temperature=0.0,
            )
            return resp.choices[0].message.content.strip().lower()
        except openai.RateLimitError as exc:
            wait = backoff ** attempt
            logger.warning("Rate limit hit (attempt %d/%d), retrying in %.1fs: %s", attempt, retries, wait, exc)
            time.sleep(wait)
        except openai.APIError as exc:
            wait = backoff ** attempt
            logger.warning("API error (attempt %d/%d), retrying in %.1fs: %s", attempt, retries, wait, exc)
            time.sleep(wait)
    raise RuntimeError(f"Origin eval API call failed after {retries} attempts.")


# ---------------------------------------------------------------------------
# Public getter functions (called by the evaluator framework)
# ---------------------------------------------------------------------------

def get_file_exists(env, config) -> bool:
    """Return True if the file at config['file_path'] exists."""
    file_path = config.get("file_path")
    if not file_path:
        logger.warning("get_file_exists: 'file_path' not specified.")
        return False
    path = _resolve_path(file_path)
    exists = os.path.exists(path)
    if exists:
        logger.info("File exists: %s", path)
    else:
        logger.warning("File not found: %s", path)
    return exists


def get_validate_image_with_model(env, config) -> bool:
    """
    Use a vision LLM to check whether the output figure satisfies the task description.

    Expected config keys:
        file_path   (str)  – path to the output image (absolute or relative to output_result/)
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

    img_data = _load_image_as_base64(file_path)
    if img_data is None:
        logger.warning("get_validate_image_with_model: could not load image, scoring as False.")
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
        return "true" in answer
    except EnvironmentError as exc:
        logger.error("Origin eval skipped — %s", exc)
        return False
    except Exception as exc:
        logger.error("Origin eval failed: %s", exc)
        return False
