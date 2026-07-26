import { useCallback, useEffect, useMemo, useState } from 'react'

import { Input } from '@/components/ui/input'
import { notifyError } from '@/store/notifications'

export function AgentsTab({ uid, rq }: { uid: number; rq: any }) {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editRole, setEditRole] = useState('')
  const [actingId, setActingId] = useState<number | null>(null)
  const [filter, setFilter] = useState('')
  const [loadError, setLoadError] = useState('')
  const [onlineMap, setOnlineMap] = useState<Record<number, boolean>>({})

  const load = useCallback(async () => {
    setLoadError('')
    try {
      const d: any = await rq('winpeek_mim_my_agents', { uid })
      setAgents(d?.agents || [])
      // Check online status
      const om: Record<number, boolean> = {}
      try {
        const r: any = await rq('winpeek_mim_online', {})
        const nodes: any[] = r?.nodes || []
        for (const a of (d?.agents || [])) {
          om[a.uid] = nodes.some((n: any) => (n.uid === a.uid || n.peer_uid === a.uid) && n.status !== 'offline')
        }
      } catch { /* online check best-effort */ }
      setOnlineMap(om)
    } catch { setLoadError('Failed to load agents') }
    setLoading(false)
  }, [uid, rq])

  useEffect(() => { load() }, [load])

  const handleSave = async (agentId: number) => {
    setActingId(agentId)
    try { await rq('winpeek_agent_upsert', { name: editName, role: editRole, agent_id: agentId, requester_uid: uid }); setEditingId(null); await load() } catch (e) { notifyError(e, 'Failed to update agent') }
    setActingId(null)
  }
  const handleDelete = async (agentId: number) => {
    if (!window.confirm('Remove this agent?')) return; setActingId(agentId)
    try { await rq('winpeek_agent_delete', { agent_id: agentId, requester_uid: uid }); await load() } catch (e) { notifyError(e, 'Failed to remove agent') }
    setActingId(null)
  }

  const filtered = useMemo(() => {
    if (!filter.trim()) return agents
    const q = filter.toLowerCase()
    return agents.filter(a => (a.nickname||'').toLowerCase().includes(q) || (a.role||'').toLowerCase().includes(q) || (a.agent_type||'').toLowerCase().includes(q))
  }, [agents, filter])

  if (loading) return <div className="grid h-full place-items-center text-xs text-(--ui-text-tertiary)} py-12">Loading...</div>

  return (
    <div className="p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-(--ui-text-secondary)">My Agents ({agents.length})</span>
        <button className="text-xs text-(--ui-text-tertiary) hover:text-foreground" onClick={load} title="Refresh">🔄</button>
      </div>
      {loadError && <div className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive mb-3">{loadError}</div>}
      {agents.length > 3 && <Input className="h-8 text-xs mb-3 rounded-lg" placeholder="Filter agents..." value={filter} onChange={e => setFilter(e.target.value)} />}
      {filtered.length === 0 ? (
        <div className="text-center py-8"><div className="mb-2 text-3xl">🤖</div><p className="text-xs text-(--ui-text-tertiary)">{filter ? 'No agents match your filter' : 'No agents bound yet'}</p><p className="text-xs text-(--ui-text-quaternary) mt-1">Agents are auto-discovered and registered by the desktop daemon</p></div>
      ) : (
        <div className="space-y-2">
          {filtered.map(a => {
            const isEditing = editingId === a.uid
            return (
              <div key={a.uid} className="flex items-center gap-3 rounded-xl border border-(--ui-stroke-tertiary) px-4 py-3">
                <div className="relative shrink-0">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-sm">🤖</span>
                  <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-(--ui-bg-surface) ${onlineMap[a.uid] ? 'bg-emerald-500' : 'bg-gray-300'}`} />
                </div>
                {isEditing ? (
                  <div className="min-w-0 flex-1 space-y-1.5">
                    <Input className="h-7 text-xs" value={editName} onChange={e => setEditName(e.target.value)} placeholder="Name" />
                    <Input className="h-7 text-xs" value={editRole} onChange={e => setEditRole(e.target.value)} placeholder="Role" />
                    <div className="flex gap-1.5"><button className="text-[0.6rem] bg-[#7c3aed] text-white px-2 py-0.5 rounded disabled:opacity-30" disabled={actingId === a.uid} onClick={() => handleSave(a.uid)}>Save</button><button className="text-[0.6rem] text-(--ui-text-secondary) px-2 py-0.5" onClick={() => setEditingId(null)}>Cancel</button></div>
                  </div>
                ) : (
                  <>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-foreground">{a.nickname}</div>
                      <div className="text-xs text-(--ui-text-tertiary)}">{a.role}{a.agent_type ? ` · ${a.agent_type}` : ''} · #{a.uid}{onlineMap[a.uid] ? ' · Online' : ''}</div>
                    </div>
                    {a.host && <span className="text-[0.6rem] text-(--ui-text-quaternary)}">{a.host}</span>}
                    <button className="text-xs text-(--ui-accent) hover:text-[#6d28d9] ml-1" onClick={() => { setEditName(a.nickname || ''); setEditRole(a.role || ''); setEditingId(a.uid) }}>Edit</button>
                    <button className="text-xs text-(--ui-text-tertiary) hover:text-destructive ml-1" disabled={actingId === a.uid} onClick={() => handleDelete(a.uid)}>✕</button>
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
