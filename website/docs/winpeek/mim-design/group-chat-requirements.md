---
title: "MIM 群聊需求分析"
description: "群聊功能模块完整需求分析 — 功能清单、模块关系、数据库设计、API接口、数据流、验收标准"
sidebar_position: 6
type: product
role: ["architect", "developer", "tester", "product"]
module: mim
status: review
last_updated: "2026-07-18"
---

> 📍 [返回 MIM 知识库地图](overview)

---

## 概述

本文档是 MIM 群聊功能的**完整需求分析**。综合旧版 winpeek-prod 的 32 个 JS 模块经验、新版 hermes-agent-cc 现有架构（Python + MySQL + MQTT）、以及 `feature-inventory.md` §四 的功能决策，按照"功能清单→模块关系→数据模型→接口→数据流→测试→验收"的完备结构编写。

**读者**：架构师（评估设计）、开发者（按规格实现）、测试者（按验收标准验证）、产品（确认功能覆盖）。

---

## 一、功能清单

群聊模块共 **10 个子功能**，分三层交付：

```
V1.5 (本期): F4.1 ~ F4.8    基础群聊（建群/收发/历史/前端/@all）
V2 (远期):  F4.9 ~ F4.10   高级功能（悄悄话/Agent自动匹配）
```

| # | 功能 | 用户故事 | 优先级 |
|---|------|---------|:--:|
| F4.1 | 群表 DDL | 作为开发者，我需要 `m_groups` / `m_group_members` 两张表存储群和成员关系 | V1.5 |
| F4.2 | 创建群 | 作为用户，我选择一个群名、添加初始成员，创建一个新群聊 | V1.5 |
| F4.3 | 邀请成员 | 作为群主，我邀请其他人加入已有群聊 | V1.5 |
| F4.4 | 群消息发送 | 作为群成员，我在群里发消息，所有在线成员实时收到 | V1.5 |
| F4.5 | 群消息接收 | 作为群成员，我打开群聊看到全部消息，新消息自动推送 | V1.5 |
| F4.6 | 群消息历史 | 作为群成员，我向上滚动看到更早的消息 | V1.5 |
| F4.7 | 群聊前端 UI | 作为用户，我看到的群聊界面与单聊一致（但有马赛克头像、发送者名字、群信息面板） | V1.5 |
| F4.8 | @all 广播 | 作为群成员，我发 @all 消息，所有人都收到通知 | V1.5 |
| F4.9 | 群悄悄话 | 作为群成员，我对某人说悄悄话，只有我俩看得到 | V2 |
| F4.10 | Agent 自动匹配 | 作为系统，群消息自动找最合适的 Agent 回复 | V2 |

---

## 二、功能模块关系

### 2.1 分层依赖

```
┌─ 前端 UI (F4.7) ──────────────────────────────────────┐
│  mim/index.tsx: 群名片 + 群聊天视图 + 群信息面板 + 新建群 │
│       │                                                 │
│       ▼ JSON-RPC (useGatewayRequest)                    │
├─ RPC 层 ───────────────────────────────────────────────┤
│  tui_gateway/server.py: @method 注册 6 个群 RPC         │
│  tools/winpeek_tools.py: 6 个 handler (含 _mim_center_call 转发) │
│       │                                                 │
│       ▼ 调 gateway/winpeek_hub/                         │
├─ 业务层 ───────────────────────────────────────────────┤
│  chat.py: send_message 加 gid 参数 + 群消息 fanout       │
│  identity.py: 群成员查昵称 (已有, 不新增)                │
│       │                                                 │
│       ├─ MySQL: m_groups / m_group_members / chat(gid)  │
│       └─ MQTT: comms/group/{gid} 广播 topic             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 功能间依赖链

```
F4.1 群表 DDL
  ├─→ F4.2 创建群 (INSERT m_groups + m_group_members)
  ├─→ F4.3 邀请成员 (INSERT m_group_members)
  ├─→ F4.4 群消息发送 (INSERT chat WHERE gid=...)
  ├─→ F4.5 群消息接收 (SUBSCRIBE comms/group/{gid})
  ├─→ F4.6 群消息历史 (SELECT chat WHERE gid=...)
  └─→ F4.7 群聊前端 UI (GROUP BY gid, 成员名字查询)
        └─→ F4.8 @all 广播 (依赖 F4.4 的消息通道)
