import { useStore } from '@nanostores/react'
import { useCallback, useMemo, useState } from 'react'

import { Button } from '../../../components/ui/button'
import { $gatewayState } from '../../../store/session'

/* ================================================================
   Mock 数据 — 从 MySQL winpeek-db2 实际数据提炼
   ================================================================ */

interface Friend {
  id: number
  wxid: string
  nickname: string
  alias: string
  region: string
  tags: string[]
  avatar_url: string
  signature: string
  shared_groups: number
  is_starred: boolean
  source: string
  first_met: string
  last_msg: string
  msg_count: number
  /** 8 维画像分 (0-100) */
  intimacy: number       // 亲密度
  trust: number          // 信任度
  respect: number        // 尊重度
  likeability: number    // 好感度
  business: number       // 商业价值
  growth: number         // 成长价值
  credit: number         // 经济信用
  reciprocity: number    // 互惠度
}

const FRIENDS: Friend[] = [
  { id:3179,wxid:'wxid_p202cnzx65ad22',nickname:'1A管家阿都',alias:'',region:'',tags:['服务','家政'],shared_groups:1,is_starred:false,source:'搜索添加',first_met:'2025-08',last_msg:'2026-05-21',msg_count:12,avatar_url:'',signature:'专业管家服务',intimacy:28,trust:55,respect:40,likeability:35,business:65,growth:10,credit:50,reciprocity:30 },
  { id:3180,wxid:'xspace777',nickname:'🔱徐久景（Xman Ming Xu)🔱',alias:'徐久景',region:'北京 朝阳',tags:['客户','投资'],shared_groups:2,is_starred:true,source:'名片分享',first_met:'2025-06',last_msg:'2026-06-15',msg_count:38,avatar_url:'',signature:'投资是一场修行',intimacy:52,trust:68,respect:72,likeability:58,business:85,growth:45,credit:70,reciprocity:60 },
  { id:3236,wxid:'wxid_zhangshan',nickname:'张三',alias:'',region:'深圳 南山',tags:['同学','技术'],shared_groups:1,is_starred:false,source:'群聊添加',first_met:'2024-03',last_msg:'2026-06-20',msg_count:156,avatar_url:'',signature:'代码改变世界',intimacy:72,trust:80,respect:65,likeability:75,business:30,growth:82,credit:78,reciprocity:68 },
  { id:3240,wxid:'wxid_lisi',nickname:'李四',alias:'李总',region:'广州 天河',tags:['客户','供应商'],shared_groups:0,is_starred:true,source:'手机号搜索',first_met:'2025-01',last_msg:'2026-06-10',msg_count:87,avatar_url:'',signature:'',intimacy:45,trust:60,respect:55,likeability:50,business:92,growth:35,credit:65,reciprocity:55 },
  { id:3274,wxid:'wangwu_weixin',nickname:'王五',alias:'',region:'北京 海淀',tags:['同事','前公司'],shared_groups:3,is_starred:false,source:'同事推荐',first_met:'2023-09',last_msg:'2026-05-28',msg_count:203,avatar_url:'',signature:'努力搬砖',intimacy:80,trust:88,respect:78,likeability:85,business:20,growth:70,credit:90,reciprocity:82 },
  { id:3301,wxid:'zhaoliu_88',nickname:'赵六',alias:'六哥',region:'上海 浦东',tags:['客户','投资'],shared_groups:1,is_starred:true,source:'群聊添加',first_met:'2025-04',last_msg:'2026-06-18',msg_count:64,avatar_url:'',signature:'天道酬勤',intimacy:48,trust:62,respect:58,likeability:52,business:88,growth:42,credit:72,reciprocity:58 },
  { id:3326,wxid:'sunqi_dev',nickname:'孙七',alias:'',region:'杭州 西湖',tags:['技术','开源'],shared_groups:2,is_starred:false,source:'GitHub',first_met:'2025-11',last_msg:'2026-06-17',msg_count:42,avatar_url:'',signature:'开源爱好者',intimacy:38,trust:55,respect:50,likeability:45,business:25,growth:78,credit:60,reciprocity:45 },
  { id:3350,wxid:'wxid_zhouba',nickname:'周八',alias:'',region:'成都 高新区',tags:['同学'],shared_groups:1,is_starred:false,source:'QQ好友',first_met:'2025-02',last_msg:'2026-04-30',msg_count:28,avatar_url:'',signature:'',intimacy:62,trust:70,respect:60,likeability:58,business:15,growth:35,credit:75,reciprocity:50 },
  { id:3374,wxid:'wujiuzhen',nickname:'吴九',alias:'九哥',region:'深圳 福田',tags:['客户','合作伙伴'],shared_groups:0,is_starred:true,source:'业务合作',first_met:'2025-05',last_msg:'2026-06-19',msg_count:95,avatar_url:'',signature:'诚信第一',intimacy:50,trust:72,respect:68,likeability:55,business:95,growth:40,credit:80,reciprocity:62 },
  { id:3400,wxid:'zhengshi_001',nickname:'郑十',alias:'',region:'广州 番禺',tags:['供应商'],shared_groups:1,is_starred:false,source:'展会',first_met:'2025-07',last_msg:'2026-05-15',msg_count:18,avatar_url:'',signature:'做好产品',intimacy:25,trust:50,respect:42,likeability:38,business:72,growth:20,credit:58,reciprocity:35 },
  { id:3625,wxid:'wxid_xiaomei',nickname:'意哥',alias:'意哥',region:'深圳',tags:['好友'],shared_groups:2,is_starred:true,source:'微信推荐',first_met:'2024-06',last_msg:'2026-06-21',msg_count:60,avatar_url:'',signature:'',intimacy:78,trust:85,respect:72,likeability:80,business:35,growth:55,credit:88,reciprocity:72 },
  { id:1857,wxid:'wxid_xg',nickname:'许国勇',alias:'国勇',region:'广东 深圳',tags:['好友','客户'],shared_groups:5,is_starred:true,source:'当面扫码',first_met:'2024-01',last_msg:'2026-06-21',msg_count:420,avatar_url:'',signature:'',intimacy:90,trust:92,respect:85,likeability:88,business:78,growth:72,credit:95,reciprocity:85 },
  { id:2143,wxid:'wxid_yym',nickname:'于杨敏',alias:'敏哥',region:'广东 深圳',tags:['同事','好友'],shared_groups:3,is_starred:true,source:'同事',first_met:'2024-08',last_msg:'2026-06-21',msg_count:312,avatar_url:'',signature:'',intimacy:82,trust:85,respect:80,likeability:78,business:55,growth:68,credit:85,reciprocity:78 },
  { id:2789,wxid:'wxid_silence',nickname:'易清清',alias:'清清',region:'',tags:['技术','好友'],shared_groups:1,is_starred:false,source:'群聊',first_met:'2025-03',last_msg:'2026-06-19',msg_count:88,avatar_url:'',signature:'全栈工程师',intimacy:68,trust:72,respect:65,likeability:70,business:40,growth:75,credit:70,reciprocity:62 },
  { id:2901,wxid:'wxid_yudahai',nickname:'于大海',alias:'大海',region:'山东 青岛',tags:['客户','合作'],shared_groups:2,is_starred:true,source:'朋友介绍',first_met:'2025-05',last_msg:'2026-06-16',msg_count:145,avatar_url:'',signature:'海纳百川',intimacy:58,trust:72,respect:60,likeability:55,business:82,growth:50,credit:78,reciprocity:65 },
]

