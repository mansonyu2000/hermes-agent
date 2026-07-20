import { useCallback, useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import { cn } from '@/lib/utils'
import { notifyError } from '@/store/notifications'

import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'
import { DetailColumn, ListColumn, MasterDetail } from '../../master-detail'

/* ── Types ── */

interface HwInfo {
  cpu: { name: string; cores: number }
  memory: { total_gb: number | string; available_gb?: number | string }
  disks: { drive?: string; mount?: string; total_gb: number }[]
  gpus: { name: string; memory_mb: string }[]
  os: { system: string; release: string; hostname: string; machine: string }
}

interface SoftwareItem {
  id: number
  name: string
  company: string
  version: string
  install_path: string
  exe_path: string
  icon_path: string
  category: string
  exit_normal: number | null
  last_launched_at: string | null
}

interface ScanResult {
  hardware: HwInfo
  software: { scanned: number; synced: number; created: number; updated: number }
}

type CatMap = Record<string, SoftwareItem[]>

const CAT_COLORS: Record<string, string> = {
  '社交': 'bg-blue-500/10 text-blue-600',
  '商城': 'bg-orange-500/10 text-orange-600',
  '金融': 'bg-red-500/10 text-red-600',
  '政务': 'bg-cyan-500/10 text-cyan-600',
  '编程': 'bg-violet-500/10 text-violet-600',
  '办公': 'bg-sky-500/10 text-sky-600',
  '图形': 'bg-pink-500/10 text-pink-600',
  '磁盘': 'bg-amber-500/10 text-amber-600',
  '影音': 'bg-indigo-500/10 text-indigo-600',
  '安全': 'bg-emerald-500/10 text-emerald-600',
  '其它': 'bg-gray-500/10 text-gray-600',
}

const CAT_ICONS: Record<string, string> = {
  '社交': '💬', '商城': '🛒', '金融': '🏦', '政务': '🏛️',
  '编程': '💻', '办公': '📋', '图形': '🎨', '磁盘': '💾',
  '影音': '🎬', '安全': '🛡️', '其它': '📦',
}

const PRIORITY_CATS = ['社交', '商城', '金融', '政务', '编程', '办公', '图形', '磁盘', '影音', '安全']

/* ── Page ── */

export function HwInfoView({ onClose }: { onClose: () => void }) {
  const { requestGateway: rq } = useGatewayRequest()
  const [hw, setHw] = useState<HwInfo | null>(null)
  const [cats, setCats] = useState<CatMap>({})
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState<ScanResult['software'] | null>(null)
  const [expandedCats, setExpandedCats] = useState<Set<string>>(new Set(PRIORITY_CATS))
  const [viewExe, setViewExe] = useState<SoftwareItem | null>(null)

  const loadAll = useCallback(async () => {
    try {
      const [hwData, catData]: [any, any] = await Promise.all([
        rq('winpeek_hwinfo', {}),
        rq('winpeek_software_by_category', {}),
      ])
      if (hwData?.hardware) setHw(hwData.hardware)
      if (catData?.categories) setCats(catData.categories)
    } catch { /* silent */ }
  }, [rq])

  useEffect(() => { loadAll() }, [loadAll])

  const handleScan = useCallback(async () => {
    setScanning(true)
    try {
      const data: any = await rq('winpeek_scan_sync', {})
      if (data?.software) setScanResult(data.software)
      await loadAll()
    } catch (e) { notifyError(e, '扫描失败') }
    setScanning(false)
  }, [rq, loadAll])

  // ── Hardware Panel ──
  const hwPanel = hw ? (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
          <div className="text-(--ui-text-quaternary)">操作系统</div>
          <div className="font-medium text-foreground">{hw.os.system} {hw.os.release}</div>
          <div className="text-(--ui-text-quaternary)">{hw.os.hostname} · {hw.os.machine}</div>
        </div>
        <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
          <div className="text-(--ui-text-quaternary)">处理器</div>
          <div className="font-medium text-foreground">{hw.cpu.cores} 核心</div>
          <div className="truncate text-(--ui-text-quaternary)">{hw.cpu.name}</div>
        </div>
        <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
          <div className="text-(--ui-text-quaternary)">内存</div>
          <div className="font-medium text-foreground">{hw.memory.total_gb} GB</div>
          {hw.memory.available_gb != null && <div className="text-(--ui-text-quaternary)">{hw.memory.available_gb} GB 可用</div>}
        </div>
        <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2">
          <div className="text-(--ui-text-quaternary)">磁盘</div>
          {hw.disks.slice(0, 3).map(d => (
            <div key={d.drive || d.mount} className="font-medium text-foreground">
              {d.drive || d.mount} {d.total_gb} GB
            </div>
          ))}
        </div>
      </div>
      {hw.gpus.length > 0 && (
        <div className="rounded-lg bg-(--ui-bg-tertiary) px-3 py-2 text-xs">
          <div className="text-(--ui-text-quaternary)">显卡</div>
          {hw.gpus.map((g, i) => (
            <div key={i} className="font-medium text-foreground">{g.name} ({g.memory_mb} MB)</div>
          ))}
        </div>
      )}
    </div>
  ) : null

  const toggleCat = (cat: string) => setExpandedCats(prev => {
    const next = new Set(prev)
    if (next.has(cat)) next.delete(cat); else next.add(cat)
    return next
  })

  const sortedCats = Object.keys(cats)
  sortedCats.sort((a, b) => {
    const ia = PRIORITY_CATS.indexOf(a), ib = PRIORITY_CATS.indexOf(b)
    if (ia === -1 && ib === -1) return a.localeCompare(b)
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })

  const totalApps = Object.values(cats).reduce((s, a) => s + a.length, 0)

  return (
    <MasterDetail>
      <ListColumn>
        <div className="flex h-full flex-col">
          <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-3 py-2.5">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">本机资产</span>
              <Badge variant="secondary" className="text-[0.6rem]">{totalApps} 应用</Badge>
            </div>
            <Button size="xs" variant="secondary" onClick={handleScan} disabled={scanning}>
              <Codicon name={scanning ? 'loading' : 'refresh'} size={12} spinning={scanning} />
              <span className="ml-1">{scanning ? '扫描中…' : '扫描同步'}</span>
            </Button>
          </header>
          <div className="flex-1 overflow-y-auto">
            {/* Hardware section */}
            <div className="border-b border-(--ui-stroke-quaternary) px-3 py-2.5">
              <div
                className="flex cursor-pointer items-center gap-2 text-xs font-medium text-(--ui-text-secondary) hover:text-foreground"
                onClick={() => toggleCat('__hw__')}
              >
                <span className="text-[0.6rem] transition-transform" style={{ transform: expandedCats.has('__hw__') ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
                <span>🖥️ 硬件信息</span>
              </div>
              {expandedCats.has('__hw__') && (hw ? hwPanel : <p className="text-xs text-(--ui-text-quaternary) px-1 py-2">加载中…</p>)}
            </div>
            {/* Software categories */}
            {sortedCats.map(cat => {
              const items = cats[cat]
              const expanded = expandedCats.has(cat)
              return (
                <div key={cat} className="border-b border-(--ui-stroke-quaternary)">
                  <div
                    className="flex cursor-pointer items-center gap-2 px-3 py-2 hover:bg-(--ui-control-hover-background)"
                    onClick={() => toggleCat(cat)}
                  >
                    <span className="text-[0.6rem] transition-transform" style={{ transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
                    <span className="text-sm">{CAT_ICONS[cat] || '📦'}</span>
                    <span className="text-xs font-medium text-foreground">{cat}</span>
                    <Badge className="ml-auto text-[0.55rem]">{items.length}</Badge>
                  </div>
                  {expanded && items.map(s => (
                    <div
                      key={s.id}
                      className={cn(
                        'flex cursor-pointer items-center gap-2.5 border-t border-(--ui-stroke-quaternary) px-5 py-1.5 text-xs hover:bg-(--ui-control-hover-background)',
                        viewExe?.id === s.id && 'bg-(--ui-control-active-background)'
                      )}
                      onClick={() => setViewExe(s)}
                    >
                      <span className="truncate flex-1 text-foreground">{s.name}</span>
                      {s.version && <span className="text-(--ui-text-quaternary) shrink-0">v{s.version}</span>}
                    </div>
                  ))}
                </div>
              )
            })}
            {sortedCats.length === 0 && (
              <p className="p-4 text-center text-xs text-(--ui-text-quaternary)">点击"扫描同步"发现已安装软件</p>
            )}
          </div>
        </div>
      </ListColumn>

      <DetailColumn>
        {viewExe ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Button size="xs" variant="ghost" onClick={() => setViewExe(null)}>← 返回</Button>
              <span className="text-sm font-medium text-foreground">{viewExe.name}</span>
            </div>
            <dl className="space-y-2 text-xs">
              {viewExe.company && <Row label="公司" value={viewExe.company} />}
              {viewExe.version && <Row label="版本" value={viewExe.version} />}
              {viewExe.category && <Row label="分类" value={viewExe.category} />}
              {viewExe.install_path && <Row label="安装路径" value={viewExe.install_path} mono />}
              {viewExe.exe_path && <Row label="可执行文件" value={viewExe.exe_path} mono />}
              {viewExe.exit_normal != null && <Row label="上次退出" value={viewExe.exit_normal ? '正常' : '异常'} />}
            </dl>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-(--ui-text-quaternary)">
            {scanResult ? (
              <div className="text-center space-y-2">
                <div className="text-2xl">✅</div>
                <p>扫描完成：{scanResult.scanned} 个条目</p>
                <p className="text-xs">同步 {scanResult.synced} · 新增 {scanResult.created} · 更新 {scanResult.updated}</p>
              </div>
            ) : (
              <p>选择一个软件查看详情</p>
            )}
          </div>
        )}
      </DetailColumn>
    </MasterDetail>
  )
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-(--ui-text-quaternary)">{label}</dt>
      <dd className={cn('mt-0.5 text-foreground', mono && 'font-mono text-[0.7rem] break-all')}>{value || '—'}</dd>
    </div>
  )
}
