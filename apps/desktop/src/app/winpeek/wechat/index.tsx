import { useCallback, useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Codicon } from '@/components/ui/codicon'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

/* ── Types ───────────────────────────────────── */

type CategoryId = 'untagged' | 'starred' | 'groups' | 'group-members' | 'fuzzy' | 'stats' | 'search' | 'sync'
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
  const [activeCategory, setActiveCategory] = useState<CategoryId>('untagged')
  const [activeContactId, setActiveContactId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<DetailTab>('basic')
  const [searchQuery, setSearchQuery] = useState('')

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

  return (
    <div className="flex h-full min-h-0 flex-col">
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