type TabKey = 'profile' | 'portrait' | 'chat' | 'finance'

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: 'profile',  icon: '📋', label: '基本档案' },
  { key: 'portrait', icon: '🧠', label: '画像' },
  { key: 'chat',     icon: '💬', label: '聊天记录' },
  { key: 'finance',  icon: '💰', label: '经济往来' },
]

/* ================================================================
   子组件
   ================================================================ */

function Avatar({ name, size = 40 }: { name: string; size?: number }) {
  const initials = name.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '').slice(0, 2)
  const hue = name.split('').reduce((a, c) => a + c.charCodeAt(0), 0) % 360
  return (
    <div
      className="flex items-center justify-center rounded-full font-medium text-white shrink-0"
      style={{ width: size, height: size, backgroundColor: `hsl(${hue}, 55%, 55%)`, fontSize: size * 0.38 }}
    >
      {initials}
    </div>
  )
}

function RadarChart({ scores, size = 140 }: { scores: number[]; size?: number }) {
  const labels = ['亲密度','信任度','尊重度','好感度','商业价值','成长价值','经济信用','互惠度']
  const cx = size / 2, cy = size / 2, r = size * 0.38
  const angles = labels.map((_, i) => (Math.PI * 2 * i) / labels.length - Math.PI / 2)
  const grid = [0.25, 0.5, 0.75, 1.0]
  const points = scores.map((v, i) => {
    const a = angles[i]
    return `${cx + r * (v / 100) * Math.cos(a)},${cy + r * (v / 100) * Math.sin(a)}`
  }).join(' ')

  return (
    <svg className="shrink-0" height={size} width={size} viewBox={`0 0 ${size} ${size}`}>
      {/* 网格 */}
      {grid.map(g => (
        <polygon
          fill="none"
          key={g}
          points={angles.map(a => `${cx + r * g * Math.cos(a)},${cy + r * g * Math.sin(a)}`).join(' ')}
          stroke="var(--ui-stroke-tertiary)"
          strokeWidth={0.5}
        />
      ))}
      {/* 轴 */}
      {angles.map((a, i) => (
        <line key={i} x1={cx} y1={cy} x2={cx + r * Math.cos(a)} y2={cy + r * Math.sin(a)}
          stroke="var(--ui-stroke-tertiary)" strokeWidth={0.5} />
      ))}
      {/* 数据 */}
      <polygon fill="var(--ui-accent)" fillOpacity={0.2} points={points} stroke="var(--ui-accent)" strokeWidth={1.5} />
      {/* 标签 */}
      {angles.map((a, i) => {
        const lx = cx + (r + 18) * Math.cos(a)
        const ly = cy + (r + 18) * Math.sin(a)
        return (
          <text key={i} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
            fill="var(--ui-text-secondary)" fontSize={8}>
            {scores[i]}
          </text>
        )
      })}
    </svg>
  )
}

