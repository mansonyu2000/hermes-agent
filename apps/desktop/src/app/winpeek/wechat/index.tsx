import { useCallback, useEffect, useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Codicon } from '@/components/ui/codicon'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'

/* ── Types ───────────────────────────────────── */

type CategoryId = 'untagged' | 'starred' | 'groups' | 'group-members' | 'fuzzy' | 'portrait' | 'stats' | 'search' | 'sync'
type DetailTab = 'basic' | 'contact' | 'tags'

interface Contact {
  id: string
  name: string
  alias: string
  avatar: string
  wechatId: string
  phone: string
  email: string
  gender: string
  region: string
  source: string
  tags: string[]
  behaviorTags: string[]
  category: CategoryId
}

interface Category {
  id: CategoryId
  label: string
  icon: string
}

/* ── Data ────────────────────────────────────── */

const CATEGORIES: Category[] = [
  { id: 'untagged', label: '未标签', icon: 'tag' },
  { id: 'starred', label: '星标', icon: 'star-full' },
  { id: 'groups', label: '群', icon: 'organization' },
  { id: 'group-members', label: '群成员', icon: 'person' },
  { id: 'fuzzy', label: '模糊', icon: 'filter' },
  { id: 'portrait', label: '好友分析', icon: 'graph' },
  { id: 'stats', label: '统计', icon: 'graph' },
  { id: 'search', label: '搜索', icon: 'search' },
  { id: 'sync', label: '同步', icon: 'sync' },
]

const MOCK_CONTACTS: Contact[] = [
  {
    id: 'c01', name: '张三', alias: '三哥', avatar: '张',
    wechatId: 'zhangsan_wx', phone: '138****1234', email: 'zhangsan@example.com',
    gender: '男', region: '广东 深圳', source: '手机通讯录',
    tags: ['朋友', '同事'], behaviorTags: ['活跃', '常联系'], category: 'starred',
  },
  {
    id: 'c02', name: '李四', alias: '', avatar: '李',
    wechatId: 'lisi_wx', phone: '139****5678', email: '',
    gender: '女', region: '北京', source: '群聊添加',
    tags: ['同学'], behaviorTags: ['新好友'], category: 'untagged',
  },
  {
    id: 'c03', name: '王五', alias: '老王', avatar: '王',
    wechatId: 'wangwu_wx', phone: '136****9012', email: 'wangwu@company.com',
    gender: '男', region: '上海', source: '二维码',
    tags: ['客户', 'VIP'], behaviorTags: ['高价值', '频繁互动'], category: 'starred',
  },
  {
    id: 'c04', name: '赵六', alias: '老赵', avatar: '赵',
    wechatId: 'zhaoliu_wx', phone: '137****3456', email: '',
    gender: '男', region: '浙江 杭州', source: '名片推荐',
    tags: ['合作伙伴'], behaviorTags: [], category: 'untagged',
  },
  {
    id: 'c05', name: '孙七', alias: 'Sunny', avatar: '孙',
    wechatId: 'sunqi_wx', phone: '135****7890', email: 'sunqi@test.com',
    gender: '女', region: '四川 成都', source: '附近的人',
    tags: ['朋友'], behaviorTags: ['低频'], category: 'untagged',
  },
  {
    id: 'c06', name: '周八', alias: '', avatar: '周',
    wechatId: 'zhouba_wx_2024', phone: '133****1111', email: 'zhouba@work.com',
    gender: '男', region: '江苏 南京', source: '群聊添加',
    tags: ['同事', '项目组'], behaviorTags: ['协作频繁'], category: 'group-members',
  },
  {
    id: 'c07', name: '吴九', alias: '小九', avatar: '吴',
    wechatId: 'wujiu_wx', phone: '158****2222', email: '',
    gender: '女', region: '湖北 武汉', source: '手机通讯录',
    tags: [], behaviorTags: [], category: 'fuzzy',
  },
  {
    id: 'c08', name: '郑十', alias: '', avatar: '郑',
    wechatId: 'zhengshi_wx', phone: '186****3333', email: 'zhengshi@corp.com',
    gender: '男', region: '福建 厦门', source: '二维码',
    tags: ['供应商'], behaviorTags: ['高价值'], category: 'untagged',
  },
]

