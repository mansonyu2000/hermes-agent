#!/usr/bin/env python3
"""agent-role.py — select identity, generate CLAUDE.md, launch Claude/Qoder.

Usage:
    python bin/agent-role.py                          # interactive
    python bin/agent-role.py Architect                # pick role
    python bin/agent-role.py Developer 大海           # pick role + nickname
    python bin/agent-role.py --resume <id>            # resume session

Config priority:
    1. ~/.winpeek/agent.conf   (migrated from WinPeek)
    2. ~/.hermes/agent.conf    (hermes-native)
    3. First-time init         (creates default)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

# ── Paths ─────────────────────────────────────────────────
HERMES_CONF = Path.home() / ".hermes" / "agent.conf"
WINPEEK_CONF = Path.home() / ".winpeek" / "agent.conf"
HERMES_DATA = Path.home() / ".hermes" / "data"
WINPEEK_DATA = Path.home() / ".winpeek" / "data"

CLAUDE_MD = ROOT / "CLAUDE.md"
CLAUDE_MODULE = ROOT / "CLAUDE-module.md"

ROLES = ["Developer", "Architect", "Ops", "QA", "PM", "Director", "Boss"]
ROLE_DESCS = {
    "Developer": "programmer - coding/bugfix/feature",
    "Architect": "architect - system design/DB/tech",
    "Ops": "ops - server/deployment/monitor",
    "QA": "QA - test/CI/coverage/bug report",
    "PM": "PM - task/沟通/团队协调",
    "Director": "director - 跨组协调/决策",
    "Boss": "boss - all/overview",
}

# ── 1. Config loading ──────────────────────────────

def load_conf() -> dict:
    """Load config: ~/.hermes/agent.conf > ~/.winpeek/agent.conf > first-time init."""
    for conf_path in [HERMES_CONF, WINPEEK_CONF]:
        if conf_path.exists():
            try:
                return json.loads(conf_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  [WARN] Bad {conf_path}: {e}")
    return first_time_init()


def first_time_init() -> dict:
    """First-run: create default config."""
    HERMES_CONF.parent.mkdir(parents=True, exist_ok=True)
    HERMES_DATA.mkdir(parents=True, exist_ok=True)

    minimal = {
        "mqtt_host": "192.168.3.23",
        "mqtt_port": 1883,
        "winpeek_hub": "http://192.168.3.44:2000",
        "roles": ROLES,
    }
    HERMES_CONF.write_text(json.dumps(minimal, indent=2, ensure_ascii=False) + "\n")
    print(f"  ✓ Created default config: {HERMES_CONF}")
    print(f"  Next: edit {HERMES_CONF} if needed, then run again.\n")
    return minimal


# ── 2. Identity registry (local cache) ─────────────

ID_FILE = SCRIPT_DIR / "identity-registry.json"

def load_identities() -> list[dict]:
    if ID_FILE.exists():
        data = json.loads(ID_FILE.read_text(encoding="utf-8"))
        return list(data.get("identities", {}).values())
    return []


def save_identity(nick: str, uid: int, role: str):
    data = {"next_uid": uid + 1, "identities": {}}
    if ID_FILE.exists():
        data = json.loads(ID_FILE.read_text(encoding="utf-8"))
    key = nick.lower().replace(" ", "-")
    data["identities"][key] = {
        "uid": uid,
        "nickname": nick,
        "role": role,
        "host": os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")),
        "registered": __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
    }
    ID_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ── 3. Hub registration ────────────────────────────

def register(nick: str, role: str, known_uid: int | None = None) -> tuple[int, str, str]:
    """Register/login via WinPeek Hub, fallback to offline mode."""
    uid = known_uid
    hub = load_conf().get("winpeek_hub", "http://192.168.3.44:2000")
    import urllib.request

    payload = json.dumps({
        "nickname": nick,
        "role": role,
        "host": os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")),
    }).encode()

    if known_uid:
        url = f"{hub}/api/identities/login"
    else:
        url = f"{hub}/api/identities/register"

    try:
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            uid = result.get("uid", known_uid)
            nick = result.get("nickname", nick)
            role = result.get("role", role)
            print(f"  [OK] Hub registered: {nick}(uid={uid}) role={role}")
    except Exception as e:
        uid = uid or 0
        print(f"  [WARN] Hub offline ({e}), using local uid={uid}")
        save_identity(nick, uid, role)
    return uid, nick, role


# ── 4. CLAUDE.md generation ────────────────────────

def generate_claude_md(uid: int, nick: str, role: str, mqtt_host: str):
    """Generate CLAUDE.md = CLAUDE-module.md + identity header."""
    module_rules = ""
    if CLAUDE_MODULE.exists():
        module_rules = CLAUDE_MODULE.read_text(encoding="utf-8")

    header = f"""# Hermes Agent: {nick} (uid={uid})
