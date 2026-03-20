$scriptFolder = "\\host.lan\Data"
$pythonScriptFile = "$scriptFolder\server\main.py"
$pythonServerPort = 5000

# ---------------------------------------------------------------------------
# Configure HTTP proxy so Python scripts (mp_api, requests, urllib) can reach
# external APIs (materialsproject.org, oqmd.org, etc.) via the container's
# tinyproxy running on the Docker bridge at 20.20.20.1:8888.
# ---------------------------------------------------------------------------
$proxyAddr = "http://20.20.20.1:8888"
[System.Environment]::SetEnvironmentVariable("HTTP_PROXY",  $proxyAddr, "Machine")
[System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", $proxyAddr, "Machine")
[System.Environment]::SetEnvironmentVariable("http_proxy",  $proxyAddr, "Machine")
[System.Environment]::SetEnvironmentVariable("https_proxy", $proxyAddr, "Machine")
# Bypass proxy for localhost and the VM server itself
[System.Environment]::SetEnvironmentVariable("NO_PROXY", "localhost,127.0.0.1,20.20.20.1", "Machine")
Write-Host "Proxy configured: $proxyAddr"

# Start the Caddy reverse proxy in a non-blocking manner
Write-Host "Running the Caddy reverse proxy from port 9222 to port 1337"
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "caddy reverse-proxy --from :9222 --to :1337"

# Start the mattoolbench server
Write-Host "Running the mattoolbench server on port $pythonServerPort..."
python $pythonScriptFile --port $pythonServerPort
