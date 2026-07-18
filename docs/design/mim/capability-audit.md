# MIM 能力审计：当前实现 vs 应有功能

> 日期: 2026-07-18 · 审计人: CC
> 对照基准: Hermes 原生聊天组件 (`apps/desktop/src/components/assistant-ui/thread/`)

---

## 1. 群聊 — NONE, 完全未实现

### 现状

**全仓搜索 `group`/`群聊`/`群组` 结果为零。** 唯一的线索：前端 `index.tsx` 里有 `contact.uid === 0 ? '群' : ...` 和 `bg-amber-500/20` 黄色样式（L475、L533），但这些代码永远不会触发——后端从来没返回过 `uid=0` 的群聊联系人。

### 缺失

| 层级 | 缺什么 |
|------|--------|
| **DB** | 无 `groups` / `group_members` 表 |
| **后端 API** | 无 `create_group` / `group_send` / `list_groups` handler |
| **前端** | 无新建群按钮、无群成员列表、无群聊界面 |
| **MQTT** | 无广播 topic (`comms/group/{gid}`) |

### 老版本参考

> 用户说"老版本是有的"——可能在更早的 commit 或分支里。需要回去翻 git history 找。

### 修复方案

群聊 = 1 张 `group_members` 表 + 1 个 `list_groups` RPC + MQTT 广播 topic。消息存储复用 `chat` 表（加 `gid` 列）。

**工作量估计**: 后端 ~60 行 / 前端 ~150 行 / DDL 1条

---

## 2. 在线状态 — BACKEND EXISTS, FRONTEND BROKEN

### 现状

| 层 | 实现情况 |
|----|---------|
| `hub.py` heartbeat | ✅ 30s 心跳，120s 自动 offline |
| `hub.py register_node` | ✅ 注册时写 `status: "online"` |
| `hub.py sweep_dead_nodes` | ✅ 超时无心跳 → `status: "offline"` |
| `hub.py list_nodes` | ✅ 返回全量节点（含 `status` 字段） |
| `tools/winpeek_tools.py` `_handle_mim_online` | ✅ 注册 handler |
| `tui_gateway/server.py` `winpeek_mim_online` | ✅ @method 注册 |

**后端 100% 就绪。问题是前端完全没用。**

### 断点位置

**断点 1** — 联系人列表加载（`index.tsx` L351）：
```tsx
// 当前代码：全部写死为 online
setContacts(data.contacts.map((c: any) => ({
  ...
  online: true,  // ← 不管后端返回什么，永远 true
})))

// 应该：调 winpeek_mim_online 拿节点状态再合并
```

**断点 2** — 排序规则（`index.tsx` L459）：
```tsx
// 当前代码：按未读数排序
const sortedContacts = [...contacts].sort(
  (a, b) => (b.unread || 0) - (a.unread || 0)
)

// 应该：online 在前，offline 在后，同类内按 name 排
const sortedContacts = [...contacts].sort((a, b) => {
  if (a.online !== b.online) return a.online ? -1 : 1
  return a.name.localeCompare(b.name)
})
```

### 视觉表现

当前虽有绿点 CSS（`bg-emerald-500`，L496），但因为所有联系人 `online: true`，所以所有人都是绿的。

### 修复方案

1. `_handle_mim_contacts` 返回每条记录时，调 `hub.is_online(uid)` 填充 `online` 字段
2. 前端排序规则改为 online 优先
3. offline 的联系人显示灰色圆点 + 置灰头像

**工作量**: 后端 3 行 / 前端 10 行，总修复 <15 行

---

## 3. 聊天消息渲染 — TEXT ONLY, NO MARKDOWN

### 对比

| 功能 | Hermes 原生 | MIM 当前 | 差距 |
|------|:--:|:--:|------|
| Markdown | ✅ Shiki 高亮 | ❌ `whitespace-pre-wrap` 纯文本 | 🔴 |
| 代码块 | ✅ `code-card.tsx` + 语法着色 | ❌ 无 | 🔴 |
| Diff 渲染 | ✅ `diff-lines.tsx` | ❌ 无 |
| 图片 | ✅ `zoomable-image.tsx` | ❌ 无 |
| 终端输出 | ✅ `terminal-output.tsx` | ❌ 无 |
| 时间戳 | ✅ `formatMessageTimestamp()` 相对时间 | ❌ 纯文本 `msg.time` | 🟡 |
| 复制按钮 | ✅ `copy-button.tsx` | ❌ 无 | 🟡 |
| 消息气泡 | ✅ `assistant-ui/react` MessagePrimitive | ⚠️ 手写 div | 🟡 |

