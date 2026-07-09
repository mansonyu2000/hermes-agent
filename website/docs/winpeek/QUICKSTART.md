---
sidebar_position: 4
title: "Quickstart"
description: "5分钟跑起 WinPeek 微信自动化"
---

# WinPeek Quickstart

WinPeek 是 Hermes Agent 的 Windows 桌面自动化扩展，目前聚焦微信生态。本文帮你 5 分钟跑通第一个自动化任务。

## 前提

- Windows 机器（微信已登录）
- 本机（Hermes Server）能访问该 Windows 机器的 `9527` 端口
- Hermes 已配置 `feat/winpeek` 分支

## 第一步：确认环境

在 Hermes 对话中输入：

```
检查 yu2 的微信状态
```

Agent 会自动调用 `mcp_winpeek_app_list` 确认微信进程 `Weixin.exe` 在运行。如果未运行，启动：

```
启动 yu2 的微信
```

## 第二步：发送一条消息

```
给张三发一条"你好，测试消息"
```

Agent 会执行 `winpeek_wechat_send` 工具，通过 UIA 直连微信：

```
1. search_and_open("张三")  — 搜索联系人
2. send_message("你好，测试消息")  — 发送消息
```

## 第三步：查看发送结果

```
张三回复了吗？
```

Agent 自动采集与张三的聊天记录，检查最新消息。

## 常用命令

| 命令 | 说明 |
|------|------|
| `给 X 发消息` | 微信发消息 |
| `采集 X 的聊天记录` | 翻页采集聊天历史 |
| `采集通讯录` | 全量采集好友列表 |
| `列出已学习的模板` | 查看 MCP 模板库 |
| `say 2022 消息` | 通过 MQTT 给其他 Agent 发消息 |
| `检查微信状态` | 确认 Weixin.exe 进程 |

## 架构一览

```
Hermes Agent ←→ WinPeek RPA Plugin ←→ WeChat UIA (毫秒级)
                                     ←→ MCP Template (秒级, 降级)
               ←→ WinPeek Hub ←→ 其他 Agent (MQTT)
```

## 下一步

- 了解完整功能：[WinPeek 产品全景](./features/OVERVIEW.md)
- 架构详解：[WinPeek Architecture](./ARCHITECTURE.md)
- 完整需求定义：[docs/requirements/wechat-prd.md](../../../docs/requirements/wechat-prd.md)

---

参见完整设计：[docs/design/wechat-automation-menu-and-action-loop.md](../../../docs/design/wechat-automation-menu-and-action-loop.md)
