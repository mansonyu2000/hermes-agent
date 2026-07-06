import { useStore } from '@nanostores/react'
import { useState } from 'react'

import { Button } from '../../../components/ui/button'
import { $gatewayState } from '../../../store/session'
import { WechatPanel } from '../wechat'

type Platform = 'wechat' | 'douyin' | 'kuaishou' | 'shipinhao' | 'xiaohongshu' | 'bilibili'

interface PlatformDef {
  desc: string
  icon: string
  key: Platform
  name: string
}

const PLATFORMS: PlatformDef[] = [
  { key: 'wechat',      icon: '💬', name: '微信',     desc: '好友管理 · 消息发送' },
  { key: 'douyin',      icon: '🎵', name: '抖音',     desc: '短视频发布 · 数据监控' },
  { key: 'kuaishou',    icon: '📺', name: '快手',     desc: '内容发布 · 直播管理' },
  { key: 'shipinhao',   icon: '📱', name: '视频号',   desc: '微信生态 · 内容运营' },
  { key: 'xiaohongshu', icon: '📕', name: '小红书',   desc: '笔记发布 · 种草营销' },
  { key: 'bilibili',    icon: '📺', name: 'B站',      desc: '视频投稿 · 弹幕互动' },
]

function PlatformCard({ active, onClick, platform }: {
  active: boolean
  onClick: () => void
  platform: PlatformDef
}) {
  return (
    <button
      className={`flex flex-col items-center gap-1 rounded-lg border px-3 py-2.5 text-xs transition-colors ${
        active
          ? 'border-(--ui-accent) bg-(--ui-bg-quaternary) text-(--ui-text-primary)'
          : 'border-transparent text-(--ui-text-tertiary) hover:bg-(--ui-bg-quaternary) hover:text-(--ui-text-secondary)'
      }`}
      onClick={onClick}
    >
      <span className="text-base">{platform.icon}</span>
      <span className="font-medium">{platform.name}</span>
    </button>
  )
}

function PlatformPlaceholder({ platform }: { platform: PlatformDef }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-(--ui-text-tertiary)">
      <span className="mb-3 text-4xl">{platform.icon}</span>
      <p className="text-sm font-medium">{platform.name}</p>
      <p className="mt-1 text-xs">{platform.desc}</p>
      <p className="mt-3 text-xs text-(--ui-text-quaternary)">
        通过 cua-driver + trace-to-template 学习操作
      </p>
      <Button className="mt-4" size="xs" variant="secondary">
        开始学习
      </Button>
    </div>
  )
}

export function AutomationView({ onClose }: { onClose: () => void }) {
  const gatewayState = useStore($gatewayState)
  const [activePlatform, setActivePlatform] = useState<Platform>('wechat')

  return (
    <div className="flex h-full flex-col bg-(--ui-editor-surface-background)">
      {/* 标题栏 */}
      <div className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold">桌面自动化</h2>
          <p className="mt-0.5 text-xs text-(--ui-text-tertiary)">
            WinPeek RPA · {gatewayState === 'open' ? '🟢 就绪' : '⏳ 连接中'}
          </p>
        </div>
        <Button onClick={onClose} size="icon" variant="ghost">✕</Button>
      </div>

      {/* 平台页签 */}
      <div className="flex gap-1 overflow-x-auto border-b border-(--ui-stroke-tertiary) px-6 py-2">
        {PLATFORMS.map(p => (
          <PlatformCard
            active={activePlatform === p.key}
            key={p.key}
            onClick={() => setActivePlatform(p.key)}
            platform={p}
          />
        ))}
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-auto p-6">
        {activePlatform === 'wechat' && <WechatPanel />}
        {activePlatform !== 'wechat' && (
          <PlatformPlaceholder platform={PLATFORMS.find(p => p.key === activePlatform)!} />
        )}
      </div>
    </div>
  )
}
