import { useCallback, useEffect, useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { notifyError } from '@/store/notifications'

import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'
import { DetailColumn, ListColumn, MasterDetail } from '../../master-detail'

interface HwInfo {
  cpu: { name: string; cores: number }
  memory: { total_gb: number | string; available_gb?: number | string }
  disks: { drive?: string; mount?: string; total_gb: number }[]
  gpus: { name: string; memory_mb: string }[]
  os: { system: string; release: string; hostname: string; machine: string }
}
interface AppInfo {
  id: number; name: string; slug: string
  company: string; version: string
  install_path: string; exe_path: string; icon_path: string
  icon_data?: string  // base64 data URI
  category: string; description: string
  exit_normal: number | null; last_launched_at: string | null
}

const CATEGORIES = ['all', 'social', 'shop', 'finance', 'gov', 'dev', 'office', 'gfx', 'disk', 'video', 'sec', 'other'] as const
type CatKey = typeof CATEGORIES[number]

const CAT_LABEL: Record<string, string> = {
  social: 'Social', shop: 'Shop', finance: 'Finance', gov: 'Gov',
  dev: 'Dev', office: 'Office', gfx: 'GFX', disk: 'Disk',
  video: 'Video', sec: 'Sec', other: 'Other',
}

const CAT_NORMALIZE: Record<string, string> = {
  'Video': 'video', 'Social': 'social',
}

function normCat(cat: string): string {
  const m = CAT_NORMALIZE[cat]
  if (m) return m
  if (CATEGORIES.includes(cat as CatKey)) return cat
  return 'other'
}

function appLetter(name: string): string { return (name || '?').charAt(0).toUpperCase() }

/** Main component */
export function HwInfoView({ onClose }: { onClose: () => void }) {
  const { requestGateway: rq } = useGatewayRequest()
  const [hw, setHw] = useState<HwInfo | null>(null)
  const [apps, setApps] = useState<AppInfo[]>([])
  const [scanning, setScanning] = useState(false)
  const [viewApp, setViewApp] = useState<AppInfo | null>(null)
  const [activeCat, setActiveCat] = useState<CatKey>('all')
  const [searchQ, setSearchQ] = useState('')

  const loadAll = useCallback(async () => {
    try {
      const [hwData, swData]: [any, any] = await Promise.all([
        rq('winpeek_hwinfo', {}),
        rq('winpeek_software_list', {}),
      ])
      if (hwData?.hardware) setHw(hwData.hardware)
      if (swData?.softwares) setApps(swData.softwares)
    } catch { /* silent */ }
  }, [rq])

  useEffect(() => { loadAll() }, [loadAll])

  const handleScan = useCallback(async () => {
    setScanning(true)
    try { await rq('winpeek_scan_sync', {}); await loadAll() }
    catch (e: any) { notifyError(e, 'Scan failed') }
    setScanning(false)
  }, [rq, loadAll])

  const normApps = useMemo(() => apps.map(a => ({
    ...a, norm: normCat(a.category || ''),
  })), [apps])

  const filtered = useMemo(() => {
    let items = normApps
    if (activeCat !== 'all') items = items.filter(a => a.norm === activeCat)
    const lq = searchQ.trim().toLowerCase()
    if (lq) {
      items = items.filter(a =>
        [a.name, a.company, a.version, a.install_path, a.exe_path, a.description]
          .some(f => (f || '').toLowerCase().includes(lq))
      )
    }
    return items.sort((a, b) => a.name.localeCompare(b.name))
  }, [normApps, activeCat, searchQ])

  const catCounts = useMemo(() => {
    const m: Record<string, number> = {}
    for (const a of normApps) m[a.norm] = (m[a.norm] || 0) + 1
    return m
  }, [normApps])

  const total = normApps.length

  return (
    <MasterDetail>
      <ListColumn>
        <div className="flex h-full flex-col">
          <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">Software</span>
              <Badge variant="secondary" className="text-[0.6rem]">{total}</Badge>
            </div>
            <Button size="xs" variant="secondary" onClick={handleScan} disabled={scanning}>
              <Codicon name={scanning ? 'loading' : 'refresh'} size={11} spinning={scanning} />
              <span className="ml-1">{scanning ? 'Scanning' : 'Scan'}</span>
            </Button>
          </header>

          <div className="border-b border-(--ui-stroke-quaternary) px-2 py-1.5">
            <Input
              className="h-7 text-xs"
              onChange={e => setSearchQ(e.target.value)}
              placeholder="Search name, company, version, path..."
              value={searchQ}
            />
          </div>

          <div className="flex gap-0.5 overflow-x-auto border-b border-(--ui-stroke-quaternary) px-2 py-1.5">
            {CATEGORIES.map(cat => {
              if (cat === 'all') {
                return (
                  <button key={cat} className={cn('shrink-0 rounded-full px-2.5 py-0.5 text-[0.65rem] font-medium transition-colors',
                    activeCat === cat ? 'bg-(--ui-accent) text-white' : 'text-(--ui-text-tertiary) hover:bg-(--ui-control-hover-background)')}
                    onClick={() => setActiveCat(cat)}>
                    All {total}
                  </button>
                )
              }
              const count = catCounts[cat] || 0
              if (count === 0) return null
              return (
                <button key={cat} className={cn('shrink-0 rounded-full px-2.5 py-0.5 text-[0.65rem] font-medium transition-colors',
                  activeCat === cat ? 'bg-(--ui-accent) text-white' : 'text-(--ui-text-tertiary) hover:bg-(--ui-control-hover-background)')}
                  onClick={() => setActiveCat(cat)}>
                  {CAT_LABEL[cat] || cat} {count}
                </button>
              )
            })}
          </div>

          <div className="flex-1 overflow-y-auto">
            {filtered.map(app => (
              <div
                key={app.id}
                className={cn('flex cursor-pointer items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2 hover:bg-(--ui-control-hover-background) transition-colors',
                  viewApp?.id === app.id && 'bg-(--ui-control-active-background)')}
                onClick={() => setViewApp(app)}
              >
                {app.icon_data ? (
                  <img className="h-8 w-8 shrink-0 rounded-lg object-contain" src={app.icon_data} alt={app.name} />
                ) : (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-(--ui-bg-tertiary) text-xs font-bold text-(--ui-text-tertiary)">
                    {appLetter(app.name)}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="truncate text-sm font-medium text-foreground">{app.name}</span>
                  </div>
                  <div className="mt-0.5 flex items-center gap-2 text-[0.6rem] text-(--ui-text-quaternary)">
                    {app.company && <span>{app.company}</span>}
                    {app.version && <span>v{app.version}</span>}
                    {app.exe_path && <span className="hidden truncate sm:inline">{app.exe_path.split('\\').pop()}</span>}
                  </div>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="p-6 text-center text-xs text-(--ui-text-quaternary)">
                {total === 0 ? 'Click Scan to discover installed software' : 'No matching apps'}
              </p>
            )}
          </div>
        </div>
      </ListColumn>

      <DetailColumn>
        <div className="space-y-4">
          {hw && (
            <div>
              <div className="mb-2 text-xs font-semibold text-(--ui-text-secondary) uppercase tracking-wider">
                Hardware &mdash; {hw.os.hostname}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <HwCard label="OS" value={hw.os.system + ' ' + hw.os.release} sub={hw.os.machine} />
                <HwCard label="CPU" value={hw.cpu.cores + ' cores'} sub={hw.cpu.name} />
                <HwCard label="RAM" value={hw.memory.total_gb + ' GB'}
                  sub={hw.memory.available_gb != null ? hw.memory.available_gb + ' GB available' : undefined} />
                <HwCard label="Disks" value="">
                  {hw.disks.slice(0, 4).map((d, i) => (
                    <div key={i} className="text-xs font-medium text-foreground truncate">{d.drive || d.mount} {d.total_gb}GB</div>
                  ))}
                </HwCard>
              </div>
              {hw.gpus.length > 0 && (
                <div className="mt-2">
                  <HwCard label="GPU" value={hw.gpus.map(g => g.name).join(', ')}
                    sub={hw.gpus.map(g => g.memory_mb + 'MB').join(', ')} />
                </div>
              )}
            </div>
          )}

          {viewApp ? (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold text-(--ui-text-secondary) uppercase tracking-wider">Details</span>
                <Button size="xs" variant="ghost" className="h-5 text-[0.6rem]" onClick={() => setViewApp(null)}>X</Button>
              </div>
              <div className="rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-4">
                <div className="mb-3 flex items-center gap-3">
                  {viewApp.icon_data ? (
                    <img className="h-12 w-12 shrink-0 rounded-xl object-contain bg-(--ui-bg-tertiary)" src={viewApp.icon_data} alt={viewApp.name} />
                  ) : (
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-(--ui-bg-tertiary) text-lg font-bold text-(--ui-text-tertiary)">
                      {appLetter(viewApp.name)}
                    </div>
                  )}
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-foreground truncate">{viewApp.name}</div>
                    <div className="mt-0.5 flex items-center gap-1.5">
                      <span className="text-[0.6rem] text-(--ui-text-quaternary)">
                        {[viewApp.company, viewApp.version ? 'v' + viewApp.version : ''].filter(Boolean).join(' - ')}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="space-y-2 text-xs">
                  {viewApp.description && <KVRow k="Description" v={viewApp.description.slice(0, 200)} />}
                  {viewApp.install_path && <KVRow k="Install path" v={viewApp.install_path} />}
                  {viewApp.exe_path && <KVRow k="Executable" v={viewApp.exe_path} />}
                  {viewApp.last_launched_at && <KVRow k="Last launched" v={viewApp.last_launched_at} />}
                  {viewApp.exit_normal != null && <KVRow k="Exit status" v={viewApp.exit_normal ? 'Normal' : 'Abnormal'} />}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center text-xs text-(--ui-text-quaternary)">
              {total > 0 ? '<- Select an app to see details' : 'Click Scan to discover installed software'}
            </div>
          )}
        </div>
      </DetailColumn>
    </MasterDetail>
  )
}

function HwCard({ label, value, sub, children }: { label: string; value: string; sub?: string; children?: any }) {
  return (
    <div className="rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-3 py-2.5">
      <div className="text-[0.6rem] text-(--ui-text-quaternary)">{label}</div>
      <div className="text-sm font-medium text-foreground truncate">{value}</div>
      {sub && <div className="mt-0.5 truncate text-[0.6rem] text-(--ui-text-quaternary)">{sub}</div>}
      {children}
    </div>
  )
}

function KVRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="w-24 shrink-0 text-(--ui-text-quaternary)">{k}</span>
      <span className="min-w-0 break-all font-mono text-[0.7rem] text-foreground">{v || '-'}</span>
    </div>
  )
}