```

**关键逻辑**：F4.1 是所有功能的唯一数据前提——DDL 不执行，其余 7 个全部阻塞。

### 2.3 与单聊的复用关系

群聊不是独立系统——80% 复用单聊已有代码：

| 复用什么 | 单聊（已存在） | 群聊怎么用 |
|---------|-------------|-----------|
| `chat` 表 INSERT | `send_message(from_uid, to_uid, body)` | 加 `gid` 参数, `to_uid=NULL` |
| `chat` 表 SELECT | `get_history(uid, peer_uid)` | 加 `gid` 参数, 忽略 `peer_uid` |
| 内存队列 `poll_messages` | `enqueue({to_uid})` | 改 `enqueue({gid})` |
| MQTT 发布 | `comms/say/{uid}` 点对点 | `comms/group/{gid}` 广播 |
| 前端消息气泡 | 同组件 | 多一条发送者名（群聊不是"我/你"二选一） |
| 发送者名取昵称 | `identity.get_by_uid(uid)` | 复用 |

---

## 三、数据库表/字段设计

### 3.1 新增表

#### `m_groups` — 群基本信息

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|:--:|------|------|
| `gid` | INT | ✅ | AUTO_INCREMENT | 群 ID（主键） |
| `title` | VARCHAR(128) | ✅ | — | 群名（创建时必填） |
| `description` | VARCHAR(512) | | `""` | 群描述 |
| `owner_uid` | INT | ✅ | — | 群主 uid（创建者） |
| `conversation_type` | VARCHAR(32) | | `"normal"` | normal / meeting |
| `status` | TINYINT | | `1` | 1=正常, 0=已解散 |
| `created_at` | DATETIME | | `NOW()` | — |
| `updated_at` | DATETIME | | `NOW()` | ON UPDATE |

```sql
CREATE TABLE IF NOT EXISTS m_groups (
    gid         INT PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(128) NOT NULL,
    description VARCHAR(512) DEFAULT '',
    owner_uid   INT NOT NULL,
    conversation_type VARCHAR(32) DEFAULT 'normal',
    status      TINYINT DEFAULT 1,
    created_at  DATETIME DEFAULT NOW(),
    updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_owner (owner_uid),
    INDEX idx_status (status)
);
```

#### `m_group_members` — 群成员关系

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|:--:|------|------|
| `gid` | INT | ✅ | — | 群 ID |
| `uid` | INT | ✅ | — | 成员 uid |
| `role` | VARCHAR(32) | | `"member"` | owner / admin / member |
| `joined_at` | DATETIME | | `NOW()` | 加入时间 |

```sql
CREATE TABLE IF NOT EXISTS m_group_members (
    gid     INT NOT NULL,
    uid     INT NOT NULL,
    role    VARCHAR(32) DEFAULT 'member',
    joined_at DATETIME DEFAULT NOW(),
    PRIMARY KEY (gid, uid),
    FOREIGN KEY (gid) REFERENCES m_groups(gid) ON DELETE CASCADE
);
```

### 3.2 改动已有表

#### `chat` — 加群聊支持

`chat` 表已存在（`gateway/winpeek_hub/chat.py` 和 MySQL winpeek-db2），只需加 1 列：

```sql
ALTER TABLE chat ADD COLUMN gid INT NULL;
CREATE INDEX idx_chat_gid ON chat(gid);
```

| 新增字段 | 类型 | 必填 | 默认 | 说明 |
|---------|------|:--:|------|------|
| `gid` | INT | | `NULL` | 群聊消息=群ID, 单聊消息=NULL |

**兼容性**：存量单聊消息 `gid=NULL`，查询逻辑加 `WHERE gid IS NULL` / `WHERE gid=?` 区分即可。

### 3.3 数据字典逻辑关系

```
m_groups.gid ───────────── 1:N ──→ m_group_members.gid
                                              │
                                    m_group_members.uid ──→ users.uid (查昵称)

m_groups.gid ───────────── 1:N ──→ chat.gid
                                    chat.from_uid ──→ users.uid (查发送者名)