### 修复方案

Hermes 已有的组件可以直接复用：
- `components/chat/compact-markdown.tsx` → 替代 MIM 的 `whitespace-pre-wrap`
- `components/ui/copy-button.tsx` → 消息长按/右键复制
- `assistant-ui/thread/timestamp.ts` → 相对时间格式

**工作量**: 前端 ~40 行，无后端改动

---

## 4. 输入框 — BARE TEXTAREA, NO ENHANCEMENTS

### 对比

| 功能 | Hermes 原生 Composer | MIM 当前 |
|------|:--:|------|
| 附件拖放 | ✅ | ❌ |
| @提及 | ✅ | ❌ |
| 队列面板 | ✅ | ❌ |
| 语音输入 | ✅ | ❌ |
| Enter 发送 / Shift+Enter 换行 | ✅ (另加 IME 组合态保护) | ⚠️ 当前有但粗糙 |
| 按钮样式 | ✅ IconButton 体系 | ❌ 只有文字 "发送" |

**进入 V1 的最小增量**：IME 组合态保护 + Enter/Shift+Enter 语义对齐 Hermes 原生。

**工作量**: 前端 ~30 行

---

## 5. 滚动行为 — NONE

| 功能 | Hermes 原生 | MIM |
|------|:--:|:--:|
| 新消息自动滚底 | ✅ | ❌ 无 |
| 用户上滚后暂停 | ✅ sticky | ❌ 无 |
| scroll-to-bottom 按钮 | ✅ 49行组件 | ❌ 无 |

**修复**: 复用 `app/chat/scroll-to-bottom-button.tsx`

**工作量**: 前端 ~15 行

---

## 6. 错误处理 — SILENT CATCH, NO UI

```tsx
// 当前代码
} catch { /* swallowed */ }
} catch (e) { /* swallowed */ }
```

Hermes 原生有 `ErrorPrimitive` + 可关闭错误卡片 + 重试。MIM 需要最低限度的错误 toast。

**工作量**: 前端 ~20 行

---

## V1 功能汇总（按优先级）

### 🔴 P0 — 现在就是坏的，必须修

| # | 功能 | 文件 | 工作量 |
|---|------|------|:--:|
| P0-1 | 在线状态前端对接 | `index.tsx` + `chat.py` | 15 行 |
| P0-2 | 联系人按 online 排序 | `index.tsx` | 5 行 |
| P0-3 | offline 视觉（灰色） | `index.tsx` | 10 行 |

### 🟡 P1 — UI 太简陋，体验要过关

| # | 功能 | 复用组件 | 工作量 |
|---|------|---------|:--:|
| P1-1 | Markdown 消息渲染 | `compact-markdown.tsx` | 30 行 |
| P1-2 | 消息复制按钮 | `copy-button.tsx` | 15 行 |
| P1-3 | 时间戳相对格式 | `timestamp.ts` | 5 行 |
| P1-4 | 滚动到底部 | `scroll-to-bottom-button.tsx` | 15 行 |
| P1-5 | 输入框 IME 保护 | 参考 Hermes Composer | 20 行 |
| P1-6 | 错误提示 | toast 组件 | 20 行 |

### ⚪ P2 — 群聊

| # | 功能 | 工作量 |
|---|------|:--:|
| P2-1 | 群聊后端 (DDL + handler + MQTT) | 60 行 |
| P2-2 | 群聊前端 (新建群 + 群对话) | 150 行 |

---

## 结论

**MIM 后端功能已经就绪**（login/send/poll/contacts/history/online 全部有），但**前端断掉了**——在线状态写死 true、排序不按 online、消息纯文本无 Markdown、无限时、无错误处理。

**P0（15 行）是断腿的 bug，必须修。P1（105 行）让 MIM 聊天体验对齐 Hermes 原生。P2（210 行）群聊留到 V1.5。**
