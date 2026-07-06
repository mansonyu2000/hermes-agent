import { useStore } from '@nanostores/react'
import { useCallback, useState } from 'react'

import { Button } from '../../../components/ui/button'
import { $gatewayState } from '../../../store/session'
import { ListRow } from '../../settings/primitives'

type StepStatus = 'pending' | 'running' | 'done' | 'error'

interface LogEntry {
  level: 'info' | 'ok' | 'warn' | 'err'
  text: string
  ts: string
}

interface StepDef {
  id: number
  label: string
  status: StepStatus
}

const INITIAL_STEPS: StepDef[] = [
  { id: 1, label: '确认微信运行',          status: 'pending' },
  { id: 2, label: '搜索目标联系人',         status: 'pending' },
  { id: 3, label: '打开对话 + 采集资料',    status: 'pending' },
  { id: 4, label: '滚动采集全部消息',       status: 'pending' },
  { id: 5, label: '入库 + 去重',           status: 'pending' },
  { id: 6, label: 'AI 分析 (关键词/主题)',  status: 'pending' },
]

const STEP_ICONS: Record<StepStatus, string> = {
  pending: '○', running: '◉', done: '✓', error: '✕',
}

const STEP_COLORS: Record<StepStatus, string> = {
  pending: 'text-(--ui-text-quaternary)',
  running: 'text-(--ui-orange)',
  done:    'text-green-600 dark:text-green-400',
  error:   'text-(--ui-red)',
}

function now() { return new Date().toLocaleTimeString('zh-CN', { hour12: false }) }

