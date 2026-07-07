import { useStore } from '@nanostores/react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import { useI18n } from '@/i18n'
import { openExternalLink } from '@/lib/external-link'
import { cn } from '@/lib/utils'
import { $gatewayState, $connection } from '@/store/session'

import { DetailColumn, ListColumn, MasterDetail } from '../../master-detail'

/* ── Types ───────────────────────────────────── */

interface Contact {
  id: string
  name: string
  uid: number
  role?: string
  lastMessage?: string
  lastTime?: string
  unread: number
  online: boolean
}

interface ChatMessage {
  id: string
  fromUid: number
  fromName: string
  content: string
  time: string
  isSelf: boolean
}

/* ── Mock data (will be replaced with Hub API) ── */

const DEFAULT_CONTACTS: Contact[] = [
  { id: 'dev',    name: '开发者',  uid: 2023, role: 'Developer', lastMessage: '好的，收到',         lastTime: '09:15', unread: 2, online: true },
  { id: 'arch',   name: '架构师',  uid: 2024, role: 'Architect', lastMessage: '接口设计已更新',     lastTime: '昨天',  unread: 0, online: true },
  { id: 'ops',    name: '运维',    uid: 2025, role: 'Ops',       lastMessage: '服务已重启',         lastTime: '昨天',  unread: 0, online: false },
  { id: 'qa',     name: '测试',    uid: 2026, role: 'QA',        lastMessage: '第3轮测试通过',      lastTime: '前天',  unread: 1, online: true },
  { id: 'pm',     name: 'PM',      uid: 2027, role: 'PM',        lastMessage: '需求文档已发',       lastTime: '周一',  unread: 0, online: true },
  { id: 'director', name: '总监',  uid: 2028, role: 'Director',  lastMessage: '下周评审',           lastTime: '周一',  unread: 0, online: false },
  { id: 'boss',   name: '老板',    uid: 2029, role: 'Boss',      lastMessage: '进度如何？',         lastTime: '上周',  unread: 3, online: false },
  { id: 'group1', name: '项目组',  uid: 0,    role: undefined,   lastMessage: '【群】@所有人 周会', lastTime: '09:30', unread: 5, online: true },
]

/* ── Component ────────────────────────────────── */

