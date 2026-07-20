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
import { ApprovalPanel, RegistrationWizard } from '../register'

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
  isGroup?: boolean
  gid?: number
  memberCount?: number
}
interface GroupRow {
  gid: number
  title: string
  description: string
  owner_uid: number
  member_count: number
  last_message: string
  last_time: string
  created_at: string
}
interface GroupDetail {
  gid: number
  title: string
  description: string
  owner_id: string
  admins: number[]
  metadata?: string
  status: number
  announcements: { id: string; text: string; created_by: number; created_at: string }[]
  members: { uid: number; nickname: string; user_role: string; participant_type: string; joined_at: string }[]
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
  const { requestGateway: rq } = useGatewayRequest()
  const [squad, setSquad] = useState<any>(null)
  const skills = identity.skills ? identity.skills.split(',').filter(Boolean) : []

  useEffect(() => {
    rq('winpeek_org_status', {}).then((d: any) => {
      if (d?.linked && d?.squad) setSquad(d.squad)
    }).catch(() => {})
  }, [rq])

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
      {/* Organization card */}
      {squad && (
        <div className="rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-3">
          <div className="mb-2 text-[0.6rem] font-medium text-(--ui-text-quaternary) uppercase">组织</div>
          <div className="text-sm font-semibold text-foreground">{squad.name}</div>
          {squad.description && <div className="mt-0.5 text-xs text-(--ui-text-tertiary)">{squad.description}</div>}
          <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            {squad.industry && <div><span className="text-(--ui-text-quaternary)">行业</span> <span>{squad.industry}</span></div>}
            {squad.address && <div><span className="text-(--ui-text-quaternary)">地址</span> <span>{squad.address}</span></div>}
            {squad.legal_person && <div><span className="text-(--ui-text-quaternary)">法人</span> <span>{squad.legal_person}</span></div>}
            {squad.contact_phone && <div><span className="text-(--ui-text-quaternary)">电话</span> <span>{squad.contact_phone}</span></div>}
            {squad.website && <div><span className="text-(--ui-text-quaternary)">网站</span> <span className="truncate">{squad.website}</span></div>}
            {squad.contact_email && <div><span className="text-(--ui-text-quaternary)">邮箱</span> <span className="truncate">{squad.contact_email}</span></div>}
            {squad.founded_at && <div><span className="text-(--ui-text-quaternary)">成立</span> <span>{squad.founded_at}</span></div>}
            {squad.created_at && <div><span className="text-(--ui-text-quaternary)">注册</span> <span>{String(squad.created_at).slice(0, 10)}</span></div>}
          </div>
        </div>
      )}
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

/* ── Collapsible Section Header ──────────────── */

function SectionHeader({ title, count, expanded, onToggle }: {
  title: string; count: number; expanded: boolean; onToggle: () => void
}) {
  return (
    <div
      className="flex cursor-pointer items-center gap-2 border-b border-(--ui-stroke-quaternary) px-3 py-2 text-(--ui-text-secondary) hover:bg-(--ui-control-hover-background) select-none sticky top-0 bg-(--ui-bg-surface)"
      onClick={onToggle}
      role="button"
      tabIndex={0}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle() }}}
    >
      <span className="text-[0.6rem] transition-transform duration-150" style={{ transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
      <span className="text-xs font-medium">{title}</span>
      <span className="text-[0.6rem] text-(--ui-text-quaternary)">({count})</span>
    </div>
  )
}

/* ── Group Settings Panel (WeChat-style) ─────── */

const SettingsRow = ({ label, value, onClick, accent }: { label: string; value?: string; onClick?: () => void; accent?: boolean }) => (
  <div
    className={cn('flex items-center justify-between border-b border-(--ui-stroke-quaternary) px-4 py-3 text-sm cursor-pointer hover:bg-(--ui-control-hover-background)', !onClick && 'cursor-default')}
    onClick={onClick}
  >
    <span className={cn(accent ? 'text-destructive' : 'text-foreground')}>{label}</span>
    <div className="flex items-center gap-1 text-(--ui-text-tertiary)">
      {value && <span className="max-w-40 truncate text-xs">{value}</span>}
      {onClick && <span className="text-xs">›</span>}
    </div>
  </div>
)

