# WinPeek 质量门禁 — 各 Agent 部署手册

每个 Agent 拿到代码后，执行自己对应的段落。

---

## CC-yu2 部署 (Claude Code, Windows, yu2)

### 1. 确认文件都存在
```bash
ls scripts/winpeek-quality-check.py .gitlab-ci.yml .claude/skills/winpeek-quality-gate/SKILL.md .claude/skills/update-docs/SKILL.md && echo "OK" || echo "MISSING"
```

### 2. 安装依赖（一次性）
```bash
cd apps/desktop && npm ci && cd ../..
pip install ruff
```

### 3. 试跑
```bash
python scripts/winpeek-quality-check.py
```

### 4. 日常使用
- Skill 已自动加载（`.claude/skills/` 目录），不需要手动配
- 每次 commit 前我会自动提示跑检查
- 你也可以说"质量检查"手动触发

---

## Hermes-htubs24 部署 (Hermes Agent, Ubuntu, htubs24)

### 1. 拉代码
```bash
cd ~/.hermes/hermes-agent
git checkout DEV && git pull
```

### 2. 安装 Python 依赖
```bash
pip install ruff
```

### 3. 试跑 (Ubuntu 无 Node.js, 跳过 TypeScript + CSS)
```bash
python3 scripts/winpeek-quality-check.py --check ruff
python3 scripts/winpeek-quality-check.py --check frontmatter
python3 scripts/winpeek-quality-check.py --check links
python3 scripts/winpeek-quality-check.py --check filename
```

### 4. 日常使用
- 每次改完 `gateway/winpeek_hub/` 下的代码后：
  ```bash
  python3 scripts/winpeek-quality-check.py --check ruff
  ```
- 每次改完 `website/docs/winpeek/` 下的文档后：
  ```bash
  python3 scripts/winpeek-quality-check.py --check frontmatter --check links --check filename
  ```
- 检查文档影响面：
  ```bash
  git diff DEV...HEAD --stat
  # → 对照 .claude/skills/update-docs/references/CODE-TO-DOCS-MAPPING.yaml
  ```

---

## Qoder-yu2 部署 (Qoder IDE, Windows, yu2)

### 1. 确认 CI 配置文件在 DEV 分支
```bash
git checkout DEV && git pull
ls .gitlab-ci.yml && echo "CI config OK" || echo "MISSING"
```

### 2. 确认 GitLab Runner 已配置
```bash
# 检查项目是否有 Runner
# GitLab → Settings → CI/CD → Runners
```

### 3. 试跑本地检查
```bash
cd apps/desktop && npm ci && cd ../..
pip install ruff
python scripts/winpeek-quality-check.py
```

### 4. 开启分支保护 (管理员权限, 一次性)
1. GitLab → Settings → Repository → Protected Branches
2. 找到 `DEV` → 点 "Protect"
3. 勾选 "Pipelines must succeed"
4. 保存

### 5. MR 门禁生效验证
```bash
# 创建一个测试 MR
git checkout -b test/quality-gate-test
echo "# test" >> website/docs/winpeek/TEST.md
git add . && git commit -m "test: quality gate trigger" && git push local test/quality-gate-test
# → GitLab 创建 MR → 观察 Pipeline 是否自动跑
# → 确认 winpeek-quality-block 报 FAIL（因为 TEST.md 缺 frontmatter + 文件名大写）
# → 删除测试 MR: git checkout DEV && git branch -D test/quality-gate-test
```

### 6. 日常使用
- Qoder 的职责是审查 MR 质量，不是自己写代码跑检查
- 每次 CC-yu2 或 Hermes-htubs24 提交 MR 时，Pipeline 自动跑
- Qoder 只需要看 Pipeline 结果 + 补充人工审查（组件命名/重复逻辑/useEffect cleanup）

---

## 检查项与 Agent 能力对照

| 检查 | CC-yu2 | Hermes-htubs24 | Qoder-yu2 |
|------|--------|---------------|-----------|
| Python ruff | ✅ | ✅ | ✅ |
| frontmatter | ✅ | ✅ | ✅ |
| 死链 | ✅ | ✅ | ✅ |
| 文件名 | ✅ | ✅ | ✅ |
| TypeScript | ✅ | ❌ (无Node.js) | ✅ |
| CSS token | ✅ | ❌ (无Node.js) | ✅ |
| MR 门禁 | - | - | ✅ (CI管理员) |
