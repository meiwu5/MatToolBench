#!/bin/bash

echo "Initializing Compute VM at startup..."

# Install dos2unix (non-interactive to avoid GUI prompts)
export DEBIAN_FRONTEND=noninteractive
sudo -E apt-get install -y -q dos2unix

# Stop dnsmasq running on port 53
sudo systemctl stop systemd-resolved

# Stop DNS service on port 53
sudo systemctl stop named.service

# Stop nginx running on port 80
sudo service nginx stop
