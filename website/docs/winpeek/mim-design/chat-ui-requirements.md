---
title: "MIM 聊天界面需求分析"
description: "MIM聊天界面的精确定义：当前状态、目标状态、边界、具体改动清单、验收标准"
sidebar_position: 7
type: product
role: ["architect", "developer", "tester", "product"]
module: mim
status: review
last_updated: "2026-07-19"
---

# MIM 聊天界面需求分析

> **目标**: 把 MIM 聊天界面的需求边界定死，不再来回拉扯。

---

## 1. 当前状态（到底现在是什么样）

### 消息气泡（L544-554）

```tsx
// 当前代码 — 纯文本，无任何组件
<div className="whitespace-pre-wrap break-words">{msg.content}</div>
```

| 能力 | 现在 | 效果 |
|------|:--:|------|
| 文字显示 | ✅ | `whitespace-pre-wrap` 可换行 |
| Markdown | ❌ | `**粗体**` 原样显示字符，不转换 |
| 代码块 | ❌ | ` ```python ` 原样显示 |
| 链接 | ❌ | `http://...` 不可点击 |
| 行内代码 | ❌ | `` `code` `` 无样式 |

### 消息操作

| 能力 | 现在 |
|------|:--:|
| 复制 | ❌ |
| 回复 | ❌ |
| 撤回 | ❌ |

### 时间戳（L551）

```tsx
// 当前代码 — 原始时间切片
{msg.time?.slice(11, 16) || ''}
```

显示格式 `10:25`（硬切割），今天/昨天/日期不分。

### 输入框（L559-566）

```tsx
// 当前代码 — 裸 textarea
<textarea
  onChange={e => setInputText(e.target.value)}
  onKeyDown={handleKeyDown}
  placeholder="输入消息..."
/>
```

| 能力 | 现在 |
|------|:--:|
| Enter 发送 | ✅ `handleKeyDown` |
| Shift+Enter 换行 | ✅ |
| IME 组合态保护 | ❌ 中文输入中按 Enter 会误发 |
| 空消息禁止 | ✅ `disabled={!inputText.trim()}` |
| 附件/文件 | ❌ |

### 滚动（L555）

```tsx
<div ref={messagesEndRef} />
```

只有一个 ref 锚点，`useEffect` 里 `scrollIntoView`。没有用户手动上滚后暂停自动滚底、没有"↓滚到底"按钮。

### 错误处理

```tsx
} catch { /* swallowed */ }
```

三处 try/catch 全部静默吞异常。用户发消息失败无任何提示。

---

## 2. 目标状态（到底要什么样）

### 原则

| 原则 | 内容 |
|------|------|
| **复用优先** | Hermes 已有的组件绝不重写，import 直接用 |
| **不做新功能** | 只补当前缺的，不新加附件/回复/撤回/表情 |
| **改动最小** | 只改 `mim/index.tsx` 一个文件，不碰其他 |

### 2.1 消息气泡 — 对齐 Hermes 聊天

**只改一行**：把 `whitespace-pre-wrap break-words` 替换为 `<Streamdown>` 组件（compact-markdown.tsx 的底层渲染器）。

```tsx
// 改前
<div className="whitespace-pre-wrap break-words">{msg.content}</div>

// 改后
<Streamdown>{msg.content}</Streamdown>
```

`Streamdown` 是 `compact-markdown.tsx` 的依赖（`import { Streamdown } from 'streamdown'`），包已安装，不需要新依赖。

**效果**：`## 标题` → 渲染为 h2、`**粗体**` → 粗体、` ```python ` → 代码块着色、`http://` → 可点击链接。

**不做**：Shiki 代码高亮（`compact-markdown.tsx` 有但不是必须），Streamdown 自带的代码块样式已够用。

### 2.2 时间戳 — 相对格式

```tsx
// 改前
{msg.time?.slice(11, 16) || ''}

// 改后
{formatMessageTimestamp(msg.msg_ts)}
```

从 `@/components/assistant-ui/thread/timestamp` import：

```
今天 → "10:25"
昨天 → "昨天 15:30"
前天～7天前 → "07-15 10:25"
更早 → "2026-07-15"
```

### 2.3 消息复制 — import 现成组件

```tsx
<CopyButton
  appearance="icon"
  text={msg.content}
  className="absolute top-1 right-1 opacity-0 group-hover/cell:opacity-100"
/>
```

包裹消息气泡的 div 加上 `group/cell` 类名，hover 时显示复制图标。

### 2.4 滚动 — import ScrollToBottomButton

```tsx
// 消息列表底部
<ScrollToBottomButton />
```

从 `@/app/chat/scroll-to-bottom-button` import。依赖 `$threadJumpButtonVisible` nanostore——如果不想引入 nanostore 依赖，可以用一个简化版：监听 `messages` 数量，新增消息时自动滚底。

**V1 取简化版**：

