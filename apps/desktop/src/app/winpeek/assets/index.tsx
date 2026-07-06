import { useStore } from '@nanostores/react'
import { useState } from 'react'

import { Button } from '../../../components/ui/button'
import { $gatewayState } from '../../../store/session'
import { ListRow } from '../../settings/primitives'

interface SoftwareItem {
  name: string
  category: string
  version: string
  publisher: string
  exe_path: string
  install_path: string
  process_name: string
  description: string
}

type TabKey = 'software' | 'im' | 'video' | 'dev' | 'office'

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: 'software', icon: '💻', label: '全部软件' },
  { key: 'im',       icon: '💬', label: 'IM' },
  { key: 'video',    icon: '🎵', label: '视频/电商' },
  { key: 'dev',      icon: '🛠️', label: '开发/工具' },
  { key: 'office',   icon: '📄', label: '办公/设计' },
]

// 扫描完成后缓存在这里（后续通过 WebSocket 真实获取）
const DEMO_APPS: SoftwareItem[] = [
  { name: '微信',             category: 'IM',     version: '4.1.11.24', publisher: 'Tencent', exe_path: 'D:\\Program Files\\Weixin\\Weixin.exe',      install_path: 'D:\\Program Files\\Weixin\\',        process_name: 'Weixin.exe',       description: '微信桌面客户端' },
  { name: 'QQ',               category: 'IM',     version: '9.9.15',    publisher: 'Tencent', exe_path: 'D:\\Program Files\\Tencent\\QQNT\\QQ.exe',   install_path: 'D:\\Program Files\\Tencent\\QQNT\\', process_name: 'QQ.exe',           description: '腾讯 QQ 桌面客户端' },
  { name: '钉钉',             category: 'IM',     version: '7.6.0',     publisher: 'Alibaba', exe_path: 'D:\\Program Files\\DingTalk\\DingTalk.exe',  install_path: 'D:\\Program Files\\DingTalk\\',      process_name: 'DingTalk.exe',     description: '钉钉桌面客户端' },
  { name: '飞书',             category: 'IM',     version: '7.18.0',    publisher: 'ByteDance', exe_path: 'C:\\Users\\Admin\\AppData\\Local\\Feishu\\Feishu.exe', install_path: '', process_name: 'Feishu.exe', description: '飞书桌面客户端' },
  { name: 'Telegram',         category: 'IM',     version: '5.2.0',     publisher: 'Telegram', exe_path: 'D:\\Program Files\\Telegram Desktop\\Telegram.exe', install_path: '', process_name: 'Telegram.exe', description: 'Telegram 桌面客户端' },
  { name: '抖音',             category: '视频',   version: '3.8.0',     publisher: 'ByteDance', exe_path: '', install_path: '', process_name: 'Douyin.exe',       description: '抖音桌面客户端' },
  { name: '剪映',             category: '视频',   version: '6.0.0',     publisher: 'ByteDance', exe_path: '', install_path: '', process_name: 'Jianying.exe',     description: '剪映专业版' },
  { name: 'VS Code',          category: '开发',   version: '1.95.0',    publisher: 'Microsoft', exe_path: 'C:\\Users\\Admin\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe', install_path: '', process_name: 'Code.exe', description: 'Visual Studio Code' },
  { name: 'Navicat Premium',  category: '数据库', version: '17.0.0',    publisher: 'PremiumSoft', exe_path: 'D:\\Program Files\\PremiumSoft\\Navicat Premium 17\\navicat.exe', install_path: '', process_name: 'navicat.exe', description: 'Navicat Premium 数据库管理工具' },
  { name: 'Chrome',           category: '浏览器', version: '131.0.0',   publisher: 'Google',    exe_path: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', install_path: '', process_name: 'chrome.exe', description: 'Google Chrome 浏览器' },
  { name: 'Edge',             category: '浏览器', version: '131.0.0',   publisher: 'Microsoft', exe_path: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', install_path: '', process_name: 'msedge.exe', description: 'Microsoft Edge 浏览器' },
]

const DISK_INFO = [
  { drive: 'C:', label: '系统盘', total: '200 GB', used: '120 GB', free: '80 GB', percent: 60 },
  { drive: 'D:', label: '数据盘', total: '500 GB', used: '320 GB', free: '180 GB', percent: 64 },
]

export function AssetsView({ onClose }: { onClose: () => void }) {
  const gatewayState = useStore($gatewayState)
  const [activeTab, setActiveTab] = useState<TabKey>('software')
  const [apps] = useState<SoftwareItem[]>(DEMO_APPS)

  const filterByTab = (a: SoftwareItem) => {
    if (activeTab === 'software') { return true; }
    if (activeTab === 'im') { return a.category === 'IM'; }
    if (activeTab === 'video') { return a.category === '视频' || a.category === '电商'; }
    if (activeTab === 'dev') { return ['开发', '数据库', '工具', '浏览器'].includes(a.category); }
    if (activeTab === 'office') { return ['办公', '设计'].includes(a.category); }
    return true;
  }
  const filtered = apps.filter(filterByTab)

  const categories = [...new Set(filtered.map(a => a.category))]

  return (
    <div className="flex h-full flex-col bg-(--ui-editor-surface-background)">
      {/* 标题栏 */}
      <div className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold">电脑资产</h2>
          <p className="mt-0.5 text-xs text-(--ui-text-tertiary)">
            软件资产 · 硬件资产 · 磁盘管理 · {gatewayState === 'open' ? '🟢 在线' : '⏳ 连接中'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => {}} size="xs" variant="secondary">🔄 重新扫描</Button>
          <Button onClick={onClose} size="icon" variant="ghost">✕</Button>
        </div>
      </div>

      {/* 页签 */}
      <div className="flex gap-1 border-b border-(--ui-stroke-tertiary) px-6 py-2">
        {TABS.map(t => (
          <button
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === t.key
                ? 'bg-(--ui-bg-quaternary) text-(--ui-text-primary)'
                : 'text-(--ui-text-tertiary) hover:text-(--ui-text-secondary)'
            }`}
            key={t.key}
            onClick={() => setActiveTab(t.key)}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-auto p-6">
        {/* 软件列表 */}
        <section className="space-y-6">
          {categories.map(cat => {
            const catApps = filtered.filter(a => a.category === cat)
            return (
              <div key={cat}>
                <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">{cat} ({catApps.length})</h3>
                <div className="space-y-2">
                  {catApps.map(app => (
                    <ListRow
                      action={
                        <span className="text-xs text-(--ui-text-quaternary)">
                          {app.version ? `v${app.version}` : '—'}
                        </span>
                      }
                      description={app.exe_path || app.description}
                      key={app.name}
                      title={app.name}
                    />
                  ))}
                </div>
              </div>
            )
          })}

          {filtered.length === 0 && (
            <div className="py-16 text-center text-(--ui-text-tertiary)">此分类下暂无软件</div>
          )}
        </section>

        {/* 硬件/磁盘区 */}
        <section className="mt-8">
          <h3 className="mb-3 text-sm font-medium text-(--ui-text-secondary)">💾 磁盘</h3>
          <div className="space-y-2">
            {DISK_INFO.map(d => (
              <ListRow
                action={
                  <span className="text-xs text-(--ui-text-quaternary)">{d.percent}%</span>
                }
                description={`${d.used} / ${d.total} · 剩余 ${d.free}`}
                key={d.drive}
                title={`${d.drive} ${d.label}`}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
