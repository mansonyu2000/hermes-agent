import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function PasswordTab({ uid, rq }: { uid: number; rq: any }) {
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [showOld, setShowOld] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const strength = newPw.length >= 12 ? 'Strong' : newPw.length >= 8 ? 'Good' : newPw.length >= 6 ? 'Fair' : newPw.length > 0 ? 'Weak' : ''
  const strengthColor = strength === 'Strong' ? 'text-emerald-500' : strength === 'Good' ? 'text-amber-500' : strength === 'Fair' ? 'text-orange-400' : 'text-red-500'

  const handleChange = async () => {
    if (!oldPw || !newPw) { setError('All fields required'); return }
    if (newPw !== confirmPw) { setError('Passwords do not match'); return }
    if (newPw.length < 4) { setError('Password must be at least 4 characters'); return }
    setLoading(true); setError(''); setSuccess('')
    try {
      const d: any = await rq('winpeek_mim_change_password', { uid, old_password: oldPw, new_password: newPw })
      if (d?.ok) { setSuccess('Password changed successfully'); setOldPw(''); setNewPw(''); setConfirmPw('') } else { setError(d?.error || 'Change failed') }
    } catch (e) { setError(e instanceof Error ? e.message : String(e)) }
    setLoading(false)
  }

  return (
    <div className="p-5 max-w-sm">
      <div className="mb-4 text-xs text-(--ui-text-secondary)">Change login password</div>
      {error && <div className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive mb-3">{error}</div>}
      {success && <div className="rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-600 mb-3">{success}</div>}
      <div className="space-y-3">
        <div>
          <label className="text-xs text-(--ui-text-secondary) block mb-1">Current Password</label>
          <div className="relative"><Input onChange={e => setOldPw(e.target.value)} placeholder="Current password" type={showOld ? 'text' : 'password'} value={oldPw} className="h-10 rounded-xl pr-8" /><button className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-(--ui-text-tertiary)" onClick={() => setShowOld(!showOld)}>{showOld ? '🙈' : '👁'}</button></div>
        </div>
        <div>
          <label className="text-xs text-(--ui-text-secondary) block mb-1">New Password</label>
          <div className="relative"><Input onChange={e => setNewPw(e.target.value)} placeholder="New password" type={showNew ? 'text' : 'password'} value={newPw} className="h-10 rounded-xl pr-8" /><button className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-(--ui-text-tertiary)" onClick={() => setShowNew(!showNew)}>{showNew ? '🙈' : '👁'}</button></div>
          {newPw.length > 0 && <p className={`text-[0.6rem] mt-1 ${strengthColor}`}>{strength} password</p>}
        </div>
        <div>
          <label className="text-xs text-(--ui-text-secondary) block mb-1">Confirm Password</label>
          <div className="relative"><Input onChange={e => setConfirmPw(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleChange()} placeholder="Re-enter new password" type={showConfirm ? 'text' : 'password'} value={confirmPw} className="h-10 rounded-xl pr-8" /><button className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-(--ui-text-tertiary)" onClick={() => setShowConfirm(!showConfirm)}>{showConfirm ? '🙈' : '👁'}</button></div>
        </div>
      </div>
      <Button className="mt-4 w-full h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] shadow-md shadow-purple-500/20" disabled={loading} onClick={handleChange} size="sm">{loading ? 'Changing...' : 'Change Password'}</Button>
    </div>
  )
}
