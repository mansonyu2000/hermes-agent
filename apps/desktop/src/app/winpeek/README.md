# WinPeek Frontend Views

Electron Desktop 内的 WinPeek 前端视图。

## 目录结构

```
apps/desktop/src/app/winpeek/
├── index.tsx          # WinPeek 主入口（路由挂载）
├── mim/               # MIM 聊天界面（微信风格双栏）
├── wechat/            # 微信管理面板
├── automation/        # 自动化任务配置
└── assets/            # 资产视图（文件/截图管理）
```

## 路由

在 `apps/desktop/src/app/routes.ts` 中注册。

## 数据流

```
用户操作 → React 组件 → useGatewayRequest() → tui_gateway → AIAgent → 工具执行 → 结果渲染
```

## 设计约定

- 复用 Hermes Desktop 的 `MasterDetail` 布局
- 使用 nanostore 管理状态（`src/store/`）
- i18n 支持：en / zh / ja / zh-hant
