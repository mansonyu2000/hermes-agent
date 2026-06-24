# Hermes Agent - Qoder Skills & Commands 索引

> 本目录包含为 Hermes Agent 项目定制的 Qoder Skills 和 Commands。
> **本文档已索引到项目知识库，从知识库主入口可访问。**
> 最后更新: 2026-04-18

---

## 📚 文档导航

### 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **项目知识库** | [../HERMES_AGENT_KNOWLEDGE_BASE.md](../HERMES_AGENT_KNOWLEDGE_BASE.md) | 知识库主入口 |
| **开发指南** | [../AGENTS.md](../AGENTS.md) | AI助手开发指南 |
| **完整开发规矩** | [../.rules/development-rules.md](../.rules/development-rules.md) | 13章完整规范 |
| **记忆系统指南** | [../.rules/memory-system-guide.md](../.rules/memory-system-guide.md) | Hindsight完整指南 |
| **测试模板** | [../.rules/test-templates.md](../.rules/test-templates.md) | 测试模板和案例 |

---

## 📦 Skills（技能）

Skills 会被 Qoder AI **自动触发**（也可手动输入 `/skill-name`）。

### 已安装的 Skills

| 技能名称 | 触发关键词 | 用途 |
|---------|-----------|------|
| **hermes-test-runner** | run tests, pytest, test suite | 运行和验证测试套件 |
| **hermes-git-commit** | git commit, commit changes | 生成规范的 Git 提交信息 |
| **hermes-tool-creator** | create tool, add tool, new tool | 创建新工具（2文件模式） |
| **hermes-slash-command** | slash command, add command | 添加斜杠命令 |
| **hermes-debug-helper** | debug, investigate error, troubleshoot | 调试 Hermes 问题 |
| **hermes-config-manager** | config, configuration, .env, api key | 管理配置文件 |
| **hermes-python-test-expert** | python test, pytest, unit test, write test | Python 单元测试专家 |
| **hermes-frontend-test-expert** | frontend test, react test, typescript test, vitest | 前端测试专家 |

### Skills 目录结构

```
.qoder/skills/
├── hermes-test-runner/
│   └── SKILL.md
├── hermes-git-commit/
│   └── SKILL.md
├── hermes-tool-creator/
│   └── SKILL.md
├── hermes-slash-command/
│   └── SKILL.md
├── hermes-debug-helper/
│   └── SKILL.md
└── hermes-config-manager/
    └── SKILL.md
```

---

## ⚡ Commands（命令）

Commands 需要**手动触发**（输入 `/command-name`）。

### 已安装的 Commands

| 命令名称 | 类型 | 用途 |
|---------|------|------|
| **hermes-full-test** | Prompt | 运行完整测试套件并报告 |
| **hermes-quick-review** | Prompt | 快速代码审查（关键规则检查） |
| **hermes-prepare-release** | Prompt | 准备发布（测试+文档+版本） |
| **hermes-env-setup** | Prompt | 验证开发环境配置 |
| **hermes-run-all-tests** | Prompt | 运行前后端完整测试 + 覆盖率 |
| **hermes-write-test** | Prompt | 指导编写单元测试（Python + TypeScript） |

### Commands 目录结构

```
.qoder/commands/
├── hermes-full-test.md
├── hermes-quick-review.md
├── hermes-prepare-release.md
├── hermes-env-setup.md
├── hermes-run-all-tests.md
└── hermes-write-test.md
```

---

## 🎯 使用方式

### 在 Qoder CLI TUI 模式中使用

```bash
# 启动 Qoder CLI
qodercli

# 查看所有可用 Skills
/skills

# 查看所有可用 Commands
/commands

# 手动触发 Skill
/hermes-test-runner

# 执行 Command
/hermes-full-test
```

### 在 Headless 模式中使用 Commands

```bash
# 执行命令（不包含额外指令）
qodercli -p '/hermes-full-test'

# 执行命令（包含额外指令）
qodercli -p '/hermes-quick-review 重点检查 Profile 隔离'
qodercli -p '/hermes-git-commit 生成提交信息'
```

### Skills 自动触发示例

直接描述需求，AI 会自动判断使用哪个 Skill：

```
# 自动触发 hermes-test-runner
"运行测试验证刚才的修改"

# 自动触发 hermes-git-commit
"准备提交代码"

# 自动触发 hermes-tool-creator
"创建一个新的 web scraper 工具"

# 自动触发 hermes-debug-helper
"调试这个 Profile 隔离问题"
```

---

## 📖 详细文档

完整的开发规矩文档：[`.rules/development-rules.md`](../.rules/development-rules.md)

---

## 🔄 更新 Skills 和 Commands

### 修改 Skill

1. 编辑对应的 `SKILL.md` 文件
2. 重启 Qoder CLI 使更改生效

### 添加新 Skill

```bash
# 创建目录
mkdir -p .qoder/skills/my-new-skill

# 创建 SKILL.md
# 包含 frontmatter 和指令内容
```

### 添加新 Command

```bash
# 创建 Markdown 文件
.qoder/commands/my-command.md

# 包含 frontmatter 和提示词
```

---

## ⚠️ 注意事项

1. **重启要求**：修改 Skills/Commands 后需要重启 Qoder CLI
2. **优先级**：项目级 > 用户级（同名时项目级优先生效）
3. **触发关键词**：在 description 中包含常用关键词可提高自动触发准确率
4. **测试**：共享前务必测试 Skill 是否能正确触发

---

**维护者**: Hermes Agent 开发团队
