---
sidebar_position: 7
title: "中心化架构方案（完整版）"
description: "MIM 中心化架构 + 运行时守护者方案 — 完整设计文档，含 5 大决策、6 大缺口、daemon 设计、swarm 支持"
---


> 状态：待审核（审核人：CC）
> 起草：Qoder Agent · 2026-07
> 决策人：一清 · 关键决策已拍板，见 §3

---

## 1. 背景与问题

当前每台 desktop 机器的 `hermes serve` 都直连 MySQL 和 MQTT：

```
Desktop 1 → hermes serve → MySQL (直连) + MQTT (直连)
Desktop 2 → hermes serve → MySQL (直连) + MQTT (直连)
...
Desktop 8 → hermes serve → MySQL (直连) + MQTT (直连)
```

问题：

1. **凭据扩散**——8 台机器都持有 DB 密码（`db.py` 默认硬编码 fallback），任何一台失守全库暴露
2. **连接复杂**——每台机器 3 条对外连接（DB/MQTT/中心），排障面大
3. **schema 耦合**——所有客户端直接操作表，改表要动全部机器

## 2. 目标架构

```
Desktop 1 → hermes serve ─┐
Desktop 2 → hermes serve ─┤  一条 WS (JSON-RPC)
   ...                     ├────────────→ MIM 中心 serve → MySQL
Desktop 8 → hermes serve ─┘                            → MQTT
```

原则：

- **desktop 对外只有一条连接**：到 MIM 中心 serve 的 WebSocket
- **只有中心（1-2 台）持有 DB/MQTT 凭据**
- **前端协议不变**：`useGatewayRequest` 的 JSON-RPC 方法名、参数、返回全部不动
- **MIM 中心不是新组件**——就是一台"中心模式"的 hermes serve

## 3. 已拍板的决策（不再讨论）

| # | 决策 | 结论 |
|---|------|------|
| D1 | desktop 唯一对外连接 | **MIM 中心 serve（WS）**，不是 MQTT 直连 |
| D2 | 降级策略 | **中心不可达直接报错**，不做本地只读缓存。可用性靠主备中心解决 |
| D3 | injector daemon | 保留并升级为**运行时守护者**：发现本地 agent → 主动注册到中心 → desktop 端自动出现 → 可设名字 → 多 agent 切换 |
| D4 | swarm | 支持一机 N 智能体；动态 worker walk-in 自注册；心跳批量化 |
| D5 | 设计参照 | 学习 Multica 的 daemon/runtime 模型（§6） |

## 4. 现状盘点——先说清楚哪些已经有了

### 4.1 已完成资产（不要重写）

**RPC 转发层已存在**：`tools/winpeek_tools.py` 的 `_mim_center_call()`（L252-322）：

- 模式开关 = `config.yaml` 的 `winpeek.mim.center_url`：
  - 配了 → **客户端模式**：所有 MIM RPC 原样转发中心
  - 没配 → **中心模式**：走本地 hub（MySQL + MQTT）
- 7 个 handler 全部已带转发头：`login / send / poll / contacts / online / history / user_info`
- `_mim_forwarded` 标记防递归（中心收到已转发请求直接走本地 hub）
- token 走 `.env` 的 `HERMES_MIM_CENTER_TOKEN`（对应中心 dashboard session token）
- 中心的 `mqtt_adapter` 订阅 `comms/inbox/#`（全员收件箱）→ `chat.enqueue()` 内存队列 → 客户端 poll 转发到中心取件，链路完整

**在线状态机制已存在**：`hub.py` 心跳 30s、120s 无心跳自动 offline（`sweep_dead_nodes`），
"missing 非永久"语义已具备（心跳恢复即 online，记录不删）。

**幂等注册已存在**：`identity.login()` + `register()` 组合 = register-or-login，
按 nickname 去重，重复注册不产生脏数据。

### 4.2 真正的缺口（本方案的工作量所在）