/* ── Portrait Analysis Types ─────────────────── */

interface PortraitItem {
  id: string
  name: string
  alias: string
  region: string
  stage: string
  tags: string[]
  metrics: Record<string, number>
  events_count: number
  last_time: string
  days_since: number
  priority: number
  category: string
  source_type: string
}

interface PortraitDetail {
  id: string
  name: string
  alias: string
  region: string
  source: string
  first_met: string
  stage: string
  metrics: Record<string, number>
  events: { date: string; title: string; summary: string; detail: string }[]
  events_count: number
}

const METRIC_LABELS: Record<string, string> = {
  familiarity: '熟悉度', trust: '信任感', curiosity: '好奇心', initiative: '主动性', risk: '风险性',
}

const CATEGORY_COLORS: Record<string, string> = {
  need_contact: 'var(--ui-warning)',
  biz_follow: 'var(--ui-accent)',
  normal: 'var(--ui-text-tertiary)',
}

/* ── Portrait Analysis Panel ─────────────────── */

function PortraitAnalysisPanel({ wxid }: { wxid: string }) {
  const { requestGateway } = useGatewayRequest()
  const [items, setItems] = useState<PortraitItem[]>([])
  const [detail, setDetail] = useState<PortraitDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    setLoading(true)
    requestGateway<any>('winpeek_portrait_list', { limit: 100, mode: 'contact', wxid })
      .then(data => { if (data?.items) { setItems(data.items); setLoading(false) } })
      .catch(async () => {
        // Gateway 不可用，降级到本地 JSON
        try {
          const resp = await fetch('/relationship-manager-heart.json')
          const json = await resp.json()
          const profiles = json?.data?.profiles || []
          const mapped: PortraitItem[] = profiles.map((p: any) => ({
            id: p.id, name: p.name, alias: p.title || '', region: p.region || '',
            stage: p.stage || '', tags: p.tags || [],
            metrics: p.metrics || {}, events_count: p.events?.length || 0,
            last_time: '', days_since: 30, priority: 1, category: 'normal', source_type: '',
          }))
          setItems(mapped)
        } catch {} finally { setLoading(false) }
      })
  }, [requestGateway, wxid])

  const loadDetail = useCallback((id: string) => {
    setDetail(null)
    requestGateway<any>('winpeek_portrait_detail', { friend_id: id })
      .then(data => { if (data?.profile) setDetail(data.profile) })
      .catch(async () => {
        // 降级：从本地 JSON 查找
        try {
          const resp = await fetch('/relationship-manager-heart.json')
          const json = await resp.json()
          const p = (json?.data?.profiles || []).find((p: any) => p.id === id)
          if (p) {
            setDetail({
              id: p.id, name: p.name, alias: p.title || '', region: p.region || '',
              source: '', first_met: '', stage: p.stage || '',
              metrics: p.metrics || {}, events: p.events || [], events_count: p.events?.length || 0,
            })
          }
        } catch {}
      })
  }, [requestGateway])

  const filtered = useMemo(() => {
    if (!search.trim()) return items
    const q = search.toLowerCase()
    return items.filter(i => i.name.toLowerCase().includes(q) || i.alias.toLowerCase().includes(q))
  }, [items, search])

  const typeCounts = useMemo(() => ({
    need_contact: items.filter(i => i.category === 'need_contact').length,
    biz_follow: items.filter(i => i.category === 'biz_follow').length,
    total: items.length,
  }), [items])

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="grid min-h-0 flex-1 grid-cols-1 sm:grid-cols-[4.5rem_14rem_minmax(0,1fr)]">
        {/* Col 1: category nav (same as parent) */}
        <nav className="flex flex-col gap-0.5 border-r border-(--ui-stroke-tertiary) bg-(--ui-bg-quaternary) p-1.5">
          {CATEGORIES.map(cat => (
            <button
              key={cat.id}
              className={cn(
                'flex flex-col items-center gap-0.5 rounded-md px-1 py-2 text-center transition-colors hover:bg-(--ui-control-hover-background)',
                cat.id === 'portrait' ? 'bg-(--ui-control-active-background) text-foreground' : 'text-(--ui-text-tertiary)',
              )}
              title={cat.label}
              disabled={cat.id !== 'portrait'}
            >
              <Codicon name={cat.id === 'portrait' ? 'graph' : cat.icon} size="0.875rem" />
              <span className="text-[0.55rem] leading-tight">{cat.label}</span>
            </button>
          ))}
        </nav>

        {/* Col 2: Contact list */}
        <aside className="flex min-h-0 flex-col border-r border-(--ui-stroke-tertiary)">
          <header className="shrink-0 border-b border-(--ui-stroke-tertiary) px-3 py-2">
            <Input className="h-7 text-xs" onChange={e => setSearch(e.target.value)} placeholder="搜索姓名..." value={search} />
          </header>
          <div className="shrink-0 border-b border-(--ui-stroke-tertiary) px-3 py-1.5 flex gap-3 text-[0.6rem] text-(--ui-text-tertiary)">
            <span>需联系 {typeCounts.need_contact}</span>
            <span>商业跟进 {typeCounts.biz_follow}</span>
            <span>共 {typeCounts.total}</span>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain [scrollbar-gutter:stable]">
            {loading ? (
              <div className="px-3 py-8 text-center text-xs text-(--ui-text-quaternary)">加载中...</div>
            ) : (
              filtered.map(item => (
                <button
                  key={item.id}
                  className={cn(
                    'flex w-full items-start gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors hover:bg-(--ui-control-hover-background)',
                    detail?.id === item.id && 'bg-(--ui-control-active-background)',
                  )}
                  onClick={() => loadDetail(item.id)}
                >
                  <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[item.category] || 'var(--ui-text-tertiary)' }} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between">
                      <span className="truncate text-sm font-medium text-foreground">{item.name}</span>
                      <span className="shrink-0 text-[0.6rem] text-(--ui-text-tertiary)">{item.last_time}</span>
                    </div>
                    <div className="mt-0.5 flex items-center gap-1 text-[0.6rem] text-(--ui-text-quaternary)">
                      <span>{item.stage}</span><span>·</span><span>{item.events_count}条消息</span>
                    </div>
                    <div className="mt-1 flex gap-1">
                      {Object.entries(item.metrics).slice(0, 3).map(([k, v]) => (
                        <div key={k} className="flex-1">
                          <div className="h-1 rounded-full bg-(--ui-bg-quaternary)">
                            <div className="h-full rounded-full bg-(--ui-accent)/40" style={{ width: `${Math.min(100, v as number)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* Col 3: Detail */}
        <main className="flex min-h-0 flex-col overflow-hidden">
          {detail ? (
            <div className="flex h-full flex-col overflow-y-auto">
              <header className="shrink-0 border-b border-(--ui-stroke-tertiary) px-5 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-sm font-bold text-(--ui-accent)">{detail.name.charAt(0)}</div>
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className="text-base font-semibold text-foreground">{detail.name}</span>
                      <span className="rounded-full bg-(--ui-accent)/10 px-2 py-0.5 text-[0.6rem] text-(--ui-accent)">{detail.stage}</span>
                    </div>
                    <p className="text-xs text-(--ui-text-tertiary)">{detail.alias && `${detail.alias} · `}{detail.region}</p>
                  </div>
                </div>
              </header>
              <div className="shrink-0 border-b border-(--ui-stroke-tertiary) px-5 py-3">
                <p className="mb-2 text-[0.65rem] font-medium text-(--ui-text-secondary)">关系维度</p>
                <div className="space-y-1.5">
                  {Object.entries(detail.metrics).map(([k, v]) => (
                    <div key={k} className="flex items-center gap-2 text-xs">
                      <span className="w-14 shrink-0 text-(--ui-text-secondary)">{METRIC_LABELS[k] || k}</span>
                      <div className="h-1.5 flex-1 rounded-full bg-(--ui-bg-quaternary)">
                        <div className={cn('h-full rounded-full', k === 'risk' ? 'bg-red-500/60' : 'bg-(--ui-accent)/60')} style={{ width: `${v}%` }} />
                      </div>
                      <span className="w-7 text-right tabular-nums text-(--ui-text-tertiary)">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="shrink-0 border-b border-(--ui-stroke-tertiary) px-5 py-3">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-(--ui-text-tertiary)">首次认识</span><div className="text-foreground">{detail.first_met || '-'}</div></div>
                  <div><span className="text-(--ui-text-tertiary)">消息总数</span><div className="text-foreground">{detail.events_count}</div></div>
                  <div className="col-span-2"><span className="text-(--ui-text-tertiary)">来源</span><div className="text-foreground">{detail.source || '-'}</div></div>
                </div>
              </div>
              <div className="flex-1 px-5 py-3">
                <p className="mb-2 text-[0.65rem] font-medium text-(--ui-text-secondary)">事件时间线 · {detail.events.length} 条</p>
                <div className="space-y-2">
                  {detail.events.slice(0, 10).map((event, i) => (
                    <div key={i} className="rounded-lg border border-(--ui-stroke-quaternary) px-3 py-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[0.65rem] text-(--ui-text-tertiary)">{event.date}</span>
                        <span className="text-[0.6rem] text-(--ui-text-quaternary)">#{i + 1}</span>
                      </div>
                      <p className="mt-0.5 text-xs text-foreground">{event.title}</p>
                      <p className="mt-0.5 text-[0.7rem] leading-relaxed text-(--ui-text-secondary)">{event.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="grid h-full place-items-center">
              <div className="text-center">
                <div className="mb-3 text-3xl">🧑</div>
                <p className="text-sm text-(--ui-text-tertiary)">选择左侧联系人查看画像</p>
                <p className="mt-1 text-xs text-(--ui-text-quaternary)">基于微信聊天记录自动生成</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

/* ── Contact List Item ───────────────────────── */

function ContactRow({
  active,
  contact,
  onSelect,
}: {
  active: boolean
  contact: Contact
  onSelect: () => void
}) {
  // displayTags: 行为标签优先，没有时回退到头两个普通标签
  const displayTags = contact.behaviorTags.length > 0
    ? contact.behaviorTags
    : contact.tags.slice(0, 2)

  return (
    <button
      className={cn(
        'flex w-full items-start gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors hover:bg-(--ui-control-hover-background)',
        active && 'bg-(--ui-control-active-background)',
      )}
      onClick={onSelect}
    >
      {/* avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-xs font-semibold text-(--ui-accent)">
        {contact.avatar}
      </div>
      {/* content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-1.5">
          <span className="truncate text-sm font-medium text-foreground">{contact.name}</span>
          {contact.alias && (
            <span className="shrink-0 text-[0.6rem] text-(--ui-text-tertiary)">{contact.alias}</span>
          )}
        </div>
        {displayTags.length > 0 && (
          <div className="mt-0.5 flex flex-wrap gap-1">
            {displayTags.map(tag => (
              <span
                className="rounded bg-(--ui-bg-quinary) px-1 py-px text-[0.55rem] leading-snug text-(--ui-text-tertiary)"
                key={tag}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </button>
  )
}

/* ── Info Row ────────────────────────────────── */

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-3 border-b border-(--ui-stroke-quaternary) py-2.5">
      <span className="w-16 shrink-0 text-xs text-(--ui-text-tertiary)">{label}</span>
      <span className="min-w-0 text-sm text-foreground">{value || '—'}</span>
    </div>
  )
}

/* ── Main View ───────────────────────────────── */

export function WechatPanel() {
  const { requestGateway } = useGatewayRequest()
  const [activeCategory, setActiveCategory] = useState<CategoryId>('untagged')
  const [activeContactId, setActiveContactId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<DetailTab>('basic')
  const [searchQuery, setSearchQuery] = useState('')

  // ── 微信账户（手动输入，localStorage 持久化）──
  const [wechatWxid, setWechatWxid] = useState<string>(
    () => localStorage.getItem('winpeek-wxid') || 'szyuyangmin'
  )
  const [wxidInput, setWxidInput] = useState(wechatWxid)
  const [saved, setSaved] = useState(false)

  const handleWxidSave = useCallback(() => {
    const v = wxidInput.trim()
    if (v) {
      setWechatWxid(v)
      localStorage.setItem('winpeek-wxid', v)
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    }
  }, [wxidInput])

  const activeContact = useMemo(
    () => MOCK_CONTACTS.find(c => c.id === activeContactId) ?? null,
    [activeContactId],
  )

  // Filter: category + keyword
  const filteredContacts = useMemo(() => {
    let list = MOCK_CONTACTS

    // "统计" "搜索" "同步" 展示全部（占位视图）
    if (activeCategory !== 'stats' && activeCategory !== 'search' && activeCategory !== 'sync') {
      list = list.filter(c => c.category === activeCategory)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      list = list.filter(c =>
        c.name.includes(q) ||
        c.alias.includes(q) ||
        c.wechatId.toLowerCase().includes(q) ||
        c.tags.some(t => t.includes(q)) ||
        c.behaviorTags.some(t => t.includes(q)),
      )
    }

    return list
  }, [activeCategory, searchQuery])

  const handleTabChange = useCallback((value: string) => {
    setActiveTab(value as DetailTab)
  }, [])

  const detailTabValue = activeTab satisfies string

  // ── 微信账户绑定栏（所有分类都显示）──
  const accountBar = (
    <div className="flex items-center gap-2 border-b border-(--ui-stroke-tertiary) px-3 py-1.5 shrink-0">
      <span className="text-[0.6rem] text-(--ui-text-tertiary) shrink-0">微信账户</span>
      <Input
        className="h-6 w-32 text-xs"
        onChange={e => { setWxidInput(e.target.value); setSaved(false) }}
        onKeyDown={e => e.key === 'Enter' && handleWxidSave()}
        placeholder="szyuyangmin"
        value={wxidInput}
      />
      <button
        className={cn(
          'rounded px-2 py-0.5 text-[0.6rem] transition-colors',
          saved ? 'bg-emerald-500/15 text-emerald-500' : 'bg-(--ui-accent)/10 text-(--ui-accent) hover:bg-(--ui-accent)/20'
        )}
        onClick={handleWxidSave}
      >{saved ? '已绑定' : '绑定'}</button>
      <span className="text-[0.55rem] text-(--ui-text-quaternary)">当前：{wechatWxid}</span>
    </div>
  )

  // ── Portrait analysis category ──
  if (activeCategory === 'portrait') {
    return (
      <div className="flex h-full min-h-0 flex-col">
        {accountBar}
        <PortraitAnalysisPanel wxid={wechatWxid} />
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      {accountBar}
      <div className="grid min-h-0 flex-1 grid-cols-1 sm:grid-cols-[4.5rem_14rem_minmax(0,1fr)]">
        {/* ── Column 1: Category Navigation ── */}
        <nav className="flex flex-col gap-0.5 border-r border-(--ui-stroke-tertiary) bg-(--ui-bg-quaternary) p-1.5">
          {CATEGORIES.map(cat => (
            <button
              className={cn(
                'flex flex-col items-center gap-0.5 rounded-md px-1 py-2 text-center transition-colors hover:bg-(--ui-control-hover-background)',
                activeCategory === cat.id
                  ? 'bg-(--ui-control-active-background) text-foreground'
                  : 'text-(--ui-text-tertiary)',
              )}
              key={cat.id}
              onClick={() => { setActiveCategory(cat.id); setSearchQuery('') }}
              title={cat.label}
            >
              <Codicon name={cat.icon} size="0.875rem" />
              <span className="text-[0.55rem] leading-tight">{cat.label}</span>
            </button>
          ))}
        </nav>

        {/* ── Column 2: Contact List ── */}
        <aside className="flex min-h-0 flex-col border-r border-(--ui-stroke-tertiary)">
          <header className="shrink-0 border-b border-(--ui-stroke-tertiary) px-3 py-2">
            <Input
              className="h-7 text-xs"
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="搜索姓名/备注/标签…"
              value={searchQuery}
            />
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain [scrollbar-gutter:stable]">
            {filteredContacts.length > 0 ? (
              filteredContacts.map(c => (
                <ContactRow
                  active={activeContactId === c.id}
                  contact={c}
                  key={c.id}
                  onSelect={() => setActiveContactId(c.id)}
                />
              ))
            ) : (
              <div className="px-3 py-8 text-center text-xs text-(--ui-text-quaternary)">
                暂无匹配联系人
              </div>
            )}
          </div>
        </aside>

        {/* ── Column 3: Detail Panel ── */}
        <main className="flex min-h-0 flex-col overflow-hidden">
          {activeContact ? (
            <>
              {/* contact header */}
              <header className="shrink-0 border-b border-(--ui-stroke-tertiary) px-5 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-sm font-bold text-(--ui-accent)">
                    {activeContact.avatar}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className="text-base font-semibold text-foreground">{activeContact.name}</span>
                      {activeContact.alias && (
                        <span className="text-sm text-(--ui-text-tertiary)">({activeContact.alias})</span>
                      )}
                    </div>
                    <div className="text-xs text-(--ui-text-tertiary)">
                      {activeContact.gender} · {activeContact.region}
                    </div>
                  </div>
                </div>
              </header>

              {/* tabs */}
              <div className="shrink-0 border-b border-(--ui-stroke-tertiary) px-5 py-2">
                <Tabs onValueChange={handleTabChange} value={detailTabValue}>
                  <TabsList>
                    <TabsTrigger value="basic">基础信息</TabsTrigger>
                    <TabsTrigger value="contact">联系方式</TabsTrigger>
                    <TabsTrigger value="tags">标签</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* tab content */}
              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain [scrollbar-gutter:stable]">
                <div className="mx-auto max-w-xl space-y-0 px-5 py-4">
                  {activeTab === 'basic' && (
                    <>
                      <InfoRow label="昵称" value={activeContact.name} />
                      <InfoRow label="备注" value={activeContact.alias} />
                      <InfoRow label="微信号" value={activeContact.wechatId} />
                      <InfoRow label="性别" value={activeContact.gender} />
                      <InfoRow label="地区" value={activeContact.region} />
                      <InfoRow label="来源" value={activeContact.source} />
                    </>
                  )}
                  {activeTab === 'contact' && (
                    <>
                      <InfoRow label="手机" value={activeContact.phone} />
                      <InfoRow label="邮箱" value={activeContact.email} />
                      <InfoRow label="微信号" value={activeContact.wechatId} />
                    </>
                  )}
                  {activeTab === 'tags' && (
                    <div className="space-y-4">
                      <section>
                        <h4 className="mb-2 text-xs font-medium text-(--ui-text-secondary)">标签</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {activeContact.tags.length > 0
                            ? activeContact.tags.map(tag => (
                                <Badge key={tag} variant="default">{tag}</Badge>
                              ))
                            : <span className="text-xs text-(--ui-text-quaternary)">暂无标签</span>}
                        </div>
                      </section>
                      <section>
                        <h4 className="mb-2 text-xs font-medium text-(--ui-text-secondary)">行为标签</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {activeContact.behaviorTags.length > 0
                            ? activeContact.behaviorTags.map(tag => (
                                <Badge key={tag} variant="muted">{tag}</Badge>
                              ))
                            : <span className="text-xs text-(--ui-text-quaternary)">暂无行为标签</span>}
                        </div>
                      </section>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            /* empty state */
            <div className="grid h-full place-items-center">
              <div className="text-center">
                <div className="mb-3 text-3xl">👥</div>
                <p className="text-sm text-(--ui-text-tertiary)">选择一个好友查看详情</p>
                <p className="mt-1 text-xs text-(--ui-text-quaternary)">WinPeek · 微信好友管理</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
