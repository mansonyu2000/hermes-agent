# MIM 功能清单与实现决策

> 版本: v1.0 · 日期: 2026-07-18 · 性质: **唯一事实来源**
> 替代: `capability-audit.md` / `migration-audit.md` / `chat-features.md` / `chat.md` / `desktop-chat.md` / `messaging.md`
>
> 本文 = 新旧两版全部 MIM 功能的完整盘点 + 每个功能的决策（做/不做/何时做/谁做）。

---

## 评估维度

| 评估字母 | 含义 |
|:--:|------|
| ✅ | 已完成，无需改动 |
| ⚠️ | 部分完成，有断点需修 |
| ❌ | 零实现，需新建 |
| V1 | 本期必须交付 |
| V1.5 | 下个版本 |
| V2 | 远期 |
| ❌-skip | 不迁移 |

---

## 一、身份与登录

| # | 功能 | 旧版 (winpeek-prod) | 新版现状 | 评估 | 决策 |
|---|------|---------------------|---------|:--:|------|
| F1.1 | 用户注册 (nickname+role+password) | `identity.json` + `upsertUser()` | `identity.register()` → MySQL | ✅ | 已完成 |
| F1.2 | 用户登录 (nickname+password) | ext_token 本机识别 | `identity.login()` → 密码验证 | ✅ | 已完成 |
| F1.3 | 统一密码 `123321` | 无此规范 | 已执行 | ✅ | 已完成 |
| F1.4 | 多身份支持 (一机多身份) | `_loginedUid` 单人类 | `mim-identities` 数组 | ⚠️ | **V1** — 包D实现 |
| F1.5 | 身份切换 (不串消息) | 无 | 无 | ❌ | **V1** — 包D实现 |
| F1.6 | 两步新建智能体 (选类型→起名) | 无 | 无 | ❌ | **V1** — 包D实现 |
| F1.7 | daemon 自动发现本机 agent | 无 | injector daemon 3种类型 | ⚠️ | **V1** — 包C扩展到15种 |

---

## 二、联系人

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F2.1 | 联系人列表 | `syncContacts()` → SQLite | `get_contacts()` → MySQL | ✅ | 已完成 |
| F2.2 | 真实在线状态 (非写死) | `nodes.status` + WS在线集合 | `hub.py` 后端有，前端写死 `online:true` | ⚠️ | **V1 P0** — 15行修复 |
| F2.3 | 按online排序 (在线在前) | online优先 > 未读 > 名字 | 按unread排 | ⚠️ | **V1 P0** — 改排序规则 |
| F2.4 | offline 灰色视觉 | 灰色点 + 半透明头像 | 全部绿点 | ⚠️ | **V1 P0** — 改CSS |
| F2.5 | 联系人实时状态推送 | `contact.status` WS事件 | 无 | ❌ | **V1.5** |
| F2.6 | 好友温度系统 | `friend-temp.js` + 每日衰减 | 无 | ❌ | **V2** — 有趣但不紧急 |
| F2.7 | 联系人搜索/过滤 | 无 | 无 | ❌ | **V1.5** |

---

## 三、单聊消息

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F3.1 | 发消息 | `insertMessage()` → MQTT + inbox push | `chat.send_message()` → MySQL + MQTT + enqueue | ✅ | 已完成 |
| F3.2 | 收消息 (poll) | WS `chat.delta` 实时推送 | `poll_messages(uid)` 轮询 | ✅ | 已完成 |
| F3.3 | 消息历史 | `getMessages(cid)` SQLite | `get_history(uid, peer_uid)` MySQL | ✅ | 已完成 |
| F3.4 | Markdown 消息渲染 | 无 (纯文本) | 无 (whitespace-pre-wrap) | ❌ | **V1 P1** — 复用 compact-markdown |
| F3.5 | 消息复制按钮 | 无 | 无 | ❌ | **V1 P1** — 复用 copy-button |
| F3.6 | 时间戳相对格式 | 无 | 纯文本 `msg.time` | ⚠️ | **V1 P1** — 复用 formatMessageTimestamp |
| F3.7 | 滚动到底部 | 无 | `messagesEndRef` 有ref但无按钮 | ⚠️ | **V1 P1** — 复用 scroll-to-bottom-button |
| F3.8 | 输入框 IME 保护 | `isComposing` 保护 | Enter/Shift+Enter 有，无IME保护 | ⚠️ | **V1 P1** — 加 isComposing |
| F3.9 | 消息错误提示 | `chat.error` 事件 | try/catch 静默吞 | ❌ | **V1 P1** — toast |
| F3.10 | @提及 | `@username` 提取 + `chat.mentioned` | 无 | ❌ | **V1.5** — 单聊也需要@ |
| F3.11 | Thread Reply (消息回复) | `reply_to` + 引用条 UI | 无 | ❌ | **V1.5** |
| F3.12 | 消息撤回 | 无 | 无 | ❌ | **V2** |
| F3.13 | 消息转发 | 无 | 无 | ❌ | **V2** |
| F3.14 | 图片/文件发送 | 无 | 无 | ❌ | **V2** |

---

