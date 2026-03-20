#!/bin/bash

echo "Starting mattoolbench VM..."

# ---------------------------------------------------------------------------
# Start tinyproxy so the Windows VM can reach the internet via this container.
# The VM subnet is 20.20.20.0/24; Python scripts on the VM should use
# http://20.20.20.1:8888 as their HTTPS_PROXY (set in on-logon.ps1).
#
# Optional env var:
#   UPSTREAM_PROXY  – if this container also needs a proxy to reach the
#                     internet, e.g. http://corporate-proxy:3128
# ---------------------------------------------------------------------------
TINYPROXY_PORT=8888
cat > /tmp/tinyproxy.conf <<EOF
User root
Port ${TINYPROXY_PORT}
Listen 0.0.0.0
Timeout 600
LogLevel Warning
MaxClients 100
Allow 127.0.0.1
Allow 20.20.20.0/24
DisableViaHeader Yes
EOF

if [ -n "${UPSTREAM_PROXY:-}" ]; then
    echo "Upstream ${UPSTREAM_PROXY}" >> /tmp/tinyproxy.conf
    echo "tinyproxy: forwarding via upstream proxy ${UPSTREAM_PROXY}"
fi

tinyproxy -c /tmp/tinyproxy.conf
echo "tinyproxy started on 0.0.0.0:${TINYPROXY_PORT}"

# Start the VM script in the background
cd / # Fix for Azure ML Job not using the correct root path
./start_vm.sh &

# Wait for the VM to start up
while true; do
  # Send a GET request to the specified URL
  response=$(curl --write-out '%{http_code}' --silent --output /dev/null 20.20.20.21:5000/probe)

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
# tinyproxy running in this container.
# Uses 'setx' (user-level, no admin needed) so all new child processes
# spawned by the Flask server will inherit the proxy settings.
# ---------------------------------------------------------------------------
PROXY_ADDR="http://20.20.20.1:${TINYPROXY_PORT}"
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

# ---------------------------------------------------------------------------
# Proxy self-test: verify tinyproxy is reachable and the VM can access the internet
# ---------------------------------------------------------------------------
echo "=== Proxy self-test ==="
# 1. Container side: tinyproxy itself can reach the internet
echo -n "[container→internet] api.materialsproject.org: "
curl -s --proxy "http://127.0.0.1:${TINYPROXY_PORT}" --connect-timeout 10 \
    -o /dev/null -w "%{http_code}" https://api.materialsproject.org/heartbeat \
    && echo "" || echo "FAIL"

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