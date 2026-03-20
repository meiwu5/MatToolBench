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