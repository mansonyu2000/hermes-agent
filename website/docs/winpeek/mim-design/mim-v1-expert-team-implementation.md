---
sidebar_position: 8
title: "MIM V1 专家团实施需求书"
description: "V1 可执行需求规格：5 个任务包、接口契约、验收标准、全局铁律"
---

# MIM V1 专家团实施需求书

> 上游设计：[MIM 中心化架构方案](mim-centralized-runtime-architecture)（已 push，待 CC 审核）
> 本文性质：**可执行需求规格**——任务包边界、接口契约、验收标准
> 执行模式：专家团（多任务包并行），两波次 + 收尾
> 决策依据：设计方案 §3 已拍板决策 D1-D5；§12 开放问题按"方案倾向"先行实现，CC 审核有异议再调

---

## 0. 目标一句话

desktop 机器上除"到 MIM 中心的一条 WS"外，**零 MySQL / 零 MQTT 出站连接**；
一机可注册 N 个智能体（15 种类型自动发现 + 手动两步新建），多身份切换聊天。

## 1. 全局铁律（所有专家共同边界，违反即打回）

| # | 铁律 |
|---|------|
| R1 | **禁改** `_mim_center_call` 转发层（`tools/winpeek_tools.py` L252-322）——已存在资产，只允许新增调用它的 handler |
| R2 | **禁改** `hermes_cli/web_server.py` 与 `hermes_cli/dashboard_auth/`——认证已修好，不在本期范围 |
| R3 | **禁改**前端 JSON-RPC 调用协议（`useGatewayRequest` 用法、已有方法名/参数语义只增不改） |
| R4 | **禁提交** `apps/desktop/package.json` / `vite.config.ts` 的 5184 端口行——本机适配，不进 git |
| R5 | 每个专家只许改自己任务包清单内的文件；需要别人文件的改动 → 提需求给对应专家，不许代改 |
| R6 | 秘密只进 `.env`（`HERMES_MIM_CENTER_TOKEN`）；行为配置只进 `config.yaml`（`winpeek.mim.*`），禁止新增 `HERMES_*` 行为类环境变量 |
| R7 | commit scope：`tools(winpeek)` / `gateway(winpeek)` / `docs(winpeek)`；提交前过 `python scripts/winpeek-quality-check.py`（Windows 上 TypeScript 项用 `npx tsc --noEmit` 手动验证） |
| R8 | 客户端模式的判定**唯一来源** = `config.yaml` 的 `winpeek.mim.center_url` 非空；禁止发明第二个开关 |
| R9 | 心跳/在线参数维持 30s/120s（方案 §12-Q3 倾向）；users 表机器归属**复用 `hostname` 列**，只新增 `agent_type` 列（§12-Q5 倾向） |

## 2. 接口契约（并行的前提，先于一切代码定死）

> 所有新 RPC 走 `tui_gateway/server.py` 的 `@method` 注册 + `tools/winpeek_tools.py` handler 模式，
> 与现有 6 个 `winpeek_mim_*` 完全同构。是否转发中心由 handler 内部 `_mim_center_call` 决定。

### 2.1 `winpeek_mim_online`（改造：加批量心跳）

```jsonc
// 请求 params（新增 uids，向后兼容：两者都不传 = 老行为，为中心自身 UID 心跳）
{ "uids": [2031, 2032, 2033] }          // 可选，int[]，为列表内每个 uid 心跳
// 响应（不变）
{ "nodes": [ { "uid": 2031, "name": "...", "role": "...", "status": "online", "last_seen": "..." } ] }
```

**转发**：是（客户端模式下转发中心）。

### 2.2 `winpeek_mim_runtime_report`（新增：daemon 上报本机运行时清单）

```jsonc
// 请求 params
{
  "machine": "yu2",                      // hostname，必填
  "daemon_version": "1.0.0",             // 必填
  "runtimes": [                          // 必填，可为空数组
    { "agent_type": "claude",  "detected_via": "config_dir", "version": "" },
    { "agent_type": "qoder",   "detected_via": "path_cmd",   "version": "" }
  ]
}
// 响应
{ "ok": true, "machine": "yu2", "count": 2 }
```

**转发**：是。**存储**：中心 `~/.hermes/winpeek/nodes.json` 新增顶层键 `"machines"`：
`{ "machines": { "yu2": { "daemon_version": "...", "last_report": "<iso>", "runtimes": [...] } } }`
覆盖式更新（同 machine 幂等），**不进 MySQL**（§12-Q1 倾向）。

### 2.3 `winpeek_mim_local_agents`（新增：desktop 前端查本机 daemon 状态）

