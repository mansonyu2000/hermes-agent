import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { notifyError } from '@/store/notifications'

import type { WinPeekIdentity } from './types'
import { ROLES } from './types'

/* ── Profile Tab ── */

export function ProfileTab({ identity, rq, onUpdate }: { identity: WinPeekIdentity; rq: any; onUpdate: (id: WinPeekIdentity) => void }) {
  const [editing, setEditing] = useState(false)
  const [nick, setNick] = useState(identity.name)
  const [title, setTitle] = useState(identity.title || '')
  const [bio, setBio] = useState(identity.bio || '')
  const [skills, setSkills] = useState(identity.skills || '')
  const [role, setRole] = useState(identity.role)
  const [saving, setSaving] = useState(false)
  const [squad, setSquad] = useState<any>(null)

  useEffect(() => {
    rq('winpeek_org_status', { uid: identity.uid }).then((d: any) => { if (d?.linked && d?.squad) setSquad(d.squad) }).catch(() => {})
  }, [rq])

  const handleSave = async () => {
    setSaving(true)
    try {
      const d: any = await rq('winpeek_mim_update_profile', { uid: identity.uid, nickname: nick, title, bio, skills, role })
      if (d?.ok) { onUpdate({ ...identity, name: nick, title, bio, skills, role }); setEditing(false) }
      else { notifyError(d?.error || 'Save failed', 'Save failed') }
    } catch (e) { notifyError(e, 'Failed to save profile') }
    setSaving(false)
  }

  const name = identity.name || ''
  const letter = name.charAt(0).toUpperCase()

  return (
    <div className="p-5 space-y-5">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7c3aed] to-[#a78bfa] text-xl font-bold text-white">{letter}</div>
        <div>
          <div className="text-base font-bold text-foreground">{identity.name}</div>
          <div className="text-xs text-(--ui-text-tertiary)">
            {identity.identity_type === 'mim-user' ? 'Peeka User' : 'MIM Agent'} · #{identity.uid}
            {identity.gender && <span className="ml-2">{identity.gender === 'female' ? '♀' : '♂'}</span>}
          </div>
        </div>
        <button className="ml-auto text-xs text-(--ui-accent) hover:text-[#6d28d9] font-medium"
          onClick={() => { if (!editing) { setNick(identity.name); setTitle(identity.title || ''); setBio(identity.bio || ''); setSkills(identity.skills || ''); setRole(identity.role) }; setEditing(!editing) }}
        >{editing ? 'Cancel' : 'Edit'}</button>
      </div>

      <div className="rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) divide-y divide-(--ui-stroke-quaternary)">
        <FieldRow label="Nickname" editing={editing} value={nick} onChange={setNick} />
        <FieldRow label="Role" editing={editing} value={role} onChange={setRole} select options={ROLES.map(r => ({ label: r, value: r }))} />
        <FieldRow label="Title" editing={editing} value={title} onChange={setTitle} />
        <FieldRow label="Bio" editing={editing} value={bio} onChange={setBio} multiline />
        <FieldRow label="Skills" editing={editing} value={skills} onChange={setSkills} placeholder="e.g. Python, React, DevOps" />
        <FieldRow label="UID" value={`#${identity.uid}`} />
        <FieldRow label="Gender" editing={editing} value={identity.gender || ''} onChange={(v) => onUpdate({ ...identity, gender: v })} select options={[{ label: 'Male', value: 'male' }, { label: 'Female', value: 'female' }]} />
        {identity.identity_type && <FieldRow label="Type" value={identity.identity_type === 'mim-user' ? 'Human User' : 'AI Agent'} />}
      </div>

      {editing && (
        <Button className="w-full h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] hover:from-[#6d28d9] hover:to-[#8b5cf6] shadow-md shadow-purple-500/20" disabled={saving} onClick={handleSave} size="sm">
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      )}

      {squad && (
        <div className="rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-surface) p-4">
          <div className="text-[0.6rem] font-medium text-(--ui-text-quaternary) uppercase mb-2">Organization</div>
          <div className="text-sm font-semibold text-foreground">{squad.name}</div>
          {squad.description && <div className="mt-1 text-xs text-(--ui-text-tertiary)">{squad.description}</div>}
          <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            {squad.industry && <div><span className="text-(--ui-text-quaternary)">Industry</span> <span>{squad.industry}</span></div>}
            {squad.address && <div><span className="text-(--ui-text-quaternary)">Address</span> <span>{squad.address}</span></div>}
            {squad.contact_email && <div><span className="text-(--ui-text-quaternary)">Email</span> <span className="truncate">{squad.contact_email}</span></div>}
          </div>
          <button className="mt-2 text-xs text-(--ui-accent) hover:text-[#6d28d9]" onClick={() => {
            const params = new URLSearchParams(window.location.search)
            params.set('tab', 'peeka:organization')
            window.history.replaceState(null, '', `?${params.toString()}`)
            window.dispatchEvent(new PopStateEvent('popstate'))
          }}>Open Organization →</button>
        </div>
      )}
    </div>
  )
}

/* ── FieldRow ── */

function FieldRow({ label, value, editing, onChange, multiline, select, options, placeholder }: {
  label: string; value?: string; editing?: boolean
  onChange?: (v: string) => void; multiline?: boolean
  select?: boolean; options?: { label: string; value: string }[]; placeholder?: string
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3 gap-3">
      <span className="text-xs text-(--ui-text-secondary) shrink-0">{label}</span>
      {editing && onChange ? (
        select && options ? (
          <select className="text-xs text-right bg-transparent border border-(--ui-stroke-tertiary) rounded-lg px-2 py-1 text-foreground outline-none" value={value || ''} onChange={e => onChange(e.target.value)}>
            {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ) : multiline ? (
          <textarea className="flex-1 text-xs text-right bg-transparent border border-(--ui-stroke-tertiary) rounded-lg px-2 py-1 text-foreground outline-none resize-none min-h-[60px]" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} />
        ) : (
          <input className="flex-1 text-xs text-right bg-transparent border border-(--ui-stroke-tertiary) rounded-lg px-2 py-1 text-foreground outline-none" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} />
        )
      ) : (
        <span className="text-xs text-foreground truncate max-w-[200px]">{value || '—'}</span>
      )}
    </div>
  )
}
