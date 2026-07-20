---
title: "WinPeek 组织注册与技术参考手册"
description: "组织模型、注册流程、设备管理、权限审批 — 完整技术文档"
date: 2026-07-20
status: draft
type: reference
---

# WinPeek 组织注册与技术参考手册

> 版本: v1.0 · 日期: 2026-07-20
> 对应代码: `gateway/winpeek_hub/organization.py`

---

## 一、数据模型

### 1.1 实体关系图

```
squad (组织)
├── id, name, description, meta
├── owner_person_id → persons.id  (组织创建者)
│
├── persons (真人, 1:N)
│   ├── id, name, email, phone, notes
│   ├── squad_id → squads.id
│   ├── approval_status: pending | approved | rejected
│   ├── approved_by → users.uid
│   │
│   ├── winpeek_accounts (1:N)
│   │   ├── person_id → persons.id
│   │   └── uid → users.uid  (一个真人可有多个 WinPeek 账号)
│   │
│   └── machines (1:N, 个人设备)
│       ├── id, hostname, device_type: pc|laptop|phone|container|vm
│       ├── person_id → persons.id
│       ├── squad_id  → squads.id  (也可直接归属组织)
│       ├── winpeek_uid → users.uid  (主账号)
│       ├── approval_status: pending | approved | rejected
│       ├── os_name, os_version, cpu_model, cpu_cores, ram_gb
│       ├── gpu_models (JSON), disks_json (JSON)
│       ├── ip_address, mac_address
│       │
│       ├── ai_agents (1:N)
│       │   ├── name, agent_type, uid, role
│       │   ├── person_id, squad_id, machine_id
│       │   └── status: active | inactive | error
│       │
│       └── winpeek_software (1:N)
│           ├── name, slug, version, category
│           ├── exe_path, launch_args, icon_path
│           └── machine_id → machines.id
│
└── machines (1:N, 组织级设备, 无 person 关联)
```

### 1.2 表清单

| 表名 | 说明 | 核心字段 |
|------|------|---------|
| `squads` | 组织/团队 | name(UNIQUE), description, meta, owner_person_id |
| `persons` | 真人用户 | name, squad_id, email, phone, approval_status |
| `machines` | 设备(PC/手机/容器等) | hostname(UNIQUE), device_type, person_id, squad_id, winpeek_uid, approval_status |
| `winpeek_accounts` | person↔uid 多对多 | person_id, uid(UNIQUE), is_main |
| `ai_agents` | AI Agent 注册 | name, agent_type, uid, machine_id, squad_id, status |
| `winpeek_software` | 已安装软件清单 | slug(UNIQUE), name, category, machine_id |
| `winpeek_software_account` | 软件登录账号 | software_id, uid, wxid, auth_type, auth_value |

### 1.3 状态枚举

| 实体 | 字段 | 可选值 |
|------|------|--------|
| persons | approval_status | `pending` / `approved` / `rejected` |
| machines | approval_status | `pending` / `approved` / `rejected` |
| machines | device_type | `pc` / `laptop` / `phone` / `tablet` / `container` / `vm` / `server` |
| ai_agents | status | `active` / `inactive` / `error` / `offline` |

### 1.4 权限模型

| 操作 | 谁能做 |
|------|--------|
| 创建组织 (squad) | 任何人 — 创建者自动成为 owner + admin |
| 批准成员注册 | squad owner / admin |
| 批准设备注册 | squad owner / admin, 或设备所属 person |
| 查看组织树 | squad 成员 |
| 修改组织信息 | squad owner / admin |
| 邀请成员 | squad owner / admin — 被邀请者直接进入 |
| 转让组织 | 仅 owner, 新 owner 必须是 squad 成员 |

---

## 二、注册流程

### 2.1 流程总览

