import { useEffect, useRef, useState } from 'react'

import { Codicon } from '@/components/ui/codicon'

interface Ident { name: string; role: string; uid: number }

export function WinPeekAccountPopup() {
  const [open, setOpen] = useState(false)
  const [sub, setSub] = useState(false)
  const [ident, setIdent] = useState<Ident | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const btn = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const read = () => { try { setIdent(JSON.parse(localStorage.getItem('mim-identity')||'')) } catch {} }
    read(); window.addEventListener('storage', read); return () => window.removeEventListener('storage', read)
  }, [])

  useEffect(() => {
    if (!open) return
    const h = (e: MouseEvent) => {
      const t = e.target as Node
      if (ref.current && !ref.current.contains(t) && btn.current && !btn.current.contains(t)) { setOpen(false); setSub(false) }
    }
    document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h)
  }, [open])

  const Row = (p: { icon: string; label: string; end?: string; danger?: boolean; onClick?: () => void }) => (
    <div
      style={{ display:'flex', alignItems:'center', gap:10, padding:'8px 12px', fontSize:13, cursor:'pointer',
        color: p.danger ? 'var(--ui-destructive, #ef4444)' : 'inherit' }}
      onMouseEnter={e => (e.currentTarget.style.background = 'var(--ui-control-hover-background, rgba(0,0,0,.05))')}
      onMouseLeave={e => (e.currentTarget.style.background = '')}
      onClick={() => { p.onClick?.(); if (p.icon !== 'arrow-swap') setOpen(false) }}
    >
      <Codicon name={p.icon} size={14} />
      <span style={{ flex:1 }}>{p.label}</span>
      {p.end && <span style={{ fontSize:11, opacity:.5 }}>{p.end}</span>}
    </div>
  )

  const HR = <div style={{ margin:'4px 12px', borderTop:'1px solid var(--ui-stroke-quaternary, #e5e7eb)' }} />

  return (
    <div style={{ flexShrink:0, borderTop:'1px solid var(--ui-stroke-quaternary, #e5e7eb)', padding:'0 10px 5px' }}>
      {/* Trigger */}
      <button
        ref={btn}
        style={{ display:'flex', alignItems:'center', gap:8, width:'100%', padding:'6px 8px', border:'none',
          background:'none', cursor:'pointer', borderRadius:6, textAlign:'left', fontSize:12,
          color:'var(--ui-text-secondary, #6b7280)' }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--ui-control-hover-background, rgba(0,0,0,.05))')}
        onMouseLeave={e => (e.currentTarget.style.background = '')}
        onClick={() => setOpen(v => !v)}
      >
        <div style={{ width:24, height:24, borderRadius:'50%', background:'var(--ui-accent, #7c3aed)',
          color:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:10, fontWeight:700, flexShrink:0 }}>
          {ident ? ident.name[0] : 'P'}
        </div>
        <span style={{ flex:1, fontWeight:500, color:'var(--ui-text-primary, #111827)' }}>
          {ident ? ident.name : 'Peeka'}
        </span>
        <span style={{ fontSize:10, opacity:.4, transform: open ? 'rotate(90deg)' : '' }}>&#9654;</span>
      </button>

      {/* Popup */}
      {open && (
        <div ref={ref} style={{
          position:'fixed', bottom:40, left:8, zIndex:99999, width:260,
          background:'var(--ui-bg-surface, #fff)', borderRadius:16,
          border:'1px solid var(--ui-stroke-tertiary, #d1d5db)',
          boxShadow:'0 20px 60px rgba(0,0,0,.2)', padding:'6px 0',
          maxHeight:'calc(100vh - 100px)', overflowY:'auto',
        }}>
          {ident ? (
            <>
              {/* Header */}
              <div style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 12px' }}>
                <div style={{ width:32, height:32, borderRadius:'50%', background:'var(--ui-accent, #7c3aed)',
                  color:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
                  fontSize:13, fontWeight:700, flexShrink:0 }}>{ident.name[0]}</div>
                <div style={{ minWidth:0 }}>
                  <div style={{ fontSize:13, fontWeight:600 }}>{ident.name}</div>
                  <div style={{ fontSize:10, opacity:.4 }}>{ident.role} · #{ident.uid}</div>
                </div>
              </div>
              {HR}

              {/* System */}
              <Row icon="settings-gear" label="设置" />
              <Row icon="star-full" label="收藏夹" />
              <Row icon="plug" label="API 服务" />
              <Row icon="arrow-up" label="检查更新" />
              <Row icon="question" label="帮助与反馈" />
              {HR}

              {/* Premium */}
              <Row icon="star-empty" label="专业能力升级" />
              {HR}

              {/* Account */}
              <Row icon="arrow-swap" label="切换账号" end=">" onClick={() => setSub(v => !v)} />
              <Row icon="sign-out" label="退出登录" danger onClick={() => {
                localStorage.removeItem('mim-identity'); setIdent(null); setOpen(false); setSub(false)
              }} />

              {/* Sub panel */}
              {sub && (
                <div style={{ margin:'4px 12px 8px', padding:4, borderRadius:12,
                  background:'var(--ui-bg-quaternary, #f3f4f6)', border:'1px solid var(--ui-stroke-tertiary, #d1d5db)' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:10, padding:'6px 8px', borderRadius:8 }}>
                    <div style={{ width:24, height:24, borderRadius:'50%', background:'var(--ui-accent, #7c3aed)',
                      color:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
                      fontSize:9, fontWeight:700, flexShrink:0 }}>{ident.name[0]}</div>
                    <span style={{ flex:1, fontSize:12 }}>{ident.name}</span>
                    <Codicon name="check" size={11} />
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:10, padding:'6px 8px', borderRadius:8,
                    cursor:'pointer', fontSize:12, opacity:.5 }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--ui-control-hover-background, rgba(0,0,0,.05))')}
                    onMouseLeave={e => (e.currentTarget.style.background = '')}>
                    <div style={{ width:24, height:24, borderRadius:'50%',
                      border:'1px dashed var(--ui-stroke-tertiary, #d1d5db)',
                      display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                      <Codicon name="add" size={12} />
                    </div>
                    <span>添加账号</span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <Row icon="sign-in" label="登录 Peeka 账号" />
          )}
        </div>
      )}
    </div>
  )
}
