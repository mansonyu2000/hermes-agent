import { useStore } from '@nanostores/react'
import { useState } from 'react'

import { Button } from '../../../components/ui/button'
import { $gatewayState } from '../../../store/session'
import { ListRow } from '../../settings/primitives'

interface PlatformStatus {
  connected: boolean
  icon: string
  name: string
  users: number
  platform: string
}

export function MimView({ onClose }: { onClose: () => void }) {
  const gatewayState = useStore($gatewayState)
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)

  const platforms: PlatformStatus[] = [
    { connected: true,  icon: '💬', name: '微信',     platform: 'wechat',   users: 1250 },
    { connected: false, icon: '📌', name: '钉钉',     platform: 'dingtalk', users: 0 },
    { connected: false, icon: '🕊️', name: '飞书',     platform: 'feishu',   users: 0 },
    { connected: false, icon: '🐧', name: 'QQ',       platform: 'qq',       users: 0 },
    { connected: false, icon: '✈️', name: 'Telegram', platform: 'telegram', users: 0 },
  ]

  return (
    <div className="flex h-full flex-col bg-(--ui-editor-surface-background)">
      {/* 标题栏 */}
      <div className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold">MIM · 多平台即时通讯</h2>
          <p className="mt-0.5 text-xs text-(--ui-text-tertiary)">
            Multi IM · 跨平台消息路由 · {gatewayState === 'open' ? '🟢 网关在线' : '⏳ 连接中'}
          </p>
        </div>
        <Button onClick={onClose} size="icon" variant="ghost">✕</Button>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-auto p-6 space-y-6">
        
        {/* 平台状态卡片 */}
        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">已接入平台</h3>
          <div className="grid grid-cols-3 gap-3">
            {platforms.map(p => (
              <PlatformCard
                active={selectedPlatform === p.platform}
                key={p.platform}
                onClick={() => setSelectedPlatform(
                  selectedPlatform === p.platform ? null : p.platform
                )}
                platform={p}
              />
            ))}
          </div>
        </section>

        {/* 选中平台详情 */}
        {selectedPlatform && (
          <PlatformDetail platform={selectedPlatform} />
        )}

        {/* Hub 状态 */}
        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">Hub 连接状态</h3>
          <div className="space-y-2">
            <ListRow
              description="192.168.3.23:3306/winpeek"
              title="MySQL 归档"
            />
            <ListRow
              description="WINPEEK_HUB_ENABLED=1 时自动启用"
              title="跨平台路由"
            />
            <ListRow
              description="消息归档引擎: mysql / jsonl / off"
              title="归档引擎"
            />
          </div>
        </section>

        {/* 消息统计 */}
        <section>
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">消息统计（今日）</h3>
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="总消息" value="—" />
            <StatCard label="跨平台" value="—" />
            <StatCard label="已归档" value="—" />
            <StatCard label="活跃用户" value="—" />
          </div>
        </section>
      </div>
    </div>
  )
}

function PlatformCard({ platform, active, onClick }: {
  active: boolean
  onClick: () => void
  platform: PlatformStatus
}) {
  return (
    <div
      className={`cursor-pointer rounded-lg border p-3 transition-colors hover:bg-(--ui-bg-quaternary) ${
        active ? 'border-(--ui-accent) bg-(--ui-bg-quaternary)' : 'border-(--ui-stroke-tertiary)'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{platform.icon}</span>
        <span className="text-sm font-medium">{platform.name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${platform.connected ? 'bg-green-500' : 'bg-(--ui-stroke-tertiary)'}`} />
        <span className="text-xs text-(--ui-text-tertiary)">
          {platform.connected ? `${platform.users} 用户` : '未接入'}
        </span>
      </div>
    </div>
  )
}

function PlatformDetail({ platform }: { platform: string }) {
  const details: Record<string, { contacts: string; messages: string; pid: string }> = {
    wechat:   { contacts: '1,250', messages: '—', pid: 'Weixin.exe (99212)' },
    dingtalk: { contacts: '—',     messages: '—', pid: '未运行' },
    feishu:   { contacts: '—',     messages: '—', pid: '未运行' },
    qq:       { contacts: '—',     messages: '—', pid: '未运行' },
    telegram: { contacts: '—',     messages: '—', pid: '未运行' },
  }
  const d = details[platform] || { contacts: '—', messages: '—', pid: '—' }
  
  return (
    <section className="rounded-lg border border-(--ui-stroke-tertiary) p-4">
      <h4 className="mb-3 text-sm font-medium">{platform} 详情</h4>
      <div className="grid grid-cols-3 gap-4 text-xs text-(--ui-text-secondary)">
        <div>
          <span className="text-(--ui-text-tertiary)">联系人</span>
          <div className="mt-1 font-mono">{d.contacts}</div>
        </div>
        <div>
          <span className="text-(--ui-text-tertiary)">消息</span>
          <div className="mt-1 font-mono">{d.messages}</div>
        </div>
        <div>
          <span className="text-(--ui-text-tertiary)">进程</span>
          <div className="mt-1 font-mono text-xs">{d.pid}</div>
        </div>
      </div>
    </section>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-(--ui-stroke-tertiary) p-3 text-center">
      <div className="text-lg font-semibold text-(--ui-text-primary)">{value}</div>
      <div className="text-xs text-(--ui-text-tertiary) mt-1">{label}</div>
    </div>
  )
}
