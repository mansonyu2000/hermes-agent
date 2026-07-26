---
sidebar_position: 10
title: "MIM 消息中心部署与客户端配置"
description: "yuyangmin 团队 8 机 MIM（即时消息）内网部署指南：服务器启动、Desktop 客户端配置、验证步骤"
---

# MIM 消息中心部署与客户端配置

> **适用环境**: 内网 192.168.3.0/24 · **读者**: 团队全员
>
> 本文档说明如何在 8 台内网机器上搭建多中心 MIM 消息网络：2 台消息中心服务器 + 6 台 Desktop 客户端。

---

## 架构总览

```
        htubs24 (192.168.3.23) — Ubuntu Server
        ┌──────────────────────────────┐
        │  MySQL  winpeek-db2  :3306   │  ← 数据层（已就绪）
        │  MQTT Broker         :1883   │  ← 消息总线（已就绪）
        └──────┬───────────┬───────────┘
               │           │
          pymysql       paho-mqtt（客户端连接，无需部署）
               │           │
        ┌──────┴──────┐ ┌──┴──────────┐
        │ yiqingqing  │ │    yu2      │
        │ 192.168.3.10│ │ 192.168.3.44│  ← 只跑 hermes serve
        │ 主消息中心   │ │ 备消息中心   │
        └──────┬──────┘ └──┬──────────┘
               │           │
        ┌──────┴───────────┴──────────┐
        │     6 台 Desktop 客户端      │
        │     npm run dev (Desktop)    │
        │     不跑 hermes serve        │
        └─────────────────────────────┘
```

**核心原则**: htubs24 提供 MySQL + MQTT 服务端；消息中心只跑 Python 桥接；客户端只跑桌面应用。

| 机器 | IP | 角色 | 运行什么 |
|------|----|------|---------|
| htubs24 | 192.168.3.23 | 数据层 | MySQL + MQTT Broker（已就绪） |
| yiqingqing | 192.168.3.10 | 主消息中心 | `hermes serve --host 192.168.3.10 --port 9119` |
| yu2 | 192.168.3.44 | 备消息中心 | `hermes serve --host 192.168.3.44 --port 9119` |
| 其余 6 台 | — | Desktop 客户端 | `npm run dev`，不跑 hermes serve |

---

## 第一部分：服务器部署（yiqingqing / yu2）

### 前提条件

| # | 检查项 | 验证命令 |
|---|--------|---------|
| 1 | Python 3.11–3.13 | `py --version` |
| 2 | 代码最新 | `cd d:\mydata\mycode\github\hermes-agent-qoder && git pull origin DEV` |
| 3 | 依赖已安装 | `py -c "import pymysql; import paho.mqtt.client; print('OK')"` |
| 4 | 9119 端口空闲 | `netstat -ano \| findstr 9119`（应无输出） |
| 5 | 能连通 MySQL | `py -c "import pymysql; c=pymysql.connect(host='192.168.3.23',port=3306,user='winpeek',password='Server33',database='winpeek-db2'); c.close(); print('OK')"` |
| 6 | 能连通 MQTT | 服务器日志中看到 `MIM connected` 即表示通过 |

### 防火墙配置

每台消息中心机器执行一次（PowerShell 管理员）：

```powershell
New-NetFirewallRule -DisplayName "Hermes MIM 9119" `
  -Direction Inbound -Protocol TCP -LocalPort 9119 `
  -RemoteAddress 192.168.3.0/24 -Action Allow
```

### 共享 Token（两台用同一个）

在其中一台上生成：

```powershell
py -c "import secrets; print(secrets.token_urlsafe(32))"
# 示例输出: xjh3BPykwsfiGxm-tGVKYcGh1TWuUVueczUUL-gNYk8
```

### Dashboard 认证（config.yaml）

绑定非 loopback 地址必须配置 basic_auth。在 `~\.hermes\config.yaml` 中：

```yaml
dashboard:
  basic_auth:
    username: admin
    password_hash: "<scrypt hash>"
```

生成密码 hash：

```powershell
py -c "from hermes_cli.dashboard_auth.basic_auth import scrypt_hash; print(scrypt_hash('hermes123'))"
```

当前 shared token: `xjh3BPykwsfiGxm-tGVKYcGh1TWuUVueczUUL-gNYk8`

### 启动命令

```powershell
# yiqingqing（主）:
cd d:\mydata\mycode\github\hermes-agent-qoder
$env:HERMES_DASHBOARD_SESSION_TOKEN="<共享Token>"
py -m hermes_cli.main serve --host 192.168.3.10 --port 9119

# yu2（备）:
cd d:\mydata\mycode\github\hermes-agent-qoder
$env:HERMES_DASHBOARD_SESSION_TOKEN="<共享Token>"
py -m hermes_cli.main serve --host 192.168.3.44 --port 9119
```

