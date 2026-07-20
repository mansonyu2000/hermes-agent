import { useCallback, useEffect, useRef, useState } from 'react'

import { Codicon } from '@/components/ui/codicon'
import { cn } from '@/lib/utils'

interface MenuItem {
  key: string; icon: string; label: string; arrow?: boolean; danger?: boolean; onClick?: () => void
}

const ROW = 'flex cursor-pointer items-center gap-2.5 rounded-md px-3 py-1.5 text-[0.8125rem] transition-colors hover:bg-(--ui-control-hover-background)'
const SEP = <div className="mx-3 my-1 border-t border-(--ui-stroke-quaternary)" />

export function WinPeekAccountPopup() {
  const [open, setOpen] = useState(false)
  const [subOpen, setSubOpen] = useState(false)
  const [ident, setIdent] = useState<{ name: string; role: string; uid: number } | null>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const trigRef = useRef<HTMLButtonElement>(null)

  const sync = useCallback(() => {
    try { const raw = localStorage.getItem('mim-identity'); setIdent(raw ? JSON.parse(raw) : null) } catch {}
  }, [])

  useEffect(() => { sync(); window.addEventListener('storage', sync); return () => window.removeEventListener('storage', sync) }, [sync])

  // Close on external click
  useEffect(() => {
    if (!open) return
    const onD = (e: MouseEvent) => {
      const t = e.target as Node
      if (popupRef.current && !popupRef.current.contains(t) && trigRef.current && !trigRef.current.contains(t)) {
        setOpen(false); setSubOpen(false)
      }
    }
    document.addEventListener('mousedown', onD)
    return () => document.removeEventListener('mousedown', onD)
  }, [open])

  const logout = () => { localStorage.removeItem('mim-identity'); setIdent(null); setOpen(false); setSubOpen(false) }

  const sysItems: MenuItem[] = [
    { key: 'settings', icon: 'settings-gear', label: '设置' },
    { key: 'fav', icon: 'star-full', label: '收藏夹' },
    { key: 'api', icon: 'plug', label: 'API 服务' },
    { key: 'update', icon: 'arrow-up', label: '检查更新' },
    { key: 'help', icon: 'question', label: '帮助与反馈' },
  ]
  const midItems: MenuItem[] = [{ key: 'pro', icon: 'star-empty', label: '专业能力升级' }]
  const accItems: MenuItem[] = [
    { key: 'switch', icon: 'arrow-swap', label: '切换账号', arrow: true, onClick: () => setSubOpen(v => !v) },
    { key: 'logout', icon: 'sign-out', label: '退出登录', danger: true, onClick: logout },
  ]

  const row = (item: MenuItem) => (
    <div key={item.key} className={cn(ROW, item.danger && 'text-destructive')}
      onClick={() => { item.onClick?.(); if (!item.arrow) setOpen(false) }}>
      <div className="flex w-4 shrink-0 justify-center"><Codicon name={item.icon} size={14} /></div>
      <span className="flex-1">{item.label}</span>
      {item.arrow && <Codicon name="chevron-right" size={10} />}
    </div>
  )

  const LoggedIn = ident ? (
    <>
      <div className="flex items-center gap-3 px-3 py-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-xs font-bold text-(--ui-accent)">{ident.name.charAt(0)}</div>
        <div className="min-w-0">
          <div className="truncate text-[0.8125rem] font-semibold text-foreground">{ident.name}</div>
          <div className="text-[0.6rem] text-(--ui-text-quaternary)">{ident.role} · #{ident.uid}</div>
        </div>
      </div>
      {SEP}
      {sysItems.map(row)}
      {SEP}
      {midItems.map(row)}
      {SEP}
      {accItems.map(row)}
      {subOpen && (
        <div className="mx-3 mb-1.5 mt-1 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-quaternary) p-1">
          <div className="flex items-center gap-2.5 rounded-lg px-3 py-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-[0.6rem] font-bold text-(--ui-accent)">{ident.name.charAt(0)}</div>
            <span className="flex-1 truncate text-xs">{ident.name}</span>
            <Codicon name="check" size={11} className="text-(--ui-accent)" />
          </div>
          <div className="flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-(--ui-text-quaternary) hover:bg-(--ui-control-hover-background) hover:text-foreground"
            onClick={() => { /* navigate to login */ }}>
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-dashed border-(--ui-stroke-tertiary)"><Codicon name="add" size={12} /></div>
            <span>添加账号</span>
          </div>
        </div>
      )}
    </>
  ) : (
    <div className="space-y-0.5 px-1 py-1">
      <div className={cn(ROW, 'text-(--ui-accent)')} onClick={() => setOpen(false)}>
        <Codicon name="sign-in" size={14} />
        <span>登录 Peeka 账号</span>
      </div>
    </div>
  )

  return (
    <div className="shrink-0">
      <button
        ref={trigRef}
        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[0.75rem] transition-colors hover:bg-(--ui-control-hover-background)"
        onClick={() => setOpen(v => !v)}
      >
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-(--ui-accent) text-[0.6rem] font-bold text-(--ui-accent-foreground)">
          {ident ? ident.name.charAt(0) : '👤'}
        </div>
        <span className="flex-1 truncate font-medium text-foreground">{ident ? ident.name : 'Peeka'}</span>
        <Codicon name="chevron-right" size={12} />
      </button>

      {open && (
        <div ref={popupRef} className="fixed bottom-12 left-2 z-[9999] w-60 rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) py-1 shadow-2xl"
          style={{ maxHeight: 'calc(100vh - 120px)', overflowY: 'auto' }}>
          {LoggedIn}
        </div>
      )}
    </div>
  )
}
