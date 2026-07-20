import { useCallback, useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { notifyError } from '@/store/notifications'

import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'

/* ── Types ── */

interface SquadRow {
  id: number; name: string; description: string
  owner_person_id?: number
}
interface PendingItem {
  id: number; name: string; hostname?: string; approval_status: string
  squad_name: string; email?: string; phone?: string
  created_at: string
}

/* ── Registration Wizard ── */

export function RegistrationWizard({
  identity, onDone,
}: {
  identity: { uid: number; name: string; role: string }
  onDone: () => void
}) {
  const { requestGateway: rq } = useGatewayRequest()
  const [tab, setTab] = useState<'create' | 'join'>('create')
  const [orgStatus, setOrgStatus] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)

  // Create form
  const [squadName, setSquadName] = useState('')
  const [squadDesc, setSquadDesc] = useState('')
  const [squadIndustry, setSquadIndustry] = useState('')
  const [squadAddr, setSquadAddr] = useState('')
  const [squadWeb, setSquadWeb] = useState('')
  const [squadEmail, setSquadEmail] = useState('')
  const [squadPhone, setSquadPhone] = useState('')
  const [squadLegal, setSquadLegal] = useState('')
  const [showMoreFields, setShowMoreFields] = useState(false)

  // Join form
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState<SquadRow[]>([])
  const [selectedSquad, setSelectedSquad] = useState<SquadRow | null>(null)
  const [joinName, setJoinName] = useState(identity.name)
  const [joinEmail, setJoinEmail] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [createdCode, setCreatedCode] = useState('')

  const checkStatus = useCallback(async () => {
    try {
      const d: any = await rq('winpeek_org_status', {})
      setOrgStatus(d)
      if (d?.linked) { onDone(); return }
    } catch { /* not loaded yet */ }
  }, [rq, onDone])

  useEffect(() => { checkStatus() }, [checkStatus])

  const handleSearch = useCallback(async (q: string) => {
    setSearchQ(q)
    if (q.length < 2) { setSearchResults([]); return }
    try {
      const d: any = await rq('winpeek_squad_search', { q })
      setSearchResults(d?.squads || [])
    } catch { /* ignore */ }
  }, [rq])

  const handleCreate = useCallback(async () => {
    if (!squadName.trim()) return
    setSubmitting(true)
    try {
      const d: any = await rq('winpeek_register_with_squad', {
        is_new_squad: true, squad_name: squadName.trim(), squad_desc: squadDesc.trim(),
        person_name: identity.name, hostname: '',
        industry: squadIndustry.trim(), address: squadAddr.trim(),
        website: squadWeb.trim(), contact_email: squadEmail.trim(),
        contact_phone: squadPhone.trim(), legal_person: squadLegal.trim(),
      })
      if (d?.ok) {
        if (d.invite_code) setCreatedCode(d.invite_code)
        onDone()
      } else { notifyError(d?.error || '创建失败', '错误') }
    } catch (e) { notifyError(e, '创建失败') }
    setSubmitting(false)
  }, [squadName, squadDesc, identity, rq, onDone])

  const handleJoin = useCallback(async () => {
    if (!selectedSquad && !inviteCode.trim()) return
    setSubmitting(true)
    try {
      const params: any = {
        is_new_squad: false,
        person_name: joinName.trim() || identity.name,
        email: joinEmail.trim(), hostname: '',
      }
      if (selectedSquad) { params.squad_id = selectedSquad.id }
      if (inviteCode.trim()) { params.invite_code = inviteCode.trim() }
      const d: any = await rq('winpeek_register_with_squad', params)
      if (d?.ok) {
        if (d.approval_status === 'approved') { onDone() }
        else { setJoinName(''); setJoinEmail(''); setSelectedSquad(null); setSearchQ(''); setInviteCode('') }
      } else { notifyError(d?.error || '加入失败', '错误') }
    } catch (e) { notifyError(e, '加入失败') }
    setSubmitting(false)
  }, [selectedSquad, joinName, joinEmail, inviteCode, identity, rq, onDone])

  if (orgStatus?.linked) return null  // already linked

  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-4">
        <div className="text-center">
          <div className="mb-2 text-4xl">🏢</div>
          <h2 className="text-lg font-semibold text-foreground">组织注册</h2>
          <p className="mt-1 text-xs text-(--ui-text-tertiary)">
            {orgStatus?.hostname ? `设备: ${orgStatus.hostname}` : '首次登录，请选择组织'}
          </p>
        </div>

        {/* Tabs */}
        <div className="flex rounded-lg bg-(--ui-bg-tertiary) p-0.5">
          {(['create', 'join'] as const).map(t => (
            <button
              key={t}
              className={cn('flex-1 rounded-md py-1.5 text-xs font-medium transition-colors',
                tab === t ? 'bg-(--ui-bg-surface) text-foreground shadow-sm' : 'text-(--ui-text-tertiary)')}
              onClick={() => setTab(t)}
            >{t === 'create' ? '创建组织' : '加入组织'}</button>
          ))}
        </div>

        {tab === 'create' ? (
          <div className="space-y-3">
            <div>
              <label className="text-xs text-(--ui-text-secondary)">组织名称 *</label>
              <Input className="mt-1" onChange={e => setSquadName(e.target.value)}
                placeholder="例: 深圳市互动时代科技有限公司" value={squadName} />
            </div>
            <div>
              <label className="text-xs text-(--ui-text-secondary)">简介 (可选)</label>
              <Input className="mt-1" onChange={e => setSquadDesc(e.target.value)}
                placeholder="简短描述" value={squadDesc} />
            </div>
            <button type="button" className="w-full text-center text-[0.6rem] text-(--ui-text-quaternary) hover:text-(--ui-accent)" onClick={() => setShowMoreFields(!showMoreFields)}>
              {showMoreFields ? '收起更多字段' : '+ 更多组织信息（行业、地址、网站、联系方式）'}
            </button>
            {showMoreFields && (
              <div className="space-y-3 rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-3">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[0.6rem] text-(--ui-text-quaternary)">行业</label>
                    <Input className="mt-0.5 h-7 text-xs" onChange={e => setSquadIndustry(e.target.value)}
                      placeholder="信息技术/金融/教育..." value={squadIndustry} />
                  </div>
                  <div>
                    <label className="text-[0.6rem] text-(--ui-text-quaternary)">法人代表</label>
                    <Input className="mt-0.5 h-7 text-xs" onChange={e => setSquadLegal(e.target.value)}
                      placeholder="姓名" value={squadLegal} />
                  </div>
                </div>
                <div>
                  <label className="text-[0.6rem] text-(--ui-text-quaternary)">注册地址</label>
                  <Input className="mt-0.5 h-7 text-xs" onChange={e => setSquadAddr(e.target.value)}
                    placeholder="省市地址" value={squadAddr} />
                </div>
                <div>
                  <label className="text-[0.6rem] text-(--ui-text-quaternary)">网站</label>
                  <Input className="mt-0.5 h-7 text-xs" onChange={e => setSquadWeb(e.target.value)}
                    placeholder="https://..." value={squadWeb} />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[0.6rem] text-(--ui-text-quaternary)">联系邮箱</label>
                    <Input className="mt-0.5 h-7 text-xs" onChange={e => setSquadEmail(e.target.value)}
                      placeholder="contact@..." value={squadEmail} />
                  </div>
                  <div>
                    <label className="text-[0.6rem] text-(--ui-text-quaternary)">联系电话</label>
                    <Input className="mt-0.5 h-7 text-xs" onChange={e => setSquadPhone(e.target.value)}
                      placeholder="区号-号码" value={squadPhone} />
                  </div>
                </div>
              </div>
            )}
            <Button className="w-full" disabled={!squadName.trim() || submitting}
              onClick={handleCreate} size="sm">
              {submitting ? '创建中...' : `创建并加入 · ${squadName ? squadName.slice(0, 12) : ''}`}
            </Button>
            {createdCode && (
              <div className="rounded-lg bg-amber-500/10 px-3 py-2 text-center">
                <div className="text-xs font-bold text-amber-600">邀请码: {createdCode}</div>
                <div className="mt-0.5 text-[0.6rem] text-(--ui-text-quaternary)">分享此码给团队成员，他们即可直接加入</div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {!selectedSquad ? (
              <>
                <div>
                  <label className="text-xs text-(--ui-text-secondary)">
                    {inviteCode ? '已在搜索框输入' : '搜索或输入邀请码'}
                  </label>
                  <Input autoFocus className="mt-1" onChange={e => {
                    const v = e.target.value
                    setSearchQ(v)
                    if (v.length === 4 && /^\d{4}$/.test(v)) { setInviteCode(v); setSearchResults([]) }
                    else { setInviteCode(''); handleSearch(v) }
                  }}
                    placeholder="公司名搜索 或 4位邀请码直接加入..." value={searchQ} />
                </div>
                {inviteCode && (
                  <div className="rounded-lg bg-emerald-500/10 px-3 py-2 text-center">
                    <div className="text-xs text-emerald-600">邀请码验证中: {inviteCode}</div>
                    <div className="mt-0.5 text-[0.6rem] text-(--ui-text-quaternary)">输入正确邀请码即可直接加入，无需审批</div>
                  </div>
                )}
                {searchResults.length > 0 && (
                  <div className="max-h-40 space-y-0.5 overflow-y-auto rounded-lg border border-(--ui-stroke-tertiary) p-1">
                    {searchResults.map(s => (
                      <div key={s.id}
                        className="cursor-pointer rounded-md px-3 py-2 text-sm hover:bg-(--ui-control-hover-background)"
                        onClick={() => setSelectedSquad(s)}
                      >
                        <div className="font-medium text-foreground">{s.name}</div>
                        {s.description && <div className="text-xs text-(--ui-text-quaternary) truncate">{s.description}</div>}
                      </div>
                    ))}
                  </div>
                )}
                {searchQ.length >= 2 && searchResults.length === 0 && (
                  <p className="text-xs text-(--ui-text-quaternary)">未找到匹配的组织</p>
                )}
              </>
            ) : (
              <>
                <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
                  <div className="text-xs text-(--ui-text-quaternary)">加入组织</div>
                  <div className="font-medium text-foreground">{selectedSquad.name}</div>
                  {selectedSquad.description && <div className="text-xs text-(--ui-text-tertiary) truncate">{selectedSquad.description}</div>}
                </div>
                <div>
                  <label className="text-xs text-(--ui-text-secondary)">你的姓名</label>
                  <Input className="mt-1" onChange={e => setJoinName(e.target.value)}
                    placeholder={identity.name} value={joinName} />
                </div>
                <div>
                  <label className="text-xs text-(--ui-text-secondary)">邮箱 (可选)</label>
                  <Input className="mt-1" onChange={e => setJoinEmail(e.target.value)}
                    placeholder="your@email.com" value={joinEmail} />
                </div>
                <div className="flex gap-2">
                  <Button className="flex-1" variant="secondary" size="sm"
                    onClick={() => { setSelectedSquad(null); setSearchQ(''); setSearchResults([]) }}>
                    返回
                  </Button>
                  <Button className="flex-1" size="sm" disabled={submitting} onClick={handleJoin}>
                    {submitting ? '提交中...' : '申请加入'}
                  </Button>
                </div>
                <p className="text-center text-[0.6rem] text-(--ui-text-quaternary)">
                  提交后等待管理员审批
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Admin Approval Panel ── */

export function ApprovalPanel({
  identity, onClose,
}: {
  identity: { uid: number; name: string }
  onClose: () => void
}) {
  const { requestGateway: rq } = useGatewayRequest()
  const [pending, setPending] = useState<{ persons: PendingItem[]; machines: PendingItem[] }>({ persons: [], machines: [] })
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    try {
      const d: any = await rq('winpeek_pending_list', {})
      setPending(d || { persons: [], machines: [] })
    } catch { /* */ }
  }, [rq])

  useEffect(() => { load() }, [load])

  const handleApprove = useCallback(async (type: 'person' | 'machine', id: number, action: 'approved' | 'rejected') => {
    setLoading(true)
    try {
      await rq(type === 'person' ? 'winpeek_person_approve' : 'winpeek_machine_approve', {
        person_id: type === 'person' ? id : undefined,
        machine_id: type === 'machine' ? id : undefined,
        action,
      })
      await load()
    } catch (e) { notifyError(e, '操作失败') }
    setLoading(false)
  }, [rq, load])

  const total = pending.persons.length + pending.machines.length

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-4 py-2.5">
        <div className="flex items-center gap-2">
          <button className="text-sm text-(--ui-text-secondary) hover:text-foreground" onClick={onClose}>←</button>
          <span className="text-sm font-semibold text-foreground">审批中心</span>
        </div>
        <Badge variant="secondary" className="text-[0.6rem]">{total} 待审</Badge>
      </header>
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Persons */}
        {pending.persons.length > 0 && (
          <div>
            <div className="mb-2 text-[0.6rem] font-medium text-(--ui-text-tertiary) uppercase">人员注册</div>
            <div className="space-y-2">
              {pending.persons.map(p => (
                <div key={`p-${p.id}`} className="flex items-center justify-between rounded-lg border border-(--ui-stroke-tertiary) px-3 py-2.5">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-foreground">{p.name}</div>
                    <div className="text-xs text-(--ui-text-tertiary)">{p.squad_name}{p.email ? ` · ${p.email}` : ''}</div>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <button className="rounded bg-emerald-500 px-2 py-1 text-[0.65rem] font-medium text-white hover:bg-emerald-600 disabled:opacity-30"
                      disabled={loading} onClick={() => handleApprove('person', p.id, 'approved')}>通过</button>
                    <button className="rounded bg-red-500/10 px-2 py-1 text-[0.65rem] font-medium text-red-500 hover:bg-red-500/20 disabled:opacity-30"
                      disabled={loading} onClick={() => handleApprove('person', p.id, 'rejected')}>拒绝</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {/* Machines */}
        {pending.machines.length > 0 && (
          <div>
            <div className="mb-2 text-[0.6rem] font-medium text-(--ui-text-tertiary) uppercase">设备注册</div>
            <div className="space-y-2">
              {pending.machines.map(m => (
                <div key={`m-${m.id}`} className="flex items-center justify-between rounded-lg border border-(--ui-stroke-tertiary) px-3 py-2.5">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-foreground">{m.hostname || m.name}</div>
                    <div className="text-xs text-(--ui-text-tertiary)}">{m.squad_name}</div>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <button className="rounded bg-emerald-500 px-2 py-1 text-[0.65rem] font-medium text-white hover:bg-emerald-600 disabled:opacity-30"
                      disabled={loading} onClick={() => handleApprove('machine', m.id, 'approved')}>通过</button>
                    <button className="rounded bg-red-500/10 px-2 py-1 text-[0.65rem] font-medium text-red-500 hover:bg-red-500/20 disabled:opacity-30"
                      disabled={loading} onClick={() => handleApprove('machine', m.id, 'rejected')}>拒绝</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {total === 0 && (
          <div className="pt-12 text-center">
            <div className="mb-2 text-3xl">✅</div>
            <p className="text-sm text-(--ui-text-tertiary)">暂无待审批项</p>
          </div>
        )}
      </div>
    </div>
  )
}
