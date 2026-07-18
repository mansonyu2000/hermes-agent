# MIM 功能清单

> 版本: v2.0 · 日期: 2026-07-18 · 性质: **唯一事实来源，新增功能先查本文**

### 三个操作

| 操作 | 怎么做 | 示例 |
|------|--------|------|
| **清点** | `Ctrl+F` 搜功能名或 ID → 找到了 = 已记录，没找到 = 漏了，新增一行 | 搜 "Markdown" → 找到 F3.4 → 已记录 ✅ |
| **标记** | 改状态列 (`✅`/`⚠️`/`❌`) 或决策列 (`V1`/`V1.5`/`V2`) | `F3.4` 做完了 → 状态改 `✅`，决策改 `已完成` |
| **修改** | 改子功能列（补充/删减）、依赖列（加减引用）、或升/降级决策 | `F3.4` 要加"表格渲染" → 子功能列追加 `, 表格渲染` |

### 三不要

- ❌ **不要新建重复 ID** — 搜到了就改已有行
- ❌ **不要改 ID 名** — `F3.4` 永远不变，联动索引用它
- ❌ **不要删行** — 不做了 = 标记 `❌-skip` + 备注原因，不要删

---

## 模块索引

| 编号 | 模块 | ID 前缀 | 功能数 |
|:--:|------|:--:|:--:|
| 1 | 身份与登录 | `F1.x` | 7 |
| 2 | 联系人 | `F2.x` | 7 |
| 3 | 单聊消息 | `F3.x` | 14 |
| 4 | 群聊 | `F4.x` | 10 |
| 5 | 在线状态与心跳 | `F5.x` | 5 |
| 6 | 消息可靠性 | `F6.x` | 5 |
| 7 | 架构治理 | `F7.x` | 8 |
| 8 | 部署与运维 | `F8.x` | 5 |
| 9 | 前端 UI | `F9.x` | 9 |

---

## 一、身份与登录

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F1.1 | 用户注册 | nickname/role/password 三字段, identity.register() → MySQL | — | ✅ | 已完成 |
| F1.2 | 用户登录 | nickname + password 验证, SHA256 比对, 无密码用户兼容 | — | ✅ | 已完成 |
| F1.3 | 统一密码 `123321` | 全部用户默认密码, DB 批量重置 | — | ✅ | 已完成 |
| F1.4 | 多身份支持 | `mim-identities` 数组存储, `mim-active-uid` 激活标识, 旧版单 key 自动迁移 | — | ⚠️ | V1 — 包D |
| F1.5 | 身份切换 | 切换清空消息列表, history 按新 uid 重查, poll 跟随新 uid, send 用新 uid | F1.4, F3.3, F9.2 | ❌ | V1 — 包D |
| F1.6 | 两步新建智能体 | 第1步: 15种类型网格(已发现高亮), 第2步: 预填名 `{machine}-{type}-{n}`, 提交调 login | F1.7, F1.4 | ❌ | V1 — 包D |
| F1.7 | daemon 自动发现本机 agent | 15种类型, 双通道检测(config_dir + path_cmd), 幂等(已注册不重复) | F7.3 | ⚠️ | V1 — 包C |

---

## 二、联系人

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F2.1 | 联系人列表 | `get_contacts()` → MySQL, 全量返回 | — | ✅ | 已完成 |
| F2.2 | 真实在线状态 | `hub.is_online(uid)` 查 nodes.json, **删除前端写死 `online:true`** | F5.1, F5.2 | ⚠️ | V1 P0 |
| F2.3 | 按 online 排序 | online 优先 > 未读数 > 名字字母序 | F2.2 | ⚠️ | V1 P0 |
| F2.4 | offline 灰色视觉 | 灰圆点 `bg-gray-400`, 头像半透明 `opacity-60`, 名字灰色 `text-quaternary` | F2.2 | ⚠️ | V1 P0 |
| F2.5 | 联系人实时状态推送 | `contact.status` WS 事件, 上线/离线即时推送 | F5.4 | ❌ | V1.5 |
| F2.6 | 好友温度系统 | 消息互动+3/天(上限15), 主人主动+5, 每日衰减-1(3天无互动后), 温度区间 0-100 | — | ❌ | V2 |
| F2.7 | 联系人搜索/过滤 | 按名字搜索, 按角色过滤, 按在线状态过滤 | — | ❌ | V1.5 |

---