```
新用户登录
  │
  ├─ WinPeek 自动: 注册 machine (hostname + device_type=pc)
  │
  ├─ 用户操作: 选择 "创建组织" 或 "加入已有组织"
  │
  ├─ 创建组织:
  │   1. 填写 squad name + description
  │   2. 自动: 注册 person (name=当前用户昵称, squad_id, approval=auto-approved)
  │   3. 自动: 关联 winpeek_account (person_id, uid)
  │   4. 自动: 关联 machine.person_id + machine.squad_id
  │   5. 自动: 设置 machine.approval_status = approved
  │
  ├─ 加入已有组织:
  │   1. 选择目标 squad
  │   2. 自动: 注册 person (approval_status = pending)
  │   3. 自动: 关联 machine.squad_id
  │   4. 自动: 设置 machine.approval_status = pending
  │   5. 管理员审批 → approved
  │
  └─ 设备扫描:
       winpeek_scan_register → 硬件入库 + 软件扫描
```

### 2.2 创建组织（Squad）

**调用接口**: `winpeek_squad_upsert`

```json
// 请求
{
  "name": "WinPeek开发团队",
  "description": "负责 WinPeek 全栈开发的团队"
}

// 响应
{ "ok": true, "id": 1 }
```

**后端自动操作**:
1. `INSERT INTO squads (name, description)`
2. 创建 person: `INSERT INTO persons (name, squad_id, approval_status='approved')`
3. 写入 `winpeek_accounts` 关联 uid
4. 更新 `machines SET squad_id=X, person_id=Y, approval_status='approved'`

### 2.3 注册真人（Person）

**调用接口**: `winpeek_person_upsert`

```json
// 请求
{
  "name": "于大海",
  "squad_id": 1,
  "email": "yudahai@example.com",
  "phone": "13800000000"
}

// 响应  
{ "ok": true, "id": 2 }
```

**注意**: 如果 person 已存在（同 name+squad_id），执行 UPDATE 而非 INSERT。

### 2.4 设备注册与审批

**阶段1 — 自动发现**

登录时 `_handle_mim_login` 自动调用:
```python
upsert_machine(hostname, device_type="pc", winpeek_uid=uid)
```
此时 `approval_status` 默认为 `pending`, `squad_id` 为 NULL。

**阶段2 — 加入组织**

用户选择组织后调用 `winpeek_join_squad`:
```json
// 请求
{ "squad_id": 1 }

// 后端操作
// 1. 验证 machine 存在且 winpeek_uid 匹配
// 2. UPDATE machines SET squad_id=1
// 3. 自动创建 person (如不存在)
// 4. INSERT winpeek_account (person_id, uid)
// 5. 设置 machine.approval_status = 'pending'
```

**阶段3 — 管理员审批**

调用 `winpeek_machine_approve`:
```json
// 请求
{ "machine_id": 3, "action": "approved" }

// 后端操作  
// 1. 验证 requester 是目标 squad 的 owner/admin
// 2. UPDATE machines SET approval_status='approved', approved_by=<uid>, approved_at=NOW()
// 3. 同时审批对应的 person (如果也是 pending)
```

### 2.5 完整注册流程（一键）

**调用接口**: `winpeek_scan_register`

```json
// 请求 — 全自动
{
  "squad_name": "我的团队",     // 可选, 创建新 squad
  "squad_id": 0,              // 可选, 加入已有 squad
}

// 响应 — 包含全部结果
{
  "ok": true,
  "squad":   { "id": 1, "name": "我的团队" },
  "person":  { "id": 2, "name": "于大海" },
  "machine": { "id": 3, "hostname": "yu2", "device_type": "pc" },
  "hardware": {
    "cpu": { "cores": 16 },
    "memory": { "total_gb": 32 },
    "disks": [{"drive": "C:", "total_gb": 512}],
    "os": {"system": "Windows", "release": "11"}
  },
  "software": {
    "scanned": 148,
    "synced": 146
  }
}
```

---

## 三、接口清单

### 3.1 Squad 接口

