import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

interface Ident { name: string; role: string; uid: number }

const S: React.CSSProperties = {
  display:'flex',alignItems:'center',gap:10,padding:'10px 16px',fontSize:13,
  cursor:'pointer',border:'none',background:'none',width:'100%',textAlign:'left',
  color:'#374151',fontFamily:'inherit',
}
const HR = <div style={{margin:'4px 14px',borderTop:'1px solid #e5e7eb'}} />

export function WinPeekAccountPopup() {
  const [open, setOpen] = useState(false)
  const [sub, setSub] = useState(false)
  const [ident, setIdent] = useState<Ident|null>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const btnRef  = useRef<HTMLButtonElement>(null)

  const sync = () => {
    try { setIdent(JSON.parse(localStorage.getItem('mim-identity')||'')) } catch { setIdent(null) }
  }
  useEffect(() => { sync(); window.addEventListener('storage', sync); return () => window.removeEventListener('storage',sync) }, [])

  useEffect(() => {
    if (!open) return
    const onD = (e: MouseEvent) => {
      const t = e.target as Node
      if (popupRef.current && !popupRef.current.contains(t) && btnRef.current && !btnRef.current.contains(t)) {
        setOpen(false); setSub(false)
      }
    }
    document.addEventListener('mousedown', onD)
    return () => document.removeEventListener('mousedown', onD)
  }, [open])

  const logout = () => {
    localStorage.removeItem('mim-identity')
    setIdent(null); setOpen(false); setSub(false)
    window.dispatchEvent(new Event('storage'))
  }

  const Row = (p: { icon: string; label: string; onClick?: () => void; danger?: boolean }) => (
    <button
      style={{...S, color: p.danger ? '#ef4444' : S.color}}
      onMouseEnter={e => e.currentTarget.style.background='#f3f4f6'}
      onMouseLeave={e => e.currentTarget.style.background=''}
      onClick={() => { p.onClick?.(); if (p.label !== '切换账号') setOpen(false) }}
    >
      <span style={{fontSize:16,width:22,textAlign:'center',flexShrink:0}}>{p.icon}</span>
      <span style={{flex:1}}>{p.label}</span>
    </button>
  )

  const popup = open ? (
    <div ref={popupRef} style={{
      position:'fixed',bottom:48,left:8,zIndex:2147483647,width:272,
      background:'#fff',borderRadius:18,border:'1px solid #d1d5db',
      boxShadow:'0 25px 80px rgba(0,0,0,.28)',padding:'8px 0',
      maxHeight:'calc(100vh - 120px)',overflowY:'auto',
    }}>
      {ident ? (
        <>
          <div style={{display:'flex',alignItems:'center',gap:12,padding:'12px 16px'}}>
            <div style={{width:36,height:36,borderRadius:'50%',background:'#7c3aed',color:'#fff',
              display:'flex',alignItems:'center',justifyContent:'center',fontSize:16,fontWeight:700,flexShrink:0}}>
              {ident.name[0]}
            </div>
            <div style={{minWidth:0}}>
              <div style={{fontSize:14,fontWeight:600,color:'#111827'}}>{ident.name}</div>
              <div style={{fontSize:11,color:'#9ca3af'}}>{ident.role} #{ident.uid}</div>
            </div>
          </div>
          {HR}
          <Row icon='⚙' label='设置' />
          <Row icon='★' label='收藏夹' />
          <Row icon='🔌' label='API 服务' />
          <Row icon='⬆' label='检查更新' />
          <Row icon='?' label='帮助与反馈' />
          {HR}
          <Row icon='✦' label='专业能力升级' />
          {HR}
          <Row icon='⇄' label='切换账号' onClick={() => setSub(v=>!v)} />
          <Row icon='⤻' label='退出登录' danger onClick={logout} />
          {sub && (
            <div style={{margin:'6px 12px 10px',padding:8,borderRadius:14,background:'#f3f4f6',border:'1px solid #e5e7eb'}}>
              <div style={{display:'flex',alignItems:'center',gap:10,padding:'6px 8px',borderRadius:8}}>
                <div style={{width:28,height:28,borderRadius:'50%',background:'#7c3aed',color:'#fff',
                  display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:700,flexShrink:0}}>
                  {ident.name[0]}
                </div>
                <span style={{flex:1,fontSize:12,color:'#111827',fontWeight:500}}>{ident.name}</span>
                <span style={{color:'#7c3aed',fontSize:16}}>✓</span>
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10,padding:'6px 8px',borderRadius:8,
                cursor:'pointer',fontSize:12,color:'#9ca3af'}}
                onMouseEnter={e => e.currentTarget.style.background='#e5e7eb'}
                onMouseLeave={e => e.currentTarget.style.background=''}>
                <div style={{width:28,height:28,borderRadius:'50%',border:'1px dashed #d1d5db',
                  display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,fontSize:18,fontWeight:300}}>+</div>
                <span>添加账号</span>
              </div>
            </div>
          )}
        </>
      ) : (
        <button style={{...S,color:'#7c3aed',fontWeight:600}} onClick={() => setOpen(false)}>
          <span style={{fontSize:16,width:22,textAlign:'center'}}>👤</span>
          <span>登录 Peeka 账号</span>
        </button>
      )}
    </div>
  ) : null

  return (
    <div style={{flexShrink:0,borderTop:'1px solid #e5e7eb',padding:'2px 8px 4px'}}>
      <button
        ref={btnRef}
        style={{display:'flex',alignItems:'center',gap:8,width:'100%',padding:'6px 8px',
          border:'none',background:'none',cursor:'pointer',borderRadius:6,textAlign:'left',fontSize:12,fontFamily:'inherit'}}
        onMouseEnter={e => e.currentTarget.style.background='#f3f4f6'}
        onMouseLeave={e => e.currentTarget.style.background=''}
        onClick={() => setOpen(v=>!v)}
      >
        <div style={{width:24,height:24,borderRadius:'50%',background:'#7c3aed',color:'#fff',
          display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,fontWeight:700,flexShrink:0}}>
          {ident ? ident.name[0] : 'P'}
        </div>
        <span style={{flex:1,fontWeight:500,color:'#111827',fontSize:12}}>{ident ? ident.name : 'Peeka'}</span>
        <span style={{fontSize:10,color:'#9ca3af'}}>{open ? '▼' : '▶'}</span>
      </button>
      {createPortal(popup, document.body)}
    </div>
  )
}
