---
sidebar_position: 3
title: "UI 交互规格"
description: "MIM 前端 UI 详细规格 — 登录页、联系人列表、聊天视图、多身份切换、两步新建智能体"
---


> 版本: v1.0 · 日期: 2026-07-18
> 对应: `docs/plan/mim-v1-expert-team-implementation.md` 任务包 D

## 1. 登录页

### 1.1 布局

```
┌────────────────────────────┐
│          💬                │
│     WinPeek MIM            │
│   登录或注册以使用消息功能    │
│                            │
│  ┌─ 已有用户 ────────────┐ │
│  │  Y  yuyangmin   PM   │ │  ← 点击=一键登录
│  │  H  Hermes       Dev │ │
│  │  Q  Qoder        QA  │ │
│  └──────────────────────┘ │
│  ┌──────────────────────┐ │
│  │ 用户名               │ │  ← input, 自动聚焦
│  └──────────────────────┘ │
│  ┌──────────────────────┐ │
│  │ 密码                 │ │  ← type=password
│  └──────────────────────┘ │
│  ┌──────────────────────┐ │
│  │       登录            │ │  ← button, Enter 提交
│  └──────────────────────┘ │
│  没有账号？立即注册         │  ← 切换注册表单
└────────────────────────────┘
```

### 1.2 本机运行时区块（登录页下方）

```
┌─ 本机运行时 ─────────────────┐
│  ✅ Claude Code    已注册    │  ← 已发现+已注册 → 绿色，点击一键进入
│  ✅ Hermes Agent   已注册    │
│  ⬜ Codex          未安装    │  ← 未安装 → 灰色，点击进入两步新建
│  ⬜ Cursor         未安装    │
│  ⬜ Qoder          已发现    │  ← 已发现未注册 → 黄色，点击进入两步新建
└─────────────────────────────┘
```

**交互规则**：
- 已注册的 agent 显示 `registered ∧ uid>0` → 一键以该身份登录（不弹创建流程）
- 已发现未注册 → 点击进入两步新建第 2 步（类型已选定，直接起名）
- 未安装 → 点击进入两步新建第 1 步（类型已选定，但提示未安装）
- 数据来源：`winpeek_mim_local_agents`（不转发，本地 RPC）

### 1.3 两步新建智能体

**第 1 步 — 选类型**：
```
┌─ 选择 Agent 类型 ───────────┐
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │
│  │CC│ │CB│ │CX│ │CP│ │OC│ │  每格 = 图标 + 类型名
│  └──┘ └──┘ └──┘ └──┘ └──┘ │  本机已发现 → 绿色边框
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │  未发现 → 灰色边框
│  │DV│ │OW│ │HM│ │PI│ │CS│ │
│  └──┘ └──┘ └──┘ └──┘ └──┘ │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │
│  │KM│ │KR│ │AG│ │QD│ │TC│ │
│  └──┘ └──┘ └──┘ └──┘ └──┘ │
│                            │
│         [← 返回]            │
└────────────────────────────┘
```

**第 2 步 — 起名**：
```
┌─ 创建智能体 ────────────────┐
│  类型: Claude Code          │  ← 不可改
│  名称: ┌──────────────────┐ │
│        │ yu2-claude-1     │ │  ← 预填 {machine}-{type}-{n}
│        └──────────────────┘ │     n = 同机同类型已注册数+1
│                            │
│     [← 返回]    [创建]      │
└────────────────────────────┘
```
点击"创建"→ 调 `winpeek_mim_login({nickname, agent_type, machine, password})` → 成功后写入 `mim-identities` 并激活。

---

## 2. 联系人列表

### 2.1 排序规则

```typescript
const sortedContacts = [...contacts].sort((a, b) => {
  // 第一优先级：在线状态
  if (a.online !== b.online) return a.online ? -1 : 1
  // 第二优先级：未读消息
  if (a.unread !== b.unread) return (b.unread || 0) - (a.unread || 0)
  // 第三优先级：名字字母序
  return a.name.localeCompare(b.name)
})
```

### 2.2 视觉表现

| 状态 | 圆点颜色 | 头像 | 名字 |
|------|:--:|------|------|
| online | 🟢 `bg-emerald-500` | 正常彩色 | 正常字体 |
| offline | ⚪ `bg-gray-400` | 半透明 `opacity-60` | 灰色 `text-(--ui-text-quaternary)` |

### 2.3 群聊联系人

- 群聊 `uid = 0` → 黄色头像 `bg-amber-500/20`，显示"群"字
- 群名 = `title`
- 最后消息预览 = `lastMessage`
- 排序：群聊按最近活动时间排在所有在线联系人之后、离线联系人之前

### 2.4 数据来源