```jsonc
// 请求 params
{}
// 响应
{
  "mode": "client",                      // "client" | "center"
  "center_url": "http://192.168.3.44:9119",  // center 模式为 ""
  "machine": "yu2",
  "agents": [
    { "agent_type": "claude", "name": "Claude Code", "detected_via": "config_dir",
      "uid": 2031, "registered": true },
    { "agent_type": "codex",  "name": "Codex",       "detected_via": "path_cmd",
      "uid": 0,    "registered": false }
  ]
}
```

**转发**：**否**——它答的是"本机 daemon 的发现结果"，语义上必须本地答（§12-Q2 倾向）。
数据源：daemon 模块级状态（见任务包 C 的 `get_local_state()`）。

### 2.4 `winpeek_mim_login`（改造：透传 2 个可选字段）

```jsonc
// 请求 params 新增（均可选，不传行为不变）
{ "nickname": "yu2-cc-w1", "password": "123321", "role": "Developer",
  "agent_type": "claude", "machine": "yu2" }
// 响应不变：{ "ok": true, "identity": { uid, nickname, role, ... } }
```

`identity.register()` 新签名：`register(nickname, role, host, password, agent_type="")`——
`host` 即 machine（复用 hostname 列），`agent_type` 写新列。

### 2.5 DDL（一次性，中心库执行）

```sql
ALTER TABLE users ADD COLUMN agent_type VARCHAR(32) NULL;
```

存量行不动；`identity._row_to_dict` 增加 `agent_type` 字段回传（NULL → `""`）。

### 2.6 4 种 agent 类型检测表（daemon 用，与前端图标 key 一致）

| agent_type | 配置目录检测 | PATH 命令检测 |
|------------|-------------|--------------|
| claude | `~/.claude/` | `claude` |
| hermes | `~/.hermes/config.yaml` | `hermes` |
| qoder | `~/.qoder/` | `qoder` |
| traecli | `~/.trae/` | `trae` |

命中任一通道即算发现；`detected_via` 取首个命中通道（`config_dir` 优先）。
Windows 用 `shutil.which()`（跨平台，勿用 `where` 子进程）。

## 3. 专家任务包

### 任务包 A：后端协议专家

**文件（独占）**：`tools/winpeek_tools.py`、`tui_gateway/server.py`

**需求**：
1. `_handle_mim_online` 支持 `uids: int[]`（契约 2.1）：有 uids → 逐个 `hub.register_node` 需求放宽为
   `hub.heartbeat(uid)`（uid 不存在 nodes.json 时先 `register_node(uid, name=f"uid-{uid}")` 占位）；
   之后照旧 `sweep_dead_nodes()` 并返回全量 nodes
2. 新增 `_handle_mim_runtime_report`（契约 2.2）：带 `_mim_center_call` 转发头；
   中心侧写 `nodes.json` 的 `machines` 键（读-改-写，容忍文件不存在/损坏）
3. 新增 `_handle_mim_local_agents`（契约 2.3）：**不带转发头**；
   `from apps.winpeek_injector.daemon import get_local_state`（惰性 import，失败返回
   `{"mode": ..., "agents": [], "error": "..."}`)；mode/center_url 从 `_mim_center()` 推导
4. `_handle_mim_login` 透传 `agent_type`/`machine`（契约 2.4）；同步改
   `gateway/winpeek_hub/identity.py` 的 `register()` 写 `agent_type` 列、`_row_to_dict` 回传
   —— **注意**：identity.py 归属包 A（仅此两处函数），包 B 不碰它
5. `server.py` 注册 3 个 method：`winpeek_mim_online`（若未注册则补）、
   `winpeek_mim_runtime_report`、`winpeek_mim_local_agents`——照现有 6 个的薄封装模板
6. 顺手删除 `daemon.py` MCP_BLOCK 里的 `MIM_BROKER` env 注入（§12-Q4 倾向）——
   **例外授权**：此一处跨入包 C 文件，改动仅删 2 行 env，需在 commit message 注明

**禁区**：R1（`_mim_center_call` 本体）、`chat.py`/`mqtt_adapter.py`/`hub_bridge.py`

**DoD**：
- [ ] `ast.parse` 通过；`winpeek_mim_online` 传 `uids:[9001,9002]` 后 `nodes.json` 出现两条 online
- [ ] 中心模式下 `runtime_report` 落盘 `machines` 键；重复上报同 machine 不产生重复
- [ ] `local_agents` 在 daemon 未启动时返回 `agents: []` 不抛错
- [ ] login 带 `agent_type` 注册后，MySQL 行 `agent_type` 列有值，contacts 回传含该字段

### 任务包 B：连接治理专家

**文件（独占）**：`gateway/winpeek_hub/hub_bridge.py`

