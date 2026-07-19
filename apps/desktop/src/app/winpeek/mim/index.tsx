import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Streamdown } from 'streamdown'

import { formatMessageTimestamp } from '@/components/assistant-ui/thread/timestamp'
import { CopyButton } from '@/components/ui/copy-button'
import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { useI18n } from '@/i18n'
import { cn } from '@/lib/utils'
import { notifyError } from '@/store/notifications'

import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'
import { DetailColumn, ListColumn, MasterDetail } from '../../master-detail'

/* ── Types ───────────────────────────────────── */

interface WinPeekIdentity {
  uid: number
  name: string
  role: string
  host: string
  title?: string
  bio?: string
  skills?: string
  manager_uid?: number
}
interface Contact {
  id: string
  name: string
  uid: number
  role?: string
  title?: string
  bio?: string
  skills?: string
  manager_uid?: number
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
  msgTs?: string
  isSelf: boolean
}

const ROLES = ['Developer', 'Architect', 'Ops', 'QA', 'PM', 'Director', 'Boss'] as const

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

/* ── Login / Register Form ───────────────────── */

function LoginPanel({ existingUsers, onLogin, onRegister }: {
  existingUsers: {uid: number; nickname: string; role: string}[]
  onLogin: (name: string, password: string) => Promise<string | null>
  onRegister: (name: string, role: string, password: string) => Promise<string | null>
  onRefreshUsers: () => void
}) {
  const [nick, setNick] = useState('')
  const [password, setPassword] = useState('123321')
  const [showRegister, setShowRegister] = useState(false)
  const [role, setRole] = useState<string>('Developer')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = useCallback(async () => {
    if (!nick.trim()) { return }
    setLoading(true); setError('')
    const err = await onLogin(nick.trim(), password)
    if (err) setError(err)
    setLoading(false)
  }, [nick, password, onLogin])

  const handleRegister = useCallback(async () => {
    if (!nick.trim()) { return }
    setLoading(true); setError('')
    const err = await onRegister(nick.trim(), role, password)
    if (err) setError(err)
    setLoading(false)
  }, [nick, role, password, onRegister])

  return (
    <div className="grid h-full place-items-center p-6">
      <div className="w-full max-w-xs space-y-4">
        <div className="text-center">
          <div className="mb-2 text-4xl">💬</div>
          <h2 className="text-lg font-semibold text-foreground">WinPeek MIM</h2>
          <p className="text-xs text-(--ui-text-tertiary)">登录或注册以使用消息功能</p>
        </div>
        {error && <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}
        {/* Existing users — quick select */}
        {existingUsers.length > 0 && !showRegister && (
          <div>
            <div className="mb-1.5 text-[0.65rem] font-medium text-(--ui-text-secondary)">已有用户</div>
            <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-(--ui-stroke-tertiary) p-1">
              {existingUsers.map(u => (
                <button
                  key={u.uid}
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs hover:bg-(--ui-control-hover-background)"
                  onClick={async () => { setNick(u.nickname); setLoading(true); setError(''); const e = await onLogin(u.nickname, password); if (e) setError(e); setLoading(false) }}
                >
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-(--ui-accent)/15 text-[0.55rem] font-semibold text-(--ui-accent)">
                    {u.nickname.charAt(0)}
                  </span>
                  <span className="font-medium text-foreground">{u.nickname}</span>
                  <span className="ml-auto text-[0.6rem] text-(--ui-text-tertiary)">{u.role}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        <Input
          onChange={e => setNick(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !showRegister && handleLogin()}
          placeholder="用户名"
          value={nick}
        />
        <Input
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !showRegister && handleLogin()}
          placeholder="密码"
          type="password"
          value={password}
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

/* ── Profile Panel (self) ────────────────────── */

function ProfilePanel({ identity, onLogout, onBack }: { identity: WinPeekIdentity; onLogout: () => void; onBack?: () => void }) {
  const skills = identity.skills ? identity.skills.split(',').filter(Boolean) : []
  return (
    <div className="p-4 space-y-4">
      {onBack && (
        <button className="text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={onBack}>← 返回</button>
      )}
      <div className="text-center">
        <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-(--ui-accent)/15 text-2xl font-bold text-(--ui-accent)">
          {identity.name.charAt(0)}
        </div>
        <h3 className="text-base font-semibold text-foreground">{identity.name}</h3>
        <p className="text-xs text-(--ui-text-tertiary)">{identity.title || identity.role} · #{identity.uid}</p>
      </div>
      <div className="space-y-2 rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs">
        <div className="flex justify-between"><span className="text-(--ui-text-secondary)">角色</span><span>{identity.role}</span></div>
        {identity.title && <div className="flex justify-between"><span className="text-(--ui-text-secondary)">职位</span><span>{identity.title}</span></div>}
        {identity.bio && <div><div className="mb-1 text-(--ui-text-secondary)">简介</div><div className="text-foreground leading-relaxed">{identity.bio}</div></div>}
        {skills.length > 0 && (
          <div>
            <div className="mb-1 text-(--ui-text-secondary)">技能</div>
            <div className="flex flex-wrap gap-1">{skills.map(s => <span key={s} className="rounded-full bg-(--ui-accent)/10 px-2 py-0.5 text-[0.6rem] text-(--ui-accent)">{s}</span>)}</div>
          </div>
        )}
      </div>
      <div className="space-y-1.5 rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs">
        <div className="flex justify-between"><span className="text-(--ui-text-secondary)">MQTT Broker</span><span className="font-mono">192.168.3.23:1883</span></div>
        <div className="flex justify-between"><span className="text-(--ui-text-secondary)">WinPeek Hub</span><span className="font-mono">127.0.0.1:9200</span></div>
        <div className="flex items-center justify-between"><span className="text-(--ui-text-secondary)">消息通知</span><Switch defaultChecked id="mim-notify" /></div>
      </div>
      <Button className="w-full" onClick={onLogout} size="xs" variant="secondary">退出登录</Button>
    </div>
  )
}


/* ── Contact Profile Panel (view others) ─────── */

function ContactProfilePanel({ uid, gatewayRequest, onBack }: { uid: number; gatewayRequest: (method: string, params: any) => Promise<any>; onBack: () => void }) {
  const [user, setUser] = useState<WinPeekIdentity | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    gatewayRequest('winpeek_mim_user_info', { uid }).then((data: any) => {
      if (data?.user) {
        setUser({
          uid: data.user.uid,
          name: data.user.nickname,
          role: data.user.role || '',
          host: data.user.host || '',
          title: data.user.title,
          bio: data.user.bio,
          skills: data.user.skills,
          manager_uid: data.user.manager_uid,
        })
      }
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [uid, gatewayRequest])

  if (loading) return <div className="grid h-full place-items-center"><p className="text-xs text-(--ui-text-tertiary)">加载中...</p></div>
  if (!user) return <div className="grid h-full place-items-center"><p className="text-xs text-(--ui-text-tertiary)">用户不存在</p></div>

  const skills = user.skills ? user.skills.split(',').filter(Boolean) : []
  return (
    <div className="p-4 space-y-4">
      <button className="text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={onBack}>← 返回聊天</button>
      <div className="text-center">
        <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-(--ui-accent)/15 text-2xl font-bold text-(--ui-accent)">
          {user.name.charAt(0)}
        </div>
        <h3 className="text-base font-semibold text-foreground">{user.name}</h3>
        <p className="text-xs text-(--ui-text-tertiary)">{user.title || user.role} · #{user.uid}</p>
      </div>
      <div className="space-y-2 rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs">
        <div className="flex justify-between"><span className="text-(--ui-text-secondary)">角色</span><span>{user.role}</span></div>
        {user.title && <div className="flex justify-between"><span className="text-(--ui-text-secondary)">职位</span><span>{user.title}</span></div>}
        {user.bio && <div><div className="mb-1 text-(--ui-text-secondary)">简介</div><div className="text-foreground leading-relaxed">{user.bio}</div></div>}
        {skills.length > 0 && (
          <div>
            <div className="mb-1 text-(--ui-text-secondary)">技能</div>
            <div className="flex flex-wrap gap-1">{skills.map(s => <span key={s} className="rounded-full bg-(--ui-accent)/10 px-2 py-0.5 text-[0.6rem] text-(--ui-accent)">{s}</span>)}</div>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Main View ───────────────────────────────── */

export function MimView({ onClose }: { onClose: () => void }) {
  const { t } = useI18n()
  const { requestGateway: gatewayRequest } = useGatewayRequest()
  const [identity, setIdentity] = useState<WinPeekIdentity | null>(loadSavedIdentity)
  const [showProfile, setShowProfile] = useState(false)
  const [viewContactUid, setViewContactUid] = useState<number | null>(null)

  const [contacts, setContacts] = useState<Contact[]>([])
  const [existingUsers, setExistingUsers] = useState<{uid: number; nickname: string; role: string}[]>([])
  const [activeContactId, setActiveContactId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatListRef = useRef<HTMLDivElement>(null)
  const [userScrolledUp, setUserScrolledUp] = useState(false)
  const [isComposing, setIsComposing] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const prevMessagesLen = useRef(messages.length)
  const identRef = useRef<WinPeekIdentity | null>(identity)
  identRef.current = identity
  const activeContactRef = useRef<Contact | null>(null)

  const refreshUsers = useCallback(() => {
    gatewayRequest<any>('winpeek_mim_contacts', {}).then(data => {
      if (data.contacts) {
        setExistingUsers(data.contacts.filter((c: any) => c.uid > 0))
      }
    }).catch(() => {})
  }, [gatewayRequest])

  // ── Load existing users for login page ──
  useEffect(() => { refreshUsers() }, [refreshUsers])

  const activeContact = useMemo(
    () => contacts.find(c => c.id === activeContactId) ?? null,
    [contacts, activeContactId]
  )
  activeContactRef.current = activeContact

  const handleLogin = useCallback(async (name: string, password: string): Promise<string | null> => {
    try {
      const data: any = await gatewayRequest('winpeek_mim_login', { nickname: name, password })
      if (data.ok && data.identity) {
        const id: WinPeekIdentity = { uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role, host: 'local' }
        saveIdentity(id)
        setIdentity(id)
        refreshUsers()
        return null
      }
      return data.error || '登录失败，请检查用户名和密码'
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return `无法连接到网关: ${msg}`
    }
  }, [gatewayRequest, refreshUsers])

  const handleRegister = useCallback(async (name: string, role: string, password: string): Promise<string | null> => {
    try {
      const data: any = await gatewayRequest('winpeek_mim_login', { nickname: name, role, password })
      if (data.ok && data.identity) {
        const id: WinPeekIdentity = { uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role, host: 'local' }
        saveIdentity(id)
        setIdentity(id)
        refreshUsers()
        return null
      }
      return data.error || '注册失败，请重试'
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return `无法连接到网关: ${msg}`
    }
  }, [gatewayRequest, refreshUsers])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('mim-identity')
    setIdentity(null)
    setActiveContactId(null)
    setMessages([])
  }, [])

  // ── Load contacts via winpeek_mim_contacts ──
  useEffect(() => {
    if (!identity) return
    gatewayRequest<any>('winpeek_mim_contacts', {}).then(data => {
      if (data.contacts) {
        setContacts(data.contacts.map((c: any) => ({
          id: String(c.uid),
          name: c.nickname,
          uid: c.uid,
          role: c.role,
          online: c.online !== false,
          lastMessage: '',
          unread: 0,
        })))
      }
    }).catch(() => {})
  }, [identity, gatewayRequest])

  // ── Load chat history when contact selected ──
  useEffect(() => {
    if (!activeContact || !identity) { setMessages([]); return }
    let cancelled = false
    setMessages([])
    gatewayRequest<any>('winpeek_mim_history', { peer_uid: activeContact.uid, uid: identity.uid, limit: 50 })
      .then(data => {
        if (cancelled || !data?.messages) return
        setMessages(data.messages.map((m: any, i: number) => ({
          id: `h-${i}-${m.msg_ts ?? ''}`,
          fromUid: m.from_uid,
          fromName: m.from_uid === identity.uid ? identity.name : (m.from_name || activeContact.name),
          content: m.content,
          msgTs: m.msg_ts || undefined,
          time: (m.msg_ts || '').slice(11, 16),
          isSelf: m.from_uid === identity.uid,
        })))
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [activeContact, identity, gatewayRequest])

  // ── Poll for new messages every 3s ──
  useEffect(() => {
    if (!identity) return
    const interval = setInterval(() => {
      gatewayRequest<any>('winpeek_mim_poll', { uid: identity.uid }).then(data => {
        if (data.messages?.length > 0) {
          // Only surface messages from the peer currently on screen — other
          // conversations reload from history (DB) when opened, nothing is lost.
          const peer = activeContactRef.current
          const relevant = data.messages.filter((m: any) =>
            peer && String(m.from_uid) === String(peer.uid) && String(m.from_uid) !== String(identity.uid))
          if (relevant.length === 0) return
          setMessages(prev => [...prev, ...relevant.map((m: any) => ({
            id: `m-${Date.now()}-${Math.random()}`,
            fromUid: m.from_uid,
            fromName: m.from_name,
            content: m.content,
            msgTs: m.time || undefined,
            time: m.time?.slice(11, 16) || '',
            isSelf: false,
          }))])
        }
      }).catch(() => {})
    }, 3000)
    return () => clearInterval(interval)
  }, [identity, gatewayRequest])

  // ── Auto-scroll: follows new messages unless user has scrolled up ──
  useEffect(() => {
    if (!userScrolledUp) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, userScrolledUp])

  const handleChatScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget
    const d = el.scrollHeight - el.scrollTop - el.clientHeight
    setUserScrolledUp(d > 60)
  }, [])

  const scrollToBottom = useCallback(() => {
    setUserScrolledUp(false)
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // ── File picker ──────────────────────────────────────────
  const handleFilePick = useCallback(() => fileInputRef.current?.click(), [])
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const text = reader.result as string
      setInputText(prev => prev ? prev + '\n' + text : text)
      textareaRef.current?.focus()
    }
    reader.readAsText(file)
    e.target.value = '' // reset so same file can be picked again
  }, [])
  // ── TTS: auto-read incoming messages ─────────────────────
  useEffect(() => {
    if (!ttsEnabled) return
    const newMsgs = messages.slice(prevMessagesLen.current)
    prevMessagesLen.current = messages.length
    for (const m of newMsgs) {
      if (!m.isSelf && m.content) {
        const u = new SpeechSynthesisUtterance(m.content.replace(/\*\*|```[\s\S]*?```|`/g, '').slice(0, 500))
        u.lang = 'zh-CN'; u.rate = 1.1
        speechSynthesis.cancel(); speechSynthesis.speak(u)
      }
    }
  }, [messages, ttsEnabled])
  // ── Auto-resize textarea ──────────────────────────────────
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [inputText])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || !activeContact || !identity) return
    try {
      await gatewayRequest('winpeek_mim_send', {
        to_uid: activeContact.uid, body: text,
        uid: identity.uid, from_name: identity.name,
      })
      // Optimistic: add locally
      setMessages(prev => [...prev, {
        id: `msg-${Date.now()}`, fromUid: identity.uid, fromName: identity.name,
        content: text,
        msgTs: new Date().toISOString(),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        isSelf: true,
      }])
    } catch (e) {
      notifyError(e, '消息发送失败，请检查网络连接')
    }
    setInputText('')
  }, [inputText, activeContact, identity, gatewayRequest])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) { e.preventDefault(); handleSend() }
  }, [handleSend, isComposing])

  // ── Not logged in ──
  if (!identity) {
    return (
      <MasterDetail>
        <LoginPanel existingUsers={existingUsers} onLogin={handleLogin} onRefreshUsers={refreshUsers} onRegister={handleRegister} />
      </MasterDetail>
    )
  }

  // ── View contact profile ──
  if (viewContactUid) {
    return (
      <MasterDetail>
        <ContactProfilePanel uid={viewContactUid} gatewayRequest={gatewayRequest} onBack={() => setViewContactUid(null)} />
      </MasterDetail>
    )
  }

  // ── Profile view ──
  if (showProfile) {
    return (
      <MasterDetail>
        <ProfilePanel identity={identity} onLogout={handleLogout} onBack={() => setShowProfile(false)} />
      </MasterDetail>
    )
  }

  // ── Chat view ──
  const sortedContacts = [...contacts].sort((a, b) => {
    // online first, then by unread, then by name
    if (a.online !== b.online) return a.online ? -1 : 1
    if (a.unread !== b.unread) return (b.unread || 0) - (a.unread || 0)
    return a.name.localeCompare(b.name)
  })

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
              <div
                key={contact.id}
                className={cn(
                  'flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors hover:bg-(--ui-control-hover-background) cursor-pointer',
                  activeContactId === contact.id && 'bg-(--ui-control-active-background)'
                )}
                onClick={() => setActiveContactId(contact.id)}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setActiveContactId(contact.id) }}}
                role="button"
                tabIndex={0}
              >
                <div className={cn('relative shrink-0', !contact.online && 'opacity-60')}>
                  <div className={cn('flex h-9 w-9 items-center justify-center rounded-full text-xs font-semibold',
                    contact.uid === 0 ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400' : 'bg-(--ui-accent)/15 text-(--ui-accent)')}>
                    {contact.uid === 0 ? '群' : contact.name.charAt(0)}
                  </div>
                  <span className={cn(
                    'absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-(--ui-bg-surface)',
                    contact.online ? 'bg-emerald-500' : 'bg-gray-400'
                  )} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between">
                    <span className={cn('truncate text-sm font-medium', contact.online ? 'text-foreground' : 'text-(--ui-text-quaternary)')}>{contact.name}</span>
                    <div className="flex items-center gap-1 shrink-0">
                      {contact.uid !== identity?.uid && (
                        <button
                          className="text-[0.55rem] text-(--ui-text-quaternary) hover:text-(--ui-accent) px-1"
                          onClick={e => { e.stopPropagation(); setViewContactUid(contact.uid) }}
                          title="查看资料"
                        >ℹ</button>
                      )}
                      {contact.lastTime && <span className="text-[0.6rem] text-(--ui-text-tertiary)">{contact.lastTime}</span>}
                    </div>
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
              </div>
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
            <div className="flex-1 space-y-3 overflow-y-auto p-4" onScroll={handleChatScroll} ref={chatListRef}>
              {messages.map(msg => (
                <div key={msg.id} className={cn('group/cell flex', msg.isSelf ? 'justify-end' : 'justify-start')}>
                  <div
                    className={cn('max-w-[70%] rounded-2xl px-3 py-2 text-sm',
                      msg.isSelf
                        ? 'bg-(--dt-user-bubble) text-foreground border border-border/50'
                        : 'bg-(--ui-bg-quaternary) text-foreground')}
                  >
                    {!msg.isSelf && <div className="mb-0.5 text-[0.6rem] font-medium text-(--ui-text-tertiary)}">{msg.fromName}</div>}
                    <div className="[&_pre]:overflow-x-auto [&_pre]:rounded [&_pre]:bg-black/10 [&_pre]:p-2 [&_pre]:text-[0.75rem] [&_code]:rounded [&_code]:bg-black/10 [&_code]:px-1 [&_code]:text-[0.8em] [&_p]:mb-1 [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4">
                      <Streamdown>{msg.content}</Streamdown>
                    </div>
                    <div className="mt-1 flex items-center justify-end gap-1 text-[0.55rem] text-(--ui-text-quaternary)">
                      <CopyButton appearance="icon" className="size-3.5" text={msg.content} />
                      <span>{formatMessageTimestamp(msg.msgTs || msg.time, t.assistant.thread)}</span>
                    </div>
                  </div>
                </div>
              ))}
              {userScrolledUp && (
                <div className="sticky bottom-0 flex justify-center pb-1">
                  <button
                    className="rounded-full border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-3 py-1 text-xs text-(--ui-text-secondary) shadow-sm hover:bg-(--ui-control-hover-background)"
                    onClick={scrollToBottom}
                  >↓ 最新消息</button>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            {/* ── Composer: Hermes-native glass dock with controls ── */}
            <div className="relative px-(--composer-surface-pad-x,1rem) pb-[var(--composer-shell-pad-block-end,0.75rem)] pt-2">
              <div className="group/composer z-30 overflow-visible rounded-2xl" data-slot="composer-root">
                <div className="data-[slot=composer-surface]:border data-[slot=composer-surface]:border-border/65 relative rounded-2xl" data-slot="composer-surface">
                  <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 rounded-[inherit] bg-(--composer-fill,var(--ui-bg-surface)) backdrop-blur-[0.75rem] backdrop-saturate-[1.12]" />
                  <div className="relative z-1 flex min-h-0 w-full flex-col gap-(--composer-row-gap,0.375rem) overflow-hidden rounded-[inherit] px-(--composer-surface-pad-x,0.75rem) py-(--composer-surface-pad-y,0.625rem) transition-opacity duration-200 ease-out opacity-100" data-slot="composer-fade">
                    {/* Control buttons: [+] [Mic] [Speaker] */}
                    <div className="flex items-center gap-(--composer-control-gap,0.25rem)">
                      <input ref={fileInputRef} accept=".txt,.md,.json,.py,.js,.ts,.tsx,.css,.html,.yaml,.yml,.log,.csv" className="hidden" onChange={handleFileChange} type="file" />
                      <button
                        aria-label="附件"
                        className="size-(--composer-control-size,1.75rem) shrink-0 rounded-md text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground grid place-items-center"
                        onClick={handleFilePick}
                        title="选择文件发送"
                        type="button"
                      ><Codicon name="add" size={14} /></button>
                      <button
                        aria-label="语音输入"
                        className="size-(--composer-control-size,1.75rem) shrink-0 rounded-md text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground grid place-items-center opacity-40 cursor-not-allowed"
                        title="语音输入 (需要 MediaRecorder 支持)"
                        disabled
                        type="button"
                      ><Codicon name="mic" size={14} /></button>
                      <button
                        aria-label={ttsEnabled ? '关闭朗读' : '朗读消息'}
                        aria-pressed={ttsEnabled}
                        className="size-(--composer-control-size,1.75rem) shrink-0 rounded-md text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground grid place-items-center aria-pressed:text-(--ui-accent) aria-pressed:bg-(--ui-accent)/10"
                        onClick={() => { setTtsEnabled(v => !v); prevMessagesLen.current = messages.length }}
                        title={ttsEnabled ? '关闭朗读收到的新消息' : '自动朗读收到的新消息'}
                        type="button"
                      ><Codicon name="megaphone" size={14} /></button>
                      <div className="ml-auto text-[0.65rem] text-(--ui-text-quaternary)">MIM {ttsEnabled && '🔊'}</div>
                    </div>
                    {/* Input row: textarea + send button */}
                    <div className="grid w-full grid-cols-[1fr_auto] items-end gap-(--composer-control-gap,0.375rem) [grid-template-areas:'input_controls']">
                      <div className="min-w-0 [grid-area:input]">
                        <textarea
                          ref={textareaRef}
                          autoCapitalize="off"
                          autoCorrect="off"
                          className="min-h-[--composer-input-min-height,2rem] max-h-[--composer-input-max-height,10rem] w-full cursor-text resize-none overflow-y-auto whitespace-pre-wrap break-words bg-transparent pb-1 pt-1 leading-normal text-foreground outline-none placeholder:text-muted-foreground/60"
                          onChange={e => setInputText(e.target.value)}
                          onCompositionEnd={() => setIsComposing(false)}
                          onCompositionStart={() => setIsComposing(true)}
                          onKeyDown={handleKeyDown}
                          placeholder="输入消息..."
                          rows={1}
                          value={inputText}
                        />
                      </div>
                      <div className="flex items-center justify-end [grid-area:controls]">
                        <button
                          aria-label="发送"
                          className={cn(
                            'size-(--composer-control-primary-size,2rem) shrink-0 rounded-full p-0 transition-colors',
                            inputText.trim()
                              ? 'bg-foreground text-background hover:bg-foreground/90'
                              : 'bg-foreground/30 text-background cursor-not-allowed opacity-100'
                          )}
                          disabled={!inputText.trim()}
                          onClick={handleSend}
                          type="button"
                        >
                          <Codicon name="arrow-up" size="0.875rem" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
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
