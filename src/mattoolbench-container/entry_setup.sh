#!/bin/bash

echo "Starting mattoolbench VM..."

# ---------------------------------------------------------------------------
# Start HTTP/HTTPS proxy so the Windows VM can reach the internet.
# Uses a pure-Python CONNECT proxy — no system packages needed.
# The VM subnet is 20.20.20.0/24; Python scripts on the VM should use
# http://20.20.20.1:18889 as their HTTPS_PROXY.
#
# Optional env var:
#   UPSTREAM_PROXY  – upstream proxy for this container, e.g. http://corp:3128
# ---------------------------------------------------------------------------
PROXY_PORT=18889

cat > /tmp/pyproxy.py <<'PYEOF'
#!/usr/bin/env python3
"""Minimal HTTP CONNECT proxy (supports HTTPS tunnelling and plain HTTP)."""
import socket, threading, select, os, sys, urllib.parse

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.environ.get("PROXY_PORT", 18889))
UPSTREAM    = os.environ.get("UPSTREAM_PROXY", "")   # optional: http://host:port
BUFSIZE     = 65536

def _upstream_connect(host, port):
    if UPSTREAM:
        u = urllib.parse.urlsplit(UPSTREAM if UPSTREAM.startswith("http") else "http://"+UPSTREAM)
        s = socket.create_connection((u.hostname, u.port or 8080), timeout=30)
        s.sendall(f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n".encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += s.recv(4096)
        if b"200" not in resp.split(b"\r\n")[0]:
            raise ConnectionError(f"Upstream CONNECT failed: {resp[:80]}")
        return s
    return socket.create_connection((host, port), timeout=30)

def _relay(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 60)
            if not r:
                break
            for s in r:
                data = s.recv(BUFSIZE)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except Exception:
        pass

def handle(conn, addr):
    try:
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                return
            data += chunk
        first = data.split(b"\r\n")[0].decode(errors="replace")
        method, target, _ = first.split()
        if method.upper() == "CONNECT":
            host, port = target.rsplit(":", 1)
            remote = _upstream_connect(host, int(port))
            conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            t = threading.Thread(target=_relay, args=(conn, remote), daemon=True)
            t.start()
            _relay(remote, conn)
            t.join()
        else:
            # Plain HTTP — forward the full request
            parsed = urllib.parse.urlsplit(target)
            host = parsed.hostname
            port = parsed.port or 80
            remote = socket.create_connection((host, port), timeout=30)
            remote.sendall(data)
            _relay(conn, remote)
    except Exception:
        pass
    finally:
        conn.close()

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind((LISTEN_HOST, LISTEN_PORT))
srv.listen(128)
print(f"pyproxy listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
while True:
    conn, addr = srv.accept()
    threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
PYEOF

PROXY_PORT=${PROXY_PORT} UPSTREAM_PROXY="${UPSTREAM_PROXY:-}" python3 /tmp/pyproxy.py &
PROXY_PID=$!
echo "pyproxy started (PID ${PROXY_PID}) on 0.0.0.0:${PROXY_PORT}"

# Watchdog: restart proxy if it dies
(while true; do
    sleep 30
    if ! kill -0 ${PROXY_PID} 2>/dev/null; then
        echo "pyproxy died, restarting..."
        PROXY_PORT=${PROXY_PORT} UPSTREAM_PROXY="${UPSTREAM_PROXY:-}" python3 /tmp/pyproxy.py &
        PROXY_PID=$!
    fi
done) &

# Start the VM script in the background
cd / # Fix for Azure ML Job not using the correct root path
./start_vm.sh &

# Wait for the VM to start up
while true; do
  response=$(no_proxy=20.20.20.0/24 curl --write-out '%{http_code}' --silent --output /dev/null 20.20.20.21:5000/probe)

  # If the response code is 200 (HTTP OK), break the loop
  if [ $response -eq 200 ]; then
    break
  fi

  echo "Waiting for a response from the windows server. This might take a while..."

  # Wait for a while before the next attempt
  sleep 5
done

echo "VM is up and running, and the Windows Arena Server is ready to use!"

# ---------------------------------------------------------------------------
# Inject proxy environment variables into the running Windows VM so that
# Python scripts (mp_api, requests, urllib) route HTTPS traffic through
# pyproxy running in this container.
# Uses 'setx' (user-level, no admin needed) so all new child processes
# spawned by the Flask server will inherit the proxy settings.
# ---------------------------------------------------------------------------
PROXY_ADDR="http://20.20.20.1:${PROXY_PORT}"
VM_API="http://20.20.20.21:5000/setup/execute"

for VAR in HTTPS_PROXY HTTP_PROXY https_proxy http_proxy; do
    curl -s -X POST "${VM_API}" \
        -H "Content-Type: application/json" \
        -d "{\"command\": [\"setx\", \"${VAR}\", \"${PROXY_ADDR}\"], \"shell\": false}" \
        > /dev/null
done
# Bypass proxy for local addresses
curl -s -X POST "${VM_API}" \
    -H "Content-Type: application/json" \
    -d '{"command": ["setx", "NO_PROXY", "localhost,127.0.0.1,20.20.20.1"], "shell": false}' \
    > /dev/null

echo "Proxy env vars injected into VM: ${PROXY_ADDR}"

# Inject MP_API_KEY into the VM.
# Two-pronged approach:
#   1. setx → persists to registry (survives future shell sessions)
#   2. /execute_windows → sets os.environ in the live Flask server process so
#      all subprocesses spawned by Flask immediately inherit the variable.
#      (setx alone does NOT update already-running processes.)
if [ -n "${MP_API_KEY:-}" ]; then
    # Registry persistence
    curl -s -X POST "${VM_API}" \
        -H "Content-Type: application/json" \
        -d "{\"command\": [\"setx\", \"MP_API_KEY\", \"${MP_API_KEY}\"], \"shell\": false}" \
        > /dev/null
    # Live Flask process environment
    curl -s -X POST "http://20.20.20.21:5000/execute_windows" \
        -H "Content-Type: application/json" \
        -d "{\"command\": \"import os; os.environ['MP_API_KEY'] = '${MP_API_KEY}'\"}" \
        > /dev/null
    echo "MP_API_KEY injected into VM (registry + live Flask env)"
else
    echo "WARNING: MP_API_KEY not set in container env — mp_api tasks may fail"
fi

# ---------------------------------------------------------------------------
# Pin mp-api / emmet-core on the VM Python 3.12 installation (once per boot).
# ---------------------------------------------------------------------------
PYTHON312="C:\\Users\\Docker\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
curl -s -X POST "${VM_API}" \
    -H "Content-Type: application/json" \
    -d "{\"command\": [\"${PYTHON312}\", \"-m\", \"pip\", \"install\", \"--quiet\",
        \"--disable-pip-version-check\", \"mp-api==0.39.5\", \"emmet-core==0.78.7\"],
        \"shell\": false}" \
    > /dev/null
echo "mp-api==0.39.5 emmet-core==0.78.7 pinned on VM (Python 3.12)"

# ---------------------------------------------------------------------------
# Ensure the 'optimade' venv has requests and optimade[server].
# Do NOT install optimade-client (OptimadeClient) — it is too heavy and has
# connection issues.  The base optimade package + optimade[server] extras
# provide the models / filter utilities without the heavy client stack.
# ---------------------------------------------------------------------------
OPTIMADE_PYTHON="C:\\Users\\Docker\\optimade\\Scripts\\python.exe"
curl -s -X POST "${VM_API}" \
    -H "Content-Type: application/json" \
    -d "{\"command\": [\"${OPTIMADE_PYTHON}\", \"-m\", \"pip\", \"install\", \"--quiet\",
        \"--disable-pip-version-check\", \"requests\", \"optimade[server]\"],
        \"shell\": false}" \
    > /dev/null
echo "requests + optimade[server] installed in optimade venv (no optimade-client)"

# ---------------------------------------------------------------------------
# Proxy self-test: verify tinyproxy is reachable and the VM can access the internet
# ---------------------------------------------------------------------------
echo "=== Proxy self-test ==="
# 1. Container side: proxy itself can reach the internet
echo -n "[container→internet] api.materialsproject.org: "
curl -s --proxy "http://127.0.0.1:${PROXY_PORT}" --connect-timeout 10 \
    -o /dev/null -w "%{http_code}" https://api.materialsproject.org/heartbeat \
    && echo "" || echo "FAIL"

# 1b. Container direct access to LLM API (agent calls this directly, no proxy)
echo -n "[container→internet] api.xi-ai.cn/v1/models: "
curl -s --connect-timeout 10 \
    -o /dev/null -w "%{http_code}" https://api.xi-ai.cn/v1/models \
    && echo "" || echo "FAIL (agent LLM calls will fail!)"

# 2. VM side: check HTTPS_PROXY was set
echo -n "[VM] HTTPS_PROXY value: "
curl -s -X POST "${VM_API}" \
    -H "Content-Type: application/json" \
    -d '{"command": ["cmd", "/c", "echo %HTTPS_PROXY%"], "shell": false}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output','').strip())"

# 3. VM side: Python requests via proxy
echo -n "[VM→proxy→internet] Python requests test: "
curl -s -X POST "${VM_API}" \
    -H "Content-Type: application/json" \
    -d '{"command": ["python", "-c", "import requests; r=requests.get(\"https://api.materialsproject.org/heartbeat\", timeout=15); print(r.status_code)"], "shell": false}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output','').strip() or d.get('error','').strip()[:80])"
echo "=== End proxy self-test ==="