```tsx
const [userScrolledUp, setUserScrolledUp] = useState(false)
// onScroll: 如果距离底部 > 50px → userScrolledUp = true
// useEffect after messages change: 如果 !userScrolledUp → scrollToBottom
// userScrolledUp 为 true 时显示"↓"按钮 → 点击滚底 + 重置 userScrolledUp
```

### 2.5 IME 保护

```tsx
const [isComposing, setIsComposing] = useState(false)

<textarea
  onCompositionStart={() => setIsComposing(true)}
  onCompositionEnd={() => setIsComposing(false)}
  onKeyDown={e => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault()
      handleSend()
    }
  }}
/>
```

### 2.6 错误提示

```tsx
// 替换静默 catch
catch {
  notifyError('消息发送失败，请检查网络连接')
}
```

`notifyError` 从 `@/store/notifications` import，Hermes 内置的 toast 系统。

---

## 3. 边界（V1 不做什么）

| 不做 | 原因 |
|------|------|
| Shiki 代码高亮 | Streamdown 默认代码块已够用。V1.5 再加。 |
| 附件/文件发送 | 需要文件服务，V2 |
| 消息回复 (Thread Reply) | 需要改 DB + API，V2 |
| 消息撤回 | 需要改 DB + API，V2 |
| 消息反应 (Emoji) | V2 |
| ScrollToBottomButton 的完整 nanostore 版本 | 引入成本高，简化版够用 |
| `@assistant-ui/react` MessagePrimitive | MIM 的消息模型与 Hermes 的 assistant-ui 不兼容（assistant-ui 用 `MessageRuntime` 状态机） |

---

## 4. 改动清单

| # | 改什么 | 位置 (mim/index.tsx) | 行数 | 依赖 |
|---|--------|---------------------|:--:|------|
| 1 | 消息内容改为 `<Streamdown>` | L550 | 1行 | npm: streamdown (已安装) |
| 2 | 时间戳改为 `formatMessageTimestamp` | L551 | 1行 | `@/components/assistant-ui/thread/timestamp` |
| 3 | 消息气泡加复制按钮 | L546 外层 | ~10行 | `@/components/ui/copy-button` |
| 4 | 滚动到底 + 停止自动滚底 | L544 外层 + L555 替换 | ~25行 | 无外部依赖 |
| 5 | IME 组合态保护 | L560 新增2个 handler | ~8行 | 无 |
| 6 | 错误 toast 替换 catch | L399-401 | ~6行 | `@/store/notifications` |

**总行数：~55 行，全在一个文件 `mim/index.tsx` 内。**

---

## 5. 验收标准

| # | 验收项 | 操作 | 预期结果 |
|---|--------|------|---------|
| 1 | Markdown 渲染 | 发送 `**粗体** 和 \`代码\`` | 渲染为粗体文字和行内代码样式 |
| 2 | 代码块渲染 | 发送 ` ```python\nprint(1)\n``` ` | 显示带背景色的代码块 |
| 3 | 链接可点击 | 发送 `http://192.168.3.23:3000` | 可点击打开链接 |
| 4 | 时间戳 | 看今天的消息 | 显示 `10:25` 而非 `2026-07-19T10:25:00` |
| 5 | 复制 | 鼠标悬停消息气泡右键 → 复制 | clipboard 有消息文本 |
| 6 | 自动滚底 | 新消息到达 | 自动滚动到最新消息 |
| 7 | 停止滚底 | 向上滚动 100px | 不再自动滚，出现"↓"按钮 |
| 8 | 滚底按钮 | 点"↓"按钮 | 滚到底部，按钮消失 |
| 9 | IME 中文不发 | 中文输入法打拼音中按 Enter | 不上发消息 |
| 10 | 空消息不能发 | 输入框为空 | 发送按钮 disabled |
| 11 | 错误提示 | 断网后发消息 | toast 显示"消息发送失败" |

---

## 6. 与其它需求的关系

| 相关需求 | 关系 |
|---------|------|
| F2.2 真实在线状态 | 独立。联系人列表排序/颜色不涉及聊天视图 |
| F2.3/F2.4 排序+视觉 | 同上 |
| F5.5 批量心跳 | 后端改动，与前端无关 |
| 群聊 F4.7 | 群聊前端 UI 复用本需求的 Streamdown + CopyButton + 滚动，合入后群聊直接受益 |
| F9.6 本机运行时 | 登录页的改动，不涉及聊天视图 |

**聊天界面是 MIM 所有功能里最独立的模块——改它不影响任何其它功能。**

---

## 7. 实施

**单人，2h。** 前端开发改一个文件 55 行，验收 11 项。

```
1. 改消息渲染 (1-3) → npm run dev 看效果 → 15min
2. 改滚动 (4) → 验证滚底 + 停止滚底 → 15min
3. 改IME + 错误 (5-6) → 15min
4. 通跑11项验收 → 15min
```

---

**本文是 MIM 聊天界面的唯一需求定义。新增功能先更新本文，再写代码。**
