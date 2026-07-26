---
sidebar_position: 11
title: "WeChat RPA 开发规范"
description: "微信自动化模块的开发规范：文件创建决策树、函数设计原则、Git 提交格式、质量门禁"
---

> 参考：[winpeek-prod/01-development-standards.md](https://github.com/winpeek-prod) + [winpeek-prod/DESIGN-SPEC.md](https://github.com/winpeek-prod)
> 📍 [返回文档索引](README) | 最后更新：2026-07-18

---

## 文件创建决策树

```
新功能 →
  ├─ 是否独立可调用 (给参数就工作)?
  │   ├─ 是 → 新文件
  │   └─ 否 → 继续判断
  ├─ 是否属于已有文件的职责范围?
  │   ├─ 是 → 加在已有文件
  │   └─ 否 → 新文件
  └─ 是否会被多处引用?
      ├─ 是 → 新文件 (可复用工具)
      └─ 否 → 可内联在调用处
```

| 场景 | 做法 | 示例 |
|------|------|------|
| 独立功能 | **新文件** | `collect_chat_msgs` → `wechat_msg_collect.py` |
| 编排/流程 | **新文件** | `collect_all_sessions` → `wechat_msg_traverse.py` |
| UI 面板入口 | 留在面板文件，≤20行 | `_collect_messages_wrapper` |
| 工具函数族 | **一个文件** | `wechat_api.py` (Eyes/Hands/Engine) |
| 配置/常量 | `config.json` + `config.py` | 不散落各处 |
| 坐标/锚点数据 | `pixel_anchors.json` | 静态数据独立于代码 |

## 函数设计原则

```python
# ✅ 正确: 给参数就工作，不依赖外部状态
def collect_chat_msgs(db, w, hands, session_name, mode='all'):
    """读单个会话消息 → 入库"""
    ...

# ❌ 错误: 依赖 self.xxx 的全局状态
def collect(self):
    self.db...
```

**回调注入**：独立函数通过回调参数接收日志/步骤通知，不直接依赖面板的 `self.log`。

## Git 规范

### Commit 格式

```
spec:  xxx        — 规格/设计文档
feat:  xxx        — 新功能
fix:   xxx        — bug 修复
refactor: xxx     — 重构
test:  xxx        — 测试

引用声明 (必须):
  spec: #issue_id  — 引用的规格文档
  fix:  #issue_id  — 修复的问题
```

### 提交前门禁

- [ ] 代码通过 lint
- [ ] 相关测试通过
- [ ] 没有调试日志残留
- [ ] TypeScript typecheck 通过

## 开发流程（7 状态机）

```
需求 → 待做 → 做了 → 自检 → 测试通过 → 完成
  ↑      ↑     ↑      ↑        ↑        ↑
 todo  todo  in_progress in_review  done  done
```

**不可跳状态**——从"做了"到"完成"必须经过"自检"和"测试通过"。