export function MimView({ onClose }: { onClose: () => void }) {
  const gatewayState = useStore($gatewayState)
  const conn = useStore($connection)

  const [contacts] = useState<Contact[]>(DEFAULT_CONTACTS)
  const [activeContactId, setActiveContactId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const activeContact = useMemo(
    () => contacts.find(c => c.id === activeContactId) ?? null,
    [contacts, activeContactId]
  )

  // Load messages when contact selected
  useEffect(() => {
    if (!activeContact) {
      setMessages([])
      return
    }
    // Mock messages (will be from Hub API)
    setMessages([
      { id: '1', fromUid: activeContact.uid, fromName: activeContact.name, content: '你好，有个事情沟通一下', time: '09:00', isSelf: false },
      { id: '2', fromUid: 2022, fromName: '我', content: '请说', time: '09:01', isSelf: true },
      { id: '3', fromUid: activeContact.uid, fromName: activeContact.name, content: activeContact.lastMessage || '...', time: '09:15', isSelf: false },
    ])
  }, [activeContact])

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text || !activeContact) return

    setMessages(prev => [...prev, {
      id: `msg-${Date.now()}`,
      fromUid: 2022,
      fromName: '我',
      content: text,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      isSelf: true,
    }])
    setInputText('')
  }, [inputText, activeContact])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  // Sort contacts: online first, then by last message time
  const sortedContacts = useMemo(() => {
    return [...contacts].sort((a, b) => {
      if (a.online !== b.online) return a.online ? -1 : 1
      return (b.unread || 0) - (a.unread || 0)
    })
  }, [contacts])

  return (
    <MasterDetail>
      {/* ── Left: Contact List ── */}
      <ListColumn className="border-r border-(--ui-stroke-tertiary)">
        <div className="flex h-full flex-col">
          <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-3 py-2.5">
            <h2 className="text-sm font-semibold text-foreground">WinPeek 消息</h2>
            <span className="text-[0.65rem] text-(--ui-text-tertiary)">
              {gatewayState === 'open' ? '🟢 在线' : '⏳ 离线'}
            </span>
          </header>

          <div className="flex-1 overflow-y-auto">
            {sortedContacts.map(contact => (
              <button
                key={contact.id}
                className={cn(
                  'flex w-full items-center gap-2.5 border-b border-(--ui-stroke-quaternary) px-3 py-2.5 text-left transition-colors',
                  'hover:bg-(--ui-control-hover-background)',
                  activeContactId === contact.id && 'bg-(--ui-control-active-background)'
                )}
                onClick={() => setActiveContactId(contact.id)}
              >
                {/* Avatar */}
                <div className="relative shrink-0">
                  <div className={cn(
                    'flex h-9 w-9 items-center justify-center rounded-full text-xs font-semibold',
                    contact.uid === 0
                      ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                      : 'bg-(--ui-accent)/15 text-(--ui-accent)'
                  )}>
                    {contact.uid === 0 ? '群' : contact.name.charAt(0)}
                  </div>
                  {contact.online && (
                    <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-(--ui-bg-surface) bg-emerald-500" />
                  )}
                </div>

                {/* Info */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between">
                    <span className="truncate text-sm font-medium text-foreground">{contact.name}</span>
                    {contact.lastTime && (
                      <span className="ml-2 shrink-0 text-[0.6rem] text-(--ui-text-tertiary)">{contact.lastTime}</span>
                    )}
                  </div>
                  <div className="mt-0.5 flex items-center justify-between">
                    <span className="truncate text-xs text-(--ui-text-tertiary)">
                      {contact.lastMessage || '暂无消息'}
                    </span>
                    {(contact.unread || 0) > 0 && (
                      <span className="ml-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[0.6rem] font-medium text-destructive-foreground">
                        {contact.unread > 99 ? '99+' : contact.unread}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </ListColumn>

      {/* ── Right: Chat Area ── */}
      <DetailColumn>
        {activeContact ? (
          <div className="flex h-full flex-col">
            {/* Chat Header */}
            <header className="flex items-center justify-between border-b border-(--ui-stroke-tertiary) px-4 py-2.5">
              <div className="flex items-center gap-2.5">
                <div className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold',
                  activeContact.uid === 0
                    ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                    : 'bg-(--ui-accent)/15 text-(--ui-accent)'
                )}>
                  {activeContact.uid === 0 ? '群' : activeContact.name.charAt(0)}
                </div>
                <div>
                  <div className="text-sm font-medium text-foreground">{activeContact.name}</div>
                  <div className="text-[0.6rem] text-(--ui-text-tertiary)">
                    {activeContact.online ? '在线' : '离线'}
                    {activeContact.role && ` · ${activeContact.role}`}
                    {activeContact.uid > 0 && ` · #${activeContact.uid}`}
                  </div>
                </div>
              </div>
            </header>

            {/* Messages */}
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={cn(
                    'flex',
                    msg.isSelf ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div className={cn(
                    'max-w-[70%] rounded-xl px-3 py-2 text-sm',
                    msg.isSelf
                      ? 'bg-(--ui-accent) text-(--ui-accent-foreground) rounded-br-md'
                      : 'bg-(--ui-bg-quaternary) text-foreground rounded-bl-md'
                  )}>
                    {!msg.isSelf && (
                      <div className="mb-0.5 text-[0.6rem] font-medium text-(--ui-text-tertiary)">
                        {msg.fromName}
                      </div>
                    )}
                    <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                    <div className={cn(
                      'mt-1 text-right text-[0.55rem]',
                      msg.isSelf ? 'text-(--ui-accent-foreground)/60' : 'text-(--ui-text-quaternary)'
                    )}>
                      {msg.time}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-(--ui-stroke-tertiary) p-3">
              <div className="flex items-end gap-2">
                <textarea
                  className={cn(
                    'min-h-[2.25rem] flex-1 resize-none rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-quaternary) px-3 py-1.5',
                    'text-sm text-foreground placeholder:text-(--ui-text-tertiary)',
                    'focus:border-(--ui-accent) focus:outline-none'
                  )}
                  onChange={e => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入消息..."
                  rows={1}
                  value={inputText}
                />
                <Button
                  className="shrink-0"
                  disabled={!inputText.trim()}
                  onClick={handleSend}
                  size="sm"
                >
                  <Codicon className="mr-1 size-3.5" name="send" />
                  发送
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* Empty state */
          <div className="grid h-full place-items-center">
            <div className="text-center">
              <div className="mb-3 text-3xl">💬</div>
              <p className="text-sm text-(--ui-text-tertiary)">选择一个联系人开始聊天</p>
              <p className="mt-1 text-xs text-(--ui-text-quaternary)">
                MIM · WinPeek 多实例消息
              </p>
            </div>
          </div>
        )}
      </DetailColumn>
    </MasterDetail>
  )
}
