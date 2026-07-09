# WinPeek 快速上手

5 分钟跑起 WinPeek，开始自动化微信操作。

## 前置条件

- Windows 10/11，已安装微信 PC 版
- Python 3.10+
- MySQL 8.0（可选，默认使用本地 SQLite）

## 安装

```bash
# 1. 进入项目
cd hermes-agent

# 2. 安装 Python 依赖
pip install uiautomation pyautogui pyperclip pymysql jieba

# 3. 初始化数据库
python plugins/winpeek_rpa/platforms/wechat/db.py --init --wxid YOUR_WXID
```

## 首次采集

```bash
# 采集通讯录（需要微信已登录且在前台）
python plugins/winpeek_rpa/platforms/wechat/contacts.py --collect --wxid YOUR_WXID

# 采集所有会话的聊天记录
python plugins/winpeek_rpa/platforms/wechat/msg_traverse.py --wxid YOUR_WXID
```

## 发送消息

```bash
# 搜索好友并发送
python plugins/winpeek_rpa/platforms/wechat/find.py --to "好友名" --msg "你好"
```

## 使用 MySQL（可选）

```bash
# 设置环境变量切换到 MySQL 后端
set DB_BACKEND=mysql
set DB_HOST=192.168.3.23
set DB_USER=winpeek
set DB_PASS=Server33
set DB_NAME=winpeek

# 初始化 MySQL 表
python plugins/winpeek_rpa/platforms/wechat/db.py --init --wxid YOUR_WXID --backend mysql
```

## 通过 Hermes Agent 调用

Agent 对话中直接使用已注册的工具：

```
winpeek_wechat_send        → 给好友发消息
winpeek_wechat_collect_msgs → 采集聊天记录
winpeek_wechat_collect_contacts → 采集通讯录
winpeek_list_templates      → 列出已学习模板
```

## 下一步

- [架构总览](ARCHITECTURE.md) — 系统架构和组件关系
- [功能全景](features/OVERVIEW.md) — 7 维度画像 + 行动闭环
- [完整需求规格](../../../docs/requirements/wechat-prd.md) — 9 大模块 / 40+ 功能点

---

> 参见完整设计：[docs/design/wechat-crm-design.md](../../../docs/design/wechat-crm-design.md)