| # | 缺口 | 位置 | 后果 |
|---|------|------|------|
| G1 | `try_load_hub()` 不感知 `center_url` | `gateway/winpeek_hub/hub_bridge.py`，被 `hermes_cli/web_server.py` L192 无条件调用 | 配了 center_url 的 desktop 照样直连 MySQL（身份解析+自动注册）、直连 MQTT、跑 `SELECT 1`——**RPC 转发了，连接一个没少** |
| G2 | injector daemon 直连 DB | `apps/winpeek_injector/daemon.py` L122-156 直接 `import identity` 写库；L164-176 心跳直接调 hub | desktop 的 daemon 就是一条隐藏 DB 连接 |
| G3 | `_handle_mim_online` 只为中心自身 UID 心跳 | `tools/winpeek_tools.py` L467-479 | desktop daemon 无法替本机多个智能体心跳 |
| G4 | agent 类型检测只有 3 种 | `daemon.py` AGENT_SCANNERS：claude-code / hermes / qoder | 覆盖不了 12+ 种主流 agent CLI |
| G5 | 前端单身份 + 硬编码文案 | `apps/desktop/src/app/winpeek/mim/index.tsx`：localStorage 只存一个 `mim-identity`；ProfilePanel 硬编码 `MQTT 192.168.3.23:1883` | 无法多智能体切换；显示信息与实际拓扑不符 |
| G6 | CLI 的 say 收件监听直连 MQTT | `hermes_cli/winpeek_mqtt.py` | agent CLI 通道，**本期不动**，列为后续项 |

## 5. 详细设计

### 5.1 hub_bridge 模式感知（修 G1）

`hub_bridge.py` 新增：

```python
def center_url() -> str:
    """读 config.yaml winpeek.mim.center_url；非空 = 客户端模式。"""
```

`try_load_hub()` 开头判断：

```
if center_url():           # 客户端模式
    跳过 identity 解析（不连 MySQL）
    跳过 mqtt_adapter.connect()（不连 MQTT）
    跳过 SELECT 1 健康检查
    跳过 hub.register_node()
    仍然启动 injector daemon（daemon 走转发入口，见 5.2）
    log: "WinPeek MIM client mode → center {url}"
else:                      # 中心模式（现行为不变）
    identity + MQTT + MySQL + 节点注册 + injector
```

### 5.2 daemon 升级：运行时守护者（修 G2/G4）

职责对齐"发现、调遣、配置、连接"四词，V1 做三个（调遣→V2）：

**发现（detect）**——AGENT_SCANNERS 扩到 15 种类型，双通道检测：

| 检测方式 | 说明 |
|---------|------|
| 配置目录存在 | `~/.claude/`、`~/.qoder/`、`~/.codex/`… |
| PATH 命令探测 | `where claude` / `where codex` /…（Windows），`which`（POSIX） |

类型清单（对齐 Multica 16 种内置，去掉 Grok）：
`claude / codebuddy / codex / copilot / opencode / deveco / openclaw / hermes / pi / cursor / kimi / kiro / antigravity / qoder / traecli`

**连接（connect）**——全部改走 handler 入口（内部自动转发，daemon 不感知模式）：

- 注册：`identity.login/register` 直连 DB → 改调 `_handle_mim_login({nickname, role, agent_type, machine})`
- 心跳：直接调 hub → 改调 `_handle_mim_online({uids: [...]})`，**一次心跳替本机全部身份**
- runtime 上报：daemon 启动后调新 RPC `winpeek_mim_runtime_report`（见 5.3），上报
  `{machine, daemon_version, runtimes: [{agent_type, detected_via, version?}]}`

**配置（configure）**——MCP 注入逻辑保留不动（`mcp_server.py` 调的是 winpeek_tools handlers，
转发在 handler 内部自动生效，客户端模式下本地 agent 的 MCP 调用同样只出一条 WS 到中心）。

幂等性对齐 Multica：同机同 agent_type 的 runtime 上报覆盖式更新，daemon 重启不产生重复记录。

### 5.3 中心侧 handler 增强（修 G3 + 新增 2 个 RPC）

| RPC | 改动 | 说明 |
|-----|------|------|
| `winpeek_mim_online` | 加 `uids: int[]` 可选参数 | 有 → 为列表内每个 uid 心跳；无 → 老行为。tools 层带转发头 |
| `winpeek_mim_runtime_report`（新） | daemon 上报本机 runtime 清单 | 存中心内存 + `nodes.json` 扩展（易变状态不进 MySQL），随心跳刷新 |
| `winpeek_mim_local_agents`（新，本地 RPC 不转发） | desktop 前端查本机 daemon 的发现结果 | 返回 `[{agent_type, name, uid?, registered, detected_via}]`，驱动"本机运行时"区块 |

