"""
Test API connection to a given base URL.
Usage:
    python scripts/test_api_connection.py [--base_url URL] [--api_key KEY] [--model MODEL]
"""

import argparse
import time
import sys

def test_connection(base_url: str, api_key: str, model: str):
    print(f"Base URL : {base_url}")
    print(f"Model    : {model}")
    print(f"API Key  : {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}")
    print("=" * 50)

    try:
        import httpx
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
        import httpx

    # ── 1. TCP connectivity ──────────────────────────────────────────────────
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    print(f"\n[1] TCP connect → {host}:{port}")
    import socket
    t0 = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        print(f"    ✅ OK ({(time.time()-t0)*1000:.0f} ms)")
    except Exception as e:
        print(f"    ❌ FAILED: {e}")
        return

    # ── 2. GET /models ───────────────────────────────────────────────────────
    models_url = base_url.rstrip("/") + "/models"
    print(f"\n[2] GET {models_url}")
    t0 = time.time()
    try:
        with httpx.Client(timeout=15, trust_env=False) as client:
            resp = client.get(models_url, headers={"Authorization": f"Bearer {api_key}"})
        elapsed = (time.time() - t0) * 1000
        print(f"    Status : {resp.status_code}  ({elapsed:.0f} ms)")
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("id", m) for m in data.get("data", [])]
            print(f"    Models : {models[:10]}" + (" ..." if len(models) > 10 else ""))
        else:
            print(f"    Body   : {resp.text[:300]}")
    except Exception as e:
        print(f"    ❌ FAILED: {e}")
        return

    # ── 3. Chat completion (non-streaming) ──────────────────────────────────
    chat_url = base_url.rstrip("/") + "/chat/completions"
    print(f"\n[3] POST {chat_url}  (non-streaming)")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word: OK"}],
        "max_tokens": 8,
        "stream": False,
    }
    t0 = time.time()
    try:
        with httpx.Client(timeout=30, trust_env=False) as client:
            resp = client.post(chat_url,
                               json=payload,
                               headers={"Authorization": f"Bearer {api_key}",
                                        "Content-Type": "application/json"})
        elapsed = (time.time() - t0) * 1000
        print(f"    Status : {resp.status_code}  ({elapsed:.0f} ms)")
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            usage   = resp.json().get("usage", {})
            print(f"    Reply  : {content!r}")
            print(f"    Usage  : {usage}")
        else:
            print(f"    Body   : {resp.text[:300]}")
    except Exception as e:
        print(f"    ❌ FAILED: {e}")
        return

    # ── 4. Chat completion (streaming) ──────────────────────────────────────
    print(f"\n[4] POST {chat_url}  (streaming)")
    payload["stream"] = True
    t0 = time.time()
    try:
        chunks = []
        with httpx.Client(timeout=30, trust_env=False) as client:
            with client.stream("POST", chat_url,
                               json=payload,
                               headers={"Authorization": f"Bearer {api_key}",
                                        "Content-Type": "application/json"}) as resp:
                ttfb = None
                for line in resp.iter_lines():
                    if ttfb is None and line:
                        ttfb = (time.time() - t0) * 1000
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        delta = json.loads(line[6:])
                        if delta.get("choices"):
                            piece = delta["choices"][0]["delta"].get("content", "")
                            chunks.append(piece)
        total = (time.time() - t0) * 1000
        print(f"    Status : {resp.status_code}")
        print(f"    TTFB   : {ttfb:.0f} ms  |  Total: {total:.0f} ms")
        print(f"    Reply  : {''.join(chunks)!r}")
    except Exception as e:
        print(f"    ❌ FAILED: {e}")

    print("\n" + "=" * 50)
    print("All tests done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_url", default="https://api.xi-ai.cn/v1")
    parser.add_argument("--api_key",  default="sk-YOUR_KEY_HERE")
    parser.add_argument("--model",    default="gpt-4o-mini")
    args = parser.parse_args()

    if args.api_key == "sk-YOUR_KEY_HERE":
        print("[WARN] No API key provided, /models may work but chat will fail.")
        print("       Use: python scripts/test_api_connection.py --api_key sk-xxx\n")

    test_connection(args.base_url, args.api_key, args.model)