**需求**：
1. 新增 `def center_url() -> str`：读 `config.yaml` `winpeek.mim.center_url`，异常返回 `""`
2. `try_load_hub()` 在 `is_enabled()` 判定后插入分支：`center_url()` 非空 →
   跳过 identity 解析 / `mqtt_adapter.connect()` / MySQL `SELECT 1` / `hub.register_node`，
   **仍然**启动 injector daemon（`start_daemon()`），
   `logger.info("WinPeek MIM client mode → center %s", url)`，置 `_HUB_LOADED = True` 后返回 True
3. 中心模式路径一行不改

**禁区**：identity.py、mqtt_adapter.py、db.py、daemon.py

**DoD**：
- [ ] 单测（新文件 `tests/gateway/test_hub_bridge_client_mode.py`）：mock config 含 center_url 时，
  `try_load_hub()` 不 import pymysql、不调用 `mqtt_adapter.connect`（`unittest.mock.patch` 断言）
- [ ] 无 center_url 时行为与现状逐行一致（现有测试不红）

### 任务包 C：daemon 专家（运行时守护者）

**文件（独占）**：`apps/winpeek_injector/daemon.py`（重写主体）

**需求**：
1. `AGENT_SCANNERS` 重构为契约 2.6 的 4 种类型表（数据驱动：`{agent_type, name, config_dir, path_cmd, config_file?}`）；
   保留现有 3 种的 `config_file` MCP 注入能力，traecli `config_file=None`（V1 不注入）
2. `scan_installed_agents()` 双通道检测（`Path.exists()` + `shutil.which()`），
   返回含 `detected_via`
3. `register_and_inject()` 改造：**删除** `from gateway.winpeek_hub import identity` 直连；
   改调 `from tools.winpeek_tools import _handle_mim_login` →
   `_handle_mim_login({"nickname": name, "role": "Agent", "agent_type": t, "machine": hostname})`，
   解析返回 JSON 拿 uid（转发与否由 handler 自动决定，daemon 零模式感知）
4. `_heartbeat_loop()` 改造：**删除** hub/identity 直连；每 30s 调
   `_handle_mim_online({"uids": [已注册的本机 uid 列表]})`
5. 启动时上报 runtime：调 `_handle_mim_runtime_report`（契约 2.2 的请求体）
6. 新增模块级状态与查询函数（供包 A 的 local_agents 用）：
   ```python
   def get_local_state() -> dict:
       # {"machine": str, "agents": [{agent_type, name, detected_via, uid, registered}]}
   ```
   线程安全（状态更新加锁），daemon 未启动时返回空 agents
7. MCP_BLOCK：接受包 A 删除 `MIM_BROKER` 的改动（见 A-6），不回加

**禁区**：winpeek_tools.py 的任何函数体（只 import 调用）、hub_bridge.py

**DoD**：
- [ ] 全文件无 `from gateway.winpeek_hub import identity` / `import hub` 残留（grep 断言）
- [ ] 单测（`tests/apps/test_winpeek_daemon_scan.py`）：tmp_path 伪造 `.claude/`/`.qoder/` 目录 +
  monkeypatch `shutil.which`，断言 15 类型表驱动的检测结果与 `detected_via` 正确
- [ ] `get_local_state()` 在 `start_daemon()` 前调用返回 `{"agents": []}` 不抛错

### 任务包 D：前端专家

**文件（独占）**：`apps/desktop/src/app/winpeek/mim/index.tsx`（可新增同目录子组件文件）

**需求**：
1. **多身份存储**：`mim-identity`（单对象）→ `mim-identities`（数组）+ `mim-active-uid`；
   首次读取时迁移旧 key（读到旧的转成单元素数组后删旧 key）
2. **本机运行时区块**：登录页与 Profile 页展示 `winpeek_mim_local_agents` 结果——
   agent 类型名 + `registered` 状态点；`registered && uid>0` 的条目一键"以此身份进入"
   （写入 identities 并激活）
3. **两步新建智能体**：
   - 第 1 步选类型：4 种网格(claude-code/hermes/qoder/traecli)，本机已发现的高亮，未发现的灰显但可选（手动路径）
   - 第 2 步起名：预填 `{machine}-{agent_type}-{n}`（n = 本机同类型已注册数 +1），可改；
     提交调 `winpeek_mim_login`（带 `agent_type`/`machine`），成功后入列并激活
4. **身份切换**：Profile 面板列出 `mim-identities` 全部身份，点击切换 `mim-active-uid`；
   聊天列表/history/poll 全部随激活身份刷新（现有 `identity` state 替换为派生自激活 uid）