```

**一条群消息的生命周期**：

```
1. 用户发消息 → chat 表 INSERT (mid, cid, gid=xxx, from_uid=1, content="你好")
2. MQTT publish → comms/group/{gid} (body: {from_uid:1, from_name:"yuyangmin", content:"你好"})
3. 所有订阅 comms/group/{gid} 的在线成员 → on_message 回调 → enqueue({gid, ...})
4. 客户端 poll → 内存队列 → 消息气泡渲染 (显示 "yuyangmin: 你好")
5. 离线成员下次上线 → 调 get_history(gid) → MySQL 返回全部消息
```

---

## 四、API 接口

### 4.1 RPC 方法清单

| RPC 方法 | 参数 | 返回 | 对应功能 |
|---------|------|------|:--:|
| `winpeek_mim_group_create` | `{title, description?, member_uids:[]}` | `{ok, gid}` | F4.2 |
| `winpeek_mim_group_list` | `{uid}` | `{groups:[{gid,title,member_count,last_message}]}` | F4.7 |
| `winpeek_mim_group_detail` | `{gid}` | `{group, members:[...]}` | F4.7 |
| `winpeek_mim_group_invite` | `{gid, uids:[]}` | `{ok}` | F4.3 |
| `winpeek_mim_group_send` | `{gid, body}` | `{ok, mid}` | F4.4 |
| `winpeek_mim_group_history` | `{gid, limit?}` | `{messages:[...]}` | F4.6 |

### 4.2 请求/响应示例

```jsonc
// 建群
→ {"jsonrpc":"2.0","method":"winpeek_mim_group_create","params":{"title":"WinPeek 开发组","member_uids":[2032,1002]}}
← {"result":{"ok":true,"gid":1}}

// 发群消息
→ {"jsonrpc":"2.0","method":"winpeek_mim_group_send","params":{"gid":1,"body":"大家好"}}
← {"result":{"ok":true,"mid":"mim-1784300000000-abc123"}}

// 群消息历史
→ {"jsonrpc":"2.0","method":"winpeek_mim_group_history","params":{"gid":1,"limit":50}}
← {"result":{"messages":[{"from_uid":1,"from_name":"yuyangmin","content":"大家好","msg_ts":"2026-07-18T10:00:00"},...]}}

// 我的群列表
→ {"jsonrpc":"2.0","method":"winpeek_mim_group_list","params":{"uid":1}}
← {"result":{"groups":[{"gid":1,"title":"WinPeek 开发组","member_count":5,"last_message":"大家好"}]}}
```

### 4.3 安全性

所有群 RPC 在 center_url 模式下的行为：
- **客户端模式**：`_mim_center_call()` 自动转发到中心（已有转发层，不新增代码）
- **中心模式**：直接操作 MySQL + MQTT
- **身份校验**：群 RPC 的 `from_uid` 从 `active_uid()` 取，不接受客户端参数（复用 F7.8 IDOR 修复后的安全基线）

---

## 五、数据流

### 5.1 群消息完整路径

```
┌─────────┐  winpeek_mim_group_send   ┌────────────┐
│ Desktop │ ────────────────────────→ │ hermes serve│
│ (前端)   │                           │ (RPC层)    │
└─────────┘                           └──────┬─────┘
                                             │
                                    ┌────────▼────────┐
                                    │ chat.send_message│
                                    │ (gid=1, body)   │
                                    └────────┬────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                     ┌──────────┐  ┌──────────────┐  ┌───────────┐
                     │ MySQL    │  │ MQTT         │  │ enqueue   │
                     │ INSERT   │  │ comms/group/1│  │ (本地投递)│
                     │ gid=1    │  │ publish      │  │ gid=1     │
                     └──────────┘  └──────┬───────┘  └─────┬─────┘
                                          │                │
                              订阅了 topic │                │本机直接poll
                              的所有在线机器│                │
                              ┌───────▼────────┐      ┌───▼──────┐
                              │ 其他 Desktop   │      │ 本机     │
                              │ mqtt_adapter   │      │ Desktop  │
                              │ _on_message    │      │ poll     │
                              │ → enqueue()    │      │          │
                              └───────┬────────┘      └───┬──────┘
                                      │                   │
                              ┌───────▼────────┐      ┌───▼──────┐
                              │ poll_messages  │      │ 渲染消息 │
                              │ (前端轮询)     │      │ 气泡     │
                              └────────────────┘      └──────────┘
