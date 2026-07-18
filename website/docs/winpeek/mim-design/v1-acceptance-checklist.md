---
sidebar_position: 5
title: "V1 集成验收 Checklist"
description: "MIM V1 完工标准 — 10 大类 45 项检查项，覆盖连接/身份/联系人/消息/在线/安全"
---


> 版本: v1.0 · 日期: 2026-07-18
> 汇总自: 架构方案 §10 + 实施计划书 §3 DoD + 能力审计 P0/P1

---

## 验收标准（一句话）

Desktop 机器上除到 MIM 中心的一条 WebSocket 外，**零 MySQL、零 MQTT 出站连接**；
前端完成登录-聊天-切换身份闭环，无需翻阅代码即可通过肉眼验收。

---

## 1. 连接治理

- [ ] **1.1** 客户端配 `center_url` → 进程 `netstat -ano | findstr "3306 1883"` 中该进程 0 条
- [ ] **1.2** 客户端模式日志含 `"WinPeek MIM client mode → center {url}"`
- [ ] **1.3** 中心模式（不配 `center_url`）行为与改造前完全一致
- [ ] **1.4** 客户端模式仍启动 injector daemon（agent 发现+注册走转发入口）

---

## 2. 身份与登录

- [ ] **2.1** 所有用户用密码 `123321` 可登录（`identity.login(nickname, password)`）
- [ ] **2.2** 旧 localStorage `mim-identity`（单对象）自动迁移为 `mim-identities` 数组 + `mim-active-uid`
- [ ] **2.3** 本机运行时区块显示 daemon 发现的 agent（类型图标 + 注册状态）
- [ ] **2.4** 两步新建智能体：选类型（15 种网格）→ 起名（预填 `{machine}-{type}-{n}`）→ 成功入列
- [ ] **2.5** `winpeek_mim_login` 带 `agent_type`/`machine` 参数后，MySQL `users` 行对应列有值

---

## 3. 联系人

- [ ] **3.1** 联系人列表按 `online 优先 > 未读数 > 名字` 排序
- [ ] **3.2** online 联系人绿点 + 正常头像；offline 灰点 + 半透明头像
- [ ] **3.3** 中心模式下 `get_contacts()` 返回真实 `online` 字段（从 `hub.is_online(uid)` 取）
- [ ] **3.4** 多用户环境下，每个用户看到的联系人在线状态正确

---

## 4. 单聊消息

- [ ] **4.1** yuyangmin 发消息 → yudahai poll 收到（本地 enqueue + 跨机 MQTT 双通道）
- [ ] **4.2** yudahai 回复 → yuyangmin poll 收到
- [ ] **4.3** 消息历史 `get_history(uid, peer_uid)` 双向完整
- [ ] **4.4** 消息气泡渲染正确（自消息右对齐蓝色，他消息左对齐灰色）
- [ ] **4.5** 消息时间戳显示相对时间格式（`formatMessageTimestamp`）
- [ ] **4.6** 消息可复制（右键或长按）
- [ ] **4.7** 新消息自动滚底，用户上滚后出现"↓ 滚到底"按钮

---

## 5. 多身份切换

- [ ] **5.1** Profile 面板列出所有已注册身份，点击切换
- [ ] **5.2** 身份 A → 身份 B 切换后，消息列表互不串（各自查各自的 history）
- [ ] **5.3** poll 轮询跟随当前激活身份 `mim-active-uid`
- [ ] **5.4** send 消息的 `from_uid` 取当前激活身份 uid

---

## 6. 在线状态

- [ ] **6.1** daemon 每 30s 心跳到中心（`_handle_mim_online({uids:[...]})` 批量心跳）
- [ ] **6.2** 杀 daemon → 120s 内对应身份 status → offline
- [ ] **6.3** 重启 daemon → 对应身份 status → online，`users` 表无重复行（幂等）
- [ ] **6.4** 中心 `nodes.json` 死节点自动清理（`sweep_dead_nodes`）

---

## 7. Runtime 上报

- [ ] **7.1** daemon 启动时调用 `winpeek_mim_runtime_report`
- [ ] **7.2** 中心 `nodes.json` 出现 `machines.{hostname}` 键，含 runtime 清单
- [ ] **7.3** 同一机器重复上报不产生重复记录（覆盖式更新）
- [ ] **7.4** `winpeek_mim_local_agents` 在 daemon 未启动时返回 `{"agents":[]}` 不抛错

---

## 8. 前端模式显示

- [ ] **8.1** ProfilePanel **删除**硬编码 `MQTT Broker 192.168.3.23:1883` 和 `WinPeek Hub 127.0.0.1:9200`
- [ ] **8.2** 替换为：`客户端模式 → {center_url}` 或 `中心模式（本机 hub）`
- [ ] **8.3** 模式信息从 `winpeek_mim_local_agents` 响应的 `mode`/`center_url` 字段取

---

## 9. 输入框

- [ ] **9.1** Enter 发送消息（非 IME 组合态）
- [ ] **9.2** Shift+Enter 换行
- [ ] **9.3** IME 组合态中（`isComposing=true`）Enter 不上发
- [ ] **9.4** 空消息禁止发送（按钮 disabled）

---

## 10. 安全

- [ ] **10.1** `_handle_mim_send` 的 `uid` 不从客户端参数取（修复 IDOR）
- [ ] **10.2** `_handle_mim_poll` 的 `uid` 不从客户端参数取
- [ ] **10.3** `_handle_mim_history` 的 `uid` 不从客户端参数取
- [ ] **10.4** `_mim_center_call` 的 token 走 HTTP Header（不走 URL 查询参数）

---

## 11. 回归

- [ ] **11.1** 中心模式（不配 `center_url`）启动：`npm run dev` 无报错
- [ ] **11.2** Vite dev server 无 `MISSING_EXPORT` 错误（zustand/leva/attr-accept）
- [ ] **11.3** 前端 TypeScript `npx tsc --noEmit` 通过
- [ ] **11.4** 所有 CSS 使用 `var(--ui-*)` token，无硬编码色值
- [ ] **11.5** 现有 winpeek 相关 pytest 不新增红色

---

## 12. 不做（明确排除）

- ❌ 任务调遣/派发/并发限制（V2）
- ❌ 自定义 runtime profile / custom_env / args（V2）
- ❌ poll 批量聚合 `uids`（V1.5）
- ❌ 主备中心自动 failover（V1.5）
- ❌ `hermes_cli/winpeek_mqtt.py` say 通道改造（V2）
- ❌ 12 种新 agent 类型的 MCP 注入（V1 只保留原 3 种）
- ❌ 转发层性能优化（连接复用/推送化）