## 四、群聊

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F4.1 | 群表 DDL | `groups` + `group_members` (SQLite) | 无 | ❌ | **V1.5** — `m_groups` + `m_group_members` |
| F4.2 | 创建群 | `createSession({conversation_type:"group"})` | 无 | ❌ | **V1.5** |
| F4.3 | 邀请成员 | `addSessionParticipants()` | 无 | ❌ | **V1.5** |
| F4.4 | 群消息发送 | `insertMessage({gid})` → fanout | 无 | ❌ | **V1.5** — 复用 chat 表 gid 列 |
| F4.5 | 群消息接收 | MQTT `comms/group/{gid}` + WS broadcast | 无 | ❌ | **V1.5** |
| F4.6 | 群消息历史 | `getMessages(cid)` where gid | 无 | ❌ | **V1.5** — 复用 get_history |
| F4.7 | 群聊前端 UI | 马赛克头像 + 发送者名 + 群信息面板 | 前端有 `uid===0?` 占位符 | ❌ | **V1.5** |
| F4.8 | @all 广播 | `isAtAll` → 全员 `chat.mentioned` | 无 | ❌ | **V1.5** |
| F4.9 | 群悄悄话 | `whisper_session_id` 隔离 | 无 | ❌ | **V2** |
| F4.10 | 群规则系统 | `group-rules.js` 6大类 | 无 | ❌ | **V2** |
| F4.11 | 议题引擎 | `/sub:` 命令 | 无 | ❌ | **V2** |
| F4.12 | 群问题板 | `group_problems` 表 | 无 | ❌ | **V2** |
| F4.13 | 群文件 | `group_files` 表 | 无 | ❌ | **V2** |
| F4.14 | Agent 自动匹配 | `group-matcher.js` 3阶段 | 无 | ❌ | **V2** |
| F4.15 | 群聊观察者/悬赏 | `group-observer.js` T+120s递增 | 无 | ❌ | **V2** |
| F4.16 | 加入群审批 | `group_join_requests` | 无 | ❌ | **V2** |

---

## 五、在线状态与心跳

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F5.1 | 心跳注册 | `upsertNode()` → SQLite | `hub.register_node()` → nodes.json | ✅ | 已完成 |
| F5.2 | 心跳更新 | `heartbeat()` 15s间隔 | `hub.heartbeat()` 30s间隔 | ✅ | 已完成 |
| F5.3 | 死节点检测 | `startDeadPeerDetector()` 45s | `hub.sweep_dead_nodes()` 120s | ✅ | 已完成 |
| F5.4 | WS事件广播 (node.joined/left) | `broadcast("node.left", ...)` | 无 | ❌ | **V1.5** |
| F5.5 | 批量心跳 (一次心跳替全机agent) | 无 | 无 | ❌ | **V1** — 包A handler改造 |

---

## 六、消息可靠性

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F6.1 | 离线消息缓存 | `message_queue` TTL 168h | MQTT broker QoS 1 | ⚠️ | **V1.5** — 应用层补缓存 |
| F6.2 | 投递确认 (ACK) | `message_acks` 表 | 无 | ❌ | **V1.5** |
| F6.3 | 已读回执 | `message_receipts` | 无 | ❌ | **V2** |
| F6.4 | 投递状态机 | pending→delivering→delivered | `delivery_status` 列已存在未利用 | ⚠️ | **V1.5** |
| F6.5 | 统一消息入口 (防重复) | ADR-010 `routeMessage()` | 无 | ❌ | **V1.5** — 应用ADR-010设计 |

---

## 七、架构治理

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F7.1 | 中心化模式 (桌面不连DB/MQTT) | 无 (所有机器直连MQTT) | `_mim_center_call` 转发层已有 | ⚠️ | **V1** — 包B断连接 |
| F7.2 | hub_bridge 客户端模式 | 无 | `try_load_hub()` 不感知 center_url | ❌ | **V1** — 包B实现 |
| F7.3 | daemon 升级 (15类型, 走转发入口) | 只发现3种, 直连DB | injector 3种, 直连 identity/hub | ❌ | **V1** — 包C重写 |
| F7.4 | runtime 上报 | 无 | 无 | ❌ | **V1** — 包A+包C |
| F7.5 | E2E 双实例验证 | 无 | 无 | ❌ | **V1** — 包E |
| F7.6 | 主备中心 failover | 无 | 无 | ❌ | **V1.5** |
| F7.7 | 多中心联邦 (公司间互联) | 无 | 无 | ❌ | **V2** |
| F7.8 | IDOR 安全修复 | 无此问题 (旧版无转发层) | `uid` 信任客户端 + token走URL | ❌ | **V1** — 包A修 |

---

## 八、部署与运维

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F8.1 | 中心服务器部署 | `server/index.js` HTTP :9527 | `hermes serve --port 9120` | ✅ | 已完成 |
| F8.2 | Desktop 开发模式 | `npm run dev` | `npm run dev` | ✅ | 已完成 |
| F8.3 | 消息归档 | `archive.py` MySQL/JSONL/off | ✅ | 已完成 |
| F8.4 | 部署文档 | `mim-message-center-setup.md` | ✅ | 已完成 |
| F8.5 | 故障排查手册 | 无 | 无 | ❌ | **V1.5** |

