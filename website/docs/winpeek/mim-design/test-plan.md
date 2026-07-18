---
sidebar_position: 4
title: "V1 测试计划"
description: "MIM V1 测试金字塔 — 单元测试 5 文件 + E2E 双实例 4 断言 + 手工验收 7 项"
---


> 版本: v1.0 · 日期: 2026-07-18
> 对应: `docs/plan/mim-v1-expert-team-implementation.md` 任务包 A-E

## 测试金字塔

```
         ╱  E2E (双实例)  ╲         1 个脚本, 4 条断言
        ╱   集成 (API+WS)   ╲        5 个场景, 每场景 3-8 用例
       ╱      单元           ╲       5 个文件, 每文件 3-8 用例
```

---

## 1. 单元测试

### 1.1 包 B — hub_bridge 客户端模式

**文件**: `tests/gateway/test_hub_bridge_client_mode.py`

| # | 用例 | Mock 策略 | 断言 |
|---|------|----------|------|
| B-1 | `center_url()` 读 config.yaml 含 `center_url` | mock `load_config` 返回 `{winpeek:{mim:{center_url:"http://192.168.3.44:9119"}}}` | 返回非空字符串 |
| B-2 | `center_url()` config 无 `center_url` | mock 无 mim 键 | 返回 `""` |
| B-3 | `try_load_hub()` 客户端模式不 import pymysql | mock `center_url` 非空, `unittest.mock.patch("pymysql")` | `pymysql.connect` 未被调用 |
| B-4 | `try_load_hub()` 客户端模式不调用 `mqtt_adapter.connect` | mock `center_url` 非空, patch `mqtt_adapter.connect` | `connect` 未被调用 |
| B-5 | `try_load_hub()` 客户端模式仍启动 daemon | mock `center_url` 非空, patch `start_daemon` | `start_daemon` 被调用一次 |
| B-6 | `try_load_hub()` 中心模式行为不变 | mock `center_url` 空 | `mqtt_adapter.connect` 被调用 |

### 1.2 包 A — 后端协议

**文件**: `tests/tools/test_mim_handlers.py`

| # | 用例 | 输入 | 断言 |
|---|------|------|------|
| A-1 | `_handle_mim_online` 传 `uids:[9001,9002]` | `{"uids":[9001,9002]}` | `nodes.json` 出现两条 online，`hub.list_nodes()` 含两个节点 |
| A-2 | `_handle_mim_online` 不传 uids 走老行为 | `{}` | 为中心自身 UID 心跳 |
| A-3 | `_handle_mim_runtime_report` 落盘 | `{"machine":"yu2","daemon_version":"1.0.0","runtimes":[...]}` | `nodes.json` 出现 `machines.yu2` |
| A-4 | `_handle_mim_runtime_report` 重复上报幂等 | 同 machine 两次 | `nodes.json` 只有一条 machine 记录 |
| A-5 | `_handle_mim_local_agents` daemon 未启动 | `{}` | 返回 `{"mode":"...","agents":[]}` 不抛错 |
| A-6 | `_handle_mim_login` 透传 `agent_type`/`machine` | `{"nickname":"test","password":"123321","agent_type":"claude","machine":"yu2"}` | MySQL `users` 行 `agent_type` 列有值 |

### 1.3 包 C — daemon 扫描

**文件**: `tests/apps/test_winpeek_daemon_scan.py`

| # | 用例 | 输入 | 断言 |
|---|------|------|------|
| C-1 | 伪造 `.claude/` 目录 | tmp_path 建 `~/.claude/` | 检测到 `claude`, `detected_via="config_dir"` |
| C-2 | monkeypatch PATH 命令 | `shutil.which` 返回 `/usr/bin/qoder` | 检测到 `qoder`, `detected_via="path_cmd"` |
| C-3 | 双通道命中取首个 | 同时存在目录+命令 | `detected_via` = `config_dir`（优先） |
| C-4 | 无 agent 时返回空列表 | 空 tmp_path + `shutil.which` 全 None | `scan_installed_agents()` 返回 `[]` |
| C-5 | `get_local_state()` 启动前 | daemon 未调用 `start_daemon()` | 返回 `{"agents":[]}` 不抛错 |
| C-6 | 15 种类型全识别 | 每种类型的目录/PATH | 15 种全在结果中 |

