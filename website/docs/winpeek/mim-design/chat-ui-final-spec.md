---
title: "MIM 聊天界面布局规范（微信风格）"
description: "完全左对齐体系 — 页面分层、组件标准、视觉权重、对齐规范、数据接口映射"
sidebar_position: 8
date: 2026-07-20
status: done
type: spec
---

# MIM 聊天界面布局规范

> 版本: v2.0 · 日期: 2026-07-20 · 状态: ✅ 已实现
> 前端文件: `apps/desktop/src/app/winpeek/mim/index.tsx`

---

## 一、页面整体分层（4 大区块）

```
┌─────────────────────────────────────────┐
│  区块1: 顶部导航栏（固定头部）           │
│  👥 群名(人数)  ·  ·  · 在线/离线 ⋯   │
├─────────────────────────────────────────┤
│  区块2: 消息卡片流（核心内容区）         │
│  头像 + 名称 + 气泡 + 时间戳            │
│  完全左对齐体系                         │
├─────────────────────────────────────────┤
│  区块3: Composer 输入区（底部固定）      │
│  [+] [🎤] [📢]  textarea  [↑]          │
└─────────────────────────────────────────┘
```

---

## 二、头部导航栏

```
左侧: 头像 + 群名(人数)  —  单聊显示在线/离线+角色
右侧: ⋯ 三点菜单按钮 (群聊时出现，点击进群资料面板)

群名格式: WinPeek工作群33(14)
  → title + 浅灰小字(成员数)
单聊格式: yuyangmin
  第二行浅灰: 在线 · PM · #2022
```

**实现要点：**
- `TextForeground` 主标题，`TextTertiary` 辅助信息
- 群名右边紧跟 `(member_count)` 浅灰色
- 三点按钮 `⋯` Unicode，hover 浅色背景

---

## 三、消息卡片流（核心）

### 3.1 统一模板

每条消息 = **头像 + 发送者信息栏 + 消息主体**

所有消息**完全左对齐**，包括自己的消息，无右对齐气泡。

```
┌─────────────────────────────────────────┐
│           7月20日 15:30                 │  ← 居中时间戳分割线
│                                         │
│ 🟡 头像  yuyangmin                      │  ← 头像(36px圆角) + 昵称
│    ┌─────────────────────────┐         │
│    │ 大家下午好啊             │         │  ← 浅灰圆角气泡
│    └─────────────────────────┘         │
│    📋 15:30                            │  ← 复制+时间
│                                         │
│  ↑ 与上条间距 12px                     │
│                                         │
│ 🟡 头像  yudahai                        │
│    ┌─────────────────────────┐         │
│    │ 下午好，今天进度如何？    │         │
│    └─────────────────────────┘         │
│    📋 15:30                            │
└─────────────────────────────────────────┘
```

### 3.2 时间戳分割

- **居中显示**，不依附任何消息框
- **出现条件**：两条消息间隔 > 5 分钟，或每天第一条消息
- 样式：`bg-(--ui-bg-tertiary) rounded-full px-3` 浅灰圆角标签
- 文字 `text-[0.6rem] text-(--ui-text-quaternary)`

### 3.3 气泡样式

| 属性 | 值 |
|------|-----|
| 背景 | `bg-(--ui-bg-tertiary)` 浅灰色 |
| 圆角 | `rounded-lg` 小半径 |
| 内边距 | `px-2.5 py-1.5` |
| 最大宽度 | `max-w-[75%]` |
| 文字 | `text-foreground text-sm` |

### 3.4 群聊发送者名

- 群聊模式：每条消息气泡上方显示发送者昵称
- 颜色：`text-(--ui-accent)` 蓝色
- 单聊模式：对方消息可省昵称或浅灰色

### 3.5 未读新消息浮标

- 用户上滚查看历史后，底部出现绿色标签
- `bg-emerald-500 text-white rounded-full`
- 文字 `↓ X条新消息`，点击回到最新消息

---

## 四、视觉层级权重

```
L1 (最重): 群名、绿色未读浮标、气泡正文
    → text-foreground, emerald-500, 标准字重

L2 (中等): 群聊发送者昵称（蓝色）、气泡背景色块
    → text-(--ui-accent), bg-(--ui-bg-tertiary)

L3 (最轻): 居中时间戳、群成员数、复制按钮、在线状态
    → text-(--ui-text-quaternary), text-[0.55rem]
```

