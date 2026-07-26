# 开发环境搭建指南

> Hermes Agent CC — WinPeek 子项目

## 前置条件

- Python 3.12+
- Node.js 20+
- Git
- 访问 gitlab.test.com 的 SSH key

## 克隆与安装

```bash
# 克隆
git clone git@gitlab.test.com:hotime/sp/hermes-agent.git
cd hermes-agent

# 切换开发分支
git checkout DEV

# Python 依赖
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# 前端依赖
cd apps/desktop
npm install
```

## 本地运行

```bash
# 启动 Gateway（后端）
python tui_gateway/server.py

# 启动桌面应用（前端）
cd apps/desktop
npm run dev
```

## 常用命令

```bash
# TypeScript 类型检查
npx tsc --noEmit

# Python lint
ruff check tools/ gateway/

# 运行测试
python -m pytest tests/ -x

# Zentao 任务查看
ZENTAO_DB_HOST=192.168.3.23 zentao task list --execution=28

# Zentao 状态同步
python bin/sync-to-zentao.py --dry-run
python bin/sync-to-zentao.py --module=mim
```

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `ZENTAO_DB_HOST` | Zentao MySQL 地址 | `192.168.3.23` |
| `ZENTAO_DB_USER` | MySQL 用户名 | `root` |
| `ZENTAO_DB_PASSWORD` | MySQL 密码 | `Server123` |
| `ZENTAO_DB_NAME` | MySQL 数据库名 | `zentao` |
| `ZENTAO_URL` | Zentao Web URL | `http://pm.test.com` |
| `HERMES_HOME` | Hermes 数据目录 | `~/.hermes` |

## 下一步

1. 读 `tasks/README.md` — 了解当前任务
2. 运行 `/onboard` — 加载项目上下文
3. 选一个 `[zentao:#NN]` 任务开始
