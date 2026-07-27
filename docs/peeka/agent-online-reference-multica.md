---
title: "Agent 在线状态 — Multica Daemon 技术方案参考"
type: "reference"
module: "mim"
version: "v1"
last_updated: "2026-07-27"
source: "D:/mydata/mycode/github/multica/server/internal/daemon/daemon.go (4674 lines) + CLI_AND_DAEMON.md"
---

# Multica Daemon 硬核技术方案

## 1. 架构总览

```
multica daemon start
  │
  ├─ resolveAuth()         — 读 CLI config 中的 PAT token
  ├─ preflightAuth()       — PAT 续期 + 初始 workspace 同步
  ├─ listenHealth()        — 健康检查端口 (另一个 daemon 检测)
  │
  ├─ syncWorkspacesFromAPI() — 列出工作区，注册每个的 runtime
  │     └─ registerRuntimesForWorkspace()
  │           ├─ detectAgentVersion(entry.Path) — PATH 扫描 CLI
  │           ├─ checkAgentMinVersion()         — 版本检查
  │           └─ POST /api/daemon/register      — 注册
  │
  ├─ heartbeatLoop()       — 每个 runtime 独立 goroutine, 15s 心跳
  ├─ pollLoop()            — 3s 轮询领取任务
  ├─ taskWakeupLoop()      — WebSocket 实时唤醒 (替代轮询)
  ├─ workspaceSyncLoop()   — 30s 检查新 workspace / 配置文件变化
  ├─ gcLoop()              — 旧环境清理
  ├─ autoUpdateLoop()      — 自动更新
  └─ tokenRenewalLoop()    — 3 天 PAT 续期
```

## 2. Agent 检测：PATH 扫描 (非配置、非窗口标题)

### 核心代码

```go
// daemon.go:91-92 (接口变量, 测试可替换)
detectAgentVersion   = agent.DetectVersion    // 实际执行 CLI --version
checkAgentMinVersion = agent.CheckMinVersion  // 版本号检查
lookPath             = exec.LookPath          // PATH 搜索
```

### registerRuntimesForWorkspace() 里的检测逻辑

```go
// daemon.go:917-987
for name, entry := range d.cfg.Agents {
    version, err := detectAgentVersion(ctx, entry.Path)
    if err != nil {
        d.logger.Warn("skip registering runtime", "name", name, "error", err)
        continue  // CLI 未安装 → 跳过,不注册
    }
    if err := checkAgentMinVersion(name, version); err != nil {
        continue  // 版本太旧 → 跳过
    }
    d.setAgentVersion(name, version)
    runtimes = append(runtimes, map[string]string{
        "name":    displayName,
        "type":    name,          // claude / hermes / codex / ...
        "version": version,
        "status":  "online",
    })
}
```

### 关键差异 vs 我们

| 维度 | Multica | Peeka Daemon |
|------|---------|-------------|
| 检测方式 | `exec.LookPath` + `--version` | `os.path.exists` 检查配置文件 |
| 注册时机 | Daemon 启动时对每个 workspace 注册 | Gateway 启动时一次性注册 |
| 注册对象 | 每个 workspace 一个独立 runtime | 每个机器一个 node |
| 心跳粒度 | 每个 runtime 独立 goroutine | 整体遍历 |
| 退出时 | `deregisterRuntimes()` 全部标记离线 | 无 |
| 自定义 runtime | 支持 (profile command override) | 无 |

## 3. 心跳机制：双通道 (HTTP + WebSocket)

### HTTP 心跳 (每 15s, 每个 runtime 独立 goroutine)

```go
// daemon.go:1916-1955
func (d *Daemon) runRuntimeHeartbeat(ctx context.Context, rid string) {
    interval := 15 * time.Second
    // Jittered initial delay to avoid thundering herd
    if jitter := time.Duration(rand.Int63n(int64(interval))); jitter > 0 {
        time.After(jitter)
    }
    ticker := time.NewTicker(interval)
    for {
        resp, err := d.client.SendHeartbeat(ctx, rid)
        if err != nil {
            if isRuntimeNotFoundError(err) {
                go d.handleRuntimeGone(rid)  // 服务器说 runtime 不存在 → 重新注册
            }
        }
        // 处理返回的 pending actions (更新/模型变更/技能同步)
        d.handleHeartbeatActions(ctx, rid, resp)
    }
}
```

### WebSocket 心跳 (双通道互补)

```go
// daemon.go:689-711
// WS 心跳 ack 时间 → 用来抑制 HTTP 心跳
// 2× HeartbeatInterval 窗口内 WS 正常 → 跳过 HTTP
// 连续两次 WS 失败 → HTTP 接管
func (d *Daemon) wsHeartbeatRecentlyAcked(runtimeID string) bool {
    last := d.wsHBLastAck[runtimeID]
    return time.Since(last) < 2 * d.cfg.HeartbeatInterval
}
```

