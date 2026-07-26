import { useCallback, useState } from 'react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'
import { loadAllIdentities, getLoginTime, recordLogin, saveIdentity, removeIdentity, type WinPeekIdentity } from './types'

const ROLES = ['Developer', 'Architect', 'Ops', 'QA', 'PM', 'Director', 'Boss'] as const

export function AccountsTab({ currentUid, onSwitch }: { currentUid: number; onSwitch: (id: WinPeekIdentity) => void }) {
  const [idents, setIdents] = useState<WinPeekIdentity[]>(loadAllIdentities)
  const [showLogin, setShowLogin] = useState(false)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [loginNick, setLoginNick] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [gender, setGender] = useState<string>('male')
  const [role, setRole] = useState<string>('Developer')
  const [showPw, setShowPw] = useState(false)
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)
  const { requestGateway: rq } = useGatewayRequest()

  const refresh = () => setIdents(loadAllIdentities())

  const sorted = [...idents].sort((a, b) => {
    if (a.uid === currentUid) return -1; if (b.uid === currentUid) return 1
    return (getLoginTime(b.uid) || 0) - (getLoginTime(a.uid) || 0)
  })

  const setDefault = (u: number) => { localStorage.setItem('mim-active-uid', String(u)); recordLogin(u); window.dispatchEvent(new CustomEvent('peeka-changed')); refresh() }

  const handleRemove = (u: number) => {
    if (!window.confirm('Remove this saved account?')) return
    removeIdentity(u); window.dispatchEvent(new CustomEvent('peeka-changed')); refresh()
  }

  const handleLogin = useCallback(async () => {
    const n = loginNick.trim(); if (!n) return
    setLoginLoading(true); setLoginError('')
    try {
      const data: any = await rq('winpeek_mim_login', { nickname: n, password: loginPassword })
      if (data.ok && data.identity) {
        const id: WinPeekIdentity = { uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role, host: 'local' }
        saveIdentity(id); onSwitch(id); setShowLogin(false); refresh()
      } else { setLoginError(data.error || 'Login failed') }
    } catch (e) { setLoginError(e instanceof Error ? e.message : String(e)) }
    setLoginLoading(false)
  }, [loginNick, loginPassword, rq, onSwitch])

  const handleRegister = useCallback(async () => {
    const n = loginNick.trim(); if (!n) return
    setLoginLoading(true); setLoginError('')
    try {
      const data: any = await rq('winpeek_mim_user_register', { name: n, gender, role, password: loginPassword })
      if (data.ok && data.identity) {
        const id: WinPeekIdentity = { uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role, host: 'local' }
        saveIdentity(id); onSwitch(id); setShowLogin(false); refresh()
      } else { setLoginError(data.error || 'Register failed') }
    } catch (e) { setLoginError(e instanceof Error ? e.message : String(e)) }
    setLoginLoading(false)
  }, [loginNick, gender, role, loginPassword, rq, onSwitch])

  const fmtTime = (ts: number | null) => ts ? new Date(ts).toLocaleDateString() + ' ' + new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : null

  return (
    <div className="p-5">
      <div className="text-xs text-(--ui-text-secondary) mb-3">Saved accounts ({idents.length})</div>
      <div className="space-y-1">
        {sorted.map(x => {
          const isDef = x.uid === currentUid
          const lastLogin = getLoginTime(x.uid)
          return (
            <div key={x.uid} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors ${isDef ? 'bg-(--ui-accent)/5 border border-(--ui-accent)/20' : 'hover:bg-(--ui-control-hover-background) border border-transparent'}`}>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-[#7c3aed] to-[#a78bfa] text-xs font-bold text-white">{(x.name || '').charAt(0).toUpperCase()}</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-foreground">{x.name}{isDef && <span className="ml-1.5 text-[0.6rem] text-(--ui-accent) font-medium">Default</span>}</div>
                <div className="text-xs text-(--ui-text-tertiary)}">{x.role} · #{x.uid}{!isDef && lastLogin && <span className="ml-1 text-(--ui-text-quaternary)}">· last: {fmtTime(lastLogin)}</span>}</div>
              </div>
              {!isDef && (<button className="text-xs text-(--ui-accent) hover:text-[#6d28d9] shrink-0" onClick={() => onSwitch(x)}>Switch</button>)}
              <button className="text-xs text-(--ui-text-secondary) hover:text-(--ui-accent) shrink-0" onClick={() => setDefault(x.uid)} title="Set as default">★</button>
              {!isDef && <button className="text-xs text-(--ui-text-tertiary) hover:text-destructive ml-1 shrink-0" onClick={() => handleRemove(x.uid)} title="Remove">✕</button>}
            </div>
          )
        })}
      </div>
      {!showLogin ? (
        <div className="flex gap-2 mt-3">
          <button className="flex-1 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) py-3 shadow-sm hover:bg-(--ui-control-hover-background) transition-colors"
            onClick={() => { setShowLogin(true); setMode('login'); setLoginNick(''); setLoginPassword(''); setLoginError('') }}>
            <div className="text-lg mb-1">🔑</div>
            <div className="text-xs font-semibold text-foreground">登录已有</div>
            <div className="text-[0.6rem] text-(--ui-text-quaternary) mt-0.5">已在别处注册过</div>
          </button>
          <button className="flex-1 rounded-xl border-2 border-[#7c3aed]/30 bg-[#7c3aed]/5 py-3 shadow-sm hover:bg-[#7c3aed]/10 transition-colors"
            onClick={() => { setShowLogin(true); setMode('register'); setLoginNick(''); setLoginPassword('test1234'); setLoginError('') }}>
            <div className="text-lg mb-1">✨</div>
            <div className="text-xs font-semibold text-[#7c3aed]">注册新号</div>
            <div className="text-[0.6rem] text-(--ui-text-quaternary) mt-0.5">创建全新身份</div>
          </button>
        </div>
      ) : (
        <div className="mt-3 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-4 space-y-3">
          {mode === 'login' ? (
            <>
              <div className="text-sm font-semibold text-foreground">🔑 添加老账户</div>
              <p className="text-xs text-(--ui-text-secondary)">输入已有的 Peeka 用户名和密码，在此电脑上登录</p>
              {loginError && <div className="text-xs text-destructive">{loginError}</div>}
              <Input autoFocus onChange={e => setLoginNick(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} placeholder="已有用户名" value={loginNick} className="h-10 rounded-xl text-sm" />
              <div className="relative">
                <Input onChange={e => setLoginPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} placeholder="密码" type={showPw ? 'text' : 'password'} value={loginPassword} className="h-10 rounded-xl text-sm pr-8" />
                <button className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-(--ui-text-tertiary)" onClick={() => setShowPw(!showPw)}>{showPw ? '🙈' : '👁'}</button>
              </div>
              <div className="flex gap-2">
                <button className="flex-1 rounded-lg border border-(--ui-stroke-tertiary) py-2 text-xs text-(--ui-text-secondary)" onClick={() => { setShowLogin(false); setLoginError('') }}>取消</button>
                <button className="flex-1 rounded-lg bg-[#7c3aed] py-2 text-xs text-white font-medium disabled:opacity-50" disabled={loginLoading || !loginNick.trim()} onClick={handleLogin}>{loginLoading ? '...' : '登录'}</button>
              </div>
            </>
          ) : (
            <>
              <div className="text-sm font-semibold text-foreground">✨ 注册新账号</div>
              <p className="text-xs text-(--ui-text-secondary)">创建全新的 Peeka 身份，在同一台电脑上使用</p>
              {loginError && <div className="text-xs text-destructive">{loginError}</div>}
              <Input autoFocus onChange={e => setLoginNick(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleRegister()} placeholder="新用户名" value={loginNick} className="h-10 rounded-xl text-sm" />
              <div className="relative">
                <Input onChange={e => setLoginPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleRegister()} placeholder="设置密码" type={showPw ? 'text' : 'password'} value={loginPassword} className="h-10 rounded-xl text-sm pr-8" />
                <button className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-(--ui-text-tertiary)" onClick={() => setShowPw(!showPw)}>{showPw ? '🙈' : '👁'}</button>
              </div>
              <div className="flex gap-2">
                {['male','female'].map(g => (
                  <button key={g} className={cn('flex-1 rounded-lg py-2 text-xs font-medium', gender === g ? 'bg-[#7c3aed] text-white' : 'bg-(--ui-bg-quaternary) text-(--ui-text-secondary)')} onClick={() => setGender(g)}>{g === 'male' ? '🚹 男' : '🚺 女'}</button>
                ))}
              </div>
              <select className="w-full h-10 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) px-3 text-sm text-foreground outline-none" value={role} onChange={e => setRole(e.target.value)}>
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
              <div className="flex gap-2">
                <button className="flex-1 rounded-lg border border-(--ui-stroke-tertiary) py-2 text-xs text-(--ui-text-secondary)" onClick={() => { setShowLogin(false); setLoginError('') }}>取消</button>
                <button className="flex-1 rounded-lg bg-[#7c3aed] py-2 text-xs text-white font-medium disabled:opacity-50" disabled={loginLoading || !loginNick.trim()} onClick={handleRegister}>{loginLoading ? '...' : '注册'}</button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
