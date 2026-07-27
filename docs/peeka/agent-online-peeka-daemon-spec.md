---
title: "Peeka Daemon Agent 在线管理 — 技术方案"
type: "design"
phase: "plan"
module: "mim"
version: "v2"
status: "draft"
last_updated: "2026-07-27"
author_subagent: "Claude Code"
references:
  - "docs/peeka/agent-online-reference-multica.md — Multica Daemon 参考方案"
  - "D:/mydata/mycode/github/multica/server/internal/daemon/daemon.go — Multica Daemon 核心代码"
  - "D:/mydata/mycode/github/multica/CLI_AND_DAEMON.md — Multica CLI & Daemon 文档"
related:
  - "./mim-message-delivery-spec.md"
  - "./mim-architecture-dev-doc.md"
  - "./agent-online-reference-multica.md"
---

# Peeka Daemon Agent 在线管理 — 技术方案

## 1. 背景

当前 Peeka Daemon 通过**配置文件检测**（`os.path.exists`）判断 Agent 是否安装，但无法区分"已安装"和"正在运行"。导致问题：
- 55 个节点全部显示在线（identity DB 里所有用户都被心跳）
- Gateway 重启后节点状态丢失（只有 JSON 持久化，没有主动注册）
- Agent 上线/下线不可靠

## 2. 设计目标

1. **精确在线检测**：只有真正在运行的 Agent 才标记为 online
2. **Agent 自汇报**：Agent 启动时主动向 Daemon 注册，运行时维持心跳
3. **Daemon 兜底**：Daemon 周期扫描，清理死节点，补注册遗漏
4. **退出即离线**：Agent 进程退出后自动标记 offline
5. **零侵入**：不修改 Agent 源码（通过 MCP tool / prompt 注入实现自汇报）

## 3. 借鉴 Multica 的部分

| 特性 | Multica 做法 | 我们采用 | 参考 |
|------|-------------|---------|------|
| Agent 检测 | `exec.LookPath` + `--version` 扫描 PATH | **PATH 扫描**，比文件检测更可靠 | `daemon.go L87-97` |
| 注册机制 | Daemon 代注册所有 runtime | **Daemon 代注册**，调用 `hub.register_node()` | `daemon.go L917-987` |
| 心跳粒度 | 每个 runtime 独立 goroutine, 15s | **统一循环 30s**，按需切换独立 goroutine | `daemon.go L1916-1955` |
| 双通道心跳 | HTTP + WebSocket，WS 正常时抑制 HTTP | **MQTT + HTTP 双通道**（MQTT 活动即心跳） | `daemon.go L689-711` |
| 退出清理 | `deregisterRuntimes()` 全部标记离线 | **Daemon 退出时清空本机节点** | `daemon.go L817-833` |
| 恢复机制 | `handleRuntimeGone` 防 stampede，30s 合并窗口 | **重新注册窗口 30s** | `daemon.go L341-391` |
> 以上参考行号均来自本地仓库: `D:/mydata/mycode/github/multica/server/internal/daemon/daemon.go`

## 4. 架构设计

```
Peeka Daemon 生命周期
─────────────────────────────────────────────────────────────────

  启动 (Gateway boot → hub_bridge.try_load_hub())
  │
  ├─ 1. detect_agents()
  │     ├─ PATH 扫描: hermes --version / claude --version / qoder --version
  │     ├─ 成功 → 记录到 _daemon_state.runtimes
  │     └─ 失败 → 跳过 (Agent 未安装)
  │
  ├─ 2. register_all()
  │     对每个检测到的 Agent:
  │       ├─ 如果还没有 identity → 自动注册到 identity DB
  │       ├─ hub.register_node(uid, name, agent_type, hostname)
  │       └─ _init_inbox(uid) + _inject_agent_prompt(uid)
  │
  ├─ 3. start_heartbeat_loop(30s)
  │     对 _daemon_state.runtimes 中注册成功(uid不为空)的:
  │       ├─ check_process_alive()  ← 🆕 进程存活检查
  │       ├─ alive → hub.heartbeat(uid)
  │       └─ dead  → 从 runtimes 中移除, 等待重新检测
  │
  ├─ 4. start_sweeper_loop(120s)
  │     hub.sweep_dead_nodes() — 无心跳超过 120s 的标记 offline
  │
  └─ 5. on_shutdown (atexit)
        hub.disconnect_all() — 本机所有节点标记 offline
```

## 5. Agent 自汇报机制

### 5.1 Hermes CLI (已实现)

```python
# cli.py 启动时
hub.register_node(cfg["uid"], socket.gethostname(), "Agent", socket.gethostname())

# cli.py 主循环每 30s
hub.heartbeat(cfg["uid"])
```

### 5.2 Claude Code (计划通过 MCP tool)

CC 没有源代码修改权限，但 Daemon 注入了 `winpeek-mim` MCP server。CC 调用 `winpeek_mim_login` 时触发心跳：

```python
# tools/winpeek_tools.py _handle_mim_login()
result = identity.login(nickname, password)
if result:
    hub.register_node(result["uid"], nickname, "Agent", socket.gethostname())
    hub.heartbeat(result["uid"])
```

CC 后续每次 MQTT 活动（收/发消息）自动更新 `last_seen` → 保持 online。

### 5.3 Qoder/TraeCLI (计划同 Hermes)

如果 Qoder/TraeCLI 的源码可修改，同 Hermes 方案。否则走 MCP 方案同 CC。

## 6. 进程存活检查 (替代文件检测)

```python
def check_process_alive(agent_type: str) -> bool:
    """检查 Agent 进程是否在运行。通过窗口标题或进程名模糊匹配。"""
    titles = {"claude-code": "Claude Code", "hermes": "Hermes", "qoder": "Qoder"}
    title = titles.get(agent_type, agent_type)
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"WINDOWTITLE eq {title}*", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return "No tasks" not in result.stdout and bool(result.stdout.strip())
    except Exception:
        return True  # 无法检测 → 假设活着 (不误判离线)
```

> ⚠️ 进程存活检查仅作为**兜底**。主要依靠 Agent 自汇报心跳。如果 Agent 崩溃退出但没有 deregister，sweeper 会在 120s 后标记 offline。

## 7. 与现有代码的集成点

| 现有文件 | 改动 | 描述 |
|---------|------|------|
| `apps/winpeek_injector/daemon.py` | 修改 `_heartbeat_loop()` | 新方案：仅 sweep，Agent 自汇报 |
| `apps/winpeek_injector/daemon.py` | 新增 `check_process_alive()` | 进程存活检查 |
| `gateway/winpeek_hub/hub.py` | 已有 `heartbeat()`/`sweep_dead_nodes()` | 不变 |
| `hermes-agent/cli.py` | 已有 `hub.register_node()` + `hub.heartbeat()` | 不变 |
| `tools/winpeek_tools.py` | 修改 `_handle_mim_login()` | 登录时自动注册 + 心跳 |

## 8. 验收标准

| 场景 | 预期结果 |
|------|---------|
| Gateway 启动 | 本机 Agent (CC + Hermes) 显示 online |
| Hermes CLI 退出 | 120s 后 Hermes 显示 offline |
| CC 窗口关闭 | 120s 后 CC 显示 offline |
| CC 登录 MIM | CC 立即显示 online (login handler 调用 heartbeat) |
| Gateway 重启 | 节点状态正确反映当前运行的 Agent |
| 远程 Agent (不在本机) | 如果有人给它发消息，MQTT 活动触发心跳 → online |