```typescript
// 加载联系人后，合并在线状态
const contactsWithOnline = contacts.map(c => ({
  ...c,
  online: onlineNodes.has(c.uid),  // ← 从 winpeek_mim_online 拿真实状态
}))
```

---

## 3. 聊天视图

### 3.1 消息气泡

```
┌─────────────────────────────── 对话界面 ───────────────────────────────┐
│  [头像] 于大海                   在线 · Architect · #2032               │
│ ────────────────────────────────────────────────────────────────────── │
│                                                                        │
│    ┌──────────────────────────┐                                        │
│    │ 你好杨敏，我是大海！       │  ← 对方消息（左对齐，灰色背景）          │
│    │ 收到你的消息了！           │     bg-(--ui-bg-quaternary)            │
│    └──────────────────────────┘                                        │
│                                              10:25                     │
│                                                     ┌───────────────┐  │
│                                                     │ 你好大海！    │  │
│                                             10:26 → │ 我是杨敏      │  │
│                                                     └───────────────┘  │
│                                                                        │
│  ⬇ (新消息自动滚底)                                                   │
│ ────────────────────────────────────────────────────────────────────── │
│  ┌──────────────────────────────────────────────────────┐ [发送]      │
│  │ 输入消息...                                          │             │
│  └──────────────────────────────────────────────────────┘             │
│  Enter 发送 · Shift+Enter 换行                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 消息渲染

| 消息类型 | 渲染方式 |
|---------|---------|
| 纯文本 | `whitespace-pre-wrap break-words` |
| Markdown | 复用 `components/chat/compact-markdown.tsx` |
| 代码块 | 复用 `components/chat/code-card.tsx`（Shiki 高亮） |
| 时间戳 | 复用 `assistant-ui/thread/timestamp.ts` (`formatMessageTimestamp`) |

### 3.3 消息操作

| 操作 | 触发 | 行为 |
|------|------|------|
| 复制 | 右键 or 长按消息气泡 | 复制消息文本，短暂 toast "已复制" |
| 滚动到底 | 用户上滚后出现 ↓ 按钮 | 复用 `app/chat/scroll-to-bottom-button.tsx` |

### 3.4 输入框

```
规则:
- Enter → 发送（无 IME 组合态时）
- Shift+Enter → 换行
- IME 组合态中 (isComposing=true) → Enter 不上发
- 空消息 → 发送按钮 disabled
- 发送中 → 按钮显示 spinner
```

---

## 4. Profile 面板（个人资料）

### 4.1 内容

```
┌─ 我的资料 ─────────────────┐
│      [头像 首字母]          │
│      yuyangmin             │
│      PM · #1               │
│                            │
│  ┌──────────────────────┐  │
│  │ 角色    PM           │  │
│  │ 职位    产品经理      │  │
│  │ 简介    ...          │  │
│  │ 技能    Product, ... │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │ 模式    客户端        │  │  ← 替换旧版硬编码 MQTT/WinPeek Hub
│  │ 中心    192.168.3.44 │  │     (从 winpeek_mim_local_agents 取)
│  │ 机器    yu2          │  │
│  └──────────────────────┘  │
│                            │
│  ┌─ 我的身份 ──────────┐   │
│  │  ✅ yuyangmin #1    │   │  ← 切换按钮，当前身份高亮
│  │     yu2-claude-1    │   │
│  │     yu2-qoder-1     │   │
│  │  [+ 新建智能体]     │   │
│  └────────────────────┘   │
│                            │
│       [退出登录]            │
└────────────────────────────┘
```

### 4.2 身份切换

```typescript
function switchIdentity(uid: number) {
  // 1. 更新 localStorage mim-active-uid
  // 2. 重新设置 active session
  // 3. 刷新联系人列表
  // 4. 清空消息列表
  // 5. 轮询/Poll 切换为目标 uid
}
```

---

## 5. 数据存储

### 5.1 localStorage 结构

```typescript
// 旧版（兼容迁移）
mim-identity: { uid, name, role, host } | null  // 单个 → 读取到自动迁移

// 新版
mim-identities: WinPeekIdentity[]  // 本机所有注册过的身份
mim-active-uid: number             // 当前激活的身份 uid

// 迁移逻辑（首次加载时）
if (localStorage.getItem('mim-identity') && !localStorage.getItem('mim-identities')) {
  const old = JSON.parse(localStorage.getItem('mim-identity'))
  localStorage.setItem('mim-identities', JSON.stringify([old]))
  localStorage.setItem('mim-active-uid', String(old.uid))
  localStorage.removeItem('mim-identity')
}
```

### 5.2 CSS 规则

- 全部颜色用 `var(--ui-*)` token
- 禁止硬编码色值（`#fff`、`rgb(...)` 等）
- 间距用 Tailwind token（`p-3`、`gap-2` 等）
- 字体用 `text-foreground` / `text-(--ui-text-*)` token链
