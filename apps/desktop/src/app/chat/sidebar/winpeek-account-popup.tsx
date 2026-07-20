import { useEffect, useRef, useState } from 'react'

interface Ident { name: string; role: string; uid: number }

const rowStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
  fontSize: 13, cursor: 'pointer', border: 'none', background: 'none',
  width: '100%', textAlign: 'left', color: '#374151',
}
const hr = <div style={{ margin: '4px 12px', borderTop: '1px solid #e5e7eb' }} />

export function WinPeekAccountPopup() {
  const [open, setOpen] = useState(false)
  const [sub, setSub] = useState(false)
  const [ident, setIdent] = useState<Ident | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const btn = useRef<HTMLButtonElement>(null)

  const sync = () => {
    try {
      const raw = localStorage.getItem('mim-identity')
      setIdent(raw ? JSON.parse(raw) : null)
    } catch { setIdent(null) }
  }
  useEffect(() => { sync(); window.addEventListener('storage', sync); return () => window.removeEventListener('storage', sync) }, [])

  useEffect(() => {
    if (!open) return
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node) && btn.current && !btn.current.contains(e.target as Node)) {
        setOpen(false); setSub(false)
      }
    }
    document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h)
  }, [open])

  const logout = () => { localStorage.removeItem('mim-identity'); setIdent(null); setOpen(false); setSub(false); window.dispatchEvent(new Event('storage')) }

  const Row = (p: { icon: string; label: string; onClick?: () => void; danger?: boolean }) => (
    <button
      style={{ ...rowStyle, color: p.danger ? '#ef4444' : rowStyle.color }}
      onMouseEnter={e => { e.currentTarget.style.background = '#f3f4f6' }}
      onMouseLeave={e => { e.currentTarget.style.background = '' }}
      onClick={() => { p.onClick?.(); if (p.label !== '切换账号') setOpen(false) }}
    >
      <span style={{ width: 18, textAlign: 'center', fontSize: 14, flexShrink: 0 }}>{p.icon}</span>
      <span style={{ flex: 1 }}>{p.label}</span>
    </button>
  )

  return (
    <div style={{ flexShrink: 0, borderTop: '1px solid #e5e7eb', padding: '0 8px 4px' }}>
      {/* Trigger */}
      <button
        ref={btn}
        style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '6px 8px',
          border: 'none', background: 'none', cursor: 'pointer', borderRadius: 6, textAlign: 'left', fontSize: 12 }}
        onMouseEnter={e => { e.currentTarget.style.background = '#f3f4f6' }}
        onMouseLeave={e => { e.currentTarget.style.background = '' }}
        onClick={() => setOpen(v => !v)}
      >
        <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#7c3aed', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, flexShrink: 0 }}>
          {ident ? ident.name[0] : 'P'}
        </div>
        <span style={{ flex: 1, fontWeight: 500, color: '#111827', fontSize: 12 }}>{ident ? ident.name : 'Peeka'}</span>
        <span style={{ fontSize: 10, color: '#9ca3af' }}>{open ? '▼' : '▶'}</span>
      </button>

      {/* Popup */}
      {open && (
        <div ref={ref} style={{
          position: 'fixed', bottom: 44, left: 6, zIndex: 99999, width: 260,
          background: '#fff', borderRadius: 16, border: '1px solid #d1d5db',
          boxShadow: '0 20px 60px rgba(0,0,0,.25)', padding: '6px 0',
          maxHeight: 'calc(100vh - 100px)', overflowY: 'auto',
        }}>
          {ident ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px' }}>
                <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#7c3aed', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, flexShrink: 0 }}>
                  {ident.name[0]}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>{ident.name}</div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>{ident.role} · #{ident.uid}</div>
                </div>
              </div>
              {hr}

              <Row icon="⚙" label="设置" />
              <Row icon="★" label="收藏夹" />
              <Row icon="🔌" label="API 服务" />
              <Row icon="⬆" label="检查更新" />
              <Row icon="?" label="帮助与反馈" />
              {hr}

              <Row icon="✦" label="专业能力升级" />
              {hr}

              <Row icon="⇄" label="切换账号" onClick={() => setSub(v => !v)} />
              <Row icon="⤻" label="退出登录" danger onClick={logout} />

              {sub && (
                <div style={{ margin: '4px 10px 8px', padding: 6, borderRadius: 12,
                  background: '#f3f4f6', border: '1px solid #e5e7eb' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px', borderRadius: 8 }}>
                    <div style={{ width: 26, height: 26, borderRadius: '50%', background: '#7c3aed', color: '#fff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, flexShrink: 0 }}>
                      {ident.name[0]}
                    </div>
                    <span style={{ flex: 1, fontSize: 12, color: '#111827' }}>{ident.name}</span>
                    <span style={{ color: '#7c3aed', fontSize: 14 }}>✓</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px',
                    borderRadius: 8, cursor: 'pointer', fontSize: 12, color: '#9ca3af' }}
                    onMouseEnter={e => { e.currentTarget.style.background = '#e5e7eb' }}
                    onMouseLeave={e => { e.currentTarget.style.background = '' }}>
                    <div style={{ width: 26, height: 26, borderRadius: '50%', border: '1px dashed #d1d5db',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 16 }}>
                      +
                    </div>
                    <span>添加账号</span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <button
              style={{ ...rowStyle, color: '#7c3aed' }}
              onClick={() => setOpen(false)}>
              <span style={{ width: 18, textAlign: 'center', fontSize: 14 }}>👤</span>
              <span>登录 Peeka 账号</span>
            </button>
          )}
        </div>
      )}
    </div>
  )
}