---

## 九、前端 UI

| # | 功能 | 旧版 | 新版现状 | 评估 | 决策 |
|---|------|------|---------|:--:|------|
| F9.1 | 联系人列表 | `Sidebar.tsx` | `mim/index.tsx` 双栏 | ✅ | 已完成 |
| F9.2 | 聊天视图 | `ChatPanel.tsx` 消息气泡 | `mim/index.tsx` 手写div | ⚠️ | **V1 P1** — 对齐 Hermes 原生 |
| F9.3 | 登录页 + 已有用户列表 | 无 | ✅ | 已完成 |
| F9.4 | Profile 面板 | 无 | ✅ | 已完成 |
| F9.5 | 联系人资料查看 | 无 | `ContactProfilePanel` | ✅ | 已完成 |
| F9.6 | 本机运行时区块 | 无 | 无 | ❌ | **V1** — 包D |
| F9.7 | 模式显示 (替代硬编码) | 无 | ProfilePanel 硬编码 MQTT IP | ⚠️ | **V1** — 改动态显示 |
| F9.8 | 空状态 (Intro) | Hermes `Intro` 组件 | 硬编码 `💬 选择联系人` | ⚠️ | **V1.5** |
| F9.9 | 加载骨架屏 | Hermes `skeletons.tsx` | 无 | ❌ | **V1.5** |

---

## 十、实施优先级总表

### 🔴 V1 P0 — 断了的功能，必须修（约 30 行）

| # | 功能 | 涉及文件 | 行数 |
|---|------|---------|:--:|
| P0-1 | 联系人真实 online 状态 | `chat.py` + `index.tsx` | 15 |
| P0-2 | 按 online 排序 + offline 灰色 | `index.tsx` | 15 |

### 🔴 V1 — 中心化架构基础（约 600 行）

| # | 功能 | 包 | 行数 |
|---|------|:--:|:--:|
| V1-1 | IDOR 安全修复 (uid不信任客户端 + token走header) | A | 20 |
| V1-2 | online 批量 uids + runtime_report RPC + local_agents RPC | A | 120 |
| V1-3 | login 透传 agent_type/machine + DDL | A | 30 |
| V1-4 | hub_bridge 客户端模式 (配center_url跳过DB/MQTT) | B | 30 |
| V1-5 | daemon 升级 15类型检测 + 注册/心跳走转发入口 | C | 150 |
| V1-6 | 前端: 多身份切换 + 本机运行时 + 两步新建 | D | 200 |
| V1-7 | E2E 双实例 | E | 80 |

### 🟡 V1 P1 — UI体验过关（约 100 行）

| # | 功能 | 复用组件 | 行数 |
|---|------|---------|:--:|
| P1-1 | Markdown 消息渲染 | `compact-markdown.tsx` | 30 |
| P1-2 | 消息复制按钮 | `copy-button.tsx` | 15 |
| P1-3 | 时间戳相对格式 | `formatMessageTimestamp` | 5 |
| P1-4 | 滚动到底部按钮 | `scroll-to-bottom-button.tsx` | 15 |
| P1-5 | 输入框 IME 保护 | 参考 Hermes Composer | 20 |
| P1-6 | 错误提示 toast | 现有 toast 组件 | 15 |

### 🟡 V1.5 — 下个版本（约 500 行）

| 群聊基础 | 离线消息缓存 | 投递确认 | 联系人搜索 | 空状态 | 加载骨架 | 实时状态推送 | 故障排查手册 |

### ⚪ V2 — 远期（约 1000 行）

| Agent自动匹配 | 群观察者/悬赏 | 群规则 | 议题引擎 | 问题板 | 群文件 | 消息撤回/转发 | 图片/文件 | 好友温度 | 多中心联邦 | 任务调遣 |

---

## 十一、被合并/废弃的文档

以下文档内容已全部并入本文，不再单独维护：

| 旧文档 | 去处 |
|--------|------|
| `capability-audit.md` | 并入 §三/§四/§九 |
| `migration-audit.md` | 并入 §一~§八 (功能对比列) |
| `group-chat-spec.md` | 并入 §四 |
| `ui-interaction-spec.md` | 并入 §九 + V1 包D |
| `test-plan.md` | 保留独立 (引用本文 §十) |
| `v1-acceptance-checklist.md` | 保留独立 (引用本文 §十) |
| `chat-features.md` (旧版) | 并入 §三/§四/§五 |
| `chat.md` (旧版) | 并入 §三 |
| `desktop-chat.md` (旧版) | 并入 §九 |
| `messaging.md` (旧版) | 并入 §三/§六 |
| `group-chat-collaboration.md` (旧版) | 并入 §四 |
| `daemon-master-protocol.md` (旧版) | V2参考 (daemon数字分身概念) |
| `adr-009-mqtt-message-network.md` (旧版) | 并入 §七 (MQTT架构) |
| `adr-010-message-entry-unification.md` (旧版) | 并入 §六 (F6.5 统一入口) |

---

**本文是 MIM 功能的唯一事实来源。新增/修改功能先更新本文，再写代码。**
