---
sidebar_position: 6
title: "WeChat RPA 代码架构地图"
description: "winpeek_rpa 插件 25 个代码文件的职责划分、调用关系、数据流"
---

> 📍 [返回文档索引](README) | 最后更新：2026-07-18

---

## 目录结构

```
plugins/winpeek_rpa/
├── __init__.py
├── mcp_server.py                    ← MCP 服务端（对外暴露工具）
├── shared/                          ← 共享基础设施
│   ├── __init__.py
│   ├── rpa_tools.py                 ← RPA 通用工具（解析、等待、截图）
│   ├── bg_input.py                  ← 后台输入（绕过前台焦点限制）
│   ├── config.py                    ← 全局配置
│   ├── position_memory.py           ← 坐标记忆（窗口缩放自适应）
│   └── software_scanner.py          ← 软件资产扫描
├── platforms/
│   ├── __init__.py
│   ├── wechat/                      ← ★ 微信平台（11 模块）
│   │   ├── __init__.py
│   │   ├── uia.py                   ← UIA 底层操作（COM 直连控件）
│   │   ├── api.py                   ← 三层架构（Eyes/Hands/Engine）
│   │   ├── db.py                    ← 数据存储（SQLite/MySQL 双后端）
│   │   ├── contacts.py              ← 联系人管理
│   │   ├── profile.py               ← 画像构建（8维 + 13树）
│   │   ├── analyze.py               ← AI 分析引擎
│   │   ├── collect.py               ← 数据采集编排
│   │   ├── collect_contacts.py      ← 联系人采集
│   │   ├── msg_collect.py           ← 消息采集
│   │   ├── msg_traverse.py          ← 消息遍历
│   │   └── find.py                  ← 搜索 + 发送消息
│   └── douyin/                      ← 抖音（规划中）
├── skills/
│   ├── __init__.py
│   ├── wechat/                      ← WeChat 技能
│   └── douyin/                      ← 抖音技能
└── plugin.yaml                      ← 插件清单
```

## 模块职责

### 核心层：UIA 操作 (`uia.py`, 854行)

```
基于 Windows UIA COM (uiautomation) 直达微信 Qt 控件。
零坐标依赖，通过 AutomationId 定位，窗口缩放/移动不失效。

关键能力：
├── 侦察模式：dump 控件树
├── 搜索联系人：--find "名字"
├── 发送消息：--send "内容"
├── 点击导航：--click-nav "通讯录"
├── 读取消息：--read 10
└── 获取当前联系人：--contact
```

### 三层架构 (`api.py`, 734行)

```
🧠 LLM 层 ── 决策（调度、分析、生成行动）
    │
    ▼
👁️ Eyes 层 ── 感知（WeChatEyes：读会话列表、读消息内容）
    │
    ▼
🤖 Hands 层 ── 执行（WeChatHands：发送、点击、搜索、滚动）
    │
    ▼
💾 Engine 层 ── 编排（WeChatEngine：采集、群发、同步）
```

### 数据层 (`db.py`, 751行)

```
SQLite（默认）/ MySQL（DB_BACKEND=mysql 切换）

核心表：
├── wechat_friend     ← 好友信息（1962行定义，含12个扩展字段）
├── wechat_chat       ← 聊天记录（2262行定义）
├── wechat_friend_relation   ← 13树关系分类
├── wechat_friend_event      ← 关键事件时间线
├── wechat_friend_finance    ← 经济往来
├── friend_sales_log         ← 拜访记录
├── friend_score_log         ← 评分日志
├── friend_opportunity       ← 商机
├── actionable_insight       ← 可执行洞察
├── action_template          ← 行动模板
├── automation_rule          ← 自动化规则
├── message_template         ← 消息模板
└── sys_enum_definition      ← 枚举定义
```

## 调用关系

```
mcp_server.py ──暴露工具──▶ Hermes Agent
    │
    ├──▶ wechat/contacts.py ──▶ db.py
    ├──▶ wechat/collect.py  ──▶ uia.py ──▶ api.py
    │                              │
    │                              └──▶ shared/position_memory.py
    ├──▶ wechat/profile.py  ──▶ analyze.py ──▶ db.py
    ├──▶ wechat/find.py     ──▶ api.py (Hands)
    └──▶ wechat/collect_contacts.py ──▶ uia.py ──▶ db.py
```

## 与 MIM 的关系

```
WeChat RPA                            MIM
─────────                             ───
采集微信消息                          消息通过 say 命令发给 Hermes Agent
  ↓                                    ↓
存入 wechat_chat 表                   Hermes 收到 → MIM 聊天窗口
  ↓                                    ↓
画像分析 → actionable_insight         用户可在 MIM 中查看/回复
```

WeChat RPA 是"采集端"，MIM 是"通讯端"。两者通过 `say` 命令桥接。