5. **模式显示**：ProfilePanel 删除硬编码 `MQTT Broker 192.168.3.23:1883` / `WinPeek Hub 127.0.0.1:9200` 两行，
   改为显示 `local_agents` 返回的 `mode`（`客户端模式 → {center_url}` / `中心模式（本机 hub）`）
6. CSS 全部用 `var(--ui-*)` token（门禁项）

**禁区**：R3（协议）、R4（端口文件）、`use-gateway-request.ts` 等共享 hooks

**DoD**：
- [ ] `npx tsc --noEmit` 通过
- [ ] 旧 localStorage 用户升级后无感（身份保留、自动迁移）
- [ ] 断网/中心不可达时新建智能体报错文案清晰（复用现有 `无法连接到网关` 模式）
- [ ] 身份 A 与身份 B 切换后，消息列表互不串（对照 history 的 uid 参数）

### 任务包 E：数据与验证专家

**文件**：`tests/` 新增 E2E 脚本 + DDL 执行

**需求**：
1. **DDL 前置**（第一波开始前执行一次）：契约 2.5 的 ALTER，在中心库（192.168.3.23 winpeek-db2）执行；
   执行前 `SHOW COLUMNS FROM users LIKE 'agent_type'` 幂等检查
2. **E2E 双实例脚本**（`tests/e2e/test_mim_client_center_e2e.py`，pytest -m e2e，CI 不跑）：
   - 启动中心 serve（临时 HERMES_HOME，无 center_url）+ 客户端 serve（center_url 指中心）
   - 断言①：客户端进程无 3306/1883 出站连接（psutil `net_connections`）
   - 断言②：客户端 login → send → 中心侧 poll 收到；history 双向可见
   - 断言③：`runtime_report` 后中心 `nodes.json` 出现 machines 键
   - 断言④：杀客户端 daemon 心跳 → 中心 `sweep_dead_nodes` 后该 uid offline；
     重启注册 → online 恢复且 users 表无重复行
3. **回归**：跑 `tests/gateway/`、`tests/tools/` 下 winpeek 相关现有用例

**禁区**：一切 `src/` 生产代码（发现 bug 提给对应专家，不代修）

**DoD**：
- [ ] 断言①-④ 全绿（本机双实例）
- [ ] 现有 winpeek 测试无新红

## 4. 执行波次与依赖

```
波次 0（前置）：E DDL 一条（幂等）
波次 1（并行）：A（协议+handler）    B（hub_bridge）
波次 2（并行）：C（daemon，调 A 的 handler）    D（前端，调 A 的 RPC）
收尾（E）：E2E 双实例 + 回归 → 汇总提交
```

## 5. 提交规范（对齐 git 历史风格）

| 包 | scope 示例 |
|----|-----------|
| A | `tools(winpeek): mim online 批量 uids + runtime_report/local_agents RPC + login 透传 agent_type` |
| B | `gateway(winpeek): hub_bridge 感知 center_url — 客户端模式跳过 MySQL/MQTT 加载` |
| C | `tools(winpeek): daemon 升级运行时守护者 — 4 类检测 + 注册/心跳走转发入口` |
| D | `gateway(winpeek): MIM 前端多身份切换 + 本机运行时 + 两步新建智能体` |
| E | `tests(winpeek): 客户端/中心双实例 E2E — 零 DB/MQTT 出站断言` |

## 6. 集成验收（合并后一次性人工确认）

1. desktop 配 `center_url` 重启 → `netstat -ano | findstr "3306 1883"` 中该进程 **0 条**
2. desktop MIM 页：本机运行时区块出现 ≥2 个已发现类型；新建 `yu2-qoder-1` 成功；
   与中心侧另一用户互发消息 + 历史可见
3. 身份切换后消息不串（两身份各自会话独立）
4. 中心 `nodes.json`：machines 含本机 runtime 清单；杀 daemon 2 分钟后本机身份 offline
5. 中心模式机器（不配 center_url）行为与改造前完全一致

## 7. 明确不做（V1 边界外，发现自己在做这些 = 越界）

- 任务调遣/派发/并发限制（V2）
- 自定义 runtime profile、custom_env/args（V2）
- poll 批量聚合 `uids`（V1.5）
- 主备中心自动 failover（V1.5，手动切 center_url）
- `hermes_cli/winpeek_mqtt.py`（say 通道）改造（V2）
- 11 种新 agent 类型的 MCP 注入（V1 仅保留原 3 种 + traecli，共 4 种）
- 转发层性能优化（连接复用/推送化）
- **MCP server MIM 工具（mim_send/poll/contacts/history/whoami）— V1.5**
- **Agent 消息回复决策 + 系统 prompt 植入 — V1.5**
