---
title: "MIM 聊天界面终极规格"
description: "一次分析+一次实现 — 决定对齐 Hermes 哪些功能、不做哪些、消息气泡/输入框精确规格"
sidebar_position: 8
type: product
role: ["developer"]
module: mim
status: approved
last_updated: "2026-07-19"
---

# MIM 聊天界面终极规格

> **目标**：一次分析，一次实现。不再反复。

---

## 0. 根因复盘：为什么前 4 次都没对齐

| 次数 | 做了什么 | 为什么不对 |
|:--:|------|------|
| 1 | 加 Streamdown/CopyButton/滚动 | 只改了渲染，没碰输入框 |
| 2 | 改输入框为 glass panel | 样式对了但结构不对——没有对齐 grid 布局 |
| 3 | 改为 grid 布局 + PRIMARY_ICON_BTN | 用户要的 voice/mic/model/+ 一个没上 |

**核心错误**：每次只修一个点，没有把 Hermes 原生 ChatBar 和 MIM 的需求差异**先说明白**。

---

## 1. MIM vs Hermes 原生：哪些该对齐，哪些不适用

### 1.1 Composer（输入框区域）

Hermes 原生 Composer 的按钮排：

```
[+] [Mic图标] [喇叭图标] [模型标签] [发送按钮]
```

| 功能 | Hermes 原生用途 | MIM 需要吗 | 决策 |
|------|----------------|:--:|------|
| **发送按钮** | 发消息 | ✅ 任何聊天都要 | V1 对齐 — 黑色圆形 + arrow-up |
| **喇叭 (AutoSpeak)** | TTS 朗读 AI 回复 | ❌ MIM 是文字聊天，不涉及 TTS | V1 **不做** |
| **Mic (Dictation)** | 语音输入转文字 | ❌ MIM 是 Agent 间文字通讯 | V1 **不做** |
| **模型标签 (ModelPill)** | 选择 LLM 模型 | ❌ MIM 不调 LLM | V1 **不做** |
| **+ (ContextMenu)** | 上传文件/文件夹/图片 | ⚠️ 未来可能需要，但现在单聊消息够用 | V1 **不做**，V1.5 考虑 |
| **Ctrl+Enter / steering wheel** | 导向模式 | ❌ MIM 无 LLM 上下文 | V1 **不做** |

**结论**：MIM Composer 比 Hermes 简单——它只需要一个 textarea + 一个发送按钮。Hermes 的 5 个控制按钮在 MIM 里只有 1 个适用。

### 1.2 消息气泡

| 功能 | Hermes 原生 | MIM 当前 | 差距 |
|------|-----------|---------|------|
| **自己发的消息** | `bg-(--dt-user-bubble)` + border + rounded-xl | `bg-(--ui-accent) text-(--ui-accent-foreground) rounded-br-md` | 🔴 颜色太鲜艳 |
| **对方发的消息** | `bg-(--dt-assistant-bubble)` 或 `bg-muted` | `bg-(--ui-bg-quaternary) text-foreground rounded-bl-md` | 🟡 可接受 |
| **Markdown** | Streamdown（同一个组件） | ✅ 已对齐 | ✅ |
| **时间戳** | formatMessageTimestamp | ✅ 已对齐 | ✅ |
| **复制** | CopyButton (appearance="tool-row") | CopyButton (appearance="icon") | ✅ 已对齐 |
| **编辑重发** | "Restore to message" — 把旧消息内容回填到 composer | ❌ 无 | 🟡 V1 做简化版 |
| **引用回复** | Thread reply — 引用条 + 蓝色左边框 | ❌ 无 | V2 |

**结论**：自己发的消息气泡用 `bg-(--dt-user-bubble)` 取代 `bg-(--ui-accent)`，是唯一的颜色修复。

### 1.3 决定——MIM Composer 最终形态

```
┌─────────────────────────────────────────────────────┐
│  [消息历史区域]                                       │
│                                                     │
│  ┌───────────────────── Composer ──────────────────┐│
│  │ ┌─────────────────────────────┐ ┌────────────┐ ││
│  │ │ 输入消息...                  │ │     ↑      │ ││
│  │ └─────────────────────────────┘ └────────────┘ ││
│  └───────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘

一条输入框 + 一个发送按钮。无 voice/mic/model/+。
```

---

## 2. 改动清单（7 项，全在一个文件）

| # | 改什么 | 当前位置 | 改成 | 理由 |
|---|--------|---------|------|------|
| 1 | 己方消息气泡颜色 | `bg-(--ui-accent)` | `bg-(--dt-user-bubble)` | 对齐 Hermes 用户消息 token |
| 2 | 己方消息文字颜色 | `text-(--ui-accent-foreground)` | `text-foreground` | 随背景 token 变 |
| 3 | 己方消息圆角 | `rounded-br-md` | `rounded-2xl` | 对齐 Hermes USER_BUBBLE rounded-xl |
| 4 | 己方消息加 border | 无 | `border border-border/50` | 对齐 Hermes standalone-glass border |
| 5 | 对方消息圆角 | `rounded-bl-md` | `rounded-2xl` | 与己方一致 |
| 6 | 编辑重发 | 无 | 点击自己消息 → 复制内容到 composer → 覆盖式重发（不是追加新消息） | 对标 Hermes Restore |
| 7 | Composer 面板 | 当前 glass dock | 保持不变（第 5 次改动后的版本已对齐） | 无需再改 |

### 2.1 编辑重发逻辑

```tsx
// 点击自己的消息 → 复制到输入框 → 再次发送时覆盖原消息
const [editingMsgId, setEditingMsgId] = useState<string | null>(null)

function handleEditResend(msg: ChatMessage) {
  setInputText(msg.content)
  setEditingMsgId(msg.id)
  textareaRef.current?.focus()
}

// handleSend 中：
if (editingMsgId) {
  // 覆盖消息内容（乐观更新）
  setMessages(prev => prev.map(m => m.id === editingMsgId ? { ...m, content: text } : m))
  setEditingMsgId(null)
  // 发新消息到后端（后端不区分编辑/新发——都是 INSERT chat 新行）
}
```

编辑后发的是新消息（后端 INSERT 新行），但前端乐观更新把旧消息气泡的内容替换掉，视觉上像编辑。

---

## 3. 不做清单（明确边界）

| 功能 | 为什么不 |
|------|---------|
| voice/喇叭 | MIM 无 TTS |
| mic/语音输入 | MIM 是文字聊天 |
| model 标签 | MIM 不调 LLM |
| + 文件选择 | V1.5 |
| Thread Reply 引用条 | V2 — 需要改 DB 加 reply_to 列 |
| 图片/表情 | V2 |
| Shiki 代码高亮 | V1.5 — Streamdown 默认代码块够用 |

---

## 4. 验收标准

| # | 操作 | 预期 |
|---|------|------|
| 1 | 看一眼自己发的消息 | 气泡是 Hermes 同款 `bg-(--dt-user-bubble)` 半透明卡片，不是亮蓝色 |
| 2 | 看一眼对方发的消息 | 气泡是 `bg-(--ui-bg-quaternary)`，圆角 rounded-2xl |
| 3 | 点击自己发的消息 | 内容回填到输入框 |
| 4 | 编辑后点发送 | 旧气泡内容更新，但后端 INSERT 新行 |
| 5 | 对方消息不可编辑 | 点击无反应 |
| 6 | 输入框 | glass dock + 黑色圆发送按钮 + 自动增高 |

---

## 5. 工时

**30 分钟，约 30 行改动。7 项全在一个文件 `mim/index.tsx`。**
