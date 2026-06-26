"""
WinPeek 环境自检 + 自愈 — Hermes 启动时运行一次

检查 5 项，能修就修，不能修警告。不阻塞 Hermes 启动。
"""
import os
import sys
import subprocess
import json
from pathlib import Path

_MQTT_HOST = os.environ.get("MQTT_HOST", "192.168.3.23")
_MQTT_PORT = 1883

_results: list[tuple[str, str, str]] = []  # (check, status, detail)


def _ok(check: str, detail: str = "") -> None:
    _results.append((check, "OK", detail))


def _fixed(check: str, detail: str = "") -> None:
    _results.append((check, "FIXED", detail))


def _warn(check: str, detail: str = "") -> None:
    _results.append((check, "WARN", detail))


def _fail(check: str, detail: str = "") -> None:
    _results.append((check, "FAIL", detail))


def _run_check(check_name: str) -> None:
    """Safe wrapper — never crash the caller."""


# ── 1. paho-mqtt ──────────────────────────────────────────────
def _find_pip() -> str | None:
    """Find the pip that belongs to the current python."""
    for cmd in [sys.executable.replace("python", "pip"),
                sys.executable.replace("python.exe", "pip.exe"),
                "pip", "pip3"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=5, check=False)
            return cmd
        except Exception:
            continue
    return None


def check_paho():
    try:
        import paho.mqtt.client  # noqa: F401
        _ok("paho-mqtt", "已安装")
    except ImportError:
        pip = _find_pip()
        if pip:
            try:
                subprocess.run([pip, "install", "paho-mqtt"],
                               capture_output=True, timeout=30, check=False)
                import paho.mqtt.client  # noqa: F401
                _fixed("paho-mqtt", f"安装完成 (pip={pip})")
            except Exception as e:
                _warn("paho-mqtt", f"安装失败: {e}")
        else:
            _warn("paho-mqtt", "未安装且找不到 pip")


# ── 2. agent.conf ─────────────────────────────────────────────
def _find_agent_conf() -> Path | None:
    candidates = [
        Path.home() / ".winpeek" / "agent.conf",
        Path.home() / ".hermes" / "data" / "agent.conf",
        Path.home() / ".claude" / "data" / "agent.conf",
        Path("agent.conf"),
        Path("bin") / "agent.conf",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _read_agent_conf(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_agent_conf():
    conf = _find_agent_conf()
    if conf:
        data = _read_agent_conf(conf)
        uid = data.get("hermes_uid", "?")
        host = data.get("mqtt_host", "?")
        port = data.get("mqtt_port", "?")
        _ok("agent.conf", f"{conf} (uid={uid} host={host}:{port})")
    else:
        default = Path.home() / ".hermes" / "data" / "agent.conf"
        try:
            default.parent.mkdir(parents=True, exist_ok=True)
            default.write_text(json.dumps({
                "hermes_uid": int(os.environ.get("WINPEEK_UID", 0)) or 0,
                "mqtt_host": _MQTT_HOST,
                "mqtt_port": _MQTT_PORT,
            }, indent=2), encoding="utf-8")
            _fixed("agent.conf", f"已创建 {default}")
        except Exception as e:
            _warn("agent.conf", f"创建失败: {e}")


# ── 3. say 命令 ────────────────────────────────────────────────
def _find_peekaboo_bin() -> str | None:
    """Locate PeekabooWin/bin/ on this machine."""
    candidates = [
        Path.home() / "PeekabooWin" / "bin",
        Path("C:/work/PeekabooWin/bin"),
        Path("D:/mydata/mycode/github/PeekabooWin/bin"),
    ]
    for d in candidates:
        if (d / "say.py").exists():
            return str(d.resolve())
    # Search HOME
    for root in [Path.home(), Path("C:/"), Path("D:/")]:
        try:
            for found in root.rglob("PeekabooWin/bin/say.py"):
                if found.exists():
                    return str(found.parent.resolve())
        except Exception:
            pass
    return None


def check_say():
    peekaboo_bin = _find_peekaboo_bin()
    if peekaboo_bin:
        say_path = Path(peekaboo_bin) / "say.py"
        if say_path.exists():
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            if peekaboo_bin in path_dirs:
                _ok("say", f"就绪 ({peekaboo_bin})")
            else:
                # 尝试自愈: 加到用户 PATH
                try:
                    result = subprocess.run(
                        ["setx", "PATH", f"{os.environ.get('PATH','')};{peekaboo_bin}"],
                        capture_output=True, timeout=5,
                    )
                    if result.returncode == 0:
                        _fixed("say", f"已加入PATH: {peekaboo_bin} (重启终端生效)")
                    else:
                        _warn("say", f"找到但不在PATH: {peekaboo_bin}")
                except Exception:
                    _warn("say", f"找到但不在PATH: {peekaboo_bin}")
            return
    _warn("say", "未找到PeekabooWin/bin/ → git clone PeekabooWin")


# ── 4. 环境变量 ────────────────────────────────────────────────
def check_env():
    issues = []
    if not os.environ.get("WINPEEK_UID"):
        issues.append("WINPEEK_UID")
    if not os.environ.get("WINPEEK_NAME"):
        issues.append("WINPEEK_NAME")
    if not os.environ.get("MQTT_HOST"):
        issues.append("MQTT_HOST")
    if issues:
        _warn("env", f"缺少: {', '.join(issues)}. 运行: setx VAR value")
    else:
        uid = os.environ["WINPEEK_UID"]
        name = os.environ["WINPEEK_NAME"]
        _ok("env", f"uid={uid} name={name}")


# ── 5. MQTT 连通 ────────────────────────────────────────────────
def check_mqtt():
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(_MQTT_HOST, _MQTT_PORT, 5)
        client.disconnect()
        _ok("mqtt", f"broker {_MQTT_HOST}:{_MQTT_PORT} 连通")
    except ImportError:
        _warn("mqtt", "paho-mqtt 未装，跳过")
    except Exception as e:
        _warn("mqtt", f"broker 不通: {e}")


# ── main ─────────────────────────────────────────────────────
CHECKS = [
    ("paho-mqtt", check_paho),
    ("agent.conf", check_agent_conf),
    ("say", check_say),
    ("env", check_env),
    ("mqtt", check_mqtt),
]


def run_all(print_report: bool = True) -> str:
    """Run all checks. Returns a 1-line summary string."""
    _results.clear()
    for name, fn in CHECKS:
        try:
            fn()
        except Exception as e:
            _fail(name, str(e))

    ok = sum(1 for _, s, _ in _results if s == "OK")
    fixed = sum(1 for _, s, _ in _results if s == "FIXED")
    warn = sum(1 for _, s, _ in _results if s == "WARN")
    fail = sum(1 for _, s, _ in _results if s == "FAIL")

    if print_report:
        parts = []
        if ok: parts.append(f"{ok}OK")
        if fixed: parts.append(f"{fixed}FIXED")
        if warn: parts.append(f"{warn}WARN")
        if fail: parts.append(f"{fail}FAIL")
        summary = f"[doctor] WinPeek自检: {', '.join(parts)}"
        print(summary, file=sys.stderr)
        for name, status, detail in _results:
            if status in ("WARN", "FAIL", "FIXED"):
                print(f"  [{status}] {name}: {detail}", file=sys.stderr)

    return f"{ok}OK/{fixed}FIX/{warn}WARN/{fail}FAIL"


if __name__ == "__main__":
    run_all()