> **重要**: 必须用 `py -m hermes_cli.main serve`（不是 `hermes serve`），
> 因为全局 `hermes` 命令指向 CC 仓库。`py -m` 会优先加载当前工作目录代码。

### 启动成功标志

日志中依次看到以下输出即表示就绪：

```
HERMES_BACKEND_READY port=9119
Hermes backend listening on 192.168.3.XX:9119
WinPeek Hub loaded: identity + tenant + routing + archive
MIM identity resolved: uid=X name=XXX
MIM started: uid=X name=XXX broker=192.168.3.23:1883
MIM connected 192.168.3.23:1883, uid=X name=XXX, inbox=all
WinPeek chat engine ready (MySQL)
WinPeek node registered: X (XXX)
```

若出现 `WinPeek Hub load skipped`，说明 `config.yaml` 中 `winpeek.mim.enabled: true` 未设置。

---

## 第二部分：客户端配置（6 台 Desktop 机器）

客户端**不需要跑 `hermes serve`**。只需启动 Desktop 应用并通过 UI 配置远程连接。

### 前提条件

| # | 检查项 | 验证 |
|---|--------|------|
| 1 | Node.js 20+ | `node --version` |
| 2 | npm | `npm --version` |
| 3 | 代码最新 | `git pull origin DEV` |
| 4 | npm 依赖已安装 | `cd apps\desktop && npm install`（仅首次） |
| 5 | 能连通消息中心 | `curl http://192.168.3.10:9119/api/status` 返回 JSON |

### 启动 Desktop（首次）

```powershell
cd d:\mydata\mycode\github\hermes-agent-qoder\apps\desktop
npm run dev
```

Desktop 启动后会看到 Electron 窗口。首次启动时 Desktop 会自启一个本地后端完成加载，
**这步正常**——然后进入配置页面改连远程中心。

### 配置远程连接

1. Desktop 主界面 → **Settings → Gateway**
2. **Mode** 切换到 **Remote**
3. **Remote URL**: `http://192.168.3.10:9119`（主中心）
4. **Session Token**: 粘贴共享 Token
5. 点 **Test remote** 验证连接
6. 点 **Save & reconnect** → Desktop 自动重连到远程中心

配置保存后，以后每次启动 Desktop 都会自动使用远程连接。
如需切换到备中心，同样在此页面修改 URL 为 `http://192.168.3.44:9119`。

### 如果 CC Desktop 已运行（端口冲突）

Qoder 和 CC 的 Desktop 可同时运行，但需要独立用户数据目录：

```powershell
$env:HERMES_DESKTOP_USER_DATA_DIR = "C:\Users\<用户名>\AppData\Roaming\hermes-qoder"
npm run dev
```

### 环境变量方式（可选，跳过 UI 配置）

如果不想每次通过 UI 设置，可直接设环境变量：

```powershell
$env:HERMES_DESKTOP_REMOTE_URL  = "http://192.168.3.10:9119"
$env:HERMES_DESKTOP_REMOTE_TOKEN = "<共享Token>"
npm run dev
```

此时 Desktop 会直接连远程中心，跳过"先自启本地后端再切远程"的流程。

---

## 第三部分：验证清单

### 服务端验证（在 yiqingqing / yu2 上）

```powershell
# 1. API 状态
Invoke-RestMethod http://192.168.3.10:9119/api/status | Select-Object version,auth_required

# 2. MIM 状态
Get-Content $env:USERPROFILE\.hermes\logs\agent.log | Select-String "WinPeek MQTT connected|chat engine ready"
```

### 客户端验证

1. Desktop 窗口正常打开，连接指示器显示绿色
2. 进入 WinPeek/MIM 模块
3. 登录（例如 `yuyangmin` / `123321`）
4. 看到联系人列表（20 个用户来自 MySQL）
5. 发送一条测试消息 → 对方实时收到

### 故障切换验证

1. 主中心 (yiqingqing) 运行中，客户端连接正常
2. 停止主中心 → 客户端连接断开
3. 客户端 Settings → Gateway → URL 改为备中心 `http://192.168.3.44:9119`
4. 点 Save & reconnect → 恢复正常

---

## 参考

| 项目 | 路径 |
|------|------|
| MIM 引擎源码 | `gateway/winpeek_hub/` |
| DB 连接管理 | `gateway/winpeek_hub/db.py` |
| MQTT 适配器 | `gateway/winpeek_hub/mqtt_adapter.py` |
| Hub 集成桥 | `gateway/winpeek_hub/hub_bridge.py` |
| WebSocket 认证 | `hermes_cli/web_server.py` → `_ws_auth_reason()` |
| Desktop 连接配置 | `apps/desktop/src/app/settings/gateway-settings.tsx` |
| 架构决策记录 | `docs/decisions/` |
| 设计文档 | `docs/design/wechat-crm-design.md` |
