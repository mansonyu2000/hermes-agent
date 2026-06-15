#!/bin/bash
# deploy-ubuntu.sh — Hermes Agent Ubuntu 一键部署
# 用法: git pull 后在仓库根目录运行  bash deploy/deploy-ubuntu.sh

set -e
SHARE="/mnt/data/projects/hermes-deploy"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Hermes Agent 部署 ==="

# 1. Python 3.12
if ! python3.12 --version &>/dev/null; then
    echo "[1/3] 安装 Python 3.12..."
    sudo apt update -qq && sudo apt install -y -qq python3.12 python3.12-venv python3-pip
fi

# 2. 安装依赖
echo "[2/3] pip install -e ..."
pip install -e "$REPO" -q

# 3. 升级钩子
echo "[3/3] 注册升级监控(每10分钟)..."
(crontab -l 2>/dev/null | grep -v hermes-upgrade; echo "*/10 * * * * python3 $REPO/deploy/auto-upgrade.py") | crontab -

echo "=== 完成 ==="
echo "启动: hermes"