## 三、单聊消息

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F3.1 | 发消息 | MySQL `chat` 表 INSERT, MQTT `comms/say/{uid}` publish, 本地 `enqueue` 投递 | — | ✅ | 已完成 |
| F3.2 | 收消息 | `poll_messages(uid)` 内存队列轮询, 3s 间隔 | — | ✅ | 已完成 |
| F3.3 | 消息历史 | `get_history(uid, peer_uid, limit)` MySQL 查询, 时间倒序, 双向 | — | ✅ | 已完成 |
| F3.4 | Markdown 消息渲染 | 复用 `compact-markdown.tsx`, 代码块 Shiki 高亮, 行内代码, 链接渲染 | F9.2 | ❌ | V1 P1 |
| F3.5 | 消息复制按钮 | 右键/长按消息 → 复制文本 → toast "已复制", 复用 `copy-button.tsx` | F9.2 | ❌ | V1 P1 |
| F3.6 | 时间戳相对格式 | `formatMessageTimestamp()`, 今天=时间, 昨天="昨天 HH:mm", 更早=日期 | F9.2 | ⚠️ | V1 P1 |
| F3.7 | 滚动到底部 | 新消息自动滚底, 用户上滚后出现 ↓ 按钮, 复用 `scroll-to-bottom-button.tsx` | F9.2 | ⚠️ | V1 P1 |
| F3.8 | 输入框 IME 保护 | Enter=发送(非IME), Shift+Enter=换行, `isComposing=true` 时 Enter 不上发, 空消息禁止发送 | F9.2 | ⚠️ | V1 P1 |
| F3.9 | 消息错误提示 | 发送失败 toast, DB 不可达提示, 网络错误提示 | F9.2 | ❌ | V1 P1 |
| F3.10 | @提及 | `@username` 模式识别, `chat.mentioned` 事件, 高亮蓝色 | — | ❌ | V1.5 |
| F3.11 | Thread Reply | `reply_to` 消息 ID, 引用条 UI(蓝色左边框), 输入框上方回复栏 | — | ❌ | V1.5 |
| F3.12 | 消息撤回 | 2分钟内可撤回, "已撤回"占位提示 | — | ❌ | V2 |
| F3.13 | 消息转发 | 转发到其他联系人或群 | — | ❌ | V2 |
| F3.14 | 图片/文件发送 | 拖放上传, 粘贴图片, 附件预览 | — | ❌ | V2 |

---

## 四、群聊

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F4.1 | 群表 DDL | `m_groups` 表(gid/title/description/owner_id/admins), `m_group_members` 表, `m_group_tags` 表, `chat` 表加 `gid` 列 | — | ❌ | V1.5 |
| F4.2 | 创建群 | 选群名+描述+初始成员, 创建者=owner, 自动写入 `m_group_members` | F4.1 | ❌ | V1.5 |
| F4.3 | 邀请成员 | 群主/管理员邀请, 写入 `m_group_members` | F4.1 | ❌ | V1.5 |
| F4.4 | 群消息发送 | `send_message()` 加 `gid` 参数, MQTT `comms/group/{gid}` 广播, 本地 enqueue | F4.1, F3.1 | ❌ | V1.5 |
| F4.5 | 群消息接收 | 订阅 `comms/group/{gid}`, `poll_messages(gid)` 轮询 | F4.1, F3.2 | ❌ | V1.5 |
| F4.6 | 群消息历史 | 复用 `get_history()` 加 `gid` 模式 | F4.1, F3.3 | ❌ | V1.5 |
| F4.7 | 群聊前端 UI | 马赛克头像(前4成员首字母), 每条消息显示发送者名, 群信息面板(成员列表/标签), 新建群入口 | F9.1, F4.2 | ❌ | V1.5 |
| F4.8 | @all 广播 | `isAtAll` → 全员 `chat.mentioned` 事件, MQTT 广播 | F4.4 | ❌ | V1.5 |
| F4.9 | 群悄悄话 | `whisper_session_id` 隔离, 仅被@者+发送者可见, 粉色"仅你和@xx可见"提示 | — | ❌ | V2 |
| F4.10 | Agent 自动匹配 | 三阶段: 专家匹配(得分>=1)→标签匹配→历史相似, EAV画像驱动, `match_stats` 统计 | — | ❌ | V2 |

---

