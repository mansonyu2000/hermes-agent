---
name: hermes-frontend-test-expert
description: >
  Expert guide for testing React + TypeScript + Vite frontend in Hermes Agent web UI.
  Use when writing frontend tests, setting up testing infrastructure, or debugging
  React component tests. Covers Vitest, React Testing Library, and best practices.
  Trigger keywords: frontend test, react test, typescript test, vitest, component test.
---

# Hermes Agent Frontend Testing Expert

## 前端技术栈

### 当前配置

**技术栈：**
- React 19
- TypeScript 5.9
- Vite 7.3.1
- Tailwind CSS v4

**现有脚本** (`web/package.json`):
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  }
}
```

**注意：** 项目当前**没有配置前端测试框架**，需要添加。

---

## 推荐测试方案

### 方案选择：Vitest + React Testing Library

**推荐理由：**
- ✅ 与 Vite 原生集成（零配置）
- ✅ 支持 TypeScript 开箱即用
- ✅ 速度快（比 Jest 快 5-10 倍）
- ✅ 兼容 Jest API（容易迁移）
- ✅ 支持 React 19

### 安装步骤

```bash
cd /root/hermes-agent/web

# 安装测试依赖
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# 或如果使用 pnpm
pnpm add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# 或如果使用 yarn
yarn add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### 配置 Vitest

**文件：** `web/vitest.config.ts`

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.ts',
      ],
    },
  },
})
```

### 测试 Setup 文件

**文件：** `web/src/test/setup.ts`

```typescript
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// 每个测试后自动清理
afterEach(() => {
  cleanup()
})
```

### 更新 package.json

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint ."
  }
}
```

---

## React 组件测试指南

### 基础测试结构

```typescript
// src/components/Button.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<Button onClick={handleClick}>Click me</Button>)
    
    await user.click(screen.getByRole('button'))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<Button loading>Loading...</Button>)
    
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })
})
```

### 测试 Hooks

```typescript
// src/hooks/useAuth.test.ts
import { renderHook } from '@testing-library/react'
import { useAuth } from './useAuth'

describe('useAuth', () => {
  it('returns initial state', () => {
    const { result } = renderHook(() => useAuth())
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })

  it('updates state after login', () => {
    const { result } = renderHook(() => useAuth())
    
    act(() => {
      result.current.login({ id: 1, name: 'Test User' })
    })
    
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user?.name).toBe('Test User')
  })
})
```

### 测试带 Context 的组件

```typescript
// src/components/Dashboard.test.tsx
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '../context/ThemeContext'
import { Dashboard } from './Dashboard'

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <ThemeProvider initialTheme="dark">
      {ui}
    </ThemeProvider>
  )
}

describe('Dashboard', () => {
  it('renders with theme context', () => {
    renderWithProviders(<Dashboard />)
    
    expect(screen.getByTestId('dashboard')).toHaveClass('dark-theme')
  })
})
```

### Mock API 调用

```typescript
// src/api/sessionApi.test.ts
import { vi } from 'vitest'
import { getSession } from './sessionApi'

// Mock fetch
global.fetch = vi.fn()

describe('sessionApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches session data', async () => {
    const mockData = { id: '123', title: 'Test Session' }
    
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response)

    const result = await getSession('123')
    
    expect(result).toEqual(mockData)
    expect(fetch).toHaveBeenCalledWith('/api/sessions/123')
  })

  it('handles API errors', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 500,
    } as Response)

    await expect(getSession('123')).rejects.toThrow('API Error')
  })
})
```

### Mock React Router

```typescript
// src/components/SessionList.test.tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SessionList } from './SessionList'

describe('SessionList', () => {
  it('navigates to session on click', () => {
    render(
      <MemoryRouter>
        <SessionList sessions={[{ id: '1', title: 'Test' }]} />
      </MemoryRouter>
    )

    // 测试路由导航
    // ...
  })
})
```

---

## 测试最佳实践

### 1. 测试用户行为，不是实现细节

```typescript
// ✅ 好的测试 - 测试用户看到的
it('shows error message on failure', async () => {
  render(<LoginForm />)
  
  await userEvent.type(screen.getByLabelText(/username/i), 'test')
  await userEvent.click(screen.getByRole('button', { name: /login/i }))
  
  expect(await screen.findByText(/login failed/i)).toBeInTheDocument()
})

// ❌ 坏的测试 - 测试内部状态
it('sets error state', () => {
  const { container } = render(<LoginForm />)
  // 测试内部 state - 容易因重构而失败
})
```

### 2. 使用 data-testid 谨慎

```typescript
// ✅ 优先使用语义查询
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/email/i)
screen.getByText(/welcome/i)

// ⚠️ 仅在必要时使用 data-testid
screen.getByTestId('custom-element')
```

### 3. 异步测试模式

```typescript
// ✅ 使用 findBy (自动等待)
it('loads data asynchronously', async () => {
  render(<DataList />)
  
  expect(screen.getByText(/loading/i)).toBeInTheDocument()
  
  // findBy 会自动等待
  const items = await screen.findAllByRole('listitem')
  expect(items).toHaveLength(3)
})

// ❌ 不要使用同步查询
it('fails with sync query', () => {
  render(<DataList />)
  // 会失败 - 数据还没加载
  expect(screen.getAllByRole('listitem')).toHaveLength(3)
})
```

### 4. Mock 外部依赖

```typescript
// src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

export const handlers = [
  http.get('/api/sessions', () => {
    return HttpResponse.json([
      { id: '1', title: 'Session 1' },
      { id: '2', title: 'Session 2' },
    ])
  }),
]

export const server = setupServer(...handlers)

// src/test/setup.ts
import { server } from './mocks/handlers'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

---

## Hermes Agent Web UI 测试示例

### 示例 1: 测试会话列表组件

```typescript
// src/components/SessionList.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SessionList } from './SessionList'
import { vi } from 'vitest'

