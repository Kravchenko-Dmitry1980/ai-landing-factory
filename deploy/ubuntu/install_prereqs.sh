#!/usr/bin/env bash
# Install prerequisites for AI Landing Factory on Ubuntu 22.04 / 24.04.
# TEMPLATE — run on the server after review. Does not deploy the app.
set -euo pipefail

echo "== apt update =="
sudo apt-get update -y

echo "== base packages =="
sudo apt-get install -y \
  curl \
  ca-certificates \
  gnupg \
  unzip \
  nginx \
  python3 \
  python3-venv \
  python3-pip

# Node.js 20.x (Nodesource)
if ! command -v node >/dev/null 2>&1; then
  echo "== install Node.js 20 =="
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
else
  echo "Node already present: $(node --version)"
fi

echo "== versions =="
python3 --version
node --version
npm --version
nginx -v

echo "Prereqs OK. Next: unpack release and follow README_FULL_SYSTEMD_DEPLOY.md"