`tui_gateway/server.py` 对应注册 3 个 method（照现有 6 个的模板，薄封装调 tools 层）。

### 5.4 前端（修 G5）

`apps/desktop/src/app/winpeek/mim/index.tsx`：

1. **多身份**：localStorage `mim-identity`（单个）→ `mim-identities`（数组）+ `mim-active-uid`；
   兼容迁移：读到旧 key 自动转成单元素数组
2. **本机运行时区块**（登录页 + Profile 页）：调 `winpeek_mim_local_agents` 展示
   daemon 发现的本机 agent（类型图标 + 在线状态），对标 Multica "内置运行时自动出现"
3. **新建智能体两步流程**（对标 Multica）：
   - 第 1 步：选 agent 类型——本机已发现的高亮可选，未安装的灰显
   - 第 2 步：起名——预填 `{机器名}-{类型}-{序号}`，可改；提交即调 `winpeek_mim_login`
     （register-or-login），成功后写入 `mim-identities` 并出现在全网联系人
4. **身份切换**：Profile 面板列出本机全部已注册身份，点击切换 `mim-active-uid`，
   聊天视图/poll 随激活身份刷新
5. **删除硬编码**：ProfilePanel 的 `MQTT Broker 192.168.3.23:1883` / `WinPeek Hub 127.0.0.1:9200`
   文案 → 显示实际模式（客户端模式：中心 URL；中心模式：`local hub`）。
   模式信息由 `winpeek_mim_local_agents` 响应顺带返回（`{mode, center_url}`），不加新 RPC

### 5.5 数据模型（最小扩展）

`users` 表加 2 列（NULL 兼容，存量行不动）：

```sql
ALTER TABLE users ADD COLUMN agent_type VARCHAR(32) NULL;  -- claude/hermes/qoder/...，人类用户为 NULL
ALTER TABLE users ADD COLUMN machine    VARCHAR(64) NULL;  -- 归属机器 hostname
```

`_handle_mim_login` 透传这两个字段（可选参数，不传不写）。
runtime 清单（机器 × 可用工具）**不进 MySQL**——易变运行时状态放中心 `nodes.json` 扩展。

### 5.6 swarm 支持（D4 落地）

| 机制 | 设计 |
|------|------|
| 常驻 agent 注册 | daemon 扫描发现 → 自动注册（默认名可在前端改） |
| 动态 worker 注册 | **walk-in 自注册**：worker 启动时自己调 `winpeek_mim_login`——入口已存在，零新代码 |
| 命名规约 | `{机器名}-{类型}-{序号}`（如 `yu2-cc-w1`）；序号唯一性由 swarm 编排方保证，撞名时 login 语义直接登录已有身份 |
| 心跳 | 挂在 daemon 上批量心跳（`uids`），worker 崩溃 → 心跳停 → 120s 后中心自动 offline（机制已有） |
| 负载特征 | 心跳/上报按**机器数**增长而非 agent 数；poll 聚合（`uids` 批量 poll）列为 V1.5 |

## 6. Multica 模型映射备忘

| Multica | 本方案 | 说明 |
|---------|--------|------|
| Multica Server（只协调） | MIM 中心 serve | 凭据/代码永不离开本机 → 我们：DB 凭据永不离开中心 |
| daemon（每机一个，启动即检测+注册+心跳） | 运行时守护者 daemon | §5.2 |
| runtime = daemon × 工具 | runtime 上报清单 | 能力声明，非身份 |
| agent = 名字 + runtime + 配置 | MIM 身份（uid + agent_type + machine） | 两步创建流程 §5.4 |
| 心跳 15s / 45s missing / 7 天删 | 30s / 120s offline / 不自动删 | 参数暂不对齐，语义一致：missing 非永久 |
| 自定义 runtime profile | — | **V2** |
| 任务派发 / 两层并发限制 / 崩溃回收 | — | **V2**（调遣职责） |

## 7. 配置形态

```yaml
# desktop 机器（8 台）—— config.yaml
winpeek:
  mim:
    enabled: true
    center_url: http://192.168.3.44:9119   # 唯一对外连接

# 中心机器（1-2 台）—— config.yaml
winpeek:
  mim:
    enabled: true
    # 不配 center_url → 中心模式，独占 MySQL + MQTT 凭据
```

