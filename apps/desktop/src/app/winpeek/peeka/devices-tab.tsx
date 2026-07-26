import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { notifyError } from '@/store/notifications'
import { useGatewayRequest } from '../../gateway/hooks/use-gateway-request'

export function DevicesTab({ uid }: { uid: number; rq: any }) {
  const { requestGateway: rq2 } = useGatewayRequest()
  const rq = rq2
  const [device, setDevice] = useState<any>(null)
  const [machines, setMachines] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState(false)
  const [loadError, setLoadError] = useState('')

  const load = useCallback(async () => {
    setLoadError('')
    try {
      const [devRes, machRes] = await Promise.all([
        rq('winpeek_mim_my_device', {}).catch(() => ({})),
        rq('winpeek_machine_list', {}).catch(() => ({ machines: [] })),
      ])
      setDevice(devRes)
      setMachines((machRes as any)?.machines || [])
    } catch (e) {
      setLoadError('Failed to load device data')
      notifyError(e, 'Load failed')
    }
    setLoading(false)
  }, [rq])

  useEffect(() => { load() }, [load])

  const handleRegister = async () => {
    setRegistering(true)
    try {
      const d = await rq('winpeek_mim_device_register', { hostname: device?.hostname || '', owner_uid: uid })
      if (d?.ok || d?.device) {
        await load()
      } else {
        notifyError(d?.error || 'Register failed', 'Error')
      }
    } catch (e) {
      notifyError(e, 'Register failed')
    }
    setRegistering(false)
  }

  if (loading) return <div className="grid h-full place-items-center text-sm text-gray-400 py-12">Loading...</div>

  const isRegistered = device?.device !== null && device?.device !== undefined

  return (
    <div className="p-5 space-y-4 max-w-lg">
      {loadError && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{loadError}</div>}

      {/* This Computer */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">本机信息</div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">主机名</span>
            <span className="font-medium text-gray-900">{device?.hostname || 'Unknown'}</span>
          </div>
          {device?.device?.os_name && (
            <div className="flex justify-between">
              <span className="text-gray-500">操作系统</span>
              <span className="font-medium text-gray-900">{device.device.os_name}</span>
            </div>
          )}
          {device?.device?.cpu_model && (
            <div className="flex justify-between">
              <span className="text-gray-500">CPU</span>
              <span className="font-medium text-gray-900 truncate ml-4 max-w-[200px]">{device.device.cpu_model}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-gray-500">状态</span>
            <span className={isRegistered ? 'text-emerald-600 font-medium' : 'text-orange-500 font-medium'}>
              {isRegistered ? '已注册' : '未注册'}
            </span>
          </div>
        </div>

        {!isRegistered && (
          <Button className="mt-4 w-full h-10 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#a78bfa] text-sm font-semibold shadow-md shadow-purple-500/20"
            size="sm" disabled={registering} onClick={handleRegister}>
            {registering ? '注册中...' : '注册此电脑'}
          </Button>
        )}
      </div>

      {/* Device list */}
      {machines.length > 0 && (
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            已注册设备 ({machines.length})
          </div>
          <div className="space-y-2">
            {machines.map((m: any) => (
              <div key={m.id} className="flex items-center gap-3 rounded-xl border border-gray-100 px-4 py-3 bg-gray-50">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-100 text-sm">💻</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-gray-900">{m.hostname}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {m.os_name && <span>{m.os_name}</span>}
                    {m.approval_status && <span className={m.approval_status === 'pending' ? 'text-orange-500 ml-2' : ''}>
                      · {m.approval_status === 'approved' ? '已授权' : '待审批'}
                    </span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