/* ================================================================
   聊天记录模拟数据
   ================================================================ */

interface ChatMsg {
  id: number
  from_me: boolean
  content: string
  ts: string
  type: string
}

const CHAT_HISTORY: Record<number, ChatMsg[]> = {
  1857: [
    { id:1, from_me:false, content:'Hermes 现在进展怎么样了？', ts:'2026-06-21 14:30', type:'text' },
    { id:2, from_me:true, content:'文档体系基本搭好了，5层分离方案落地了', ts:'2026-06-21 14:32', type:'text' },
    { id:3, from_me:false, content:'不错，那数据库那边呢？', ts:'2026-06-21 14:33', type:'text' },
    { id:4, from_me:true, content:'查过了，winpeek-db2 有 63814 条记录，量挺大', ts:'2026-06-21 14:35', type:'text' },
    { id:5, from_me:false, content:'好，那我这边CC在处理了', ts:'2026-06-21 14:36', type:'text' },
    { id:6, from_me:true, content:'OK，处理完我审核', ts:'2026-06-21 14:38', type:'text' },
  ],
  2143: [
    { id:1, from_me:false, content:'yu2 上 Claude Code 装好了', ts:'2026-06-20 09:15', type:'text' },
    { id:2, from_me:true, content:'好的，我这边 Hermes 也能连了', ts:'2026-06-20 09:20', type:'text' },
    { id:3, from_me:false, content:'MQTT 通了，say 命令正常', ts:'2026-06-20 10:00', type:'text' },
    { id:4, from_me:true, content:'收到，我测试一下', ts:'2026-06-20 10:05', type:'text' },
  ],
  3625: [
    { id:1, from_me:false, content:'兄弟，最近忙啥呢', ts:'2026-06-21 20:00', type:'text' },
    { id:2, from_me:true, content:'搞微信自动化，一堆事', ts:'2026-06-21 20:05', type:'text' },
  ],
}

/* ================================================================
   主组件
   ================================================================ */

type SortKey = 'name' | 'recent' | 'intimacy' | 'business'