---

## 五、对齐与排版规范

| 规则 | 说明 |
|------|------|
| 左对齐体系 | 头像、名称、气泡全部左对齐形成垂直参考线 |
| 水平安全边距 | 页面左右 `px-4`（16px） |
| 垂直间距 | 消息之间 `mb-3`（12px），气泡与发送者名 `mb-0.5`（2px） |
| 头像尺寸 | 36px 圆角方形 `rounded-md h-9 w-9` |
| 文字层次 | 主标题 `text-sm font-medium`，辅信息 `text-[0.6rem] text-tertiary` |
| 容器圆角 | 时间戳 `rounded-full`，气泡 `rounded-lg`，统一视觉语言 |

---

## 六、统一复用组件

1. **消息行组件** — 头像 + 名称 + 气泡 + CopyButton，逐条复用
2. **时间戳分割组件** — 居中圆角标签，`>5min` 间隔自动插入
3. **未读浮标组件** — 绿色悬浮标签，仅上滚时出现
4. **CopyButton** — 复用 `@/components/ui/copy-button`，`appearance="icon"`
5. **Streamdown** — 复用 `streamdown` Markdown 渲染

---

## 七、数据接口映射

| 界面元素 | 数据来源 |
|----------|---------|
| 群名 + 人数 | `winpeek_mim_contacts` → `groups[].title` + `member_count` |
| 群公告 | `winpeek_mim_group_info` → `metadata.announcement` |
| 消息列表 | `winpeek_mim_history` → `messages[] {from_uid, from_name, content, msg_ts}` |
| 在线状态 | `winpeek_mim_contacts` → `contacts[].online` (hub.is_online) |
| 群成员 | `winpeek_mim_group_info` → `members[] {uid, nickname, participant_type}` |
| 未读数 | `winpeek_mim_contacts` → `contacts[].unread_count` |
| 用户资料 | `winpeek_mim_user_info` → `{uid, nickname, role, title, bio, skills}` |
| 群操作 | `winpeek_mim_group_update` / `winpeek_mim_group_transfer` / `winpeek_mim_group_invite` |

---

## 八、群资料面板

右侧详情列显示，通过群聊头部 `⋯` 按钮进入。

```
┌─ 群资料 ──────────────────────┐
│                                │
│  成员网格 (5列头像+昵称)        │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐   │
│  │头│ │头│ │头│ │头│ │ + │    │
│  │名│ │名│ │名│ │名│ │邀请│   │
│  └──┘ └──┘ └──┘ └──┘ └──┘   │
│  查看更多 (14人) ›             │
│  ─────────────────────────    │
│  群聊名称    WinPeek工作群33   │
│  群公告     ›                  │
│    公告正文...                 │
│  ─────────────────────────    │
│  🟡 yuyangmin  PM    群主    │
│  🟡 yudahai   Arch  转让    │
│  ...                          │
│  ─────────────────────────    │
│  清空聊天记录                 ›│
│  退出群聊（红色）             ›│
└────────────────────────────────┘
```

**功能清单：**

| 功能 | 权限 | 数据接口 |
|------|------|---------|
| 查看成员列表 | 群成员 | `winpeek_mim_group_info` |
| 点击成员看资料 | 群成员 | `winpeek_mim_user_info` |
| 改名 | owner/admin | `winpeek_mim_group_update {title}` |
| 编辑公告 | owner/admin | `winpeek_mim_group_update {announcement}` |
| 邀请成员 | owner/admin | `winpeek_mim_group_invite` |
| 转让群主 | owner only | `winpeek_mim_group_transfer` |
| 清空聊天 | 本人 | 仅清空前端 messages 列表 |
| 退出/解散 | 本人 | 待实现 `winpeek_mim_group_leave` |

---

## 九、与原 Hermes 的差异

| 项目 | Hermes 原生 | MIM |
|------|------------|-----|
| 气泡对齐 | 己右蓝，彼左灰 | **全部左对齐**，统一浅灰 |
| 时间戳 | 每条右下角 | **居中**分割线，>5min 出现 |
| 头像 | 圆形 | **圆角方形** (rounded-md) |
| 群聊 | 无 | 群名(人数) + 公告横幅 + 发送者名 |
| 未读提示 | 红点数字 | **绿色浮标** "↓ X条新消息" |
