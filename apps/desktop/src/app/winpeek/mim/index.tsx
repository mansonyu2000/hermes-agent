import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'

import { DetailColumn, ListColumn, MasterDetail } from '../../master-detail'

/* ── Types ───────────────────────────────────── */

interface WinPeekIdentity {
  uid: number
  name: string
  role: string
  host: string
}
interface Contact {
  id: string
  name: string
  uid: number
  role?: string
  lastMessage?: string
  lastTime?: string
  unread: number
  online: boolean
}
interface ChatMessage {
  id: string
  fromUid: number
  fromName: string
  content: string
  time: string
  isSelf: boolean
}

const ROLES = ['Developer', 'Architect', 'Ops', 'QA', 'PM', 'Director', 'Boss'] as const
const HUB = 'http://127.0.0.1:2000'

/* ── Identity Store (localStorage) ───────────── */

function loadSavedIdentity(): WinPeekIdentity | null {
  try {
    const raw = localStorage.getItem('mim-identity')
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}
function saveIdentity(id: WinPeekIdentity) {
  localStorage.setItem('mim-identity', JSON.stringify(id))
}

/* ── Contacts ────────────────────────────────── */

const DEFAULT_CONTACTS: Contact[] = [
  { id: 'pm', name: 'PM', uid: 2022, role: 'PM', lastMessage: '已收到', lastTime: '10:30', unread: 0, online: true },
  { id: 'arch', name: '架叔', uid: 2027, role: 'Architect', lastMessage: '架构方案已发', lastTime: '昨天', unread: 0, online: true },
  { id: 'dev1', name: '大海', uid: 2023, role: 'Developer', lastMessage: '代码提交了', lastTime: '09:15', unread: 2, online: true },
  { id: 'qa', name: '清清', uid: 2026, role: 'QA', lastMessage: '测试通过', lastTime: '前天', unread: 0, online: false },
  { id: 'ops', name: '运维', uid: 2025, role: 'Ops', lastMessage: '服务已重启', lastTime: '昨天', unread: 0, online: true },
  { id: 'director', name: '总监', uid: 2028, role: 'Director', lastMessage: '下周评审', lastTime: '周一', unread: 0, online: false },
  { id: 'boss', name: '老板', uid: 2029, role: 'Boss', lastMessage: '项目进度确认', lastTime: '上周', unread: 3, online: false },
  { id: 'group1', name: '项目群', uid: 0, role: undefined, lastMessage: '[群] 周会通知', lastTime: '10:00', unread: 5, online: true },
]

/* ── Login / Register Form ───────────────────── */

function LoginPanel({ onLogin, onRegister }: {
  onLogin: (name: string) => void
  onRegister: (name: string, role: string) => void
}) {
  const [nick, setNick] = useState('')
  const [showRegister, setShowRegister] = useState(false)
  const [role, setRole] = useState<string>('Developer')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = useCallback(() => {
    if (!nick.trim()) { return }
    const id: WinPeekIdentity = { uid: 2027, name: nick.trim(), role: 'Developer', host: 'local' }
    saveIdentity(id)
    onLogin(nick.trim())
  }, [nick, onLogin])

  const handleRegister = useCallback(() => {
    if (!nick.trim()) { return }
    const id: WinPeekIdentity = { uid: 2000 + Math.floor(Math.random() * 100), name: nick.trim(), role, host: 'local' }
    saveIdentity(id)
    onRegister(nick.trim(), role)
  }, [nick, role, onRegister])

  return (
    <div className="grid h-full place-items-center p-6">
      <div className="w-full max-w-xs space-y-4">
        <div className="text-center">
          <div className="mb-2 text-4xl">💬</div>
          <h2 className="text-lg font-semibold text-foreground">WinPeek MIM</h2>
          <p className="text-xs text-(--ui-text-tertiary)">登录或注册以使用消息功能</p>
        </div>
        {error && <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}
        <Input
          onChange={e => setNick(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !showRegister && handleLogin()}
          placeholder="用户名"
          value={nick}
        />
        {showRegister ? (
          <>
            <div className="flex flex-wrap gap-1.5">
              {ROLES.map(r => (
                <button
                  key={r}
                  className={cn(
                    'rounded-full px-2.5 py-1 text-xs font-medium transition-colors',
                    role === r
                      ? 'bg-(--ui-accent) text-(--ui-accent-foreground)'
                      : 'bg-(--ui-bg-quaternary) text-(--ui-text-secondary) hover:bg-(--ui-control-hover-background)'
                  )}
                  onClick={() => setRole(r)}
                >{r}</button>
              ))}
            </div>
            <Button className="w-full" disabled={loading || !nick.trim()} onClick={handleRegister} size="sm">
              {loading ? '注册中...' : '注册新用户'}
            </Button>
            <button className="w-full text-center text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={() => setShowRegister(false)}>
              ← 返回登录
            </button>
          </>
        ) : (
          <Button className="w-full" disabled={loading || !nick.trim()} onClick={handleLogin} size="sm">
            {loading ? '登录中...' : '登录'}
          </Button>
        )}
        {!showRegister && (
          <button className="w-full text-center text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={() => setShowRegister(true)}>
            没有账号？立即注册
          </button>
        )}
      </div>
    </div>
  )
}

/* ── Profile Panel ───────────────────────────── */

function ProfilePanel({ identity, onLogout }: { identity: WinPeekIdentity; onLogout: () => void }) {
  return (
    <div className="p-4 space-y-3">
      <div className="text-center">
        <div className="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-full bg-(--ui-accent)/15 text-xl font-bold text-(--ui-accent)">
          {identity.name.charAt(0)}
        </div>
        <h3 className="text-sm font-semibold text-foreground">{identity.name}</h3>
        <p className="text-xs text-(--ui-text-tertiary)}">{identity.role} · #{identity.uid}</p>
        <p className="text-[0.6rem] text-(--ui-text-quaternary)">主机: {identity.host}</p>
      </div>
      <div className="space-y-1.5 border-t border-(--ui-stroke-tertiary) pt-3">
        <div className="flex items-center justify-between text-xs text-(--ui-text-secondary)">
          <span>MQTT Broker</span><span className="font-mono text-(--ui-text-tertiary)">192.168.3.23:1883</span>
        </div>
        <div className="flex items-center justify-between text-xs text-(--ui-text-secondary)">
          <span>WinPeek Hub</span><span className="font-mono text-(--ui-text-tertiary)">{HUB}</span>
        </div>
        <div className="flex items-center justify-between text-xs text-(--ui-text-secondary)">
          <span>消息通知</span>
          <Switch defaultChecked id="mim-notify" />
        </div>
      </div>
      <Button className="w-full" onClick={onLogout} size="xs" variant="secondary">
        退出登录
      </Button>
    </div>
  )
}

/* ── Main View ───────────────────────────────── */

export function MimView({ onClose }: { onClose: () => void }) {
  const [identity, setIdentity] = useState<WinPeekIdentity | null>(loadSavedIdentity)
  const [showProfile, setShowProfile] = useState(false)

  const [contacts] = useState<Contact[]>(DEFAULT_CONTACTS)
  const [activeContactId, setActiveContactId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const activeContact = useMemo(
    () => contacts.find(c => c.id === activeContactId) ?? null,
    [contacts, activeContactId]
  )

  const handleLogin = useCallback((name: string) => {
    const id = loadSavedIdentity() ?? { uid: 2027, name, role: 'Developer', host: 'offline' }
    setIdentity(id)
  }, [])

  const handleRegister = useCallback((name: string, role: string) => {
    const id = loadSavedIdentity() ?? { uid: Date.now() % 10000, name, role, host: 'offline' }
    setIdentity(id)
  }, [])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('mim-identity')
    setIdentity(null)
    setActiveContactId(null)
    setMessages([])
  }, [])

  useEffect(() => {
    if (!activeContact) { setMessages([]); return }
    setMessages([
      { id: '1', fromUid: activeContact.uid, fromName: activeContact.name, content: `你好，我是${activeContact.name}`, time: '09:00', isSelf: false },
      { id: '2', fromUid: identity?.uid ?? 0, fromName: identity?.name ?? '我', content: `收到，${activeContact.lastMessage ?? '请说'}`, time: '09:01', isSelf: true },
      { id: '3', fromUid: activeContact.uid, fromName: activeContact.name, content: activeContact.lastMessage ?? '...', time: '09:15', isSelf: false },
    ])
  }, [activeContact, identity])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text || !activeContact || !identity) return
    setMessages(prev => [...prev, {
      id: `msg-${Date.now()}`, fromUid: identity.uid, fromName: identity.name,
      content: text,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      isSelf: true,
    }])
    setInputText('')
  }, [inputText, activeContact, identity])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }, [handleSend])

  // ── Not logged in ──
  if (!identity) {
    return (
      <MasterDetail>
        <LoginPanel onLogin={handleLogin} onRegister={handleRegister} />
      </MasterDetail>
    )
  }

  // ── Profile view ──
  if (showProfile) {
    return (
      <MasterDetail>
        <ProfilePanel identity={identity} onLogout={handleLogout} />
      </MasterDetail>
    )
  }

  // ── Chat view ──
  const sortedContacts = [...contacts].sort((a, b) => (b.unread || 0) - (a.unread || 0))

  return (
    <MasterDetail>
      <ListColumn>
        <div className="flex h-full flex-col">
          <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-3 py-2.5">
            <button className="flex items-center gap-2 text-left hover:opacity-80" onClick={() => setShowProfile(true)}>
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-(--ui-accent)/15 text-[0.6rem] font-semibold text-(--ui-accent)">
                {identity.name.charAt(0)}
              </div>
              <div>
                <div className="text-xs font-semibold text-foreground">{identity.name}</div>
                <div className="text-[0.55rem] text-(--ui-text-tertiary)}">{identity.role} · #{identity.uid}</div>
              </div>
            </button>
            <span className="text-[0.65rem] text-(--ui-text-tertiary)">🟢 在线</span>
          </header>

          <div className="flex-1 overflow-y-auto">
            {sortedContacts.map(contact => (
              <button
                key={contact.id}
                className={cn(
                  'flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors hover:bg-(--ui-control-hover-background)',
                  activeContactId === contact.id && 'bg-(--ui-control-active-background)'
                )}
                onClick={() => setActiveContactId(contact.id)}
              >
                <div className="relative shrink-0">
                  <div className={cn('flex h-9 w-9 items-center justify-center rounded-full text-xs font-semibold',
                    contact.uid === 0 ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400' : 'bg-(--ui-accent)/15 text-(--ui-accent)')}>
                    {contact.uid === 0 ? '群' : contact.name.charAt(0)}
                  </div>
                  {contact.online && <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-(--ui-bg-surface) bg-emerald-500" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between">
                    <span className="truncate text-sm font-medium text-foreground">{contact.name}</span>
                    {contact.lastTime && <span className="ml-2 shrink-0 text-[0.6rem] text-(--ui-text-tertiary)}">{contact.lastTime}</span>}
                  </div>
                  <div className="mt-0.5 flex items-center justify-between">
                    <span className="truncate text-xs text-(--ui-text-tertiary)}">{contact.lastMessage ?? '暂无消息'}</span>
                    {(contact.unread || 0) > 0 && (
                      <span className="ml-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[0.6rem] font-medium text-destructive-foreground">
                        {contact.unread > 99 ? '99+' : contact.unread}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </ListColumn>

      <DetailColumn>
        {activeContact ? (
          <div className="flex h-full flex-col">
            <header className="flex items-center border-b border-(--ui-stroke-tertiary) px-4 py-2.5">
              <div className="flex items-center gap-2.5">
                <div className={cn('flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold',
                  activeContact.uid === 0 ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400' : 'bg-(--ui-accent)/15 text-(--ui-accent)')}>
                  {activeContact.uid === 0 ? '群' : activeContact.name.charAt(0)}
                </div>
                <div>
                  <div className="text-sm font-medium text-foreground">{activeContact.name}</div>
                  <div className="text-[0.6rem] text-(--ui-text-tertiary)}">
                    {activeContact.online ? '在线' : '离线'}{activeContact.role && ` · ${activeContact.role}`}{activeContact.uid > 0 && ` · #${activeContact.uid}`}
                  </div>
                </div>
              </div>
            </header>
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.map(msg => (
                <div key={msg.id} className={cn('flex', msg.isSelf ? 'justify-end' : 'justify-start')}>
                  <div className={cn('max-w-[70%] rounded-xl px-3 py-2 text-sm',
                    msg.isSelf ? 'bg-(--ui-accent) text-(--ui-accent-foreground) rounded-br-md' : 'bg-(--ui-bg-quaternary) text-foreground rounded-bl-md')}>
                    {!msg.isSelf && <div className="mb-0.5 text-[0.6rem] font-medium text-(--ui-text-tertiary)}">{msg.fromName}</div>}
                    <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                    <div className={cn('mt-1 text-right text-[0.55rem]', msg.isSelf ? 'text-(--ui-accent-foreground)/60' : 'text-(--ui-text-quaternary)')}>{msg.time}</div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="border-t border-(--ui-stroke-tertiary) p-3">
              <div className="flex items-end gap-2">
                <textarea
                  className="min-h-[2.25rem] flex-1 resize-none rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-quaternary) px-3 py-1.5 text-sm text-foreground placeholder:text-(--ui-text-tertiary) focus:border-(--ui-accent) focus:outline-none"
                  onChange={e => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入消息..."
                  rows={1}
                  value={inputText}
                />
                <Button className="shrink-0" disabled={!inputText.trim()} onClick={handleSend} size="sm">
                  <Codicon className="mr-1 size-3.5" name="send" />发送
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid h-full place-items-center">
            <div className="text-center">
              <div className="mb-3 text-3xl">💬</div>
              <p className="text-sm text-(--ui-text-tertiary)">选择一个联系人开始聊天</p>
              <p className="mt-1 text-xs text-(--ui-text-quaternary)}">MIM · WinPeek 多实例消息</p>
            </div>
          </div>
        )}
      </DetailColumn>
    </MasterDetail>
  )
}
