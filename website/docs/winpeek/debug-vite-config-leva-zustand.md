---
sidebar_position: 91
title: "复盘：vite.config.ts 调试记录 (2026-07-18)"
description: "leva / zustand 兼容问题 → 4 次提交失败 → 最终回退到干净状态的全过程与经验教训"
---

# 复盘：vite.config.ts 调试记录

> **日期**: 2026-07-18 · **分支**: `DEV`

## 时间线

| # | Commit | 做了什么 | 结果 |
|---|--------|----------|------|
| 1 | `c2a0bf1` | 加 `dedupe: ['zustand']` + transform 插件 + `optimizeDeps.exclude` | ❌ Vite dev `MISSING_EXPORT: zustand/shallow` |
| 2 | `b0bb38a` | 修 transform 正则 `(.js$)` → `(.js)(\?|$)` | ❌ 仍然报错（问题不在正则） |
| 3 | `0ed449e` | `optimizeDeps.exclude` 从 5 个包扩到 6 个 | ❌ `attr-accept` default export 错误 |
| 4 | `17acba1` | **全部回退**，回到只有端口修改的干净状态 | ✅ Vite 正常启动 |

## 根因分析

### 问题来源

`leva@0.10.1` 使用两种旧式 CJS 默认导入：

```js
import create from 'zustand'           // CJS default export
import shallow from 'zustand/shallow'   // CJS default export
```

但在 `npm install` 的正确行为下，leva 用的是**自己嵌套安装的** `node_modules/leva/node_modules/zustand@3.7.2`，
而其他包（`@assistant-ui`、`@react-three/fiber`）用的是根部的 `zustand@5.0.14`。
**两者互不干扰** — 这是 npm 的标准嵌套机制。

### 破坏点

我加了 `resolve.dedupe: ['zustand']`，强制 leva 也去用根部的 zustand@5。
v5 移除了 default export，leva 的 `import create from 'zustand'` 就找不到目标了。

### 为什么会越修越坏

加了 dedupe 之后，我试图用三种手段修它，每种都产生新问题：

**手段 A — transform 插件**
```ts
// 把 leva 源码里的 import default 改成 named import
import create from 'zustand'  →  import { create } from 'zustand'
```
失败原因：Vite dev server 传给 `transform()` 的 `id` 带 `?v=xxxxx` 查询参数，
正则 `/\.js$/` 要求以 `.js` 结尾，匹配不到。修改正则为 `(\.js)(\?|$)` 后仍然不生效，
因为 **optimizer 阶段在 transform 之前就跑完了**，插件压根没运行到。

**手段 B — optimizeDeps.exclude: ['leva']**
阻止 esbuild 预打包 leva，强行让 transform 插件介入。
失败原因：leva 被排除后裸加载，其子依赖 `react-dropzone → attr-accept` 也跟着裸加载。
`attr-accept` 的 ESM 文件只是 `exports.default = ...`（CommonJS 转译产物），
浏览器原生 ESM 不认 `exports.default`（需要 esbuild 的 synthetic default wrapper），
导致 `attr-accept does not provide an export named 'default'`。

**手段 C — 把 leva 所有子依赖也加入 exclude**
```ts
exclude: ['leva', 'react-dropzone', 'attr-accept', 'zustand', 'zustand/shallow']
```
失败原因：排除越多，裸加载的包越多，CJS-in-ESM 不兼容的问题扩散到更多模块。

### 为什么最终回退是正解

npm 自己就能处理这种情况：

```
node_modules/
├── zustand@5.0.14          ← @assistant-ui 等用它
├── leva/
│   └── node_modules/
│       └── zustand@3.7.2   ← leva 自己用它
```

根本不需要 dedupe。leva 用 v3（有 default export），其他包用 v5（命名 export），各用各的，互不干扰。

## 经验教训

1. **先跑起来，再修 bug。** 不要提前防御性地加代码。
   Vite 配置文件每加一行，都要确认它能跑。我一次加了 3 种机制（dedupe + plugin + exclude），
   出错后无法判断到底是哪个引起的。

2. **出问题时，先回退，再诊断。** 加了 dedupe 之后出现 MISSING_EXPORT，
   应该立刻意识到 dedupe 是根因并回退它，而不是继续加更多层去"修补"它。

3. **了解 npm 的嵌套机制。** npm 天然支持同一包的多版本共存。
   dedupe 破坏了这种隔离，然后我花了 3 个 commit 去修一个根本不存在的问题。

4. **正则要带测试。** 写 `transform` 插件时，如果先用几个真实 `id` 字符串测试正则会怎样匹配，
   立刻就能发现 `?v=xxxx` 的问题，甚至发现 transform 根本跑不到这一步。

5. **Windows 和 Bash 的差异。** `${VAR:-default}` 在 Bash 里是默认值语法，
   在 Windows cmd.exe 里是字面量。npm scripts 在工作区使用 cmd.exe 执行，
   所以这个语法会导致 Vite 把字符串 `"${HERMES_DESKTOP_DEV_PORT:-5175}"` 当端口号。

---

*本文记录一次典型的"自造 bug → 修 bug → 引更多 bug → 回退"的调试过程。*
*改写 vite config 时优先考虑：是不是 npm 本身就已经解决了？*
