# WinPeek 前端视图

桌面自动化模块的 React 前端，在 Hermes Desktop Electron 应用中运行。

## 目录结构

```
winpeek/
├── index.tsx          # barrel: 导出所有视图
├── assets/            # 电脑资产 — 软件/硬件扫描器
├── automation/        # 桌面自动化 — 平台切换器(微信/抖音/快手...)
├── wechat/            # 微信面板 — 采集流程UI (WechatPanel)
├── mim/               # 多平台即时通讯 — MasterDetail 聊天视图
├── components/        # 共享组件
├── hooks/             # 共享 hooks
└── store/             # 共享 nanostores
```

## 路由

| 路由 | 视图 | 入口 |
|------|------|------|
| `/automation` | AutomationView | 侧边栏 + 状态栏 |
| `/mim` | MimView | 侧边栏 |
| `/winpeek-wechat` | WechatPanel | 状态栏"微信"按钮 |

## 当前状态

- **WechatPanel** — 6 步采集管线 UI (全用 setTimeout 模拟, 未接入真实 API)
- **MimView** — 硬编码 mock 数据, 未对接后端
- **AutomationView** — 平台选择器骨架, 仅微信有内容

## 待开发

参见 [PRD](/docs/requirements/wechat-prd.md) — Phase 1-6 完整路线图。

## 技术栈

- React 19 + TypeScript (strict)
- Vite 6
- nanostores (状态管理)
- Tailwind CSS + shadcn/ui
- `useGatewayRequest()` → Hermes IPC 桥接