## 五、在线状态与心跳

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F5.1 | 心跳注册 | `hub.register_node(uid, name, role, host)` → `nodes.json`, uid 不存在时占位注册 | — | ✅ | 已完成 |
| F5.2 | 心跳更新 | `hub.heartbeat(uid)` 每 30s 刷新 `last_seen`, 标记 `status:online` | — | ✅ | 已完成 |
| F5.3 | 死节点检测 | `hub.sweep_dead_nodes()` 120s 无心跳 → `status:offline` | — | ✅ | 已完成 |
| F5.4 | WS 事件广播 | `node.joined` 上线推送, `node.left` 离线推送, 全客户端广播 | F5.1 | ❌ | V1.5 |
| F5.5 | 批量心跳 | daemon 收集本机全部 uid → `uids:[]` 参数 → 中心逐个 `heartbeat`, **一次心跳替整机所有 agent** | F1.7, F5.2 | ❌ | V1 — 包A+包C |

---

## 六、消息可靠性

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F6.1 | 离线消息缓存 | `message_queue` 表, TTL 168h, 上线自动推送全部未读 | F3.1, F5.1 | ⚠️ | V1.5 |
| F6.2 | 投递确认 (ACK) | `message_acks` 表, `ack_from_node` + `status`, 物流回签通知 | F3.1 | ❌ | V1.5 |
| F6.3 | 已读回执 | `message_receipts` 表, 已读/未读标识, 联系人列表未读数 | — | ❌ | V2 |
| F6.4 | 投递状态机 | pending → delivering → delivered, 超时 retry, 24h 无确认 → expired | F3.1 | ⚠️ | V1.5 |
| F6.5 | 统一消息入口 `routeMessage()` | 标准化 from_uid/from_name/to_uid/body, 一次 INSERT + 一次 push, `delivery_status` 闭环 | F3.1, F4.4 | ❌ | V1.5 |

---

## 七、架构治理

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F7.1 | 中心化模式 | 客户端只有一条 WS 到中心, **零 3306/1883 出站**, `_mim_center_call` 转发层 | — | ⚠️ | V1 — 包B |
| F7.2 | hub_bridge 客户端感知 | `center_url()` 读 config, 配了→跳过 MySQL/MQTT/健康检查, 仍启动 daemon | F7.1 | ❌ | V1 — 包B |
| F7.3 | daemon 升级 | 15种类型检测表, 注册/心跳改调 handler(不直连 identity/hub), `get_local_state()` | F1.7, F7.2 | ❌ | V1 — 包C |
| F7.4 | runtime 上报 | daemon 启动上报 `{machine, daemon_version, runtimes[...]}`, 中心写 `nodes.json` machines 键, 覆盖式更新 | F7.3 | ❌ | V1 — 包A+包C |
| F7.5 | E2E 双实例验证 | assert 零3306/1883, assert login→send→poll, assert runtime_report, assert 杀daemon→offline→重启online | F7.1, F7.2, F7.3 | ❌ | V1 — 包E |
| F7.6 | 主备中心 failover | 主中心宕→手动切 center_url 到备中心 | — | ❌ | V1.5 |
| F7.7 | 多中心联邦 | 公司间 P2P 互联, 对等节点发现, 跨公司消息路由 | — | ❌ | V2 |
| F7.8 | IDOR 安全修复 | `uid` 不从客户端参数取(回退 `active_uid()`), token 走 HTTP Header 不走 URL | F3.1, F3.2, F3.3 | ❌ | V1 — 包A |

---

## 八、部署与运维

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F8.1 | 中心服务器部署 | `hermes serve --host 0.0.0.0 --port 9120`, config.yaml `mim.enabled:true`, 不配 `center_url` | — | ✅ | 已完成 |
| F8.2 | Desktop 开发模式 | `npm run dev` → Vite :5175 + Electron spawn 后端 | — | ✅ | 已完成 |
| F8.3 | 消息归档 | `archive.py`, MySQL/JSONL/off 三种引擎, `HUB_ARCHIVE_ENGINE` 环境变量切换 | — | ✅ | 已完成 |
| F8.4 | 部署文档 | `mim-message-center-setup.md`, 8机部署步骤, 主备配置 | — | ✅ | 已完成 |
| F8.5 | 故障排查手册 | 消息发不出诊断, 离线检测诊断, MQTT 断连恢复, MySQL 断连恢复 | — | ❌ | V1.5 |

---

## 九、前端 UI