Role: {role}. HERMES_HOME={Path.home() / '.hermes'} MQTT_HOST={mqtt_host}
## Communication
say <uid> "message"
## Contacts: central directory — curl http://192.168.3.44:2000/api/contacts
## Iron Rules
Don't kill processes. Ask before modifying config.yaml. Use say command for all inter-agent communication.
"""

    CLAUDE_MD.write_text(header + "\n" + module_rules, encoding="utf-8")
    print(f"  [OK] CLAUDE.md generated: {nick}-{role}-{uid}")


# ── 5. Main ──

def main():
    cfg = load_conf()
    mqtt_host = os.environ.get("MQTT_HOST") or cfg.get("mqtt_host") or "192.168.3.23"
    resume_id = None

    args = [a for a in sys.argv[1:] if not a.startswith("--resume")]
    for a in sys.argv[1:]:
        if a == "--resume":
            idx = sys.argv.index(a)
            resume_id = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""

    role_arg = args[0].capitalize() if args else None
    nick_arg = args[1] if len(args) > 1 else None

    cached = load_identities()
    known_uid = None

    if role_arg and role_arg in [r.capitalize() for r in ROLES]:
        role = role_arg
        nick = nick_arg or os.environ.get("USERNAME", os.environ.get("USER", "anon"))
        for c in cached:
            if c.get("nickname", "").lower() == nick.lower():
                known_uid = c["uid"]
                break
    else:
        # Interactive
        print("\n═══ Hermes Agent — Identity Setup ═══\n")
        nick_arg = input(f"  Display name [{os.environ.get('USERNAME', 'anon')}]: ").strip()
        nick = nick_arg or os.environ.get("USERNAME", "anon")
        for c in cached:
            if c.get("nickname", "").lower() == nick.lower():
                known_uid = c["uid"]
                role = c.get("role", "")
                print(f"  → Existing identity: {nick}(uid={known_uid}) role={role}")
                break

        if not known_uid:
            print("\n  Select role:")
            for i, r in enumerate(ROLES, 1):
                desc = ROLE_DESCS.get(r, "")
                print(f"    {i}. {r:12s} — {desc}")
            role_idx = input(f"\n  Role [1]: ").strip()
            role = ROLES[max(0, (int(role_idx) - 1) if role_idx.isdigit() else 0)]

    # Register / login
    uid, nick, role = register(nick, role, known_uid)

    # Generate CLAUDE.md
    generate_claude_md(uid, nick, role, mqtt_host)

    os.environ["HERMES_UID"] = str(uid)
    os.environ["HERMES_NAME"] = nick
    os.environ["MQTT_HOST"] = mqtt_host

    # Add bin/ to PATH so `say` command is available
    bin_dir = str(SCRIPT_DIR.resolve())
    path_sep = ";" if sys.platform == "win32" else ":"
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = bin_dir + path_sep + os.environ.get("PATH", "")
        # Persist for future sessions
        try:
            import subprocess
            subprocess.run(["setx", "PATH", bin_dir + path_sep + "%PATH%"],
                          capture_output=True, timeout=5, shell=True)
        except Exception:
            pass

    print(f"\n  HERMES_UID={uid}  Ready.  bin/{path_sep} added to PATH.")
    print(f"  Run: claude (or hermes) to start working.\n")


if __name__ == "__main__":
    main()