| RPC | 方法 | 权限 |
|-----|------|------|
| `winpeek_squad_list` | 列出所有 squad | 任何人 |
| `winpeek_squad_upsert` | 创建/更新 squad (name 唯一键) | 任何人(创建) / owner(更新) |
| `winpeek_org_status` | 查询当前用户归属状态 | 登录用户 |

### 3.2 Person 接口

| RPC | 方法 | 权限 |
|-----|------|------|
| `winpeek_person_list` | 列出人员 (可按 squad_id 过滤) | squad 成员 |
| `winpeek_person_upsert` | 创建/更新人员 | 同 squad 成员 |
| `winpeek_person_approve` | 审批人员注册 | squad owner/admin |

### 3.3 Machine 接口

| RPC | 方法 | 权限 |
|-----|------|------|
| `winpeek_machine_list` | 列出设备 (可按 person_id/squad_id 过滤) | squad 成员 |
| `winpeek_machine_detail` | 设备详情 + 软件清单 | machine owner 或同 squad |
| `winpeek_machine_approve` | 审批设备注册 | squad owner/admin |
| `winpeek_scan_register` | 一键扫描注册 | 登录用户 |
| `winpeek_join_squad` | 加入组织 | 登录用户 |

### 3.4 Agent 接口

| RPC | 方法 | 权限 |
|-----|------|------|
| `winpeek_agent_list` | 列出 AI Agent (按 squad/machine 过滤) | squad 成员 |
| `winpeek_agent_upsert` | 注册/更新 Agent | 目标 squad 成员 |

### 3.5 组织树接口

| RPC | 方法 | 说明 |
|-----|------|------|
| `winpeek_org_tree` | 完整组织树 | squads → persons → machines → software 一览 |

---

## 四、数据库 DDL 参考

```sql
-- squads: 组织表
CREATE TABLE squads (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(128) NOT NULL UNIQUE,
  description TEXT,
  owner_person_id INT COMMENT '创建者 persons.id',
  meta        TEXT COMMENT 'JSON 扩展',
  created_at  DATETIME DEFAULT NOW(),
  updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW()
);

-- persons: 真人表
CREATE TABLE persons (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(128) NOT NULL,
  squad_id        INT,
  email           VARCHAR(128),
  phone           VARCHAR(32),
  notes           TEXT,
  approval_status VARCHAR(16) DEFAULT 'pending',
  approved_by     INT COMMENT '审批者 users.uid',
  approved_at     DATETIME,
  meta            TEXT,
  created_at      DATETIME DEFAULT NOW(),
  updated_at      DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (squad_id) REFERENCES squads(id) ON DELETE SET NULL
);

-- machines: 设备表
CREATE TABLE machines (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  hostname        VARCHAR(128) NOT NULL UNIQUE,
  device_type     VARCHAR(32) DEFAULT 'pc',
  person_id       INT,
  squad_id        INT,
  winpeek_uid     INT COMMENT '主账号 users.uid',
  os_name         VARCHAR(64),
  os_version      VARCHAR(64),
  cpu_model       VARCHAR(256),
  cpu_cores       INT,
  ram_gb          DECIMAL(6,1),
  gpu_models      TEXT COMMENT 'JSON array',
  disks_json      TEXT,
  ip_address      VARCHAR(64),
  mac_address     VARCHAR(64),
  approval_status VARCHAR(16) DEFAULT 'pending',
  approved_by     INT,
  approved_at     DATETIME,
  last_seen       DATETIME,
  meta            TEXT,
  created_at      DATETIME DEFAULT NOW(),
  updated_at      DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
);

-- winpeek_accounts: 真人 ↔ WinPeek 账号
CREATE TABLE winpeek_accounts (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  person_id INT NOT NULL,
  uid       INT NOT NULL,
  is_main   TINYINT DEFAULT 0,
  created_at DATETIME DEFAULT NOW(),
  UNIQUE KEY (person_id, uid),
  FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
);

-- ai_agents: AI Agent 注册
CREATE TABLE ai_agents (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(128) NOT NULL,
  agent_type  VARCHAR(64),
  uid         INT,
  person_id   INT,
  squad_id    INT,
  machine_id  INT,
  role        VARCHAR(64),
  status      VARCHAR(32) DEFAULT 'active',
  config_json TEXT,
  created_at  DATETIME DEFAULT NOW(),
  updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE SET NULL
);
```