| # | 功能 | 子功能 | 依赖 | 状态 | 决策 |
|---|------|--------|------|:--:|------|
| F9.1 | 联系人列表 | MasterDetail 双栏, 头像+昵称+角色+在线状态绿点 | F2.1, F2.2 | ✅ | 已完成 |
| F9.2 | 聊天视图 | 消息气泡(自消息右对齐蓝, 他消息左对齐灰), 输入框+发送按钮 | F3.1, F3.2 | ⚠️ | V1 P1 |
| F9.3 | 登录页 | 已有用户快速选择, 用户名+密码输入, 注册切换 | F1.1, F1.2 | ✅ | 已完成 |
| F9.4 | Profile 面板 | 头像+昵称+角色+UID, 我的身份列表, 退出登录 | F1.4 | ✅ | 已完成 |
| F9.5 | 联系人资料查看 | `ContactProfilePanel`, title/bio/skills/manager_uid 展示 | F2.1 | ✅ | 已完成 |
| F9.6 | 本机运行时区块 | daemon 发现结果展示, 已注册=一键进入, 未注册=两步新建, 未安装=灰显 | F1.7, F9.3 | ❌ | V1 — 包D |
| F9.7 | 模式显示 | **删除** ProfilePanel 硬编码 `MQTT Broker 192.168.3.23:1883` 和 `WinPeek Hub 127.0.0.1:9200`, 替换为 `客户端模式→{center_url}` 或 `中心模式(本机 hub)` | F7.1 | ⚠️ | V1 — 包D |
| F9.8 | 空状态 Intro | 对齐 Hermes `Intro` 组件, 随机文案, 人格化问候 | — | ⚠️ | V1.5 |
| F9.9 | 加载骨架屏 | 历史加载骨架, 联系人加载骨架, 复用 Hermes `skeletons.tsx` | — | ❌ | V1.5 |

---

## 实施优先级

### 🔴 V1 P0 — 断了的功能 (约 30 行)

| # | 功能 | 具体改动 |
|---|------|---------|
| F2.2 | 真实在线状态 | `chat.py` get_contacts 加 `hub.is_online(uid)`, 前端删 `online:true` |
| F2.3 | 按 online 排序 | 改 `sortedContacts` 比较函数 |
| F2.4 | offline 灰色视觉 | CSS: 灰圆点 + 半透明头像 + 灰色名字 |

### 🔴 V1 — 中心化架构 (约 600 行, 5 个并行包)

| 包 | 功能 | 行数 |
|:--:|------|:--:|
| A | F7.8 IDOR + F5.5 批量心跳 + F7.4 runtime_report + F1.7 透传 agent_type + DDL | 170 |
| B | F7.2 hub_bridge 客户端模式 | 30 |
| C | F7.3 daemon 升级 15 类型 | 150 |
| D | F1.4 多身份 + F1.5 切换 + F1.6 两步新建 + F9.6 运行时区块 + F9.7 模式显示 | 200 |
| E | F7.5 E2E 双实例 | 80 |

### 🟡 V1 P1 — UI 体验 (约 100 行)

| 功能 | 复用组件 | 行数 |
|------|---------|:--:|
| F3.4 Markdown 渲染 | `compact-markdown.tsx` | 30 |
| F3.5 消息复制 | `copy-button.tsx` | 15 |
| F3.6 相对时间戳 | `formatMessageTimestamp` | 5 |
| F3.7 滚动到底 | `scroll-to-bottom-button.tsx` | 15 |
| F3.8 IME 保护 | Hermes Composer 参考 | 20 |
| F3.9 错误提示 | toast 组件 | 15 |

---

## 联动索引

> 改一个功能时，查下表 → 受影响的功能 → 评估是否需要联动更新。

| 你改了 | 可能需要联动更新 |
|--------|----------------|
| F1.4 多身份 | F1.5, F9.4, F9.6 |
| F1.7 daemon 发现 | F1.6, F5.5, F7.3, F9.6 |
| F2.2 真实在线 | F2.3, F2.4, F9.1 |
| F3.1 发消息 | F4.4, F6.1, F6.2, F6.4, F6.5, F7.8, F9.2 |
| F3.2 收消息 | F4.5, F7.8, F9.2 |
| F3.3 消息历史 | F1.5, F4.6, F7.8 |
| F3.4-F3.9 消息UI | F9.2 (全部依赖聊天视图组件) |
| F5.1 心跳注册 | F2.2, F5.4, F5.5, F6.1 |
| F5.2 心跳更新 | F2.2, F5.5 |
| F7.1 中心化 | F7.2, F7.5, F9.7 |
| F7.2 hub_bridge | F7.3, F7.5 |
| F7.3 daemon | F1.7, F7.4, F7.5 |
| F9.2 聊天视图 | F3.4-F3.9, F1.5 |

---

**本文是 MIM 功能的唯一事实来源。新增功能→先 Ctrl+F 查重→取新 ID→写清依赖→更新联动索引。**
