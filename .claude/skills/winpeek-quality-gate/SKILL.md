---
name: winpeek-quality-gate
description: WinPeek 质量门禁 — 提交前检查、文档更新、CI 堵门。适用于 CC-yu2 / Hermes-htubs24 / Qoder-yu2 全部 Agent。每次写代码前自动加载。
---

# WinPeek 质量门禁 — 三 Agent 统一操作指南

**每次 commit 之前，必须跑：**

```bash
python scripts/winpeek-quality-check.py
```

输出 `PASS` → 可以提交。输出 `FAIL (N violations)` → 修复后再提交。

---

## 一、各 Agent 使用方式

### CC-yu2 (Claude Code, yu2 机器)

**自动生效** — Claude Code 启动时自动加载 AGENTS.md + CLAUDE.md。你不需要手动配置。

**主动调用**：说"质量检查"或"跑检查"，我会自动执行 `python scripts/winpeek-quality-check.py`。

**提交前**：
```bash
# 1. 跑检查
python scripts/winpeek-quality-check.py

# 2. 检查文档是否要更新
git diff DEV...HEAD --stat
# → 对照 .claude/skills/update-docs/references/CODE-TO-DOCS-MAPPING.yaml

# 3. 提交
git add ... && git commit -m "feat(tools): xxx" && git push
```

### Hermes-htubs24 (Hermes Agent, htubs24 机器)

**Ubuntu 环境** — Node.js 不在 PATH，跳过 TypeScript 检查。只跑 Python + 文档检查。

```bash
# 安装依赖（一次性）
pip install ruff

# 跑检查（跳过 TypeScript）
python scripts/winpeek-quality-check.py --check ruff
python scripts/winpeek-quality-check.py --check frontmatter
python scripts/winpeek-quality-check.py --check links
python scripts/winpeek-quality-check.py --check filename
python scripts/winpeek-quality-check.py --check css
```

**或者**：直接用 `--json` 输出，只用 Python 相关的三项：
```bash
python scripts/winpeek-quality-check.py --check ruff --json
python scripts/winpeek-quality-check.py --check frontmatter --json
python scripts/winpeek-quality-check.py --check links --json
```

### Qoder-yu2 (Qoder IDE, yu2 机器)

**IDE 环境** — Node.js + TypeScript + Python 全可用。跑全量检查。

```bash
# 全量（作为 MR 门禁）
python scripts/winpeek-quality-check.py

# 或者增量（只看某人 MR 的变更）
python scripts/winpeek-quality-check.py --diff DEV
```

**CI 流水线** — 自动运行，不需要手动跑。Qoder 只需：
1. 确认 `.gitlab-ci.yml` 已在 DEV 分支
2. 确认 GitLab Runner 已配置
3. 确认 DEV 分支保护 "Pipelines must succeed" 已开启

---

## 二、6 项检查速查

| # | 检查 | 谁需要跑 | 失败怎么改 |
|---|------|---------|-----------|
| 1 | TypeScript | CC-yu2, Qoder-yu2 | 看 error 消息修正类型 |
| 2 | CSS token | CC-yu2, Qoder-yu2 | `color: #333` → `var(--ui-text-secondary)` |
| 3 | Python ruff | 全部 | `open(f)` → `open(f, encoding="utf-8")` |
| 4 | frontmatter | 全部 | 加 `---\nsidebar_position: N\ntitle: "xxx"\n---` |
| 5 | 文件名 | 全部 | `QUICKSTART.md` → `git mv ... quickstart.md` |
| 6 | 死链 | 全部 | 修正或删除不存在的链接 |

---

## 三、改了代码 → 文档怎么跟

```
1. git diff DEV...HEAD --stat          → 看改了什么文件
2. 查这份映射表（谁改了代码谁就更新对应的文档）:
   .claude/skills/update-docs/references/CODE-TO-DOCS-MAPPING.yaml
3. 读当前文档 → 更新内容 → 跑检查 → 同一次 commit
```

**新建文档用模板**：
```
.claude/skills/update-docs/references/templates/
├── user-guide.md        → website/docs/winpeek/user-guide/
├── developer-guide.md   → website/docs/winpeek/developer-guide/
├── api-reference.md     → website/docs/winpeek/reference/
└── tutorial.md          → website/docs/winpeek/
```

---

## 四、提交规范

```
分支: feature/what-you-are-doing  (从 DEV 拉)
提交: <type>(<scope>): <description>

scope 用上游 Hermes 的: tools, gateway, skills, agent, docs, cli

示例:
  feat(tools): winpeek_list_contacts 分页/搜索/排序
  fix(gateway): MQTT 重连时消息队列丢失
  docs(winpeek): 微信CRM 用户指南
```

---

## 五、CI 堵门（管理员配一次）

GitLab → DEV 分支 → Settings → Protected Branches → "Pipelines must succeed" ✅

之后所有 MR:
- `winpeek-quality-diff`  → 增量对比，贴评论（不堵门）
- `winpeek-quality-block` → 全量扫描，失败则 Pipeline ❌ → MR 无法合并

---

## 六、MR 被堵了怎么办

```
1. 看 Pipeline 日志 → 找到违反项
2. 本地跑 python scripts/winpeek-quality-check.py
3. 修复 → git add + git commit --amend → git push --force
4. Pipeline 自动重新跑 → PASS ✅
```
