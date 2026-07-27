---
title: "Agent 在线状态 — Multica 参考方案"
type: "reference"
module: "mim"
version: "v1"
last_updated: "2026-07-27"
source: "D:/mydata/mycode/github/multica/CLI_AND_DAEMON.md + server/internal/daemon/daemon.go"
---

# Agent 在线状态 — Multica 参考方案

## Multica 做法

### Agent 检测
Daemon 通过 **PATH 搜索** 检测已安装的 Agent CLI：
```go
// daemon.go:87-91
detectAgentVersion = agent.DetectVersion  // 扫描 PATH 找到 claude/hermes/codex 等
```

不是查配置文件，不是查窗口标题，是 **直接查 CLI 命令是否存在**。

### 注册 + 心跳
```
multica daemon start
  → 1. detect CLI on PATH (claude/hermes/codex/...)
  → 2. register runtime for each agent in each watched workspace
  → 3. poll server 3s (get assigned tasks)
  → 4. heartbeat 15s (keep daemon alive)
  → 5. on shutdown: deregister ALL runtimes
```

```
Daemon 启动
  │
  ├─ detect_cli_on_PATH() → ["claude", "hermes", "codex"]
  │
  ├─ register_runtime(workspace, agent)
  │     → POST /api/runtimes {name, version, workspace}
  │
  ├─ poll_tasks(interval=3s) → get assigned work
  │
  └─ heartbeat(interval=15s)
       → POST /api/daemon/heartbeat
```

### 关键差异

| 维度 | Multica | 我们当前 |
|------|---------|---------|
| Agent 检测 | PATH 扫描 CLI 命令 | 配置文件检查 |
| 谁汇报 | Daemon 代替所有 Agent 汇报给 Multica 服务器 | Agent 自己调用 hub.register_node() |
| 心跳 | Daemon 15s 心跳一次 | Hermes CLI 30s 心跳一次 |
| 离线 | Daemon 退出时 deregister 所有 runtime | sweep_dead_nodes 120s |
| 粒度 | workspace 级别 (每个 workspace 一个 runtime) | machine 级别 (每个机器一个 node) |

## 对我们 DAEMON 的启发

1. **PATH 检测比文件检测更可靠** — 能执行 `hermes --version` = Agent 真正可用
2. **Agent 不需要向 Daemon 汇报** — Daemon 自己知道哪些 CLI 在 PATH 上
3. **Daemon 统一代汇报** — 不需要每个 Agent 自己调 hub API
4. **Daemon 退出 = 所有 Agent 下线** — deregister 所有 runtime，干净利落

## 改进方向

```
当前: Agent CLI 自己调 hub.register_node() + hub.heartbeat()
       → 每个 Agent 需要改动代码 (只改了 Hermes)

Multica 风格:
  Daemon 启动 → detect PATH 上的 CLI → register ALL runtimes
  Daemon 心跳 → POST hub (每 15s)
  Daemon 退出 → deregister ALL runtimes
  sweep_dead_nodes → 120s 无心跳 = offline

优点:
  - 零侵入 — 不需要改 Agent 代码
  - 准确 — CLI 在 PATH 上 = 可用
  - 干净 — Daemon 退出自动清理
```