function GroupSettingsPanel({
  detail, myUid, onClose,
  onRename, onAnnouncement, onTransfer, onInvite,
  onViewMember, onClearChat, onLeave,
  onDeleteAnnouncement,
  existingUsers,
}: {
  detail: GroupDetail
  myUid: number
  onClose: () => void
  onRename: (name: string) => void
  onAnnouncement: (text: string) => void
  onTransfer: (uid: number) => void
  onInvite: (uid: number) => void
  onViewMember: (uid: number) => void
  onClearChat: () => void
  onLeave: () => void
  onDeleteAnnouncement: (anId: string) => void
  existingUsers: {uid: number; nickname: string; role: string}[]
}) {
  const [editing, setEditing] = useState<'name' | 'announcement' | null>(null)
  const [inputVal, setInputVal] = useState('')
  const [showInvite, setShowInvite] = useState(false)
  const [showAllAnnouncements, setShowAllAnnouncements] = useState(false)
  const isOwner = String(detail.owner_id) === String(myUid)
  const memberList = detail.members || []
  const headMembers = memberList.slice(0, 10)
  const announcements = detail.announcements || []
  const latestAnn = announcements.length > 0 ? announcements[announcements.length - 1] : null

  const startEdit = (mode: 'name' | 'announcement') => {
    setInputVal(mode === 'name' ? detail.title : '')
    setEditing(mode)
  }
  const saveEdit = () => {
    if (editing === 'name') onRename(inputVal)
    else if (editing === 'announcement') { onAnnouncement(inputVal); setInputVal('') }
    setEditing(null)
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-2 border-b border-(--ui-stroke-tertiary) px-4 py-2.5">
        <button className="text-sm text-(--ui-text-secondary) hover:text-foreground" onClick={onClose}>← 返回</button>
        <span className="text-sm font-semibold text-foreground">群资料</span>
      </header>

      <div className="flex-1 overflow-y-auto">
        {/* ── 成员网格 ── */}
        <div className="px-4 py-4">
          <div className="grid grid-cols-5 gap-x-1 gap-y-3">
            {headMembers.map(m => (
              <div key={m.uid} className="flex flex-col items-center gap-1 cursor-pointer" onClick={() => onViewMember(m.uid)}>
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-(--ui-accent)/15 text-xs font-semibold text-(--ui-accent)">{m.nickname.charAt(0)}</div>
                <span className="text-[0.6rem] text-(--ui-text-secondary) text-center leading-tight line-clamp-1 w-full text-center">{m.nickname.length > 4 ? m.nickname.slice(0, 4) + '…' : m.nickname}</span>
              </div>
            ))}
            <div className="flex flex-col items-center gap-1 cursor-pointer" onClick={() => { setShowInvite(!showInvite); setInputVal(''); setEditing(null) }}>
              <div className="flex h-10 w-10 items-center justify-center rounded-md border border-dashed border-(--ui-stroke-tertiary) text-(--ui-text-tertiary) text-lg">+</div>
              <span className="text-[0.6rem] text-(--ui-text-tertiary)">邀请</span>
            </div>
          </div>
          {memberList.length > 10 && (
            <div className="mt-1 text-center text-[0.6rem] text-(--ui-accent) cursor-pointer" onClick={() => {}}>查看更多 ({memberList.length}人) ›</div>
          )}
          {/* Invite quick panel */}
          {showInvite && (
            <div className="mt-2 max-h-28 space-y-0.5 overflow-y-auto rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-2">
              {existingUsers.filter(u => !memberList.some(m => m.uid === u.uid) && u.uid !== myUid).slice(0, 20).map(u => (
                <div key={u.uid} className="flex items-center justify-between rounded px-2 py-1 text-xs hover:bg-(--ui-control-hover-background)" onClick={() => { onInvite(u.uid); setShowInvite(false) }}>
                  <span>{u.nickname}<span className="ml-1 text-(--ui-text-quaternary)}">#{u.uid}</span></span>
                  <span className="text-(--ui-accent) text-[0.6rem]">+ 邀请</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="h-2 bg-(--ui-bg-quaternary)" />

        {/* ── 编辑区 ── */}
        {editing && (
          <div className="mx-4 mt-3 flex gap-2">
            {editing === 'announcement' ? (
              <textarea autoFocus className="flex-1 rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-2 py-1 text-sm" onChange={e => setInputVal(e.target.value)} rows={3} value={inputVal} />
            ) : (
              <input autoFocus className="flex-1 rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-2 py-1 text-sm" onChange={e => setInputVal(e.target.value)} value={inputVal} />
            )}
            <button className="text-xs text-(--ui-accent)" onClick={saveEdit}>保存</button>
            <button className="text-xs text-(--ui-text-tertiary)" onClick={() => setEditing(null)}>取消</button>
          </div>
        )}

        {/* ── 群聊名称 ── */}
        <SettingsRow label="群聊名称" value={detail.title} onClick={() => isOwner && startEdit('name')} />

        {/* ── 群公告 ── */}
        <div className="border-b border-(--ui-stroke-quaternary)">
          <div className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-foreground">群公告</span>
            {isOwner && (
              <button className="text-xs text-(--ui-accent)" onClick={() => startEdit('announcement')}>发布</button>
            )}
          </div>
          {latestAnn ? (
            <div className="px-4 pb-2">
              <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="flex-1 text-xs text-(--ui-text-secondary) whitespace-pre-wrap">{latestAnn.text}</span>
                  {isOwner && (
                    <button className="shrink-0 text-[0.55rem] text-(--ui-text-quaternary) hover:text-destructive"
                      onClick={() => onDeleteAnnouncement(latestAnn.id)}>✕</button>
                  )}
                </div>
                <div className="mt-1 text-[0.55rem] text-(--ui-text-quaternary)}">{latestAnn.created_at}</div>
              </div>
              {announcements.length > 1 && (
                <button
                  className="mt-1 w-full text-center text-[0.6rem] text-(--ui-accent)"
                  onClick={() => setShowAllAnnouncements(!showAllAnnouncements)}
                >{showAllAnnouncements ? '收起' : `查看全部 ${announcements.length} 条公告`}</button>
              )}
            </div>
          ) : (
            <div className="px-4 pb-2 text-xs text-(--ui-text-quaternary)}">暂无公告</div>
          )}
          {showAllAnnouncements && announcements.length > 1 && (
            <div className="px-4 pb-2 space-y-2">
              {[...announcements].reverse().slice(1).map(an => (
                <div key={an.id} className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="flex-1 text-xs text-(--ui-text-secondary) whitespace-pre-wrap">{an.text}</span>
                    {isOwner && (
                      <button className="shrink-0 text-[0.55rem] text-(--ui-text-quaternary) hover:text-destructive"
                        onClick={() => onDeleteAnnouncement(an.id)}>✕</button>
                    )}
                  </div>
                  <div className="mt-1 text-[0.55rem] text-(--ui-text-quaternary)}">{an.created_at}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="h-2 bg-(--ui-bg-quaternary)" />

        {/* ── 成员列表 ── */}
        {memberList.map(m => (
          <div key={m.uid} className="flex items-center justify-between border-b border-(--ui-stroke-quaternary) px-4 py-2.5 cursor-pointer hover:bg-(--ui-control-hover-background)" onClick={() => onViewMember(m.uid)}>
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-(--ui-accent)/15 text-xs font-semibold text-(--ui-accent)">{m.nickname.charAt(0)}</div>
              <div>
                <div className="text-sm text-foreground">{m.nickname}</div>
                <div className="text-[0.6rem] text-(--ui-text-quaternary)}">{m.user_role || ''}</div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {String(m.uid) === String(detail.owner_id) && <span className="text-[0.6rem] text-amber-500">群主</span>}
              {m.participant_type === 'admin' && <span className="text-[0.6rem] text-(--ui-accent)">管理员</span>}
              {isOwner && String(m.uid) !== String(myUid) && (
                <button className="ml-1 text-[0.6rem] text-(--ui-text-tertiary) hover:text-(--ui-accent)" onClick={e => { e.stopPropagation(); onTransfer(m.uid) }} title="转让群主">转让</button>
              )}
            </div>
          </div>
        ))}

        <div className="h-3 bg-(--ui-bg-quaternary)" />

        {/* ── 清空聊天记录 ── */}
        <SettingsRow label="清空聊天记录" onClick={onClearChat} />

        {/* ── 退出/删除群 ── */}
        <SettingsRow label={isOwner ? '解散群聊' : '退出群聊'} onClick={onLeave} accent />
      </div>
    </div>
  )
}

/* ── Main View ───────────────────────────────── */

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
  const [showCreateGroup, setShowCreateGroup] = useState(false)
  const [groupTitle, setGroupTitle] = useState('')
  const [groupMemberUids, setGroupMemberUids] = useState<number[]>([])
  const [activeTab, setActiveTab] = useState<'messages' | 'contacts'>('messages')
  const [needRegistration, setNeedRegistration] = useState(false)
  const [orgChecked, setOrgChecked] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['friends', 'groups']))
  const [showGroupSettings, setShowGroupSettings] = useState(false)
  const [groupDetail, setGroupDetail] = useState<GroupDetail | null>(null)
  const prevMessagesLen = useRef(messages.length)
  const identRef = useRef<WinPeekIdentity | null>(identity)
  identRef.current = identity
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
        const d2: any = await gatewayRequest('winpeek_org_status', {}).catch(() => ({}))
        setNeedRegistration(!d2?.linked)
        setOrgChecked(true)
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
        const d2: any = await gatewayRequest('winpeek_org_status', {}).catch(() => ({}))
        setNeedRegistration(!d2?.linked)
        setOrgChecked(true)
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
    gatewayRequest<any>('winpeek_mim_contacts', { uid: identity.uid }).then(data => {
      const list: Contact[] = []
      if (data.contacts) {
        for (const c of data.contacts) {
          list.push({
            id: String(c.uid), name: c.nickname, uid: c.uid,
            role: c.role, online: c.online !== false,
            lastMessage: c.last_message || '', lastTime: c.last_msg_ts || '',
            unread: c.unread_count || 0,
          })
        }
      }
      if (data.groups) {
        for (const g of data.groups) {
          list.push({
            id: `g-${g.gid}`, name: g.title, uid: 0, online: true,
            lastMessage: g.last_message || '', lastTime: g.last_time || '',
            unread: 0, isGroup: true, gid: g.gid,
            memberCount: g.member_count || 0,
          })
        }
      }
      setContacts(list)
    }).catch(() => {})
  }, [identity, gatewayRequest])

  // ── Load chat history when contact selected ──
  useEffect(() => {
    if (!activeContact || !identity) { setMessages([]); return }
    let cancelled = false
    setMessages([])
    const hparams: any = { uid: identity.uid, limit: 50 }
    if (activeContact.isGroup && activeContact.gid) {
      hparams.gid = activeContact.gid
    } else {
      hparams.peer_uid = activeContact.uid
    }
    gatewayRequest<any>('winpeek_mim_history', hparams)
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
          const peer = activeContactRef.current
          const relevant = data.messages.filter((m: any) => {
            if (!peer) return false
            if (m.from_uid === identity.uid) return false
            // Group message → match by gid; single message → match by from_uid
            if (peer.isGroup && peer.gid) return m.gid === peer.gid
            return String(m.from_uid) === String(peer.uid)
          })
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
      const sp: any = { body: text, uid: identity.uid, from_name: identity.name }
      if (activeContact.isGroup && activeContact.gid) {
        sp.gid = activeContact.gid
      } else {
        sp.to_uid = activeContact.uid
      }
      await gatewayRequest('winpeek_mim_send', sp)
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

  const handleCreateGroup = useCallback(async () => {
    const title = groupTitle.trim()
    if (!title || groupMemberUids.length === 0 || !identity) return
    try {
      const data: any = await gatewayRequest('winpeek_mim_group_create', {
        title, member_uids: groupMemberUids, uid: identity.uid,
      })
      if (data.ok && data.gid) {
        setContacts(prev => [...prev, {
          id: `g-${data.gid}`, name: title, uid: 0, online: true,
          lastMessage: '', lastTime: '', unread: 0,
          isGroup: true, gid: data.gid,
          memberCount: groupMemberUids.length + 1,
        }])
      }
    } catch (e) { notifyError(e, '创建群聊失败') }
    setShowCreateGroup(false)
    setGroupTitle('')
    setGroupMemberUids([])
  }, [groupTitle, groupMemberUids, identity, gatewayRequest])

  // ── Group settings callbacks ──
  const loadGroupDetail = useCallback(async (gid: number) => {
    try {
      const data: any = await gatewayRequest('winpeek_mim_group_info', { gid, uid: identity?.uid })
      if (data.group) {
        let announcements: any[] = []
        if (data.group.metadata) {
          try {
            const m = typeof data.group.metadata === 'string' ? JSON.parse(data.group.metadata) : data.group.metadata
            announcements = m.announcements || []
          } catch {}
        }
        setGroupDetail({ ...data.group, announcements })
      }
    } catch {}
  }, [gatewayRequest, identity])

  const handleUpdateGroup = useCallback(async (field: string, value: string) => {
    if (!activeContact?.gid || !identity) return
    const params: any = { gid: activeContact.gid, uid: identity.uid }
    if (field === 'name') params.title = value
    else if (field === 'announcement') params.announcement = value
    try {
      await gatewayRequest('winpeek_mim_group_update', params)
      if (groupDetail) {
        if (field === 'name') setGroupDetail({ ...groupDetail, title: value })
        else { loadGroupDetail(activeContact.gid!) } // announcement: refresh from DB
      }
      // Refresh contact list to show updated name
      if (field === 'name') {
        setContacts(prev => prev.map(c => c.gid === activeContact.gid ? { ...c, name: value } : c))
      }
    } catch (e) { notifyError(e, '更新失败') }
  }, [activeContact, identity, gatewayRequest, groupDetail])

  const handleTransferOwnership = useCallback(async (newOwnerUid: number) => {
    if (!activeContact?.gid || !identity) return
    try {
      await gatewayRequest('winpeek_mim_group_transfer', { gid: activeContact.gid, new_owner_uid: newOwnerUid, uid: identity.uid })
      loadGroupDetail(activeContact.gid)
    } catch (e) { notifyError(e, '转让失败') }
  }, [activeContact, identity, gatewayRequest, loadGroupDetail])

  const handleInviteToGroup = useCallback(async (uid: number) => {
    if (!activeContact?.gid || !identity) return
    try {
      await gatewayRequest('winpeek_mim_group_invite', { gid: activeContact.gid, uids: [uid], uid: identity.uid })
      loadGroupDetail(activeContact.gid)
    } catch (e) { notifyError(e, '邀请失败') }
  }, [activeContact, identity, gatewayRequest, loadGroupDetail])

  const handleDeleteAnnouncement = useCallback(async (anId: string) => {
    if (!activeContact?.gid || !identity) return
    try {
      await gatewayRequest('winpeek_mim_announcement_delete', { gid: activeContact.gid, an_id: anId, uid: identity.uid })
      loadGroupDetail(activeContact.gid)
    } catch (e) { notifyError(e, '删除失败') }
  }, [activeContact, identity, gatewayRequest, loadGroupDetail])

  const handleLeaveGroup = useCallback(async () => {
    if (!activeContact?.gid || !identity) return
    try {
      await gatewayRequest('winpeek_mim_group_leave', { gid: activeContact.gid, uid: identity.uid })
      setContacts(prev => prev.filter(c => c.gid !== activeContact.gid))
      setActiveContactId(null); setMessages([]); setShowGroupSettings(false)
    } catch (e) { notifyError(e, '操作失败') }
  }, [activeContact, identity, gatewayRequest])

  // Load group detail when selecting a group
  useEffect(() => {
    if (activeContact?.isGroup && activeContact.gid) {
      loadGroupDetail(activeContact.gid)
    } else {
      setGroupDetail(null)
    }
  }, [activeContact, loadGroupDetail])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) { e.preventDefault(); handleSend() }
  }, [handleSend, isComposing])

  // ── Registration check ──
  if (identity && orgChecked && needRegistration) {
    return (
      <MasterDetail>
        <RegistrationWizard
          identity={{ uid: identity.uid, name: identity.name, role: identity.role }}
          onDone={() => { setNeedRegistration(false); setOrgChecked(false) }}
        />
      </MasterDetail>
    )
  }

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

  // ── Group settings view ──
  if (showGroupSettings && activeContact?.isGroup) {
    return (
      <MasterDetail>
        <ListColumn>
          <div className="flex h-full flex-col">
            <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-3 py-2.5">
              <button className="flex items-center gap-2 text-left hover:opacity-80" onClick={() => setShowProfile(true)}>
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-(--ui-accent)/15 text-[0.6rem] font-semibold text-(--ui-accent)">{identity.name.charAt(0)}</div>
                <div>
                  <div className="text-xs font-semibold text-foreground">{identity.name}</div>
                  <div className="text-[0.55rem] text-(--ui-text-tertiary)}">{identity.role} · #{identity.uid}</div>
                </div>
              </button>
            </header>
            <div className="flex-1 overflow-y-auto">
              {/* simplified contact list for navigation */}
              {contacts.map(contact => (
                <div
                  key={contact.id}
                  className={cn('flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left cursor-pointer hover:bg-(--ui-control-hover-background)',
                    activeContactId === contact.id && 'bg-(--ui-control-active-background)')}
                  onClick={() => { setActiveContactId(contact.id); setShowGroupSettings(false) }}
                >
                  <div className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold bg-(--ui-accent)/15 text-(--ui-accent)">
                    {contact.isGroup ? '👥' : contact.name.charAt(0)}
                  </div>
                  <span className="truncate text-sm">{contact.name}</span>
                </div>
              ))}
            </div>
          </div>
        </ListColumn>
        <DetailColumn>
          {groupDetail ? (
            <GroupSettingsPanel
              detail={groupDetail}
              myUid={identity.uid}
              onClose={() => setShowGroupSettings(false)}
              onRename={name => handleUpdateGroup('name', name)}
              onAnnouncement={text => handleUpdateGroup('announcement', text)}
              onTransfer={handleTransferOwnership}
              onInvite={handleInviteToGroup}
              onViewMember={uid => setViewContactUid(uid)}
              onClearChat={() => { setMessages([]); setShowGroupSettings(false) }}
              onLeave={handleLeaveGroup}
              onDeleteAnnouncement={handleDeleteAnnouncement}
              existingUsers={existingUsers}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-(--ui-text-tertiary)">加载中...</div>
          )}
        </DetailColumn>
      </MasterDetail>
    )
  }

  // ── Chat view ──
  const sortedContacts = [...contacts].sort((a, b) => {
    // Most recent message at top — groups and contacts mixed
    const ta = a.lastTime || ''
    const tb = b.lastTime || ''
    if (ta && tb && ta !== tb) return ta > tb ? -1 : 1
    if (ta && !tb) return -1
    if (!ta && tb) return 1
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
          </header>

          {/* ── Tab bar ── */}
          <div className="flex border-b border-(--ui-stroke-tertiary)">
            {(['messages', 'contacts'] as const).map(tab => (
              <button
                key={tab}
                className={cn(
                  'flex-1 py-2 text-xs font-medium transition-colors',
                  activeTab === tab
                    ? 'text-(--ui-accent) border-b-2 border-(--ui-accent)'
                    : 'text-(--ui-text-tertiary) hover:text-(--ui-text-secondary)'
                )}
                onClick={() => setActiveTab(tab)}
              >{tab === 'messages' ? '消息' : '通讯录'}</button>
            ))}
          </div>

          {/* ── 消息 Tab: flat list sorted by last message time ── */}
          {activeTab === 'messages' && (
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
                {contact.isGroup ? (
                  <div className="shrink-0 flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-sm">👥</div>
                ) : (
                  <div className={cn('relative shrink-0', !contact.online && 'opacity-60')}>
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-(--ui-accent)/15 text-xs font-semibold text-(--ui-accent)">
                      {contact.name.charAt(0)}
                    </div>
                    <span className={cn(
                      'absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-(--ui-bg-surface)',
                      contact.online ? 'bg-emerald-500' : 'bg-gray-400'
                    )} />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between">
                    <span className="truncate text-sm font-medium text-foreground">{contact.name}</span>
                    <div className="flex items-center gap-1 shrink-0">
                      {contact.lastTime && <span className="text-[0.6rem] text-(--ui-text-tertiary)">{formatMessageTimestamp(contact.lastTime, t.assistant.thread)}</span>}
                    </div>
                  </div>
                  <div className="mt-0.5 flex items-center justify-between">
                    {contact.lastMessage && (
                      <span className="truncate text-xs text-(--ui-text-tertiary)}">
                        {contact.lastMessage.slice(0, 30)}{contact.lastMessage.length > 30 ? '...' : ''}
                      </span>
                    )}
                    {!contact.lastMessage && contact.isGroup && (
                      <span className="truncate text-xs text-(--ui-text-quaternary)}">{contact.memberCount} 位成员</span>
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
          )}

          {/* ── 通讯录 Tab: collapsible sections ── */}
          {activeTab === 'contacts' && (
          <div className="flex-1 overflow-y-auto">
            <SectionHeader
              title="好友"
              count={contacts.filter(c => !c.isGroup).length}
              expanded={expandedSections.has('friends')}
              onToggle={() => setExpandedSections(prev => {
                const next = new Set(prev)
                if (next.has('friends')) next.delete('friends'); else next.add('friends')
                return next
              })}
            />
            {expandedSections.has('friends') && contacts.filter(c => !c.isGroup).sort((a, b) => a.name.localeCompare(b.name)).map(contact => (
              <div
                key={contact.id}
                className={cn(
                  'flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors hover:bg-(--ui-control-hover-background) cursor-pointer',
                  activeContactId === contact.id && 'bg-(--ui-control-active-background)'
                )}
                onClick={() => { setActiveContactId(contact.id); setActiveTab('messages') }}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setActiveContactId(contact.id); setActiveTab('messages') }}}
                role="button" tabIndex={0}
              >
                <div className={cn('relative shrink-0', !contact.online && 'opacity-60')}>
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-(--ui-accent)/15 text-xs font-semibold text-(--ui-accent)">
                    {contact.name.charAt(0)}
                  </div>
                  <span className={cn(
                    'absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-(--ui-bg-surface)',
                    contact.online ? 'bg-emerald-500' : 'bg-gray-400'
                  )} />
                </div>
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium text-foreground">{contact.name}</span>
                  {contact.role && <span className="ml-1 text-xs text-(--ui-text-quaternary)}">{contact.role}</span>}
                </div>
              </div>
            ))}
            <SectionHeader
              title="群聊"
              count={contacts.filter(c => c.isGroup).length}
              expanded={expandedSections.has('groups')}
              onToggle={() => setExpandedSections(prev => {
                const next = new Set(prev)
                if (next.has('groups')) next.delete('groups'); else next.add('groups')
                return next
              })}
            />
            {expandedSections.has('groups') && contacts.filter(c => c.isGroup).map(contact => (
              <div
                key={contact.id}
                className={cn(
                  'flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors hover:bg-(--ui-control-hover-background) cursor-pointer',
                  activeContactId === contact.id && 'bg-(--ui-control-active-background)'
                )}
                onClick={() => { setActiveContactId(contact.id); setActiveTab('messages') }}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setActiveContactId(contact.id); setActiveTab('messages') }}}
                role="button" tabIndex={0}
              >
                <div className="shrink-0 flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-sm">👥</div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-foreground">{contact.name}</div>
                  <div className="text-xs text-(--ui-text-quaternary)}">{contact.memberCount} 位成员</div>
                </div>
              </div>
            ))}
            {/* ── 建群入口 ── */}
            <div
              className="flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left cursor-pointer hover:bg-(--ui-control-hover-background)"
              onClick={() => setShowCreateGroup(true)}
              role="button" tabIndex={0}
            >
              <div className="shrink-0 flex h-9 w-9 items-center justify-center rounded-full bg-(--ui-accent)/10 text-(--ui-accent) text-sm">+</div>
              <span className="text-sm text-(--ui-accent)">新建群聊</span>
            </div>
          </div>
          )}
        </div>
      </ListColumn>

      <DetailColumn fullWidth={true}>
        {activeContact ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <header
              className="flex cursor-pointer items-center border-b border-(--ui-stroke-tertiary) px-4 py-2.5 hover:bg-(--ui-control-hover-background)"
              onClick={() => {
                if (activeContact.isGroup && activeContact.gid) { loadGroupDetail(activeContact.gid); setShowGroupSettings(true) }
                else if (!activeContact.isGroup && activeContact.uid > 0) { setViewContactUid(activeContact.uid) }
              }}
              title={activeContact.isGroup ? '点击查看群资料' : '点击查看用户资料'}
            >
              <div className={cn('mr-2.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
                activeContact.isGroup ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-(--ui-accent)/15 text-(--ui-accent)')}>
                {activeContact.isGroup ? '👥' : activeContact.name.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-foreground truncate">
                  {activeContact.isGroup
                    ? <>{activeContact.name}<span className="ml-1 text-xs font-normal text-(--ui-text-tertiary)}">({activeContact.memberCount || '?'})</span></>
                    : activeContact.name}
                </div>
                {!activeContact.isGroup && (
                  <div className="text-[0.6rem] text-(--ui-text-tertiary)}">
                    {activeContact.online ? '在线' : '离线'}{activeContact.role && ` · ${activeContact.role}`}{activeContact.uid > 0 && ` · #${activeContact.uid}`}
                  </div>
                )}
              </div>
              <span className="text-xs text-(--ui-text-quaternary)">›</span>
            </header>
            {/* ── Group announcement bar (latest) ── */}
            {activeContact.isGroup && groupDetail && groupDetail.announcements.length > 0 && (
              <div className="border-b border-(--ui-stroke-quaternary) bg-amber-500/5 px-4 py-1.5">
                <div className="flex items-start gap-1.5">
                  <span className="text-[0.6rem] shrink-0">📢</span>
                  <span className="text-[0.65rem] text-(--ui-text-secondary) line-clamp-2">
                    {groupDetail.announcements[groupDetail.announcements.length - 1].text}
                  </span>
                  {groupDetail.announcements.length > 1 && (
                    <span className="ml-1 shrink-0 text-[0.55rem] text-(--ui-text-quaternary)}">+{groupDetail.announcements.length - 1}</span>
                  )}
                </div>
              </div>
            )}
            <div className="flex-1 overflow-y-auto px-4 py-2" onScroll={handleChatScroll} ref={chatListRef}>
              {messages.map((msg, i) => {
                // Centered timestamp divider: show when gap > 5 min or first message
                const showTs = (() => {
                  if (i === 0) return true
                  const prev = messages[i - 1]
                  if (!prev?.msgTs || !msg.msgTs) return false
                  try {
                    return new Date(msg.msgTs).getTime() - new Date(prev.msgTs).getTime() > 300000
                  } catch { return false }
                })()
                return (
                  <div key={msg.id}>
                    {showTs && msg.msgTs && (
                      <div className="my-3 text-center">
                        <span className="inline-block rounded-full bg-(--ui-bg-tertiary) px-3 py-0.5 text-[0.6rem] text-(--ui-text-quaternary)">
                          {formatMessageTimestamp(msg.msgTs, t.assistant.thread)}
                        </span>
                      </div>
                    )}
                    {/* ── Message row: self=right, other=left ── */}
                    <div className={cn('mb-3 flex gap-2.5', msg.isSelf ? 'flex-row-reverse' : 'flex-row')}>
                      {/* Avatar — clickable to view profile */}
                      <div
                        className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-(--ui-accent)/15 text-xs font-semibold text-(--ui-accent)', !msg.isSelf && 'cursor-pointer hover:ring-2 hover:ring-(--ui-accent)/30')}
                        onClick={() => { if (!msg.isSelf && msg.fromUid > 0) setViewContactUid(msg.fromUid) }}
                        title={!msg.isSelf ? `查看 ${msg.fromName} 的资料` : undefined}
                      >
                        {msg.fromName?.charAt(0) || '?'}
                      </div>
                      {/* Content column — takes remaining space; bubble at 70% max */}
                      <div className={cn('w-0 flex-1', msg.isSelf && 'flex flex-col items-end')}>
                        {/* Sender name */}
                        <div className={cn('mb-0.5 text-[0.65rem]',
                          activeContact?.isGroup && !msg.isSelf ? 'text-(--ui-accent)' : 'text-(--ui-text-tertiary)')}>
                          {activeContact?.isGroup || !msg.isSelf ? msg.fromName : ''}
                        </div>
                        {/* Bubble */}
                        <div className={cn('inline-block max-w-[70%] rounded-lg px-2.5 py-1.5 text-sm',
                          msg.isSelf
                            ? 'bg-(--dt-user-bubble) text-foreground border border-border/50'
                            : 'bg-(--ui-bg-tertiary) text-foreground')}>
                          <div className="[&_pre]:overflow-x-auto [&_pre]:rounded [&_pre]:bg-black/10 [&_pre]:p-2 [&_pre]:text-[0.75rem] [&_code]:rounded [&_code]:bg-black/10 [&_code]:px-1 [&_code]:text-[0.8em] [&_p]:mb-1 [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4">
                            <Streamdown>{msg.content}</Streamdown>
                          </div>
                        </div>
                        {/* Footer: copy + time */}
                        <div className="mt-0.5 flex items-center gap-1 text-[0.55rem] text-(--ui-text-quaternary)">
                          <CopyButton appearance="icon" className="size-3" text={msg.content} />
                          <span>{msg.time}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
              {userScrolledUp && (
                <div className="sticky bottom-0 flex justify-center pb-1">
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500 px-3 py-0.5 text-[0.65rem] text-white shadow-sm cursor-pointer" onClick={scrollToBottom}>
                    ↓ 8条新消息
                  </span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            {/* ── Composer: full-width input area ── */}
            <div className="w-full px-4 pb-3 pt-2">
              <div className="overflow-visible rounded-2xl border border-border/65 bg-(--ui-bg-surface)">
                <div className="flex min-h-0 w-full flex-col gap-1 overflow-hidden rounded-[inherit] px-3 py-2.5">
                    {/* Control buttons: [+] [🎤] [📢] */}
                    <div className="flex items-center gap-1">
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

      {/* ── Create Group Dialog ── */}
      {showCreateGroup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowCreateGroup(false)}>
          <div className="w-96 rounded-2xl bg-(--ui-bg-surface) p-5 shadow-2xl border border-(--ui-stroke-tertiary)" onClick={e => e.stopPropagation()}>
            <h3 className="mb-3 text-sm font-semibold text-foreground">新建群聊</h3>
            <input
              autoFocus
              className="mb-3 w-full rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-3 py-1.5 text-sm text-foreground outline-none placeholder:text-muted-foreground/60"
              onChange={e => setGroupTitle(e.target.value)}
              placeholder="群名称"
              value={groupTitle}
            />
            <div className="mb-1 text-xs font-medium text-(--ui-text-tertiary)}">选择成员</div>
            <div className="mb-3 max-h-40 space-y-1 overflow-y-auto">
              {existingUsers.filter(u => u.uid !== identity?.uid).map(u => (
                <label key={u.uid} className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-(--ui-control-hover-background)">
                  <input
                    checked={groupMemberUids.includes(u.uid)}
                    className="size-3.5 accent-(--ui-accent)"
                    onChange={() => setGroupMemberUids(prev => prev.includes(u.uid) ? prev.filter(x => x !== u.uid) : [...prev, u.uid])}
                    type="checkbox"
                  />
                  <span className="truncate">{u.nickname}<span className="ml-1 text-xs text-(--ui-text-quaternary)}">#{u.uid}</span></span>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <button
                className="rounded-lg border border-(--ui-stroke-tertiary) px-3 py-1.5 text-xs text-(--ui-text-secondary) hover:bg-(--ui-control-hover-background)"
                onClick={() => { setShowCreateGroup(false); setGroupTitle(''); setGroupMemberUids([]) }}
              >取消</button>
              <button
                className="rounded-lg bg-(--ui-accent) px-3 py-1.5 text-xs text-white disabled:opacity-40"
                disabled={!groupTitle.trim() || groupMemberUids.length === 0}
                onClick={handleCreateGroup}
              >创建 ({groupMemberUids.length + 1}人)</button>
            </div>
          </div>
        </div>
      )}
    </MasterDetail>
  )
}
