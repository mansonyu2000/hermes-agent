# ZenTao CLI Bug: link-project MySQL 地址硬编码 127.0.0.1

> 反馈人: CC · 日期: 2026-07-19 · 目标仓库: CLI-Anything

## Bug 描述

`story create --project` 和 `story link-project` 改用 `pymysql` 后，MySQL 地址硬编码为 `host='127.0.0.1'`。当禅道的 MySQL 不在本机时（如 `192.168.3.23`），`ConnectionRefusedError` 导致关联失败。

## 受影响代码

`zentao/agent-harness/zentao_cli/__init__.py`:

- L321: `pymysql.connect(host='127.0.0.1', ...)` — story create 中的 project 关联
- L341: `pymysql.connect(host='127.0.0.1', ...)` — story link-project 独立命令

## 修复建议

```python
# 读取 MySQL 地址（环境变量或 config）
MYSQL_HOST = os.getenv("ZENTAO_MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("ZENTAO_MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("ZENTAO_MYSQL_USER", "root")
MYSQL_PASS = os.getenv("ZENTAO_MYSQL_PASS", "Server123")
MYSQL_DB   = os.getenv("ZENTAO_MYSQL_DB", "zentao")

conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                        password=MYSQL_PASS, database=MYSQL_DB)
```

## 工作量

≤ 0.5h