---

## 五、后端代码结构

```
gateway/winpeek_hub/
├── organization.py    ← 组织 CRUD (squad/person/machine/agent)
│   ├── ensure_tables()        建表 DDL
│   ├── _get_user_squad_ids()  用户 squad 查询 (权限校验)
│   ├── _can_access_squad()    权限开关
│   ├── list_squads / upsert_squad
│   ├── list_persons / upsert_person
│   ├── list_machines / upsert_machine / get_machine_detail
│   ├── link_account / list_accounts_for_person
│   ├── list_agents / upsert_agent
│   ├── get_org_status / join_squad
│   ├── scan_and_register_machine()  一键全扫
│   └── get_org_tree()           完整组织树
│
├── scanner.py           ← 系统扫描 (软件+硬件)
│   ├── get_hardware_info()    CPU/RAM/GPU/disk
│   ├── scan_software()        注册表扫描 → 入库
│   └── SOFTWARE_CATEGORIES    12 类分类规则
│
└── software.py          ← 软件管理
    ├── list_softwares / upsert_software
    ├── list_accounts / upsert_account
    ├── set_active_account()   切换激活账号
    └── delete_account()

tools/winpeek_tools.py   ← RPC 注册层 (33 个 handler)
tui_gateway/server.py    ← HTTP 方法注册层
```

---

## 六、安全模型

| 层级 | 机制 |
|------|------|
| 身份 | 所有 handler 使用 `active_uid()`，不接受客户端传 uid |
| Squad 范围 | `_can_access_squad(uid, squad_id)` — 查询 machines.winpeek_uid 或 winpeek_accounts |
| Machine 范围 | `get_machine_detail` 校验 requester 是否为 owner 或同 squad |
| Person 范围 | `upsert_person` 更新前校验 requester 属于同一 squad |
| Agent 范围 | `list_agents` 按 squad 过滤；`upsert_agent` 校验 squad 归属 |
| 审批 | `approve_*` 操作校验 requester 为目标 squad 的 owner/admin |

---

## 七、常见问题

**Q: 一个人有多台电脑怎么处理？**
A: 每台电脑对应一条 `machines` 记录，`winpeek_uid` 相同，`hostname` 不同。

**Q: 手机怎么注册？**
A: `device_type='phone'`，`os_name='Android'/'iOS'`。手机端可通过 API 直接调用 `upsert_machine`，不需要运行扫描器。

**Q: 组织管理员怎么审批新设备？**
A: 调用 `winpeek_machine_approve {machine_id, action:'approved'}`。后端校验 requester 为该 machine 所属 squad 的 owner/admin。

**Q: 一个人可以属于多个组织吗？**
A: 当前是 1:1 (`persons.squad_id`)。多组织支持通过 `winpeek_accounts` 表扩展（一个 uid 可关联多个 person，每个 person 在不同 squad）。

---

## 八、后续迭代

| 优先级 | 功能 |
|:--:|------|
| P0 | 审批流前端 — 管理员面板显示 pending 设备和人员 |
| P0 | 设备离线检测 — 根据 `machines.last_seen` 自动标记 |
| P1 | 组织转让 — owner 转让给 squad 成员 |
| P1 | 多组织支持 — person 可加入多个 squad |
| P1 | 手机注册 — Android/iOS client `upsert_machine` 调用 |
| P2 | 软件启动器 — 从 `winpeek_software` 直接启动应用 |
| P2 | 跨机任务分发 — 根据 squad tree 路由任务 |