export function WechatPanel({ onClose }: { onClose?: () => void }) {
  const gatewayState = useStore($gatewayState)
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<number>(1857) // 默认选中许国勇
  const [activeTab, setActiveTab] = useState<TabKey>('profile')
  const [sortBy, setSortBy] = useState<SortKey>('recent')
  const [filterTag, setFilterTag] = useState<string | null>(null)

  const allTags = useMemo(() => [...new Set(FRIENDS.flatMap(f => f.tags))].sort(), [])

  const filtered = useMemo(() => {
    let list = [...FRIENDS]
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(f =>
        f.nickname.toLowerCase().includes(q) ||
        f.alias.toLowerCase().includes(q) ||
        f.wxid.toLowerCase().includes(q)
      )
    }
    if (filterTag) {
      list = list.filter(f => f.tags.includes(filterTag))
    }
    if (sortBy === 'name') list.sort((a, b) => a.nickname.localeCompare(b.nickname, 'zh'))
    else if (sortBy === 'recent') list.sort((a, b) => b.last_msg.localeCompare(a.last_msg))
    else if (sortBy === 'intimacy') list.sort((a, b) => b.intimacy - a.intimacy)
    else if (sortBy === 'business') list.sort((a, b) => b.business - a.business)
    return list
  }, [search, filterTag, sortBy])

  const selected = FRIENDS.find(f => f.id === selectedId)!

  const [chatInput, setChatInput] = useState('')
  const chatMsgs = CHAT_HISTORY[selectedId] ?? []

  return (
    <div className="flex h-full bg-(--ui-editor-surface-background)">
      {/* ===== 左侧列表 ===== */}
      <div className="flex w-[320px] shrink-0 flex-col border-r border-(--ui-stroke-tertiary)">
        {/* 标题 */}
        <div className="flex items-center justify-between px-4 py-3">
          <h2 className="text-base font-semibold">微信 CRM</h2>
          {onClose && <button className="text-(--ui-text-tertiary) hover:text-(--ui-text-primary)" onClick={onClose}>✕</button>}
        </div>

        {/* 搜索 */}
        <div className="px-4 pb-2">
          <input
            className="w-full rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-card) px-3 py-1.5 text-sm outline-none placeholder:text-(--ui-text-quaternary) focus:border-(--ui-accent)"
            placeholder="🔍 搜索好友昵称/微信号..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* 排序+标签 */}
        <div className="flex items-center gap-2 px-4 pb-2">
          <select className="rounded border border-(--ui-stroke-tertiary) bg-transparent px-2 py-0.5 text-xs text-(--ui-text-secondary)"
            value={sortBy} onChange={e => setSortBy(e.target.value as SortKey)}>
            <option value="recent">最近聊天</option>
            <option value="name">按名称</option>
            <option value="intimacy">亲密度</option>
            <option value="business">商业价值</option>
          </select>
          {filterTag && (
            <button className="rounded bg-(--ui-accent)/10 px-2 py-0.5 text-xs text-(--ui-accent)"
              onClick={() => setFilterTag(null)}>
              {filterTag} ✕
            </button>
          )}
        </div>

        {/* 标签快速筛选 */}
        <div className="flex flex-wrap gap-1 px-4 pb-2">
          {['好友','客户','技术','同学','同事','投资','供应商'].map(t => (
            <button key={t}
              className={`rounded-full px-2 py-0.5 text-xs transition-colors ${
                filterTag === t
                  ? 'bg-(--ui-accent) text-white'
                  : 'bg-(--ui-bg-quaternary) text-(--ui-text-tertiary) hover:text-(--ui-text-secondary)'
              }`}
              onClick={() => setFilterTag(filterTag === t ? null : t)}
            >
              {t}
            </button>
          ))}
        </div>

        {/* 好友列表 */}
        <div className="flex-1 overflow-auto">
          {filtered.map(f => (
            <button
              className={`flex w-full items-center gap-3 border-b border-(--ui-stroke-tertiary) px-4 py-2.5 text-left transition-colors hover:bg-(--ui-bg-quaternary) ${
                selectedId === f.id ? 'bg-(--ui-bg-quaternary)' : ''
              }`}
              key={f.id}
              onClick={() => setSelectedId(f.id)}
            >
              <Avatar name={f.nickname} size={36} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="truncate text-sm font-medium">{f.alias || f.nickname}</span>
                  {f.is_starred && <span className="text-xs">⭐</span>}
                </div>
                <div className="truncate text-xs text-(--ui-text-tertiary)">
                  {f.last_msg === '2026-06-21' ? '刚刚' : f.last_msg}
                </div>
              </div>
              <div className="flex shrink-0 flex-col items-end">
                <span className="text-xs text-(--ui-text-quaternary)">{f.msg_count}条</span>
                {f.business >= 80 && <span className="mt-0.5 rounded bg-green-500/10 px-1 text-[10px] text-green-500">高价值</span>}
              </div>
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="py-12 text-center text-sm text-(--ui-text-tertiary)">无匹配好友</div>
          )}
        </div>

        {/* 底部统计 */}
        <div className="border-t border-(--ui-stroke-tertiary) px-4 py-2 text-xs text-(--ui-text-quaternary)">
          共 {FRIENDS.length} 位联系人 · 显示 {filtered.length} 位
        </div>
      </div>

      {/* ===== 右侧详情 ===== */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* 顶部信息栏 */}
        <div className="flex items-center gap-4 border-b border-(--ui-stroke-tertiary) px-6 py-4">
          <Avatar name={selected.nickname} size={48} />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold">{selected.alias || selected.nickname}</h2>
              {selected.is_starred && <span className="text-sm">⭐</span>}
              {selected.business >= 80 && <span className="rounded bg-green-500/10 px-1.5 py-0.5 text-[10px] font-medium text-green-500">高价值客户</span>}
            </div>
            <p className="mt-0.5 text-xs text-(--ui-text-tertiary)">
              {selected.region && `${selected.region} · `}{selected.shared_groups} 个共同群 · 首遇 {selected.first_met}
            </p>
          </div>
          <Button size="xs" variant="secondary">✉️ 发消息</Button>
          <Button size="xs" variant="outline">📊 数据同步</Button>
        </div>

        {/* Tab 页签 */}
        <div className="flex gap-0 border-b border-(--ui-stroke-tertiary) px-6">
          {TABS.map(t => (
            <button key={t.key}
              className={`border-b-2 px-4 py-2.5 text-xs font-medium transition-colors ${
                activeTab === t.key
                  ? 'border-(--ui-accent) text-(--ui-text-primary)'
                  : 'border-transparent text-(--ui-text-tertiary) hover:text-(--ui-text-secondary)'
              }`}
              onClick={() => setActiveTab(t.key)}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Tab 内容 */}
        <div className="flex-1 overflow-auto p-6">
          {/* 基本档案 */}
          {activeTab === 'profile' && (
            <div className="grid max-w-2xl grid-cols-2 gap-x-8 gap-y-3 text-sm">
              <div className="text-(--ui-text-tertiary)">昵称</div><div>{selected.nickname}</div>
              <div className="text-(--ui-text-tertiary)">微信号</div><div className="font-mono text-xs">{selected.wxid}</div>
              <div className="text-(--ui-text-tertiary)">备注</div><div>{selected.alias || '—'}</div>
              <div className="text-(--ui-text-tertiary)">地区</div><div>{selected.region || '—'}</div>
              <div className="text-(--ui-text-tertiary)">签名</div><div className="text-(--ui-text-secondary)">{selected.signature || '—'}</div>
              <div className="text-(--ui-text-tertiary)">标签</div>
              <div className="flex flex-wrap gap-1">
                {selected.tags.map(t => (
                  <span key={t} className="rounded bg-(--ui-bg-quaternary) px-1.5 py-0.5 text-xs">{t}</span>
                ))}
              </div>
              <div className="text-(--ui-text-tertiary)">添加来源</div><div>{selected.source}</div>
              <div className="text-(--ui-text-tertiary)">首次认识</div><div>{selected.first_met}</div>
              <div className="text-(--ui-text-tertiary)">共同群聊</div><div>{selected.shared_groups} 个</div>
              <div className="text-(--ui-text-tertiary)">消息总数</div><div>{selected.msg_count} 条</div>
              <div className="text-(--ui-text-tertiary)">最后消息</div><div>{selected.last_msg}</div>
            </div>
          )}

          {/* 画像 */}
          {activeTab === 'portrait' && (
            <div className="space-y-6">
              <div className="flex items-start gap-8">
                <RadarChart scores={[selected.intimacy, selected.trust, selected.respect, selected.likeability, selected.business, selected.growth, selected.credit, selected.reciprocity]} size={180} />
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">画像摘要</h4>
                  <p className="max-w-md text-xs leading-relaxed text-(--ui-text-secondary)">
                    {selected.nickname} 与你的关系整体
                    {selected.intimacy >= 70 ? '密切' : selected.intimacy >= 40 ? '一般' : '疏远'}，
                    信任度{selected.trust >= 80 ? '较高' : selected.trust >= 50 ? '中等' : '偏低'}。
                    {selected.business >= 80 ? '具有较高的商业价值，建议重点维护。' : ''}
                    {selected.growth >= 70 ? '在成长价值方面可互相学习。' : ''}
                    {selected.credit >= 80 ? '经济信用良好，值得信赖。' : ''}
                  </p>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 pt-2">
                    {[
                      ['亲密度', selected.intimacy],
                      ['信任度', selected.trust],
                      ['尊重度', selected.respect],
                      ['好感度', selected.likeability],
                      ['商业价值', selected.business],
                      ['成长价值', selected.growth],
                      ['经济信用', selected.credit],
                      ['互惠度', selected.reciprocity],
                    ].map(([label, score]) => (
                      <div className="flex items-center gap-2 text-xs" key={label as string}>
                        <span className="w-16 text-(--ui-text-tertiary)">{label as string}</span>
                        <div className="h-1.5 flex-1 rounded-full bg-(--ui-bg-quaternary)">
                          <div className="h-full rounded-full bg-(--ui-accent)" style={{ width: `${score}%`, opacity: 0.5 + (score as number) / 200 }} />
                        </div>
                        <span className="w-6 text-right font-mono text-(--ui-text-secondary)">{score as number}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 聊天记录 */}
          {activeTab === 'chat' && (
            <div className="flex h-full flex-col">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-xs text-(--ui-text-tertiary)">共 {chatMsgs.length} 条消息（模拟）</span>
                <Button size="xs" variant="secondary">🔄 采集更多</Button>
              </div>
              <div className="flex-1 space-y-3 overflow-auto">
                {chatMsgs.length === 0 ? (
                  <div className="py-16 text-center text-sm text-(--ui-text-tertiary)">暂无聊天记录，点击「采集更多」获取</div>
                ) : (
                  chatMsgs.map(m => (
                    <div className={`flex ${m.from_me ? 'justify-end' : 'justify-start'}`} key={m.id}>
                      <div className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${
                        m.from_me
                          ? 'bg-(--ui-accent) text-white'
                          : 'bg-(--ui-bg-quaternary) text-(--ui-text-primary)'
                      }`}>
                        <p>{m.content}</p>
                        <p className={`mt-1 text-[10px] ${m.from_me ? 'text-white/60' : 'text-(--ui-text-quaternary)'}`}>{m.ts}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
              {/* 输入框 */}
              <div className="mt-3 flex gap-2 border-t border-(--ui-stroke-tertiary) pt-3">
                <input
                  className="flex-1 rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-card) px-3 py-1.5 text-sm outline-none placeholder:text-(--ui-text-quaternary) focus:border-(--ui-accent)"
                  placeholder="输入消息..."
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { setChatInput(''); } }}
                />
                <Button disabled={!chatInput} onClick={() => setChatInput('')} size="sm" variant="secondary">发送</Button>
              </div>
            </div>
          )}

          {/* 经济往来 */}
          {activeTab === 'finance' && (
            <div className="max-w-lg space-y-4">
              <div className="rounded-lg border border-(--ui-stroke-tertiary) p-4">
                <h4 className="mb-2 text-sm font-medium">借贷记录</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between rounded bg-green-500/5 px-3 py-2">
                    <span>借款 ¥20,000</span>
                    <span className="text-xs text-(--ui-text-tertiary)">约定 2025-12 还</span>
                    <span className="text-xs text-green-500">未到期</span>
                  </div>
                  <div className="flex items-center justify-between rounded bg-red-500/5 px-3 py-2">
                    <span>代付 ¥500</span>
                    <span className="text-xs text-(--ui-text-tertiary)">逾期 3 天</span>
                    <span className="text-xs text-red-500">⚠️ 逾期</span>
                  </div>
                </div>
              </div>
              <div className="rounded-lg border border-(--ui-stroke-tertiary) p-4">
                <h4 className="mb-2 text-sm font-medium">交易统计</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-(--ui-text-tertiary)">总借出</span><br/><span className="text-lg font-semibold">¥25,000</span></div>
                  <div><span className="text-(--ui-text-tertiary)">已收回</span><br/><span className="text-lg font-semibold">¥4,500</span></div>
                  <div><span className="text-(--ui-text-tertiary)">净头寸</span><br/><span className="text-lg font-semibold text-red-500">-¥20,500</span></div>
                  <div><span className="text-(--ui-text-tertiary)">守信率</span><br/><span className="text-lg font-semibold text-green-500">85%</span></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
