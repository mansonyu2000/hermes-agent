#!/bin/bash
# deploy-ubuntu.sh — Hermes + WinPeek 开发机一键部署
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$HOME/mydata/mycode/github"
WINPEEK="$WORK/winpeek-prod"

echo "=== Hermes + WinPeek 开发机部署 ==="

# 1. Python 3.12
if ! python3.12 --version &>/dev/null; then
    echo "[1/5] Python 3.12..."
    sudo apt update -qq && sudo apt install -y -qq python3.12 python3.12-venv python3-pip
else echo "[1/5] Python 3.12 OK"; fi

# 2. WinPeek-prod
echo "[2/5] WinPeek-prod..."
if [ ! -d "$WINPEEK" ]; then
    mkdir -p "$WORK"
    git clone http://gitlab.test.com:8080/mansonyu/PeekabooWin.git "$WINPEEK"
else
    cd "$WINPEEK" && git pull origin prod
fi

# 3. Hermes
echo "[3/5] pip install hermes..."
pip install -e "$REPO" -q

# 4. WinPeek
echo "[4/5] pip install winpeek-say..."
pip install -e "$WINPEEK/bin" -q

# 5. 定时任务
echo "[5/5] 注册定时任务..."
(crontab -l 2>/dev/null | grep -v 'hermes-upgrade\|winpeek-health'; cat <<CRON
*/10 * * * * python3 $REPO/deploy/auto-upgrade.py
*/5 * * * * python3 $WINPEEK/bin/health-check.py
CRON
) | crontab -

echo "=== 部署完成 ==="
echo "Hermes: hermes"
echo "WinPeek: cd $WINPEEK"