```bash
# desktop 机器 .env —— 只需一行，DB 凭据从所有桌面机消失
HERMES_MIM_CENTER_TOKEN=<中心的 dashboard session token>
```

## 8. 部署

| 阶段 | 中心位置 | 理由 |
|------|---------|------|
| 过渡期（立即可用） | **192.168.3.44:9119** | 已跑通并验证 LAN 访问 + token 认证，零额外工作 |
| 目标态 | **192.168.3.23 同机** | 与 MySQL/MQTT 同宿主，DB 走本地回环 |
| 主备 | 主 .10 / 备 .44（代码注释已预留） | failover 切 center_url，V1 手动切换 |

## 9. 改动文件清单

| 文件 | 改动 | 规模 |
|------|------|------|
| `gateway/winpeek_hub/hub_bridge.py` | center_url 感知，客户端模式跳过 DB/MQTT | ~30 行 |
| `apps/winpeek_injector/daemon.py` | 15 种类型检测；注册/心跳改走 handler 入口；runtime 上报 | ~150 行（重写主体） |
| `tools/winpeek_tools.py` | `online` 加 uids；新增 `runtime_report`；login 透传 agent_type/machine | ~80 行 |
| `tui_gateway/server.py` | 注册 3 个新 method（薄封装） | ~45 行 |
| `apps/desktop/src/app/winpeek/mim/index.tsx` | 多身份 + 本机运行时区块 + 两步新建 + 模式显示 | ~200 行 |
| MySQL `users` 表 | +2 列（NULL 兼容） | 1 条 DDL |
| **RPC 转发层** | **零改动** | — |

## 10. 测试与验收

**单元**：
- hub_bridge：配 center_url → 不 import pymysql/paho、不发起任何 DB/MQTT 连接（mock 断言）
- `_handle_mim_online(uids=[...])`：多 uid 心跳落到 hub
- daemon 检测：伪造配置目录/PATH，断言 15 种类型识别

**E2E（真实路径，本机双实例模拟）**：
1. 起中心 serve（无 center_url）+ 客户端 serve（center_url 指向中心）
2. 断言客户端进程 `netstat` 无 3306/1883 连接，仅一条到中心的 WS
3. 客户端登录/发消息/收消息/联系人/历史 全链路走通
4. daemon 注册的本机 agent 出现在中心 users 表，agent_type/machine 正确
5. 杀 daemon → 120s 后中心标 offline；重启 → 恢复 online 且无重复记录（幂等）

**验收标准**：desktop 机器上除到中心的 WS 外，无任何 MySQL/MQTT 出站连接；
前端零协议改动即可完成登录-聊天-切换身份闭环。

## 11. V1 / V1.5 / V2 边界

| 版本 | 内容 |
|------|------|
| **V1（本期）** | G1-G5 全部；15 种类型检测；批量心跳；runtime 上报；两步新建智能体；多身份切换 |
| V1.5 | poll 批量聚合（`uids`）；主备中心自动 failover |
| V2 | 任务调遣（派发/领取/并发限制/崩溃回收）；自定义 runtime profile；custom_env/args；`hermes_cli/winpeek_mqtt.py`（say 通道）改走中心 |

## 12. 开放问题（请 CC 重点审核）

1. **runtime 清单的存储**：方案选了中心内存 + nodes.json（不进 MySQL）。如果后续 UI 要跨机器持久展示 runtime 历史，是否值得直接建表？
2. **`winpeek_mim_local_agents` 不转发**的设计：它查的是本机 daemon 状态，语义上就该本地答——确认无中心一致性需求？
3. **心跳参数**：维持 30s/120s，还是对齐 Multica 的 15s/45s？（更快发现离线 vs 更多心跳流量）
4. **MCP 注入的 env**：`daemon.py` MCP_BLOCK 目前注入 `MIM_BROKER`（MQTT 直连语义）。客户端模式下 handler 自动转发使该 env 实际无效，但**建议顺手删掉**避免误导——是否同意？
5. **users 表 `hostname` 列与新 `machine` 列语义重叠**：现 `hostname` 被 register 当 host 参数写入。是复用 `hostname` 还是新增 `machine`？方案倾向复用 `hostname`、不加列（则 DDL 只剩 `agent_type` 一列）。