```

### 5.2 MQTT Topic 设计

| Topic | 用途 | 订阅者 |
|-------|------|--------|
| `comms/say/{uid}` | 单聊消息（已有） | 目标 uid 对应的 Desktop |
| **`comms/group/{gid}`** | **群聊广播（新增）** | **该群全部在线成员** |

### 5.3 单聊/群聊消息存储对比

| 字段 | 单聊 | 群聊 |
|------|:--:|:--:|
| `cid` | `"1-2032"` (uid小的在前) | `"g1"` (g前缀) |
| `gid` | `NULL` | `1` (群ID) |
| `from_uid` | 发送者 uid | 发送者 uid |
| `to_uid` | 接收者 uid | `NULL` |

---

## 六、测试计划

### 6.1 单元测试

| # | 测试点 | 输入 | 断言 |
|---|--------|------|------|
| T1 | 建群 | `{title:"测试群", member_uids:[2032]}` | `m_groups` 写入1行, `m_group_members` 写入2行(owner+member) |
| T2 | 建群幂等 | 同参数两次 | 第二次返回已有群 gid (not duplicate) |
| T3 | 邀请成员 | `{gid:1, uids:[2033]}` | `m_group_members` 新增1行 |
| T4 | 邀请重复成员 | 邀请已在群的 uid | 静默成功(INSERT IGNORE) |
| T5 | 群消息发送 | `{gid:1, body:"hello"}` | `chat` 表 gid=1 写入, mid 返回 |
| T6 | 非成员发消息 | uid不在群内的人发群消息 | 返回 error "not a member" |
| T7 | 群消息历史 | `{gid:1, limit:10}` | 返回最近10条, 时间倒序后再反转(正序) |
| T8 | 空群消息历史 | 新群无消息 | 返回 `[]` |

### 6.2 集成测试

| # | 场景 | 步骤 | 断言 |
|---|------|------|------|
| I1 | 两人群聊完整链路 | ① A建群(B在群) ② A发消息 ③ B poll | B 收到消息, from_name 正确 |
| I2 | 三人群聊 fanout | ① A建群(B,C在群) ② A发消息 ③ B poll ④ C poll | B和C都收到同一消息 |
| I3 | 离线成员补历史 | ① A建群(B在群) ② A发消息(B离线) ③ B上线调 history | B 看到离线期间的消息 |
| I4 | 群列表 | ① A建群1, A建群2 ② list_groups(A) | 返回2个群, 各有 member_count |
| I5 | 群详情 | ① detail(gid=1) | 返回群名+成员列表(含昵称) |

### 6.3 手工验收

| # | 验收项 | 操作 | 通过标准 |
|---|--------|------|---------|
| M1 | 创建群 | MIM界面 → "+" → 填群名 → 选成员 → 创建 | 联系人列表出现群名片 |
| M2 | 群聊对话 | 点群名片 → 发消息 → 另一个账号查看 | 消息实时显示, 显示发送者名 |
| M3 | 马赛克头像 | 4人群 | 头像显示 2×2 首字母马赛克 |
| M4 | @all | 输入 "@all 开会了" → 发送 | 所有成员收到通知 |
| M5 | 群信息面板 | 点群名 → 右侧面板 | 显示成员列表+群名+创建时间 |

---

## 七、验收标准

### 7.1 功能完整性

- [ ] 用户可创建群（选群名 + 初始成员）
- [ ] 群成员可发消息，所有在线成员实时收到
- [ ] 离线成员重新上线后能看到历史消息
- [ ] 联系人列表出现群名片（在单聊联系人之后）
- [ ] 群聊天视图显示每条消息的发送者名字
- [ ] 群信息面板显示成员列表（含昵称+角色）
- [ ] @all 消息全员通知
- [ ] 群聊与单聊共享同一套消息气泡/输入框组件

### 7.2 架构约束

- [ ] 群消息走中心转发（客户端模式与单聊同路径）
- [ ] 群聊不新增 MySQL 连接（复用已有 `db.get_conn()`）
- [ ] 群聊不新增 MQTT topic 订阅模式（复用 `_on_message` 的通配订阅 `comms/#`）

### 7.3 性能

- [ ] 10人群发消息 fanout < 500ms
- [ ] 群消息历史 50条查询 < 100ms
- [ ] 群列表（100个群）加载 < 200ms

---

## 八、实现方法

### 8.1 改动文件清单

| 文件 | 改动 | 行数 |
|------|------|:--:|
| DDL | 2 条 CREATE TABLE + 1 条 ALTER | 20 |
| `gateway/winpeek_hub/chat.py` | `send_message` 加 `gid` 参数, 群成员校验, MQTT 广播 topic | 50 |
| `tools/winpeek_tools.py` | 6 个 handler: group_create/list/detail/invite/send/history | 80 |
| `tui_gateway/server.py` | 注册 6 个 `@method` | 60 |
| `apps/desktop/.../mim/index.tsx` | 群名片组件, 群聊天视图, 群信息面板, 新建群弹窗, 马赛克头像 | 200 |
| `gateway/winpeek_hub/mqtt_adapter.py` | `_on_message` 处理 `comms/group/` topic | 10 |

