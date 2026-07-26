/* ── Shared types for Peeka tabs (used by SettingsView integration) ── */

export interface WinPeekIdentity {
  uid: number; name: string; role: string; host: string
  title?: string; bio?: string; skills?: string
  manager_uid?: number; agent_type?: string
  identity_type?: string; gender?: string
}

export const ROLES = ['Developer', 'Architect', 'Ops', 'QA', 'PM', 'Director', 'Boss'] as const

/* ── localStorage helpers ── */

export function loadSavedIdentity(): WinPeekIdentity | null {
  try {
    const arr = loadAllIdentities()
    if (arr.length === 0) return null
    const auid = Number(localStorage.getItem('mim-active-uid') || 0)
    return arr.find(x => x.uid === auid) || arr[arr.length - 1] || null
  } catch { return null }
}
export function loadAllIdentities(): WinPeekIdentity[] {
  try { return JSON.parse(localStorage.getItem('mim-identities') || '[]') } catch { return [] }
}
export function saveIdentity(id: WinPeekIdentity) {
  try {
    const arr = loadAllIdentities()
    const idx = arr.findIndex(x => x.uid === id.uid)
    if (idx >= 0) arr[idx] = id; else arr.push(id)
    localStorage.setItem('mim-identities', JSON.stringify(arr))
    localStorage.setItem('mim-active-uid', String(id.uid))
    recordLogin(id.uid)
    if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('peeka-changed'))
  } catch {}
}
export function removeIdentity(uid: number) {
  try {
    const arr = loadAllIdentities().filter(x => x.uid !== uid)
    localStorage.setItem('mim-identities', JSON.stringify(arr))
    if (Number(localStorage.getItem('mim-active-uid') || 0) === uid) localStorage.removeItem('mim-active-uid')
    if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('peeka-changed'))
  } catch {}
}

/* ── Login history ── */

export function recordLogin(uid: number) {
  try {
    const raw = localStorage.getItem('mim-login-history')
    const history: Record<string, number> = raw ? JSON.parse(raw) : {}
    history[String(uid)] = Date.now()
    localStorage.setItem('mim-login-history', JSON.stringify(history))
  } catch {}
}
export function getLoginTime(uid: number): number | null {
  try {
    const raw = localStorage.getItem('mim-login-history')
    const history: Record<string, number> = raw ? JSON.parse(raw) : {}
    return history[String(uid)] || null
  } catch { return null }
}