## 4. 任务执行：spawn CLI → 注入环境变量 → 运行 → 返回

### 核心流程

```go
// daemon.go:3451-3530
func (d *Daemon) runTask(ctx context.Context, task Task, provider string, slot int, taskLog *slog.Logger) (TaskResult, error) {
    // 1. 获取 agent entry (path to CLI binary)
    entry := d.cfg.Agents[provider]

    // 2. 准备隔离的执行环境 (环境变量注入)
    taskCtx := execenv.TaskContextForEnv{
        IssueID:              task.IssueID,
        AgentName:            task.Agent.Name,
        AgentInstructions:    task.Agent.Instructions,  // ← 用户的提示词
        AgentSkills:          convertSkillsForEnv(task.Agent.Skills),
        Repos:                convertReposForEnv(task.Repos),
        ProjectDescription:   task.ProjectDescription,
        ChatSessionID:        task.ChatSessionID,
        ...
    }

    // 3. 创建隔离的 workspace 目录
    envRoot := ...

    // 4. spawn agent CLI → 像 shell 命令一样执行
    cmd := exec.CommandContext(ctx, entry.Path, args...)
    cmd.Env = append(os.Environ(), taskEnv...)
    output, err := cmd.Output()

    // 5. 返回结果
    return TaskResult{Output: string(output)}, err
}
```

### 对话模式：非持久、每次重新 spawn

Multica 的对话 = 用户提问 → Daemon spawn Agent CLI → 注入提示词到环境变量 → Agent 运行 → 结果返回。速度慢的原因：每次都要启动 Agent CLI 进程 + 初始化 + 推理。

## 5. shutdown 清理：deregister 所有 runtime

```go
// daemon.go:817-833
func (d *Daemon) deregisterRuntimes() {
    runtimeIDs := d.allRuntimeIDs()
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    err := d.client.Deregister(ctx, runtimeIDs)
    // 全部标记离线, 不留僵尸
}
```

## 6. Runtime 恢复：服务器端删除后的重注册

```go
// daemon.go:341-391
func (d *Daemon) handleRuntimeGone(runtimeID string) {
    // 1. 从本地状态删除
    workspaceID, removed := d.removeStaleRuntime(runtimeID)

    // 2. 检查是否该重新注册 (防 stampede: coalesce window 30s)
    d.tryClaimRegisterSlot(workspaceID, entryAt, time.Now())

    // 3. 重新注册 (使用 rootCtx, 不受当前 runtime ctx 取消影响)
    d.reregisterWorkspaceAfterRuntimeGone(d.recoveryContext(), workspaceID)
}
```

## 7. 对我们 Peeka Daemon 的启发

### 可以借鉴的

| 特性 | Multica 做法 | 我们如何应用 |
|------|-------------|------------|
| **检测** | `exec.LookPath` 查 CLI | Daemon 扫描 PATH 找 hermes/claude/qoder |
| **注册** | Daemon 代注册所有 runtime | Daemon `register_node()` 每个检测到的 Agent |
| **心跳** | HTTP + WS 双通道 | Daemon 用 MQTT activity + HTTP 双通道心跳 |
| **退出** | deregister 所有 | Daemon 退出时清空本机所有节点 |
| **恢复** | handleRuntimeGone 防 stampede | Daemon 周期检查 + 重新注册丢失的节点 |

### 我们不需要照搬的

- **每 workspace 一个 runtime** — 我们没有 workspace 概念
- **spawn CLI 执行任务** — 我们走 MQTT 消息通道，不需要 spawn 进程

### 我们独有的优势

- **MQTT 被动投递** — Multica 没有，Agent 随时收信不用轮询
- **L1/L2/L3 分级路由** — Multica 没有，减少 LLM 干扰
- **文件 inbox** — Multica 没有，离线消息不丢

## 8. Peeka Daemon 建议架构 (结合 Multica 方案)

```
Peeka Daemon 启动
  │
  ├─ resolve_auth()            — 读 identity DB
  │
  ├─ detect_agents_on_path()   — PATH 扫描 hermes/claude/qoder/traecli
  │     └─ subprocess.run(["hermes", "--version"]) → 成功 = 已安装
  │     └─ subprocess.run(["claude", "--version"]) → 成功 = 已安装
  │
  ├─ register_all_detected()   — 对每个检测到的 Agent:
  │     ├─ hub.register_node(uid, name, agent_type, hostname)
  │     └─ 如果还没有 identity → 自动注册到 identity DB
  │
  ├─ heartbeat_loop(15s)       — 对每个**正在运行的** Agent:
  │     ├─ check_process_alive(pid)  → 活着才心跳
  │     └─ hub.heartbeat(uid)
  │
  ├─ sweep_dead_nodes(120s)    — 清理离线节点
  │
  └─ on_shutdown:              — deregister 所有本机节点
        └─ hub.mark_all_offline()
```
