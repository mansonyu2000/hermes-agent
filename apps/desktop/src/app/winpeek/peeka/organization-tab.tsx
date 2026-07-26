import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { notifyError } from '@/store/notifications'

/* ── Standardized data ── */
const INDUSTRY_OPTIONS = [
  '信息技术/软件', '金融/保险', '教育培训', '医疗健康', '制造业',
  '零售/电商', '房地产/建筑', '交通运输', '能源/环保', '农业/食品',
  '媒体/广告', '法律服务', '政府/非营利', '咨询服务', '其他',
]
const PROVINCE_OPTIONS = [
  '北京', '上海', '广东(广州)', '广东(深圳)', '浙江(杭州)',
  '江苏(南京)', '四川(成都)', '湖北(武汉)', '陕西(西安)', '山东(济南)',
  '福建(厦门)', '天津', '重庆', '河南(郑州)', '湖南(长沙)', '其他',
]
const SCALE_OPTIONS = ['1-10人', '11-50人', '51-200人', '201-500人', '501-1000人', '1000人以上']
const ORG_TYPE_OPTIONS = ['企业法人', '个体工商户', '其他组织']

function Select({ value, onChange, options, placeholder }: {
  value: string; onChange: (v: string) => void; options: string[]; placeholder?: string
}) {
  return (
    <select
      className="w-full h-9 rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-3 text-xs text-foreground outline-none focus:ring-1 focus:ring-(--ui-accent)"
      value={value}
      onChange={e => onChange(e.target.value)}
    >
      <option value="">{placeholder || '— 请选择 —'}</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

/* ── Organization Tab ── */
export function OrganizationTab({ uid, rq }: { uid: number; rq: any }) {
  const [org, setOrg] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'info' | 'members' | 'devices' | 'approvals'>('info')
  const [editing, setEditing] = useState(false)
  const [editFields, setEditFields] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [persons, setPersons] = useState<any[]>([])
  const [machines, setMachines] = useState<any[]>([])
  const [pending, setPending] = useState<any>({ persons: [], machines: [] })
  const [actingId, setActingId] = useState<number | null>(null)
  const [loadError, setLoadError] = useState('')
  // Create form
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ name: '', desc: '', orgType: '', industry: '', province: '', scale: '', businessScope: '', website: '', email: '', phone: '', legal: '', foundedAt: '' })
  const [createStep, setCreateStep] = useState(1)
  // Join form
  const [showJoin, setShowJoin] = useState(false)
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searchDone, setSearchDone] = useState(false)
  const [selectedSquad, setSelectedSquad] = useState<any>(null)
  const [joinName, setJoinName] = useState('')
  const [joinEmail, setJoinEmail] = useState('')
  const [detailPersonId, setDetailPersonId] = useState<number | null>(null)
  const [showInvite, setShowInvite] = useState(false)
  const [inviteCopied, setInviteCopied] = useState(false)

  const isOwner = org?.is_owner === true

  const updateCreate = (k: string, v: string) => setCreateForm(p => ({ ...p, [k]: v }))

  const load = useCallback(async () => {
    setLoadError('')
    try {
      const d: any = await rq('winpeek_org_status', { uid })
      setOrg(d)
      if (d?.linked && d?.squad) {
        const sqid = d.squad.id
        const [pRes, mRes, pendRes] = await Promise.all([
          rq('winpeek_person_list', { squad_id: sqid }).catch(() => ({ persons: [] })),
          rq('winpeek_machine_list', {}).catch(() => ({ machines: [] })),
          rq('winpeek_pending_list', { squad_id: sqid, uid }).catch(() => ({ persons: [], machines: [] })),
        ])
        setPersons((pRes as any)?.persons || [])
        setMachines((mRes as any)?.machines || [])
        setPending(pendRes || { persons: [], machines: [] })
      }
    } catch (e: any) {
      const msg = e?.message || String(e)
      setLoadError(msg)
      notifyError(e, 'Failed to load organization data')
    }
    setLoading(false)
  }, [rq, uid])

  useEffect(() => { load() }, [load])

  // ── Create Org ──
  const handleCreate = async () => {
    const f = createForm
    if (!f.name.trim()) return
    const address = [f.province, f.scale].filter(Boolean).join(' · ')
    setSaving(true)
    try {
      const d: any = await rq('winpeek_register_with_squad', {
        uid, is_new_squad: true,
        squad_name: f.name.trim(), squad_desc: f.desc.trim(),
        person_name: '', hostname: '',
        industry: f.industry, address,
        website: f.website, contact_email: f.email,
        contact_phone: f.phone, legal_person: f.legal,
        org_type: f.orgType, business_scope: f.businessScope, founded_at: f.foundedAt,
      })
      if (d?.ok) {
        setShowCreate(false)
        setCreateForm({ name: '', desc: '', orgType: '', industry: '', province: '', scale: '', businessScope: '', website: '', email: '', phone: '', legal: '', foundedAt: '' })
        setCreateStep(1)
        await load()
      } else { notifyError(d?.error || '创建失败，请重试', '创建失败') }
    } catch (e: any) { notifyError(e?.message || String(e), '创建失败') }
    setSaving(false)
  }

  // ── Join org ──
  const handleSearch = async () => {
    const q = searchQ.trim()
    if (q.length < 2 && q.length !== 4) return
    setSearchDone(true)
    try {
      // 4-digit → try as invite code
      if (/^\d{4}$/.test(q)) {
        // Search by invite code is not a separate RPC; try name search first
        const d: any = await rq('winpeek_squad_search', { q })
        setSearchResults(d?.squads || d || [])
      } else {
        const d: any = await rq('winpeek_squad_search', { q })
        setSearchResults(d?.squads || d || [])
      }
    } catch { setSearchResults([]) }
  }

  const handleJoin = async () => {
    if (!selectedSquad) return
    setSaving(true)
    try {
      const d: any = await rq('winpeek_register_with_squad', {
        uid, is_new_squad: false, squad_id: selectedSquad.id,
        person_name: joinName, email: joinEmail, hostname: '',
      })
      if (d?.ok) {
        setShowJoin(false); setSearchQ(''); setSearchResults([])
        setSelectedSquad(null); setJoinName(''); setJoinEmail(''); setSearchDone(false)
        await load()
      } else { notifyError(d?.error || '加入失败', '加入失败') }
    } catch (e: any) { notifyError(e?.message || String(e), '加入失败') }
    setSaving(false)
  }

  const handleJoinByCode = async () => {
    if (!/^\d{4}$/.test(searchQ.trim())) return
    setSaving(true)
    try {
      const d: any = await rq('winpeek_register_with_squad', {
        uid, is_new_squad: false,
        invite_code: searchQ.trim(), person_name: joinName, email: joinEmail, hostname: '',
      })
      if (d?.ok) {
        setShowJoin(false); setSearchQ(''); setSelectedSquad(null); setJoinName(''); setJoinEmail(''); setSearchDone(false)
        await load()
      } else { notifyError(d?.error || '加入失败', '加入失败') }
    } catch (e: any) { notifyError(e?.message || String(e), '加入失败') }
    setSaving(false)
  }

  // ── Edit ──
  const startEdit = () => {
    const s = org?.squad; if (!s) return
    setEditFields({ name: s.name || '', description: s.description || '', org_type: s.org_type || '', industry: s.industry || '', address: s.address || '', business_scope: s.business_scope || '', founded_at: s.founded_at || '', website: s.website || '', contact_email: s.contact_email || '', contact_phone: s.contact_phone || '', legal_person: s.legal_person || '' })
    setEditing(true)
  }
  const saveOrg = async () => {
    if (!editFields.name.trim()) { notifyError('组织名称不能为空', '验证失败'); return }
    setSaving(true)
    try {
      const s = org?.squad
      const d: any = await rq('winpeek_squad_upsert', { name: editFields.name, requester_uid: uid, squad_id: s?.id, ...editFields })
      if (d?.ok || d?.id) { await load(); setEditing(false) } else { notifyError(d?.error || '保存失败', '保存失败') }
    } catch (e: any) { notifyError(e?.message || String(e), '保存失败') }
    setSaving(false)
  }

  // ── Approve / Delete / Transfer ──
  const handleApprove = async (type: 'person' | 'machine', id: number, action: 'approved' | 'rejected') => {
    setActingId(id)
    const fn = type === 'person' ? 'winpeek_person_approve' : 'winpeek_machine_approve'
    const params: any = { action, requester_uid: uid }
    if (type === 'person') params.person_id = id; else params.machine_id = id
    try { await rq(fn, params); await load() } catch (e: any) { notifyError(e?.message || String(e), '操作失败') }
    setActingId(null)
  }
  const handleDelete = async (type: 'person' | 'machine', id: number) => {
    if (!window.confirm(`确认删除此${type === 'person' ? '成员' : '设备'}？`)) return
    setActingId(id)
    const params: any = { requester_uid: uid }
    if (type === 'person') params.person_id = id; else params.machine_id = id
    try { await rq(`winpeek_${type}_delete`, params); await load() } catch (e: any) { notifyError(e?.message || String(e), '删除失败') }
    setActingId(null)
  }
  const handleTransfer = async (newOwnerPersonId: number) => {
    if (!window.confirm('确认将组织所有权转让给该成员？转让后你将失去管理员权限。')) return
    setActingId(newOwnerPersonId)
    try {
      await rq('winpeek_squad_upsert', { name: org?.squad?.name, requester_uid: uid, squad_id: org?.squad?.id, owner_person_id: newOwnerPersonId })
      await load()
    } catch (e: any) { notifyError(e?.message || String(e), '转让失败') }
    setActingId(null)
  }
  const copyInvite = () => { navigator.clipboard.writeText(org?.squad?.invite_code || ''); setInviteCopied(true); setTimeout(() => setInviteCopied(false), 2000) }

  if (loading) return <div className="grid h-full place-items-center text-sm text-(--ui-text-tertiary) py-12">加载中...</div>

  /* ── Not linked ── */
  if (!org?.linked || !org?.squad) {
    return (<div className="grid h-full place-items-center p-5 overflow-y-auto"><div className="text-center max-w-lg w-full">
      <div className="mb-3 text-4xl">🏢</div>
      <div className="text-base font-bold text-foreground mb-1">尚未加入组织</div>
      <p className="text-sm text-(--ui-text-secondary) mb-6">创建或加入一个组织，管理团队、设备和 AI Agent</p>

      {loadError && <div className="rounded-lg bg-destructive/10 px-4 py-3 text-xs text-destructive mb-4 text-left">{loadError}</div>}

      <div className="flex gap-3 justify-center mb-6">
        <Button className="h-11 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] shadow-md shadow-purple-500/20 text-sm font-semibold" size="sm" onClick={() => { setShowCreate(true); setShowJoin(false); setCreateStep(1) }}>创建组织</Button>
        <Button className="h-11 px-6 rounded-xl" variant="secondary" size="sm" onClick={() => { setShowJoin(true); setShowCreate(false); setSearchQ(''); setSearchDone(false); setSearchResults([]); setSelectedSquad(null) }}>加入组织</Button>
      </div>

      {/* ── CREATE FORM ── */}
      {showCreate && (<div className="rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-5 text-left space-y-4 shadow-sm">
        <div className="text-sm font-semibold text-foreground">创建新组织</div>

        {createStep === 1 && (<>
          <p className="text-xs text-(--ui-text-secondary)">填写基本信息以创建组织，带 * 为必填</p>
          <div>
            <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">组织名称 <span className="text-destructive">*</span></label>
            <Input className="h-10 rounded-xl text-sm" placeholder="例如: 深圳市互动时代科技有限公司" value={createForm.name} onChange={e => updateCreate('name', e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">组织类型</label>
              <Select value={createForm.orgType} onChange={v => updateCreate('orgType', v)} options={ORG_TYPE_OPTIONS} />
            </div>
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">所属行业</label>
              <Select value={createForm.industry} onChange={v => updateCreate('industry', v)} options={INDUSTRY_OPTIONS} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">所在地区</label>
              <Select value={createForm.province} onChange={v => updateCreate('province', v)} options={PROVINCE_OPTIONS} />
            </div>
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">组织规模</label>
              <Select value={createForm.scale} onChange={v => updateCreate('scale', v)} options={SCALE_OPTIONS} />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">组织简介</label>
            <Input className="h-10 rounded-xl text-sm" placeholder="一句话描述" value={createForm.desc} onChange={e => updateCreate('desc', e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button className="flex-1 h-10 rounded-xl" variant="secondary" size="sm" onClick={() => setCreateStep(2)}>下一步：联系信息 →</Button>
          </div>
        </>)}

        {createStep === 2 && (<>
          <p className="text-xs text-(--ui-text-secondary)">填写组织详细信息（选填，可后续补充）</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">法人代表</label>
              <Input className="h-10 rounded-xl text-sm" placeholder="姓名" value={createForm.legal} onChange={e => updateCreate('legal', e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">成立时间</label>
              <Input className="h-10 rounded-xl text-sm" placeholder="2024-01-01" value={createForm.foundedAt} onChange={e => updateCreate('foundedAt', e.target.value)} />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">营业范围</label>
            <Input className="h-10 rounded-xl text-sm" placeholder="例如: 软件开发、技术服务、咨询..." value={createForm.businessScope} onChange={e => updateCreate('businessScope', e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">网站</label>
            <Input className="h-10 rounded-xl text-sm" placeholder="https://" value={createForm.website} onChange={e => updateCreate('website', e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">联系邮箱</label>
              <Input className="h-10 rounded-xl text-sm" placeholder="contact@" value={createForm.email} onChange={e => updateCreate('email', e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">联系电话</label>
              <Input className="h-10 rounded-xl text-sm" placeholder="区号-号码" value={createForm.phone} onChange={e => updateCreate('phone', e.target.value)} />
            </div>
          </div>
          <div className="flex gap-2">
            <Button className="flex-1 h-10 rounded-xl" variant="secondary" size="sm" onClick={() => setCreateStep(1)}>← 上一步</Button>
            <Button className="flex-1 h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] shadow-md shadow-purple-500/20 text-sm font-semibold" size="sm" disabled={saving || !createForm.name.trim()} onClick={handleCreate}>{saving ? '创建中…' : '完成创建'}</Button>
          </div>
        </>)}

        <button className="w-full text-xs text-(--ui-text-secondary) py-1" onClick={() => { setShowCreate(false); setCreateStep(1) }}>取消</button>
      </div>)}

      {/* ── JOIN FORM ── */}
      {showJoin && (<div className="rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-5 text-left space-y-4 shadow-sm">
        <div className="text-sm font-semibold text-foreground">加入已有组织</div>

        {!selectedSquad ? (<>
          <p className="text-xs text-(--ui-text-secondary)">搜索组织名称，或输入 4 位邀请码直接加入</p>
          <div className="flex gap-2">
            <Input className="flex-1 h-10 rounded-xl text-sm" placeholder="输入组织名称搜索（至少2个字符）" value={searchQ}
              onChange={e => { setSearchQ(e.target.value); setSearchDone(false) }}
              onKeyDown={e => { if (e.key === 'Enter') handleSearch() }} />
            <Button className="h-10 px-5 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] text-sm font-semibold" size="sm" onClick={handleSearch}>搜索</Button>
          </div>
          {/^\d{4}$/.test(searchQ.trim()) && !searchResults.length && searchDone && (
            <div className="rounded-xl bg-amber-500/10 px-4 py-3 text-xs">
              <div className="font-medium text-amber-700 mb-1">检测到 4 位邀请码: {searchQ.trim()}</div>
              <p className="text-amber-600/80 mb-2">未搜索到名称匹配的组织。是否使用邀请码直接加入？</p>
              <div className="space-y-2">
                <Input className="h-9 rounded-lg text-xs" placeholder="你的姓名（可选）" value={joinName} onChange={e => setJoinName(e.target.value)} />
                <Input className="h-9 rounded-lg text-xs" placeholder="你的邮箱（可选）" value={joinEmail} onChange={e => setJoinEmail(e.target.value)} />
                <Button className="w-full h-9 rounded-lg bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] text-xs" size="sm" disabled={saving} onClick={handleJoinByCode}>
                  {saving ? '加入中…' : '使用邀请码加入'}
                </Button>
              </div>
            </div>
          )}
          {searchDone && !/^\d{4}$/.test(searchQ.trim()) && (
            <div className="text-xs text-(--ui-text-secondary)">
              找到 <span className="font-semibold text-foreground">{searchResults.length}</span> 个结果
            </div>
          )}
          {searchResults.length > 0 && (
            <div className="max-h-56 overflow-y-auto space-y-1 rounded-xl border border-(--ui-stroke-tertiary) p-1">
              {searchResults.map((s: any) => (
                <div key={s.id} className="flex items-center justify-between rounded-xl px-4 py-3 hover:bg-(--ui-control-hover-background) cursor-pointer border border-transparent hover:border-(--ui-stroke-tertiary)"
                  onClick={() => { setSelectedSquad(s); setJoinName(''); setJoinEmail('') }}>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-foreground">{s.name}</div>
                    {s.description && <div className="text-xs text-(--ui-text-tertiary) truncate mt-0.5">{s.description}</div>}
                    {s.industry && <div className="text-[0.6rem] text-(--ui-text-quaternary) mt-0.5">{s.industry}</div>}
                  </div>
                  <span className="shrink-0 text-xs text-(--ui-accent) font-medium ml-3">选择 →</span>
                </div>
              ))}
            </div>
          )}
        </>) : (<>
          <div className="rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-secondary) p-4">
            <div className="text-xs text-(--ui-text-quaternary) mb-1">已选择组织</div>
            <div className="text-sm font-semibold text-foreground">{selectedSquad.name}</div>
            {selectedSquad.description && <div className="text-xs text-(--ui-text-tertiary) mt-0.5">{selectedSquad.description}</div>}
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">你的姓名</label>
              <Input className="h-10 rounded-xl text-sm" placeholder="姓名（可选）" value={joinName} onChange={e => setJoinName(e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">你的邮箱</label>
              <Input className="h-10 rounded-xl text-sm" placeholder="邮箱（可选）" value={joinEmail} onChange={e => setJoinEmail(e.target.value)} />
            </div>
          </div>
          <p className="text-xs text-(--ui-text-quaternary)">提交后将由组织管理员审核</p>
          <div className="flex gap-2">
            <Button className="flex-1 h-10 rounded-xl" variant="secondary" size="sm" onClick={() => { setSelectedSquad(null); setJoinName(''); setJoinEmail('') }}>← 重新选择</Button>
            <Button className="flex-1 h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] text-sm font-semibold" size="sm" disabled={saving} onClick={handleJoin}>
              {saving ? '提交中…' : '提交加入申请'}
            </Button>
          </div>
        </>)}

        <button className="w-full text-xs text-(--ui-text-secondary) py-1" onClick={() => { setShowJoin(false); setSelectedSquad(null); setSearchQ(''); setSearchResults([]); setSearchDone(false) }}>取消</button>
      </div>)}
    </div></div>)
  }

  /* ── Linked org ── */
  const s = org.squad
  return (
    <div className="flex flex-col h-full">
      <div className="flex border-b border-(--ui-stroke-tertiary) px-5">
        {(['info','members','devices','approvals'] as const).map(t => (
          <button key={t} className={cn('px-4 py-2.5 text-sm font-medium', tab===t ? 'text-(--ui-accent) border-b-[3px] border-(--ui-accent)' : 'text-(--ui-text-tertiary) hover:text-(--ui-text-secondary)')} onClick={()=>setTab(t)}>
            {{ info:'基本信息', members:`成员(${persons.length})`, devices:`设备(${machines.length})`, approvals:`审批(${pending.persons.length+pending.machines.length})` }[t]}
          </button>
        ))}
        <button className="ml-auto text-sm text-(--ui-text-tertiary) hover:text-foreground px-3" onClick={load} title="刷新">🔄</button>
      </div>

      <div className="flex-1 overflow-y-auto p-5">
        {loadError && <div className="rounded-xl bg-destructive/10 px-4 py-3 text-sm text-destructive mb-4">{loadError}</div>}

        {/* ── INFO TAB ── */}
        {tab==='info' && (<div className="space-y-4 max-w-lg mx-auto">
          <div className="text-center mb-2">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7c3aed] to-[#a78bfa] text-xl font-bold text-white shadow-md shadow-purple-500/30">🏢</div>
            <h3 className="text-base font-bold text-foreground">{s.name}</h3>
            {s.description && <p className="text-sm text-(--ui-text-secondary) mt-1">{s.description}</p>}
          </div>

          {!editing ? (<>
            <div className="rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-5 shadow-sm">
              <div className="text-xs font-semibold text-(--ui-text-quaternary) uppercase tracking-wider mb-3">组织信息</div>
              <div className="grid grid-cols-2 gap-x-5 gap-y-3 text-sm">
                {s.industry && <div><span className="text-(--ui-text-quaternary) text-xs">行业</span><div className="text-foreground font-medium mt-0.5">{s.industry}</div></div>}
                {s.address && <div><span className="text-(--ui-text-quaternary) text-xs">地址</span><div className="text-foreground font-medium mt-0.5">{s.address}</div></div>}
                {s.legal_person && <div><span className="text-(--ui-text-quaternary) text-xs">法人代表</span><div className="text-foreground font-medium mt-0.5">{s.legal_person}</div></div>}
                {s.contact_phone && <div><span className="text-(--ui-text-quaternary) text-xs">电话</span><div className="text-foreground font-medium mt-0.5">{s.contact_phone}</div></div>}
                {s.website && <div className="col-span-2"><span className="text-(--ui-text-quaternary) text-xs">网站</span><div className="text-foreground font-medium mt-0.5 truncate">{s.website}</div></div>}
                {s.contact_email && <div className="col-span-2"><span className="text-(--ui-text-quaternary) text-xs">邮箱</span><div className="text-foreground font-medium mt-0.5 truncate">{s.contact_email}</div></div>}
                {s.created_at && <div><span className="text-(--ui-text-quaternary) text-xs">创建时间</span><div className="text-foreground font-medium mt-0.5">{String(s.created_at).slice(0,10)}</div></div>}
              </div>
            </div>
            {isOwner && <Button className="w-full h-10 rounded-xl text-sm" variant="secondary" onClick={startEdit}>编辑组织信息</Button>}
          </>) : (<div className="rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-5 space-y-3 shadow-sm">
            <div className="text-sm font-semibold text-foreground mb-2">编辑组织信息</div>
            <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">名称<span className="text-destructive">*</span></label><Input className="h-10 rounded-xl text-sm" value={editFields.name||''} onChange={e=>setEditFields(p=>({...p,name:e.target.value}))}/></div>
            <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">简介</label><Input className="h-10 rounded-xl text-sm" value={editFields.description||''} onChange={e=>setEditFields(p=>({...p,description:e.target.value}))}/></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">组织类型</label><Select value={editFields.org_type||''} onChange={v=>setEditFields(p=>({...p,org_type:v}))} options={ORG_TYPE_OPTIONS}/></div>
              <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">行业</label><Select value={editFields.industry||''} onChange={v=>setEditFields(p=>({...p,industry:v}))} options={INDUSTRY_OPTIONS}/></div>
            </div>
            <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">地址</label><Input className="h-10 rounded-xl text-sm" value={editFields.address||''} onChange={e=>setEditFields(p=>({...p,address:e.target.value}))}/></div>
            <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">营业范围</label><Input className="h-10 rounded-xl text-sm" placeholder="软件开发、技术服务..." value={editFields.business_scope||''} onChange={e=>setEditFields(p=>({...p,business_scope:e.target.value}))}/></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">成立时间</label><Input className="h-10 rounded-xl text-sm" placeholder="2024-01-01" value={editFields.founded_at||''} onChange={e=>setEditFields(p=>({...p,founded_at:e.target.value}))}/></div>
              <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">法人代表</label><Input className="h-10 rounded-xl text-sm" value={editFields.legal_person||''} onChange={e=>setEditFields(p=>({...p,legal_person:e.target.value}))}/></div>
            </div>
            <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">网站</label><Input className="h-10 rounded-xl text-sm" placeholder="https://" value={editFields.website||''} onChange={e=>setEditFields(p=>({...p,website:e.target.value}))}/></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">邮箱</label><Input className="h-10 rounded-xl text-sm" placeholder="contact@" value={editFields.contact_email||''} onChange={e=>setEditFields(p=>({...p,contact_email:e.target.value}))}/></div>
              <div><label className="text-xs font-medium text-(--ui-text-secondary) block mb-1">电话</label><Input className="h-10 rounded-xl text-sm" placeholder="区号-号码" value={editFields.contact_phone||''} onChange={e=>setEditFields(p=>({...p,contact_phone:e.target.value}))}/></div>
            </div>
            <div className="flex gap-2 pt-1">
              <Button className="flex-1 h-10 rounded-xl" variant="secondary" size="sm" onClick={()=>setEditing(false)}>取消</Button>
              <Button className="flex-1 h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] text-sm font-semibold shadow-md shadow-purple-500/20" size="sm" disabled={saving||!editFields.name?.trim()} onClick={saveOrg}>{saving?'保存中…':'保存修改'}</Button>
            </div>
          </div>)}

          {s.invite_code && (
            <div className="rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-5 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-semibold text-(--ui-text-quaternary) uppercase tracking-wider">邀请码</div>
                <button className="text-sm text-(--ui-accent) hover:text-[#6d28d9] font-medium" onClick={copyInvite}>{inviteCopied ? '✓ 已复制!' : '📋 复制'}</button>
              </div>
              <div className="text-2xl font-mono font-bold text-[#7c3aed] tracking-widest select-all">{s.invite_code}</div>
              <p className="text-xs text-(--ui-text-tertiary) mt-2">分享此邀请码给团队成员，他们可直接加入组织，无需审核</p>
              {isOwner && <Button className="mt-3 h-9 rounded-xl text-sm" size="sm" variant="secondary" onClick={() => setShowInvite(true)}>邀请成员</Button>}
            </div>
          )}

          <div className="space-y-2 pt-2">
            {isOwner && (
              <Button className="w-full h-10 rounded-xl text-sm text-destructive hover:bg-destructive/10" variant="secondary" size="sm"
                onClick={() => { if (window.confirm('确认永久删除该组织？此操作不可恢复！\n\n删除将同时移除所有成员关联、设备记录和 Agent 配置。')) rq('winpeek_squad_delete', { squad_id: s.id, uid }).then(load) }}>
                删除组织
              </Button>
            )}
            {!isOwner && (
              <Button className="w-full h-10 rounded-xl text-sm" variant="secondary" size="sm"
                onClick={() => { if (window.confirm('确认退出该组织？退出后你将失去对组织数据和 Agent 的访问权限。')) rq('winpeek_squad_delete', { squad_id: s.id, uid, leave_only: true }).then(load) }}>
                退出组织
              </Button>
            )}
          </div>
        </div>)}

        {/* ── MEMBERS ── */}
        {tab==='members' && (<div className="space-y-2 max-w-lg mx-auto">
          {persons.length === 0 && <p className="text-sm text-(--ui-text-tertiary) text-center py-12">暂无成员</p>}
          {persons.map((p: any) => (<div key={p.id}>
            <div className="flex items-center gap-3 rounded-xl border border-(--ui-stroke-tertiary) px-4 py-3 cursor-pointer hover:bg-(--ui-control-hover-background) transition-colors"
              onClick={() => setDetailPersonId(detailPersonId === p.id ? null : p.id)}>
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#7c3aed]/20 to-[#a78bfa]/20 text-sm font-bold text-[#7c3aed] shrink-0">{(p.name || '?').charAt(0).toUpperCase()}</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-foreground flex items-center gap-1.5">
                  {p.name}
                  {String(p.id) === String(s.owner_person_id) && <span className="text-xs bg-amber-500/15 text-amber-600 px-1.5 py-0.5 rounded-md font-medium">管理员</span>}
                  {p.approval_status === 'pending' && <span className="text-xs bg-orange-500/15 text-orange-600 px-1.5 py-0.5 rounded-md">待审批</span>}
                </div>
                <div className="text-xs text-(--ui-text-tertiary) mt-0.5">{p.email || '—'}</div>
              </div>
              {p.approval_status === 'pending' && isOwner && (
                <div className="flex gap-1.5 shrink-0" onClick={e => e.stopPropagation()}>
                  <button className="text-xs bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-emerald-600 disabled:opacity-30 transition-colors" disabled={actingId === p.id} onClick={() => handleApprove('person', p.id, 'approved')}>通过</button>
                  <button className="text-xs bg-red-500/10 text-red-500 px-3 py-1.5 rounded-lg font-medium hover:bg-red-500/20 disabled:opacity-30 transition-colors" disabled={actingId === p.id} onClick={() => handleApprove('person', p.id, 'rejected')}>拒绝</button>
                </div>
              )}
            </div>
            {detailPersonId === p.id && (
              <div className="ml-12 mt-1.5 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-4 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-(--ui-text-quaternary) text-xs">姓名</span><span className="font-medium">{p.name}</span></div>
                {p.email && <div className="flex justify-between"><span className="text-(--ui-text-quaternary) text-xs">邮箱</span><span>{p.email}</span></div>}
                {p.phone && <div className="flex justify-between"><span className="text-(--ui-text-quaternary) text-xs">电话</span><span>{p.phone}</span></div>}
                {p.created_at && <div className="flex justify-between"><span className="text-(--ui-text-quaternary) text-xs">加入时间</span><span>{String(p.created_at).slice(0, 10)}</span></div>}
                <div className="flex gap-2 pt-1">
                  {isOwner && (<>
                    <button className="text-xs bg-[#7c3aed] text-white px-3 py-1.5 rounded-lg font-medium hover:bg-[#6d28d9] disabled:opacity-30 transition-colors" disabled={actingId === p.id} onClick={() => handleTransfer(p.id)}>转让所有权</button>
                    {p.approval_status === 'approved' && <button className="text-xs bg-red-500/10 text-red-500 px-3 py-1.5 rounded-lg font-medium hover:bg-red-500/20 disabled:opacity-30 transition-colors" disabled={actingId === p.id} onClick={() => handleDelete('person', p.id)}>移除成员</button>}
                  </>)}
                </div>
              </div>
            )}
          </div>))}
        </div>)}

        {/* ── DEVICES ── */}
        {tab === 'devices' && (<div className="space-y-2 max-w-lg mx-auto">
          {machines.length === 0 && <p className="text-sm text-(--ui-text-tertiary) text-center py-12">暂无设备</p>}
          {machines.map((m: any) => (
            <div key={m.id} className="flex items-center gap-3 rounded-xl border border-(--ui-stroke-tertiary) px-4 py-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-base shrink-0">💻</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-foreground">{m.hostname}</div>
                <div className="text-xs text-(--ui-text-tertiary) mt-0.5">
                  {m.os_name && <span>{m.os_name}</span>}
                  {m.approval_status && <span className={m.approval_status === 'pending' ? 'text-orange-500 ml-2' : ''}>· {m.approval_status === 'approved' ? '已授权' : '待审批'}</span>}
                </div>
              </div>
              {m.approval_status === 'pending' && isOwner && (
                <div className="flex gap-1.5 shrink-0">
                  <button className="text-xs bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-emerald-600 disabled:opacity-30" disabled={actingId === m.id} onClick={() => handleApprove('machine', m.id, 'approved')}>通过</button>
                  <button className="text-xs bg-red-500/10 text-red-500 px-3 py-1.5 rounded-lg font-medium hover:bg-red-500/20 disabled:opacity-30" disabled={actingId === m.id} onClick={() => handleApprove('machine', m.id, 'rejected')}>拒绝</button>
                </div>
              )}
              {isOwner && <button className="text-sm text-(--ui-text-tertiary) hover:text-destructive ml-1 shrink-0" disabled={actingId === m.id} onClick={() => handleDelete('machine', m.id)} title="移除">✕</button>}
            </div>
          ))}
        </div>)}

        {/* ── APPROVALS ── */}
        {tab === 'approvals' && (<div className="space-y-5 max-w-lg mx-auto">
          {pending.persons.length === 0 && pending.machines.length === 0 && <p className="text-sm text-(--ui-text-tertiary) text-center py-12">暂无待审批项</p>}
          {pending.persons.length > 0 && (<div>
            <div className="text-xs font-semibold text-(--ui-text-quaternary) uppercase tracking-wider mb-3">待审批成员 ({pending.persons.length})</div>
            <div className="space-y-2">
              {pending.persons.map((p: any) => (<div key={`p-${p.id}`} className="flex items-center gap-3 rounded-xl border border-(--ui-stroke-tertiary) px-4 py-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-500/20 text-sm shrink-0">⏳</span>
                <div className="min-w-0 flex-1"><div className="text-sm font-medium text-foreground">{p.name}</div><div className="text-xs text-(--ui-text-tertiary) mt-0.5">{p.squad_name}{p.email && ` · ${p.email}`}</div></div>
                <div className="flex gap-1.5 shrink-0">
                  <button className="text-xs bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-emerald-600 disabled:opacity-30 transition-colors" disabled={actingId === p.id} onClick={() => handleApprove('person', p.id, 'approved')}>通过</button>
                  <button className="text-xs bg-red-500/10 text-red-500 px-3 py-1.5 rounded-lg font-medium hover:bg-red-500/20 disabled:opacity-30 transition-colors" disabled={actingId === p.id} onClick={() => handleApprove('person', p.id, 'rejected')}>拒绝</button>
                </div>
              </div>))}
            </div>
          </div>)}
          {pending.machines.length > 0 && (<div>
            <div className="text-xs font-semibold text-(--ui-text-quaternary) uppercase tracking-wider mb-3">待审批设备 ({pending.machines.length})</div>
            <div className="space-y-2">
              {pending.machines.map((m: any) => (<div key={`m-${m.id}`} className="flex items-center gap-3 rounded-xl border border-(--ui-stroke-tertiary) px-4 py-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-500/20 text-sm shrink-0">💻</span>
                <div className="min-w-0 flex-1"><div className="text-sm font-medium text-foreground">{m.hostname || m.name}</div><div className="text-xs text-(--ui-text-tertiary) mt-0.5">{m.squad_name}</div></div>
                <div className="flex gap-1.5 shrink-0">
                  <button className="text-xs bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-emerald-600 disabled:opacity-30 transition-colors" disabled={actingId === m.id} onClick={() => handleApprove('machine', m.id, 'approved')}>通过</button>
                  <button className="text-xs bg-red-500/10 text-red-500 px-3 py-1.5 rounded-lg font-medium hover:bg-red-500/20 disabled:opacity-30 transition-colors" disabled={actingId === m.id} onClick={() => handleApprove('machine', m.id, 'rejected')}>拒绝</button>
                </div>
              </div>))}
            </div>
          </div>)}
        </div>)}
      </div>

      {/* ── Invite Modal ── */}
      {showInvite && (
        <div className="fixed inset-0 z-[99999] bg-black/40 flex items-center justify-center" onClick={() => setShowInvite(false)}>
          <div className="bg-(--ui-bg-surface) rounded-2xl p-6 max-w-sm w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-foreground mb-2">邀请新成员</h3>
            <p className="text-sm text-(--ui-text-secondary) mb-4">分享此邀请码给团队成员，他们输入后可直接加入组织，无需管理员审批。</p>
            <div className="rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-secondary) p-5 text-center mb-4">
              <div className="text-3xl font-mono font-bold text-[#7c3aed] tracking-widest select-all mb-3">{s.invite_code}</div>
              <Button className="rounded-xl text-sm" size="sm" variant="secondary" onClick={copyInvite}>{inviteCopied ? '✓ 已复制!' : '📋 复制到剪贴板'}</Button>
            </div>
            <Button className="w-full h-10 rounded-xl text-sm" variant="secondary" size="sm" onClick={() => setShowInvite(false)}>关闭</Button>
          </div>
        </div>
      )}
    </div>
  )
}
