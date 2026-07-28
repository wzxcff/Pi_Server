#!/bin/bash

set -e

echo "=================================================="
echo "        Clean System Initialization RPI5          "
echo "=================================================="

echo "[1/7] Run system update..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git ufw

echo "[2/7] Downloading Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
else
    echo "Docker already installed."
fi

echo "Adding $USER to docker group..."
sudo usermod -aG docker $USER

echo "[3/7] Downloading Cockpit..."
sudo apt install -y cockpit
sudo systemctl enable --now cockpit.socket

echo "[4/7] Downloading Tailscale..."
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "Tailscale already installed."
fi

echo "[5/7] Saving Wi-Fi profile 'FREE WIFI FN'..."
sudo iw dev wlan0 set power_save off || true

if ! nmcli connection show "FREE WIFI FN" &> /dev/null; then
    sudo nmcli connection add type wifi con-name "FREE WIFI FN" ifname wlan0 ssid "FREE WIFI FN"
    sudo nmcli connection modify "FREE WIFI FN" autoconnect no
    echo "Profile 'FREE WIFI FN' successfully added (autoconnection off)."
else
    echo "Profile 'FREE WIFI FN' already exists."
fi

echo "[6/7] Configuring UFW (Access only through Tailscale in local network)..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow in on tailscale0 comment 'Allow all via Tailscale'

sudo ufw allow in on eth0 comment 'Allow local Ethernet access' || true
sudo ufw allow in on end0 comment 'Allow local Ethernet access' || true

sudo ufw --force enable

echo "[7/7] Starting Tailscale auth..."
echo "Auth link will pop up now"
echo "--------------------------------------------------"
sudo tailscale up

echo "=================================================="
echo "        System configured successfully!           "
echo "=================================================="
echo "IMPORTANT: Run 'newgrp docker' or re-loggin ssh,"
echo "or docker command will not work without sudo"

