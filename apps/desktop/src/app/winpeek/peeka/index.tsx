/* ── Barrel exports for Peeka tab components (used by SettingsView) ── */

import { useCallback, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'
import { loadSavedIdentity, saveIdentity, type WinPeekIdentity } from './types'

export { ProfileTab } from './profile-tab'
export { AccountsTab } from './accounts-tab'
export { PasswordTab } from './password-tab'
export { OrganizationTab } from './organization-tab'
export { AgentsTab } from './agents-tab'
export { DevicesTab } from './devices-tab'
export { loadSavedIdentity, loadAllIdentities, saveIdentity, removeIdentity, recordLogin, getLoginTime } from './types'
export type { WinPeekIdentity } from './types'

const ROLES = ['Developer', 'Architect', 'Ops', 'QA', 'PM', 'Director', 'Boss'] as const

/* ── Login / Register panel for unauthenticated SettingsView Peeka tabs ── */

export function PeekaLoginPanel({ onLogin }: { onLogin: () => void }) {
  const { requestGateway: rq } = useGatewayRequest()
  const [mode, setMode] = useState<null | 'login' | 'register'>(null)
  const [nick, setNick] = useState('')
  const [password, setPassword] = useState('a@123321')
  const [gender, setGender] = useState<string>('male')
  const [role, setRole] = useState<string>('Developer')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = useCallback(async () => {
    const n = nick.trim(); if (!n) return
    setLoading(true); setError('')
    try {
      const data: any = await rq('winpeek_mim_login', { nickname: n, password })
      if (data.ok && data.identity) {
        saveIdentity({ uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role, host: 'local' })
        window.dispatchEvent(new CustomEvent('peeka-changed'))
        onLogin()
      } else { setError(data.error || 'Login failed') }
    } catch (e) { setError(e instanceof Error ? e.message : String(e)) }
    setLoading(false)
  }, [nick, password, rq, onLogin])

  const handleRegister = useCallback(async () => {
    const n = nick.trim(); if (!n) return
    setLoading(true); setError('')
    try {
      const data: any = await rq('winpeek_mim_user_register', { name: n, gender, role, password })
      if (data.ok && data.identity) {
        saveIdentity({ uid: data.identity.uid, name: data.identity.nickname, role: data.identity.role, host: 'local' })
        window.dispatchEvent(new CustomEvent('peeka-changed'))
        onLogin()
      } else { setError(data.error || 'Register failed') }
    } catch (e) { setError(e instanceof Error ? e.message : String(e)) }
    setLoading(false)
  }, [nick, gender, role, password, rq, onLogin])

  return (
    <div className="p-8 max-w-sm mx-auto">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-[#7c3aed] to-[#a78bfa] mb-3 shadow-lg shadow-purple-500/20">
          <span className="text-2xl">🐉</span>
        </div>
        <h2 className="text-lg font-bold text-foreground">Peeka</h2>
        <p className="text-xs text-(--ui-text-secondary) mt-1">登录已有账号，或注册新账号</p>
      </div>

      {error && <div className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive mb-4">{error}</div>}

      {!mode ? (
        <div className="space-y-3">
          <button className="w-full rounded-2xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-5 text-left shadow-sm hover:bg-(--ui-control-hover-background) transition-colors"
            onClick={() => { setMode('login'); setNick(''); setPassword(''); setError('') }}>
            <span className="text-2xl">🔑</span>
            <div className="text-sm font-bold text-foreground mt-2">登录已有账号</div>
            <div className="text-xs text-(--ui-text-secondary) mt-1">已有 Peeka 用户名和密码</div>
          </button>
          <button className="w-full rounded-2xl border-2 border-[#7c3aed]/30 bg-[#7c3aed]/5 p-5 text-left shadow-sm hover:bg-[#7c3aed]/10 transition-colors"
            onClick={() => { setMode('register'); setNick(''); setPassword('test1234'); setError('') }}>
            <span className="text-2xl">✨</span>
            <div className="text-sm font-bold text-[#7c3aed] mt-2">注册新账号</div>
            <div className="text-xs text-(--ui-text-secondary) mt-1">创建全新的 Peeka 身份</div>
          </button>
        </div>
      ) : mode === 'login' ? (<>
        <div className="text-sm font-semibold text-foreground mb-3">🔑 登录已有账号</div>
        <p className="text-xs text-(--ui-text-secondary) mb-4">输入已有的 Peeka 用户名和密码</p>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-(--ui-text-secondary) block mb-1">用户名</label>
            <Input autoFocus onChange={e => setNick(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} placeholder="已有用户名" value={nick} className="h-10 rounded-xl" />
          </div>
          <div>
            <label className="text-xs text-(--ui-text-secondary) block mb-1">密码</label>
            <Input onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} placeholder="输入密码" type="password" value={password} className="h-10 rounded-xl" />
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <Button className="flex-1 h-10 rounded-xl" variant="secondary" size="sm" onClick={() => setMode(null)}>← 返回</Button>
          <Button className="flex-1 h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa]" size="sm" disabled={loading || !nick.trim()} onClick={handleLogin}>{loading ? '...' : '登 录'}</Button>
        </div>
      </>) : (<>
        <div className="text-sm font-semibold text-foreground mb-3">✨ 注册新账号</div>
        <p className="text-xs text-(--ui-text-secondary) mb-4">创建全新的 Peeka 身份</p>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-(--ui-text-secondary) block mb-1">用户名</label>
            <Input autoFocus onChange={e => setNick(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleRegister()} placeholder="选择新用户名" value={nick} className="h-10 rounded-xl" />
          </div>
          <div>
            <label className="text-xs text-(--ui-text-secondary) block mb-1">密码</label>
            <Input onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleRegister()} placeholder="设置密码" type="password" value={password} className="h-10 rounded-xl" />
          </div>
          <div>
            <label className="text-xs text-(--ui-text-secondary) block mb-1">性别</label>
            <div className="flex gap-2">
              {['male','female'].map(g => (
                <button key={g} className={cn('flex-1 rounded-lg py-2 text-xs font-medium', gender === g ? 'bg-[#7c3aed] text-white' : 'bg-(--ui-bg-quaternary) text-(--ui-text-secondary) hover:bg-(--ui-control-hover-background)')}
                  onClick={() => setGender(g)}>{g === 'male' ? '🚹 男' : '🚺 女'}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs text-(--ui-text-secondary) block mb-1.5">角色</label>
            <div className="flex flex-wrap gap-1.5">
              {ROLES.map(r => (
                <button key={r} className={cn('rounded-full px-3 py-1.5 text-xs font-medium transition-all',
                  role === r ? 'bg-[#7c3aed] text-white shadow-sm' : 'bg-(--ui-bg-quaternary) text-(--ui-text-secondary) hover:bg-(--ui-control-hover-background)')}
                  onClick={() => setRole(r)}>{r}</button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <Button className="flex-1 h-10 rounded-xl" variant="secondary" size="sm" onClick={() => setMode(null)}>← 返回</Button>
          <Button className="flex-1 h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa]" size="sm" disabled={loading || !nick.trim()} onClick={handleRegister}>{loading ? '...' : '注 册'}</Button>
        </div>
      </>)}
    </div>
  )
}