describe('SessionList', () => {
  const mockSessions = [
    { id: '1', title: 'Session 1', created_at: '2026-04-18' },
    { id: '2', title: 'Session 2', created_at: '2026-04-17' },
  ]

  it('renders session list', () => {
    render(<SessionList sessions={mockSessions} />)
    
    expect(screen.getByText('Session 1')).toBeInTheDocument()
    expect(screen.getByText('Session 2')).toBeInTheDocument()
  })

  it('calls onSelect when session clicked', async () => {
    const handleSelect = vi.fn()
    const user = userEvent.setup()
    
    render(
      <SessionList 
        sessions={mockSessions} 
        onSelect={handleSelect} 
      />
    )
    
    await user.click(screen.getByText('Session 1'))
    
    expect(handleSelect).toHaveBeenCalledWith('1')
  })

  it('shows empty state when no sessions', () => {
    render(<SessionList sessions={[]} />)
    
    expect(screen.getByText(/no sessions/i)).toBeInTheDocument()
  })
})
```

### 示例 2: 测试聊天界面

```typescript
// src/components/ChatInterface.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInterface } from './ChatInterface'
import { vi } from 'vitest'

describe('ChatInterface', () => {
  it('displays messages', () => {
    const messages = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there!' },
    ]
    
    render(<ChatInterface messages={messages} />)
    
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('sends message on submit', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    
    render(<ChatInterface messages={[]} onSend={onSend} />)
    
    const input = screen.getByPlaceholderText(/type a message/i)
    await userEvent.type(input, 'Test message')
    await userEvent.keyboard('{Enter}')
    
    expect(onSend).toHaveBeenCalledWith('Test message')
  })

  it('shows typing indicator', () => {
    render(
      <ChatInterface 
        messages={[]} 
        isTyping={true} 
      />
    )
    
    expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()
  })
})
```

### 示例 3: 测试自定义 Hooks

```typescript
// src/hooks/useSession.test.ts
import { renderHook, act } from '@testing-library/react'
import { useSession } from './useSession'
import { vi } from 'vitest'

describe('useSession', () => {
  it('initializes with empty state', () => {
    const { result } = renderHook(() => useSession())
    
    expect(result.current.messages).toEqual([])
    expect(result.current.isLoading).toBe(false)
  })

  it('adds message', () => {
    const { result } = renderHook(() => useSession())
    
    act(() => {
      result.current.addMessage('user', 'Hello')
    })
    
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0]).toEqual({
      role: 'user',
      content: 'Hello'
    })
  })

  it('loads session data', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      messages: [{ role: 'user', content: 'Loaded' }]
    })
    
    global.fetch = mockFetch
    
    const { result } = renderHook(() => useSession())
    
    await act(async () => {
      await result.current.loadSession('123')
    })
    
    expect(result.current.messages).toHaveLength(1)
    expect(mockFetch).toHaveBeenCalledWith('/api/sessions/123')
  })
})
```

---

## 运行前端测试

### 基本命令

```bash
cd /root/hermes-agent/web

# 运行测试 (watch 模式)
npm test

# 运行一次并退出
npm run test:run

# 运行带 UI
npm run test:ui

# 生成覆盖率报告
npm run test:coverage
```

### 过滤测试

```bash
# 运行特定文件
npm test -- SessionList.test.tsx

# 运行匹配的测试
npm test -- -t "renders session list"

# 更新快照
npm test -- -u
```

---

## E2E 测试（可选）

### 使用 Playwright

```bash
# 安装 Playwright
npm install -D @playwright/test
npx playwright install

# 创建配置
# e2e/playwright.config.ts
```

**示例 E2E 测试：**

```typescript
// e2e/session.spec.ts
import { test, expect } from '@playwright/test'

test('user can create and view session', async ({ page }) => {
  await page.goto('http://localhost:9119')
  
  // 创建新会话
  await page.getByRole('button', { name: /new session/i }).click()
  
  // 发送消息
  await page.getByPlaceholder(/type a message/i).fill('Hello')
  await page.keyboard.press('Enter')
  
  // 验证响应
  await expect(page.getByText(/hello/i)).toBeVisible()
})
```

---

## 快速参考

### 常用查询方法

```typescript
// 按角色 (推荐)
screen.getByRole('button', { name: /submit/i })
screen.getByRole('textbox', { name: /email/i })

// 按文本
screen.getByText(/welcome/i)
screen.getByText('Exact Text')

// 按标签
screen.getByLabelText(/username/i)

// 按测试 ID (最后选择)
screen.getByTestId('custom-element')

// 异步查询
await screen.findByText(/loaded/i)
await screen.findAllByRole('listitem')
```

### 常用断言

```typescript
// 存在性
expect(element).toBeInTheDocument()
expect(element).not.toBeInTheDocument()

// 可见性
expect(element).toBeVisible()
expect(element).not.toBeVisible()

// 状态
expect(element).toBeDisabled()
expect(element).toBeEnabled()
expect(element).toHaveClass('active')
expect(element).toHaveAttribute('href', '/path')

// 内容
expect(element).toHaveTextContent(/hello/i)
expect(element).toContainElement(child)
```

---

## 相关文档

- **Vitest 文档**: https://vitest.dev/
- **React Testing Library**: https://testing-library.com/docs/react-testing-library/intro/
- **后端测试 Skill**: `/hermes-python-test-expert`
- **项目测试配置**: `pyproject.toml`
