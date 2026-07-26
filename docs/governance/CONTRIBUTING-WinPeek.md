# CONTRIBUTING — WinPeek 子项目

> Hermes Agent CC | 最后更新: 2026-07-26

## 分支策略

- **`DEV`** — 开发主干，所有 WinPeek 功能在此分支开发
- **`feat/*`** / **`fix/*`** — 功能/修复分支，合并到 DEV
- **`main`** — 上游追踪（不直接提交）

## Commit 格式

```
<type>(<scope>): <简描>

evidence: <brainstorm|debug|none>
tdd: <test文件|pending>
verified: <验证方法>
```

| Type | 证据 |
|------|------|
| `feat:` | `brainstorm:` + `tdd:` + `verified:` |
| `fix:` | `debug:` + `tdd:` + `verified:` |
| `chore/docs/refactor:` | `evidence: none` |

## 代码风格

- Python: ruff lint, 4空格, UTF-8
- TypeScript: nanostores + shadcn/ui + CSS variables (`var(--ui-*)`)
- 前端: React + Vite, `apps/desktop/src/app/winpeek/`
- 后端: RPC handler 工厂模式（参照 `_make_org_handler`）

## 审查流程

1. `python scripts/winpeek-quality-check.py`
2. `npx tsc --noEmit`
3. `/review` 或 `code-review-and-quality` skill
4. 合并 → GitLab CI 自动门禁

## Zentao

- 任务: `tasks/*-todo.md` → Zentao project #6
- 查看: `ZENTAO_DB_HOST=192.168.3.23 zentao task list --execution=28`
- 同步: `python bin/sync-to-zentao.py`
