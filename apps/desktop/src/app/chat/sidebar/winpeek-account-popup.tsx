import { useEffect, useRef, useState } from 'react'

import { Codicon } from '@/components/ui/codicon'
import { cn } from '@/lib/utils'

interface MenuItem {
  key: string
  icon: string
  label: string
  arrow?: boolean
  danger?: boolean
  onClick?: () => void
}

const ROW_STYLE = 'flex cursor-pointer items-center gap-2.5 px-4 py-2 text-sm transition-colors hover:bg-(--ui-control-hover-background)'
const DIVIDER = <div className="mx-4 border-t border-(--ui-stroke-quaternary)" />

export function WinPeekAccountPopup() {
  const [open, setOpen] = useState(false)
  const [subOpen, setSubOpen] = useState(false)
  const [ident, setIdent] = useState<{ name: string; role: string; uid: number } | null>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const trigRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const read = () => {
      try { const raw = localStorage.getItem('mim-identity'); setIdent(raw ? JSON.parse(raw) : null) } catch {}
    }
    read(); window.addEventListener('storage', read)
    return () => window.removeEventListener('storage', read)
  }, [])

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node
      if (popupRef.current && !popupRef.current.contains(t) && trigRef.current && !trigRef.current.contains(t)) {
        setOpen(false); setSubOpen(false)
      }
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  if (!ident) return null

  const logout = () => {
    localStorage.removeItem('mim-identity')
    setIdent(null); setOpen(false); setSubOpen(false)
    window.dispatchEvent(new Event('storage'))
  }

  const sysItems: MenuItem[] = [
    { key: 'settings', icon: 'gear', label: '设置' },
    { key: 'fav', icon: 'star-full', label: '收藏夹' },
    { key: 'api', icon: 'plug', label: 'API 服务' },
    { key: 'update', icon: 'arrow-up', label: '检查更新' },
    { key: 'help', icon: 'question', label: '帮助与反馈' },
  ]

  const midItems: MenuItem[] = [
    { key: 'pro', icon: 'star-empty', label: '专业能力升级' },
  ]

  const accItems: MenuItem[] = [
    { key: 'switch', icon: 'arrow-swap', label: '切换账号', arrow: true, onClick: () => setSubOpen(v => !v) },
    { key: 'logout', icon: 'sign-out', label: '退出登录', danger: true, onClick: logout },
  ]

  const renderRow = (item: MenuItem) => (
    <div key={item.key} className={cn(ROW_STYLE, item.danger && 'text-destructive')} onClick={() => { item.onClick?.(); if (!item.arrow) setOpen(false) }}>
      <div className="flex w-4 justify-center"><Codicon name={item.icon} size={14} /></div>
      <span className="flex-1">{item.label}</span>
      {item.arrow && <Codicon name="chevron-right" size={10} />}
    </div>
  )

  return (
    <div className="shrink-0">
      {/* Trigger button */}
      <button
        ref={trigRef}
        className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-[0.75rem] text-(--ui-text-tertiary) transition-colors hover:bg-(--ui-control-hover-background) hover:text-foreground"
        onClick={() => setOpen(v => !v)}
      >
        <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-[3px] bg-(--ui-accent)/15 text-[0.55rem] font-semibold text-(--ui-accent)">
          {ident.name.charAt(0)}
        </div>
        <span className="flex-1 truncate">{ident.name}</span>
        <Codicon name="chevron-right" size={10} />
      </button>

      {/* Popup */}
      {open && (
        <div ref={popupRef} className="fixed bottom-12 left-3 z-50 w-64 rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) py-1 shadow-2xl" style={{ maxHeight: 'calc(100vh - 80px)', overflowY: 'auto' }}>
          {/* Header: current account */}
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-sm font-bold text-(--ui-accent)">{ident.name.charAt(0)}</div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-foreground">{ident.name}</div>
              <div className="text-[0.6rem] text-(--ui-text-quaternary)">{ident.role} · #{ident.uid}</div>
            </div>
          </div>

          {DIVIDER}
          {sysItems.map(renderRow)}
          {DIVIDER}
          {midItems.map(renderRow)}
          {DIVIDER}
          {accItems.map(renderRow)}

          {/* Sub-panel: switch account */}
          {subOpen && (
            <div className="mx-4 mb-2 mt-1 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-quaternary) p-1">
              <div className="flex items-center gap-2.5 rounded-lg px-3 py-2">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-(--ui-accent)/15 text-[0.6rem] font-bold text-(--ui-accent)">{ident.name.charAt(0)}</div>
                <span className="flex-1 truncate text-xs">{ident.name}</span>
                <Codicon name="check" size={11} className="text-(--ui-accent)" />
              </div>
              <div className="flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-(--ui-text-quaternary) hover:bg-(--ui-control-hover-background) hover:text-foreground">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-dashed border-(--ui-stroke-tertiary)"><Codicon name="add" size={12} /></div>
                <span>添加账号</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
