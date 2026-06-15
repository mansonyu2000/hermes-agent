#!/usr/bin/env python3
"""auto-upgrade.py — 每10分钟检查升级信号，自动 git pull + pip install -e
由 deploy-win.ps1 (计划任务) 或 deploy-ubuntu.sh (cron) 注册
"""
import json, os, subprocess, sys
from pathlib import Path

SIGNAL_FILE = os.environ.get("HERMES_UPGRADE_SIGNAL",
    r"\\192.168.3.23\projects\hermes-deploy\upgrade-signal" if sys.platform == "win32"
    else "/mnt/data/projects/hermes-deploy/upgrade-signal")

# 仓库 = 本脚本的上级目录
REPO = Path(__file__).resolve().parent.parent
STATE_FILE = Path.home() / ".hermes" / "upgrade-state.json"

def load_signal():
    try:
        with open(SIGNAL_FILE) as f:
            return json.load(f)
    except:
        return None

def load_state():
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except:
        return {}

def save_state(s):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s))

def main():
    signal = load_signal()
    if not signal:
        return

    state = load_state()
    current = signal.get("version")
    if current and current == state.get("version"):
        return

    action = signal.get("action", "upgrade")
    print(f"[hermes-upgrade] {action} → {current}")

    os.chdir(REPO)

    if action == "upgrade":
        subprocess.run(["git", "pull", "origin", "main"], check=False)
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".", "-q"], check=False)

    save_state({"version": current, "ts": signal.get("ts", "")})
    print(f"[hermes-upgrade] done")

if __name__ == "__main__":
    main()
