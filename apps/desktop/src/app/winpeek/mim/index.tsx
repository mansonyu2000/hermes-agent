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
  agent_type?: string // persisted — set on creation, never editable
}
interface SavedIdentity extends WinPeekIdentity { agent_type?: string; peeka_name?: string }
interface Contact {
  id: string
  name: string
  uid: number
  role?: string
  title?: string
  bio?: string
  skills?: string
  manager_uid?: number
  identity_type?: string
  gender?: string
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
interface LocalAgent {
  agent_type: string
  name: string
  icon: string
  detected_via: string
  uid: number       // 0 = not registered
  registered: boolean
}

const ROLES = ['Developer', 'Architect', 'Ops', 'QA', 'PM', 'Director', 'Boss'] as const

const AGENT_TYPES = [
  { key: 'claude', name: 'Claude Code', icon: '🟠' },
  { key: 'hermes', name: 'Hermes Agent', icon: '🔵' },
  { key: 'qoder', name: 'Qoder', icon: '🟣' },
  { key: 'traecli', name: 'Trae CLI', icon: '🟢' },
] as const

/* ── Identity Store (localStorage) ───────────── */

const KEY_IDENTITIES = 'mim-identities'
const KEY_ACTIVE_UID = 'mim-active-uid'

/** Migrate old single‑identity format → multi‑identity, then load */
function loadIdentities(): SavedIdentity[] {
  try {
    // 1. If new format exists, use it
    const arr = localStorage.getItem(KEY_IDENTITIES)
    if (arr) return JSON.parse(arr) as SavedIdentity[]

    // 2. Migrate from legacy single key
    const old = localStorage.getItem('mim-identity')
    if (old) {
      const single = JSON.parse(old) as SavedIdentity
      saveIdentities([single])
      localStorage.removeItem('mim-identity')
      return [single]
    }
  } catch { /* corrupt data, start fresh */ }
  return []
}

function saveIdentities(ids: SavedIdentity[]) {
  localStorage.setItem(KEY_IDENTITIES, JSON.stringify(ids))
}

function getActiveUid(): number | null {
  const raw = localStorage.getItem(KEY_ACTIVE_UID)
  if (!raw) return null
  const uid = Number(raw)
  return Number.isFinite(uid) ? uid : null
}

function setActiveUid(uid: number | null) {
  if (uid == null) localStorage.removeItem(KEY_ACTIVE_UID)
  else localStorage.setItem(KEY_ACTIVE_UID, String(uid))
}

/* ── Login / Register Form ───────────────────── */

function LoginPanel({ existingUsers, onLogin, onRegister, onRegisterUser, myDevice }: {
  existingUsers: {uid: number; nickname: string; role: string}[]
  onLogin: (name: string, password: string) => Promise<string | null>
  onRegister: (name: string, role: string, password: string) => Promise<string | null>
  onRefreshUsers: () => void
  onRegisterUser: (name: string, gender: string, password: string) => Promise<string | null>
  myDevice: { hostname: string; device: any; humanUsers: {uid:number;nickname:string;gender:string;role:string}[] } | null
}) {
  const hostnum = Math.floor(Math.random() * 900) + 100
  const defaultNick = myDevice?.hostname ? `${myDevice.hostname}${hostnum}` : `user${hostnum}`
  const [nick, setNick] = useState(defaultNick)
  const [password] = useState('a@123321')
  const [role, setRole] = useState<string>('Developer')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<'begin' | 'newUser' | 'mim'>('begin')
  const [gender, setGender] = useState<string>('male')
  const [, refresh] = useState(0)

  const doMimRegister = useCallback(async () => {
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
          <p className="text-xs text-(--ui-text-tertiary)">
            {step === 'begin' && '欢迎使用 Peeka'}
            {step === 'newUser' && '注册 Peeka User（真人）'}
            {step === 'mim' && '注册本机 MIM 身份'}
          </p>
        </div>
        {error && <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}

        {/* Step 0: 是否已注册 Peeka User？ */}
        {step === 'begin' && (<>
          <p className="text-xs text-(--ui-text-secondary) leading-relaxed">
            Peeka User 是你在整个 Peeka 体系中的真人身份。每台电脑的 MIM Agent 属于一个 Peeka User。
          </p>
          {myDevice?.humanUsers && myDevice.humanUsers.length > 0 ? (
            <div>
              <div className="mb-1 text-[0.65rem] font-medium text-(--ui-text-secondary)">已注册的 Peeka User — 点击选择</div>
              <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-(--ui-stroke-tertiary) p-1">
                {myDevice.humanUsers.map(u => (
                  <button key={u.uid} className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs hover:bg-(--ui-control-hover-background)"
                    onClick={async () => {
                      setLoading(true); setError('')
                      const err = await onLogin(u.nickname, password)
                      if (!err) { setStep('mim'); setNick(defaultNick) }
                      else setError(err)
                      setLoading(false)
                    }}>
                    <span>{u.gender === 'female' ? '🚺' : '🚹'}</span>
                    <span className="font-medium text-foreground">{u.nickname}</span>
                    <span className="ml-auto text-[0.6rem] text-(--ui-text-tertiary)">{u.role}</span>
                  </button>
                ))}
              </div>
              <p className="mt-1 text-center text-[0.6rem] text-(--ui-text-tertiary)">或者</p>
            </div>
          ) : (
            <p className="text-xs text-(--ui-text-tertiary)">你还没有注册过 Peeka User</p>
          )}
          <Button className="w-full" size="sm" onClick={() => { setNick(''); setStep('newUser') }}>
            + 注册新 Peeka User（真人）
          </Button>
        </>)}

        {/* Step 1: 注册新 Peeka User */}
        {step === 'newUser' && (<>
          <Input onChange={e => setNick(e.target.value)} placeholder="名字（如: 于杨敏）" value={nick} />
          <div className="flex gap-2">
            <button className={cn('flex-1 rounded-md px-2 py-1.5 text-xs border transition-colors',
              gender === 'male' ? 'border-(--ui-accent) bg-(--ui-accent)/10 text-foreground' : 'border-(--ui-stroke-tertiary) text-(--ui-text-secondary)')}
              onClick={() => setGender('male')}>🚹 男</button>
            <button className={cn('flex-1 rounded-md px-2 py-1.5 text-xs border transition-colors',
              gender === 'female' ? 'border-(--ui-accent) bg-(--ui-accent)/10 text-foreground' : 'border-(--ui-stroke-tertiary) text-(--ui-text-secondary)')}
              onClick={() => setGender('female')}>🚺 女</button>
          </div>
          <p className="text-[0.6rem] text-(--ui-text-tertiary)">密码: a@123321</p>
          <div className="flex gap-2">
            <Button className="flex-1" size="sm" disabled={loading || !nick.trim()} onClick={async () => {
              setLoading(true); setError('')
              const err = await onRegisterUser(nick.trim(), gender, 'a@123321')
              if (err) setError(err)
              else { setNick(defaultNick); setStep('mim'); refresh(v => v + 1) }
              setLoading(false)
            }}>{loading ? '...' : '注册 Peeka User'}</Button>
            <Button className="flex-1" size="sm" variant="secondary" onClick={() => setStep('begin')}>返回</Button>
          </div>
        </>)}

        {/* Step 2: 注册本机 MIM Agent */}
        {step === 'mim' && (<>
          <p className="text-xs text-(--ui-text-secondary) leading-relaxed">
            为这台电脑注册 MIM 身份。该身份自动绑定到你选择的 Peeka User。
          </p>
          {myDevice && (
            <p className="text-[0.6rem] text-(--ui-text-tertiary)">主机名: {myDevice.hostname}</p>
          )}
          <Input onChange={e => setNick(e.target.value)} onKeyDown={e => e.key === 'Enter' && doMimRegister()}
            placeholder="MIM 用户名" value={nick} />
          <p className="text-[0.6rem] text-(--ui-text-tertiary)">密码: a@123321（自动生成）</p>
          <div className="flex flex-wrap gap-1.5">
            {ROLES.map(r => (
              <button key={r} className={cn('rounded-full px-2.5 py-1 text-xs font-medium transition-colors',
                role === r ? 'bg-(--ui-accent) text-(--ui-accent-foreground)' : 'bg-(--ui-bg-quaternary) text-(--ui-text-secondary) hover:bg-(--ui-control-hover-background)')}
                onClick={() => setRole(r)}>{r}</button>
            ))}
          </div>
          <div className="flex gap-2">
            <Button className="flex-1" disabled={loading || !nick.trim()} onClick={doMimRegister} size="sm">
              {loading ? '注册中...' : '注册 MIM'}
            </Button>
            <Button className="flex-1" size="sm" variant="secondary" onClick={() => setStep('begin')}>返回</Button>
          </div>
        </>)}
      </div>
    </div>
  )
}

/* ── Profile Panel (self + multi‑identity) ──── */

function ProfilePanel({ identities, activeUid, localAgents, serverMode,
  onSwitch, onLogout, onAddAgent, onBack }: {
  identities: SavedIdentity[]
  activeUid: number | null
  localAgents: LocalAgent[]
  serverMode: string
  onSwitch: (uid: number) => void
  onLogout: (uid: number) => void
  onAddAgent: () => void
  onBack?: () => void
}) {
  const identity = identities.find(i => i.uid === activeUid)
  if (!identity) return null
  const skills = identity.skills ? identity.skills.split(',').filter(Boolean) : []

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      {onBack && (
        <button className="text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={onBack}>← 返回</button>
      )}
      {/* Current identity */}
      <div className="text-center">
        <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-(--ui-accent)/15 text-2xl font-bold text-(--ui-accent)">
          {identity.name.charAt(0)}
        </div>
        <h3 className="text-base font-semibold text-foreground">{identity.name}</h3>
        <p className="text-xs text-(--ui-text-tertiary)}">
          {identity.title || identity.role} · #{identity.uid}
          {identity.agent_type && <span className="ml-1">{AGENT_TYPES.find(t => t.key === identity.agent_type)?.icon}</span>}
        </p>
        {identity.peeka_name && (
          <p className="mt-0.5 text-[0.6rem] font-mono text-(--ui-text-quaternary)}">{identity.peeka_name}</p>
        )}
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
      {/* ── Identity switcher ── */}
      {identities.length > 1 && (
        <div className="space-y-1.5 rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs">
          <div className="mb-1 text-(--ui-text-secondary)">切换身份</div>
          {identities.map(id => (
            <button
              key={id.uid}
              className={cn(
                'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors',
                id.uid === activeUid ? 'bg-(--ui-accent)/10' : 'hover:bg-(--ui-control-hover-background)',
              )}
              onClick={() => onSwitch(id.uid)}
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-(--ui-accent)/15 text-[0.55rem] font-semibold text-(--ui-accent)">
                {id.name.charAt(0)}
              </span>
              <span className="font-medium text-foreground">{id.name}</span>
              {id.agent_type && (
                <span className="ml-auto text-[0.7rem]">{AGENT_TYPES.find(t => t.key === id.agent_type)?.icon}</span>
              )}
              {id.uid === activeUid && <span className="text-[0.6rem] text-(--ui-accent)">当前</span>}
            </button>
          ))}
        </div>
      )}
      {/* ── Server mode ── */}
      <div className="space-y-1.5 rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs">
        <div className="flex justify-between"><span className="text-(--ui-text-secondary)">模式</span><span className="font-mono">{serverMode || '—'}</span></div>
        <div className="flex justify-between"><span className="text-(--ui-text-secondary)">消息通知</span><Switch defaultChecked id="mim-notify" /></div>
      </div>
      {/* ── Local agents (runtime) ── */}
      {localAgents.length > 0 && (
        <div className="space-y-1.5 rounded-lg border border-(--ui-stroke-tertiary) p-3 text-xs">
          <div className="mb-1 flex items-center justify-between text-(--ui-text-secondary)">
            <span>本机运行时</span>
            <span className="text-[0.6rem] text-(--ui-text-quaternary)}">by daemon</span>
          </div>
          {localAgents.map(a => {
            const alreadyLogged = identities.some(i => i.uid === a.uid && a.registered)
            return (
              <div key={a.agent_type} className="flex items-center gap-2 py-0.5">
                <span className="text-sm">{a.icon}</span>
                <span className="font-medium text-foreground">{a.name}</span>
                <span className="text-[0.6rem] text-(--ui-text-quaternary)}">{a.detected_via}</span>
                {a.registered ? (
                  alreadyLogged
                    ? <span className="ml-auto text-[0.6rem] text-emerald-500">已登录</span>
                    : <span className="ml-auto text-[0.6rem] text-(--ui-text-tertiary)}">已注册</span>
                ) : (
                  <span className="ml-auto text-[0.6rem] text-amber-500">未注册</span>
                )}
              </div>
            )
          })}
        </div>
      )}
      <div className="space-y-2">
        <Button className="w-full" onClick={onAddAgent} size="xs" variant="secondary">+ 添加智能体</Button>
        <Button className="w-full" onClick={() => onLogout(identity.uid)} size="xs" variant="secondary">退出登录</Button>
      </div>
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

/* ── Two‑step New Agent Panel ───────────────── */

function NewAgentPanel({ onRegister, onBack }: {
  onRegister: (name: string, role: string, password: string, agentType?: string, machine?: string) => Promise<string | null>
  onBack: () => void
}) {
  const [step, setStep] = useState(1)
  const [selectedType, setSelectedType] = useState<string>('')
  const [nick, setNick] = useState('')
  const [role, setRole] = useState<string>('Developer')
  const [password, setPassword] = useState('123321')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = useCallback(async () => {
    if (!nick.trim() || !selectedType) return
    setLoading(true); setError('')
    const err = await onRegister(nick.trim(), role, password, selectedType, '')
    if (err) setError(err)
    setLoading(false)
  }, [nick, role, password, selectedType, onRegister])

  return (
    <div className="grid h-full place-items-center p-6">
      <div className="w-full max-w-xs space-y-4">
        <div className="text-center">
          <div className="mb-2 text-4xl">🤖</div>
          <h2 className="text-lg font-semibold text-foreground">新建智能体</h2>
          <p className="text-xs text-(--ui-text-tertiary)}">{step === 1 ? '选择智能体类型' : '输入智能体信息'}</p>
        </div>
        {error && <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}

        {step === 1 ? (
          <div className="grid grid-cols-2 gap-2">
            {AGENT_TYPES.map(at => (
              <button
                key={at.key}
                className={cn(
                  'flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center transition-colors',
                  selectedType === at.key
                    ? 'border-(--ui-accent) bg-(--ui-accent)/10'
                    : 'border-(--ui-stroke-tertiary) hover:bg-(--ui-control-hover-background)'
                )}
                onClick={() => { setSelectedType(at.key); setStep(2); setNick('') }}
              >
                <span className="text-2xl">{at.icon}</span>
                <span className="text-xs font-medium text-foreground">{at.name}</span>
              </button>
            ))}
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 rounded-md bg-(--ui-bg-quaternary) px-3 py-2">
              <span className="text-lg">{AGENT_TYPES.find(t => t.key === selectedType)?.icon}</span>
              <span className="text-sm font-medium text-foreground">{AGENT_TYPES.find(t => t.key === selectedType)?.name}</span>
              <button className="ml-auto text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={() => setStep(1)}>切换</button>
            </div>
            <Input
              autoFocus
              onChange={e => setNick(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              placeholder="智能体名称（如 yu2-claude-1）"
              value={nick}
            />
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
            <Input
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              placeholder="密码"
              type="password"
              value={password}
            />
            <Button className="w-full" disabled={loading || !nick.trim()} onClick={handleSubmit} size="sm">
              {loading ? '创建中...' : '创建智能体'}
            </Button>
          </>
        )}
        <button className="w-full text-center text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={onBack}>
          ← 返回登录
        </button>
      </div>
    </div>
  )
}

/* ── Main View ───────────────────────────────── */

export function MimView({ onClose }: { onClose: () => void }) {
  const { t } = useI18n()
  const { requestGateway: gatewayRequest } = useGatewayRequest()

  /* ── Multi‑identity state ──────────────── */
  const [identities, setIdentities] = useState<SavedIdentity[]>(loadIdentities)
  const [activeUid, setActiveUidState] = useState<number | null>(getActiveUid)
  // Derive active identity (memo stable unless identities or activeUid change)
  const identity = useMemo(
    () => identities.find(i => i.uid === activeUid) ?? null,
    [identities, activeUid],
  )
  const identRef = useRef<WinPeekIdentity | null>(identity)
  identRef.current = identity

  const [showProfile, setShowProfile] = useState(false)
  const [viewContactUid, setViewContactUid] = useState<number | null>(null)
  const [showNewAgent, setShowNewAgent] = useState(false)
  const [localAgents, setLocalAgents] = useState<LocalAgent[]>([])
  const [serverMode, setServerMode] = useState<string>('')

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
  const activeContactRef = useRef<Contact | null>(null)

  const refreshUsers = useCallback(() => {
    gatewayRequest<any>('winpeek_mim_contacts', identity ? { uid: identity.uid } : {}).then(data => {
      if (data.contacts) {
        setExistingUsers(data.contacts.filter((c: any) => c.uid > 0))
      }
    }).catch(() => {})
  }, [gatewayRequest, identity])

  // ── Load existing users for login page ──
  useEffect(() => { refreshUsers() }, [refreshUsers])

  // ── Load local agents + mode ──
  useEffect(() => {
    gatewayRequest<any>('winpeek_mim_local_agents', {}).then(data => {
      if (data) {
        if (data.mode) setServerMode(data.mode)
        if (data.agents) {
          setLocalAgents(data.agents.map((a: any) => ({
            agent_type: a.agent_type,
            name: a.name || a.agent_type,
            icon: AGENT_TYPES.find(t => t.key === a.agent_type)?.icon || '🤖',
            detected_via: a.detected_via || '',
            uid: a.uid || 0,
            registered: a.registered || false,
          })))
        }
      }
    }).catch(() => {})
  }, [gatewayRequest])

  const activeContact = useMemo(
    () => contacts.find(c => c.id === activeContactId) ?? null,
    [contacts, activeContactId]
  )
  activeContactRef.current = activeContact

  // ── Persist active uid when it changes ──
  // ── Device detection ──
  const [myDevice, setMyDevice] = useState<{ hostname: string; device: any; humanUsers: any[] } | null>(null)

  // Detect device on mount
  useEffect(() => {
    gatewayRequest<any>('winpeek_mim_my_device', {}).then(data => {
      if (data) setMyDevice(data)
    }).catch(() => {})
  }, [gatewayRequest])

  const switchToIdentity = useCallback((uid: number) => {
    setActiveUidState(uid)
    setActiveUid(uid)
    setActiveContactId(null)
    setMessages([])
  }, [])

  const handleLogin = useCallback(async (name: string, password: string, agentType?: string, machine?: string): Promise<string | null> => {
    try {
      const params: any = { nickname: name, password }
      if (agentType) params.agent_type = agentType
      if (machine) params.machine = machine
      const data: any = await gatewayRequest('winpeek_mim_login', params)
      if (data.ok && data.identity) {
        const id: SavedIdentity = {
          uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role,
          host: machine || 'local', agent_type: agentType,
          peeka_name: data.identity.peeka_name || '',
        }
        setIdentities(prev => {
          // If this uid already exists (e.g. re‑login), replace
          const filtered = prev.filter(i => i.uid !== id.uid)
          const next = [...filtered, id]
          saveIdentities(next)
          return next
        })
        setActiveUidState(id.uid)
        setActiveUid(id.uid)
        refreshUsers()
        return null
      }
      return data.error || '登录失败，请检查用户名和密码'
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return `无法连接到网关: ${msg}`
    }
  }, [gatewayRequest, refreshUsers])

  const handleRegister = useCallback(async (name: string, role: string, password: string, agentType?: string, machine?: string): Promise<string | null> => {
    try {
      const params: any = { nickname: name, role, password }
      if (agentType) params.agent_type = agentType
      if (machine) params.machine = machine
      const data: any = await gatewayRequest('winpeek_mim_login', params)
      if (data.ok && data.identity) {
        const id: SavedIdentity = {
          uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role,
          host: machine || 'local', agent_type: agentType,
          peeka_name: data.identity.peeka_name || '',
        }
        setIdentities(prev => {
          const filtered = prev.filter(i => i.uid !== id.uid)
          const next = [...filtered, id]
          saveIdentities(next)
          return next
        })
        setActiveUidState(id.uid)
        setActiveUid(id.uid)
        refreshUsers()
        return null
      }
      return data.error || '注册失败，请重试'
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return `无法连接到网关: ${msg}`
    }
  }, [gatewayRequest, refreshUsers])

  const handleRegisterUser = useCallback(async (name: string, gender: string, password: string): Promise<string | null> => {
    try {
      const data: any = await gatewayRequest('winpeek_mim_user_register', { name, gender, password })
      if (data.ok && data.identity) {
        const id: SavedIdentity = {
          uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role,
          host: 'local',
        }
        setIdentities(prev => {
          const filtered = prev.filter(i => i.uid !== id.uid)
          const next = [...filtered, id]
          saveIdentities(next)
          return next
        })
        setActiveUidState(id.uid)
        setActiveUid(id.uid)
        refreshUsers()
        return null
      }
      return data.error || '注册失败'
    } catch (e) {
      return `无法连接到网关: ${e instanceof Error ? e.message : String(e)}`
    }
  }, [gatewayRequest, refreshUsers])

  const handleLogout = useCallback((uid?: number) => {
    const targetUid = uid ?? activeUid
    setIdentities(prev => {
      const next = prev.filter(i => i.uid !== targetUid)
      saveIdentities(next)
      return next
    })
    if (targetUid === activeUid) {
      // Switch to the first remaining identity, or clear
      const remaining = identities.filter(i => i.uid !== targetUid)
      if (remaining.length > 0) {
        switchToIdentity(remaining[0].uid)
      } else {
        setActiveUidState(null)
        setActiveUid(null)
        setActiveContactId(null)
        setMessages([])
      }
    }
  }, [activeUid, identities, switchToIdentity])

  // ── Reset if active uid disappeared ──
  useEffect(() => {
    if (activeUid === null && identities.length > 0) {
      setActiveUidState(identities[0].uid)
      setActiveUid(identities[0].uid)
    }
  }, [activeUid, identities])

  // ── Load contacts via winpeek_mim_contacts ──
  useEffect(() => {
    if (!identity) return
    gatewayRequest<any>('winpeek_mim_contacts', { uid: identity.uid }).then(data => {
      if (data.contacts) {
        setContacts(data.contacts.map((c: any) => ({
          id: String(c.uid),
          name: c.nickname,
          uid: c.uid,
          role: c.role,
          online: c.online !== false,
          lastMessage: c.last_message || '',
          lastTime: c.last_msg_ts || '',
          unread: c.unread_count || 0,
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

  // ── Not logged in (identities may exist but none is active) ──
  if (!identity) {
    if (showNewAgent) {
      return (
        <MasterDetail>
          <NewAgentPanel onRegister={handleRegister} onBack={() => setShowNewAgent(false)} />
        </MasterDetail>
      )
    }
    return (
      <MasterDetail>
        <LoginPanel existingUsers={existingUsers} onLogin={handleLogin} onRefreshUsers={refreshUsers} onRegister={handleRegister} onRegisterUser={handleRegisterUser} myDevice={myDevice} />
      </MasterDetail>
    )
  }

  // ── New agent creation ──
  if (showNewAgent) {
    return (
      <MasterDetail>
        <NewAgentPanel onRegister={handleRegister} onBack={() => setShowNewAgent(false)} />
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
        <ProfilePanel
          identities={identities} activeUid={activeUid}
          localAgents={localAgents} serverMode={serverMode}
          onSwitch={switchToIdentity} onLogout={handleLogout}
          onAddAgent={() => setShowNewAgent(true)}
          onBack={() => setShowProfile(false)}
        />
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
                      {contact.lastTime && <span className="text-[0.6rem] text-(--ui-text-tertiary)">{formatMessageTimestamp(contact.lastTime, t.assistant.thread)}</span>}
                    </div>
                  </div>
                  <div className="mt-0.5 flex items-center justify-between">
                    {contact.lastMessage && (
                      <span className="truncate text-xs text-(--ui-text-tertiary)}">
                        {contact.lastMessage.slice(0, 30)}{contact.lastMessage.length > 30 ? '...' : ''}
                      </span>
                    )}
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
                      <div className="ml-auto text-[0.65rem] text-(--ui-text-quaternary)">{serverMode === 'center' ? 'MIM Center' : serverMode === 'client' ? 'MIM Client' : 'MIM'} {ttsEnabled && '🔊'}</div>
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
            </div>
          </div>
        )}
      </DetailColumn>
    </MasterDetail>
  )
}