**总工作量：约 420 行**

### 8.2 实现顺序

```
Step 1: DDL (前置, 1分钟)
  └─ mysql -h 192.168.3.23 -u winpeek -p winpeek-db2 < group_ddl.sql

Step 2: chat.py 改造 (后端核心, 单文件, 独立)
  └─ send_message 加 gid 参数 + 成员校验 + MQTT 广播
  └─ get_history 加 gid 参数
  └─ enqueue/poll 支持 gid 维度

Step 3: winpeek_tools.py 6 个 handler (RPC层, 独立)
  └─ _handle_mim_group_create / list / detail / invite / send / history
  └─ 每个带 _mim_center_call 转发头

Step 4: server.py 注册 (薄封装, 5分钟)
  └─ 6 个 @method 照模板注册

Step 5: 前端 UI (最费时, 但可以并行)
  └─ 群名片组件 (复用联系人卡片, 头像改马赛克)
  └─ 群聊天视图 (复用 chat 视图, 加发送者名)
  └─ 群信息面板 (右侧 panel)
  └─ 新建群弹窗 (Modal)

Step 6: 测试 → 修问题 → 验收
```

### 8.3 关键实现细节

**A. `send_message` 加 gid 参数**（向后兼容）：

```python
def send_message(from_uid: int, from_name: str, to_uid: int = 0, body: str = "", gid: int = 0) -> dict:
    if gid:
        # 群聊路径
        # 校验 sender 是群成员
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM m_group_members WHERE gid=%s AND uid=%s", (gid, from_uid))
            if not cur.fetchone():
                return {"ok": False, "error": "not a member"}
        # 写入 DB
        INSERT INTO chat (mid, cid, gid, from_uid, content, ...)
        # MQTT 广播
        mqtt_send(f"comms/group/{gid}", body, from_name)
        # 本地投递
        enqueue({"gid": gid, "from_uid": from_uid, "from_name": from_name, "content": body, ...})
    else:
        # 现有单聊路径（不改）
        ...
```

**B. 前端马赛克头像**：

```
┌─┐ ┌─┐
│Y│ │H│   4个成员的首字母 → 2×2 网格
└─┘ └─┘   背景色: bg-amber-500/20 (区分于单聊蓝色)
┌─┐ ┌─┐   少于4人 → 空位灰色占位
│B│ │ │
└─┘ └─┘
```

**C. 群聊 vs 单聊的消息气泡**：

唯一的区别是群聊消息多一行发送者名：

```
   ┌──────────────────────────┐
   │ yudahai                  │ ← 仅群聊显示
   │ 大家好，数据库方案确定了  │
   │                     10:30│
   └──────────────────────────┘
```

---

## 九、风险与降级

| 风险 | 概率 | 影响 | 降级方案 |
|------|:--:|------|------|
| MySQL 建表超时 | 低 | DDL 卡住 → 全部阻塞 | 提前在后端跑 `SHOW COLUMNS` 幂等检查 |
| MQTT 广播延迟 | 中 | 群消息不同步 | 本地 `enqueue` 兜底（同机成员通过 poll 收到） |
| 前端群聊组件改动大 | 中 | 工期延期 | 先做群名片+群聊天视图（最小可用），群信息面板/新建群弹窗可放到 V1.5 后半段 |
| 单聊发消息函数改出回归 | 低 | 单聊消息中断 | `gid=0` 时走原路径不改，加单测 |

---

## 十、参考

| 来源 | 内容 |
|------|------|
| 旧版 `winpeek-prod/server/chat/db.js` | 群聊 DDL (groups/group_members/chat.gid) |
| 旧版 `winpeek-prod/server/chat/ws-chat.js` | fanout 广播逻辑 |
| 旧版 `winpeek-prod/docs/topics/group-chat-collaboration.md` | 群聊协作架构 |
| 旧版 `winpeek-prod/docs/specs/group-features-audit.md` | 群功能审计 |
| `feature-inventory.md` §四 | 功能决策（哪些做/哪些V2） |
| `feature-inventory.md` §三 | 单聊基础（群聊复用对象） |
| `mim-centralized-architecture.md` §5.2 | daemon 升级（群聊与 daemon 无关） |

---

**下一步**：架构师审核 → 开发按 §八 实现顺序 → 测试按 §六 跑用例 → 产品按 §七 验收。