### 1.4 包 E — 数据验证

**文件**: `tests/gateway/test_hub_tables.py`

| # | 用例 | 断言 |
|---|------|------|
| E-1 | `users` 表有 `agent_type` 列 | `SHOW COLUMNS` 含 `agent_type` |
| E-2 | `agent_type` 默认 NULL | 存量行 `agent_type IS NULL` |
| E-3 | DDL 幂等 | 重复执行不报错 |

---

## 2. E2E 测试

**文件**: `tests/e2e/test_mim_client_center_e2e.py`（pytest marker: `e2e`，CI 不跑）

**前置**: 临时 `HERMES_HOME`，起两个 `hermes serve` 进程：
- 中心：无 `center_url`
- 客户端：`center_url` 指中心

| # | 断言语义 | 验证方法 |
|---|---------|---------|
| ②-1 | **客户端进程零 3306/1883 出站** | `psutil.Process().net_connections()` 无 MySQL/MQTT 端口 |
| ②-2 | 客户端 login → send → 中心 poll 收到 | websocket-client 调 RPC，双向验证 |
| ②-3 | `runtime_report` 后中心 `nodes.json` 出现 machines 键 | 读文件 json 解析 |
| ②-4 | 杀 daemon → 120s 后 offline / 重启 → online 且无重复 | `hub.is_online(uid)` + `SELECT COUNT(*) FROM users WHERE nickname=...` |

---

## 3. 手工验收（集成后一次性）

| # | 验收项 | 操作 | 通过标准 |
|---|--------|------|---------|
| M-1 | 客户端零直连 | `netstat -ano \| findstr "3306 1883"` | 客户端进程 0 条 |
| M-2 | 本机运行时区块 | 打开 MIM 登录页 | 出现 ≥2 个已发现 agent 类型 |
| M-3 | 两步新建智能体 | 选类型→起名→提交 | 列表中新增，可切换身份进入 |
| M-4 | 双人对话 | yuyangmin → yudahai 发消息 | 双方 poll 收到，history 双向可见 |
| M-5 | 身份隔离 | 身份 A 切到 身份 B | 消息列表不串，各自会话独立 |
| M-6 | 离线检测 | 杀 daemon，等 2 分钟 | 该身份 status=offline，前端灰色 |
| M-7 | 中心模式回归 | 不配 center_url 启动 | 行为与改造前一致 |

---

## 4. 测试环境

| 环境 | 用途 | 启动方式 |
|------|------|---------|
| 本机双实例 | E2E | 临时 HERMES_HOME × 2 + 不同 port |
| 本机单实例 | 手工验收-中心模式 | `hermes serve --port 9120` |
| 本机单实例 | 手工验收-客户端模式 | `HERMES_DESKTOP_REMOTE_URL=http://127.0.0.1:9120 npm run dev` |
| 公司内网 | 8 机真实环境 | 1 台中心 + 7 台客户端 |

## 5. 数据准备

```sql
-- 测试用户（密码 sha256('123321') = a320480f534776bddb5cdd31a9d2c9af4b9a1f8cf9b3e19c3af89f0e3a1b1c2d）
INSERT INTO users (uid, nickname, role, password_hash, is_active) VALUES
  (2031, 'test-mim-1', 'Developer', 'a320480f534776bddb5cdd31a9d2c9af4b9a1f8cf9b3e19c3af89f0e3a1b1c2d', 1),
  (2032, 'test-mim-2', 'Developer', 'a320480f534776bddb5cdd31a9d2c9af4b9a1f8cf9b3e19c3af89f0e3a1b1c2d', 1)
ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash);
```