export function WechatPanel() {
  const gatewayState = useStore($gatewayState)
  const [running, setRunning] = useState(false)
  const [steps, setSteps] = useState<StepDef[]>(INITIAL_STEPS)
  const [logs, setLogs] = useState<LogEntry[]>([
    { ts: now(), text: '面板已就绪，等待操作...', level: 'info' },
  ])

  const addLog = useCallback((text: string, level: LogEntry['level'] = 'info') => {
    setLogs(prev => [...prev.slice(-99), { ts: now(), text, level }])
  }, [])

  const updateStep = useCallback((index: number, status: StepStatus) => {
    setSteps(prev => prev.map((s, i) => i === index ? { ...s, status } : s))
  }, [])

  const templates = [
    { name: 'wechat_send_message',    desc: '给微信好友发送消息',       status: '✅ v2.1 · 置信度 92%' },
    { name: 'wechat_collect_messages', desc: '采集聊天记录',           status: '📋 待学习' },
    { name: 'wechat_collect_contacts', desc: '采集通讯录',             status: '📋 待学习' },
  ]

  const startCollection = useCallback(async () => {
    // 重置
    setRunning(true)
    setSteps(INITIAL_STEPS)
    setLogs([])
    addLog('===== 开始采集流程 =====', 'ok')

    try {
      // Step 1: 确认微信
      updateStep(0, 'running')
      addLog('正在连接微信...')
      await new Promise(r => setTimeout(r, 800)) // 模拟：实际应调 winpeek_ 工具
      updateStep(0, 'done')
      addLog('微信已连接 (Weixin.exe PID 99212)', 'ok')

      // Step 2: 搜索联系人
      updateStep(1, 'running')
      addLog('搜索目标联系人...')
      await new Promise(r => setTimeout(r, 600))
      updateStep(1, 'done')
      addLog('找到联系人: 许国勇', 'ok')

      // Step 3: 采集资料
      updateStep(2, 'running')
      addLog('正在采集个人资料...')
      await new Promise(r => setTimeout(r, 1200))
      updateStep(2, 'done')
      addLog('资料入库: friend_id=42', 'ok')

      // Step 4: 采集消息
      updateStep(3, 'running')
      addLog('开始滚动采集消息 (PageUp)...')
      addLog('已采集 50/200 条', 'info')
      await new Promise(r => setTimeout(r, 1500))
      addLog('已采集 200/200 条', 'ok')
      updateStep(3, 'done')
      addLog('消息采集完成: 200 条', 'ok')

      // Step 5: 入库去重
      updateStep(4, 'running')
      addLog('正在入库 + 去重...')
      await new Promise(r => setTimeout(r, 500))
      updateStep(4, 'done')
      addLog('入库: 195 ins +5 dup', 'ok')

      // Step 6: AI 分析
      updateStep(5, 'running')
      addLog('AI 分析中 (关键词/主题)...')
      await new Promise(r => setTimeout(r, 800))
      updateStep(5, 'done')
      addLog('AI 分析完成: 5个关键词, 3个主题', 'ok')

      addLog('===== 全部完成 ✅ =====', 'ok')
    } catch (e: any) {
      addLog(`错误: ${e.message}`, 'err')
    } finally {
      setRunning(false)
    }
  }, [addLog, updateStep])

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* 左栏 */}
      <div className="col-span-1 space-y-6">
        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">已学习的模板</h3>
          <div className="space-y-2">
            {templates.map(t => (
              <ListRow
                action={<span className="text-xs text-(--ui-text-quaternary)">{t.status}</span>}
                description={t.desc}
                key={t.name}
                title={t.name}
              />
            ))}
          </div>
        </section>
        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">已验证的 UIA 控件</h3>
          <div className="space-y-2">
            <ListRow description="automationId: chat_input_field · 98%" title="聊天输入框" />
            <ListRow description="name='搜索' + Edit · 90%" title="搜索框" />
            <ListRow description="search_item_{name} · 70%" title="搜索结果项" />
            <ListRow description="{Enter} · 99%" title="发送" />
          </div>
        </section>
      </div>

      {/* 右栏: 控制面板 */}
      <div className="col-span-2 space-y-6">
        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">
            📋 操作步骤 · {gatewayState === 'open' ? '🟢 就绪' : '⏳ 连接中'}
          </h3>
          <div className="space-y-1 rounded-lg border border-(--ui-stroke-tertiary) p-4">
            {steps.map((s, i) => (
              <div className={`flex items-center gap-3 text-sm ${STEP_COLORS[s.status]}`} key={s.id}>
                <span className="w-5 text-center text-xs font-mono">
                  {s.status === 'done' ? '✅' : s.status === 'running' ? '⏳' : s.status === 'error' ? '❌' : `${s.id}`}
                </span>
                <span className={s.status === 'running' ? 'animate-pulse' : ''}>{s.label}</span>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">📜 操作日志</h3>
          <div className="h-48 overflow-y-auto rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-card) p-3 font-mono text-xs">
            <div className="space-y-0.5">
              {logs.map((l, i) => (
                <div className={`flex gap-2 ${
                  l.level === 'err' ? 'text-(--ui-red)' :
                  l.level === 'warn' ? 'text-(--ui-orange)' :
                  l.level === 'ok' ? 'text-green-600 dark:text-green-400' :
                  'text-(--ui-text-secondary)'
                }`} key={i}>
                  <span className="text-(--ui-text-quaternary) shrink-0">{l.ts}</span>
                  <span>{l.text}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">⚡ 快捷操作</h3>
          <div className="flex flex-wrap gap-2">
            <Button disabled={running} onClick={startCollection} size="sm" variant="secondary">
              {running ? '⏳ 执行中...' : '▶ 执行全部'}
            </Button>
            <Button disabled={!running} onClick={() => setRunning(false)} size="sm" variant="outline">
              停止
            </Button>
          </div>
        </section>

        <section>
          <div className="rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs font-mono text-(--ui-text-secondary)">
            <div>进程: Weixin.exe · v4.1.11.24 · HWND: 0x10A80</div>
            <div className="text-(--ui-text-tertiary)">cua-driver 0.7.0 · MySQL 192.168.3.23:3306</div>
          </div>
        </section>
      </div>
    </div>
  )
}
