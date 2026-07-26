import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { codiconIcon } from '@/components/ui/codicon'
import { Tip } from '@/components/ui/tooltip'
import { getHermesConfigDefaults, getHermesConfigRecord, saveHermesConfig } from '@/hermes'
import { useI18n } from '@/i18n'
import { triggerHaptic } from '@/lib/haptics'
import { Archive, Bell, Cpu, Download, Globe, Info, KeyRound, Lock, RefreshCw, Settings2, Upload, Users, Wrench, Zap } from '@/lib/icons'
import { notifyError } from '@/store/notifications'

import { useRouteEnumParam } from '../hooks/use-route-enum-param'
import { OverlayIconButton } from '../overlays/overlay-chrome'
import { OverlayMain, OverlayNav, type OverlayNavGroup, OverlaySplitLayout } from '../overlays/overlay-split-layout'
import { OverlayView } from '../overlays/overlay-view'
import { SKILLS_ROUTE } from '../routes'

import { AboutSettings } from './about-settings'
import { AppearanceSettings } from './appearance-settings'
import { ConfigSettings } from './config-settings'
import { SECTIONS } from './constants'
import { GatewaySettings } from './gateway-settings'
import { KEYS_VIEWS, KeysSettings, type KeysView } from './keys-settings'
import { NotificationsSettings } from './notifications-settings'
import { PROVIDER_VIEWS, ProvidersSettings, type ProviderView } from './providers-settings'
import { SessionsSettings } from './sessions-settings'
import type { SettingsPageProps, SettingsView as SettingsViewId } from './types'

import {
  AccountsTab,
  AgentsTab,
  DevicesTab,
  OrganizationTab,
  PasswordTab,
  PeekaLoginPanel,
  ProfileTab,
  loadSavedIdentity,
  removeIdentity,
  saveIdentity,
  type WinPeekIdentity,
} from '../winpeek/peeka'
import { useGatewayRequest } from '../gateway/hooks/use-gateway-request'

const PEEKA_VIEWS = ['profile', 'accounts', 'password', 'organization', 'devices', 'agents'] as const

const SETTINGS_VIEWS: readonly SettingsViewId[] = [
  ...SECTIONS.map(s => `config:${s.id}` as SettingsViewId),
  ...PEEKA_VIEWS.map(v => `peeka:${v}` as SettingsViewId),
  'providers',
  'gateway',
  'keys',
  'notifications',
  'sessions',
  'about'
]

export function SettingsView({ onClose, onConfigSaved, onMainModelChanged }: SettingsPageProps) {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { hash, pathname, search } = useLocation()
  const { requestGateway: rq } = useGatewayRequest()

  // Peeka identity state — synced across sidebar, MIM, and SettingsView
  const [peekaIdent, setPeekaIdent] = useState<WinPeekIdentity | null>(loadSavedIdentity)
  const refreshPeeka = useCallback(() => setPeekaIdent(loadSavedIdentity()), [])

  useEffect(() => {
    const onPeekaChanged = () => refreshPeeka()
    window.addEventListener('peeka-changed', onPeekaChanged)
    window.addEventListener('storage', onPeekaChanged) // cross-tab
    return () => {
      window.removeEventListener('peeka-changed', onPeekaChanged)
      window.removeEventListener('storage', onPeekaChanged)
    }
  }, [refreshPeeka])

  // MCP moved out of Settings into Capabilities (/skills?tab=mcp). Keep old
  // `/settings?tab=mcp` deep links working — `useRouteEnumParam` would silently
  // coerce the unknown tab to the default view otherwise. Preserve `server=` so
  // an old bookmark still lands on (and highlights) the selected server.
  useEffect(() => {
    const params = new URLSearchParams(search)

    if (params.get('tab') === 'mcp') {
      const server = params.get('server')
      const suffix = server ? `&server=${encodeURIComponent(server)}` : ''
      navigate(`${SKILLS_ROUTE}?tab=mcp${suffix}`, { replace: true })
    }
  }, [navigate, search])

  const [activeView, setActiveView] = useRouteEnumParam('tab', SETTINGS_VIEWS, 'config:model' as SettingsViewId)
  // Providers subnav (Accounts vs API keys) lives in its own param so each
  // sub-view is deep-linkable and survives a refresh.
  const [providerView, setProviderView] = useRouteEnumParam<ProviderView>('pview', PROVIDER_VIEWS, 'accounts')
  const [keysView] = useRouteEnumParam<KeysView>('kview', KEYS_VIEWS, 'tools')

  // Jump to a section + its sub-view in one navigate. Two sequential setters
  // would each read the same stale `search` and the second would clobber the
  // first's `tab` — so the sub-view never opened on narrow screens.
  const openSubView = (tab: SettingsViewId, param: string, value: string, fallback: string) => {
    const params = new URLSearchParams(search)
    params.set('tab', tab)

    if (value === fallback) {
      params.delete(param)
    } else {
      params.set(param, value)
    }

    const qs = params.toString()
    navigate({ hash, pathname, search: qs ? `?${qs}` : '' }, { replace: true })
  }

  const openProviderView = (view: ProviderView) => openSubView('providers', 'pview', view, 'accounts')
  const openKeysView = (view: KeysView) => openSubView('keys', 'kview', view, 'tools')

  const importInputRef = useRef<HTMLInputElement | null>(null)

  const exportConfig = async () => {
    try {
      const cfg = await getHermesConfigRecord()
      const blob = new Blob([JSON.stringify(cfg, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'hermes-config.json'
      a.click()
      URL.revokeObjectURL(url)
      triggerHaptic('success')
    } catch (err) {
      notifyError(err, t.settings.exportFailed)
    }
  }

  const resetConfig = async () => {
    if (!window.confirm(t.settings.resetConfirm)) {
      return
    }

    try {
      await saveHermesConfig(await getHermesConfigDefaults())
      triggerHaptic('success')
      onConfigSaved?.()
    } catch (err) {
      notifyError(err, t.settings.resetFailed)
    }
  }

  const navGroups: OverlayNavGroup[] = [
    ...SECTIONS.map(s => {
      const view = `config:${s.id}` as SettingsViewId

      return {
        active: activeView === view,
        icon: s.icon,
        id: view,
        label: t.settings.sections[s.id] ?? s.label,
        onSelect: () => setActiveView(view)
      }
    }),
    // ── Peeka identity group ──
    ...(peekaIdent ? [{
      active: activeView.startsWith('peeka:'),
      children: [
        ...PEEKA_VIEWS.map(v => ({
          active: activeView === `peeka:${v}`,
          icon: v === 'profile' ? Info : v === 'password' ? Lock : v === 'organization' ? Globe : v === 'devices' ? Cpu : v === 'agents' ? Zap : Users,
          id: `peeka:${v}`,
          label: { profile: 'Personal Info', accounts: 'Account Switch', password: 'Change Password', organization: 'Organization', devices: 'My Devices', agents: 'My Agents' }[v],
          onSelect: () => setActiveView(`peeka:${v}` as SettingsViewId),
        })),
        {
          active: false,
          icon: Lock,
          id: 'peeka:logout',
          label: `退出 (${peekaIdent.name})`,
          onSelect: () => {
            removeIdentity(peekaIdent.uid)
            setPeekaIdent(null)
            window.dispatchEvent(new CustomEvent('peeka-changed'))
            window.location.reload()
          },
        },
      ],
      gapBefore: true,
      icon: Users,
      id: 'peeka',
      label: 'Peeka',
      onSelect: () => setActiveView('peeka:profile' as SettingsViewId),
    }] : [{
      active: activeView.startsWith('peeka:'),
      icon: Users,
      id: 'peeka',
      label: 'Peeka',
      onSelect: () => setActiveView('peeka:profile' as SettingsViewId),
    }]),
    {
      active: activeView === 'notifications',
      icon: Bell,
      id: 'notifications',
      label: t.settings.nav.notifications,
      onSelect: () => setActiveView('notifications')
    },
    {
      active: activeView === 'providers',
      children: [
        {
          active: activeView === 'providers' && providerView === 'accounts',
          icon: codiconIcon('account'),
          id: 'pview:accounts',
          label: t.settings.nav.providerAccounts,
          onSelect: () => openProviderView('accounts')
        },
        {
          active: activeView === 'providers' && providerView === 'keys',
          icon: KeyRound,
          id: 'pview:keys',
          label: t.settings.nav.providerApiKeys,
          onSelect: () => openProviderView('keys')
        }
      ],
      gapBefore: true,
      icon: Zap,
      id: 'providers',
      label: t.settings.nav.providers,
      onSelect: () => setActiveView('providers')
    },
    {
      active: activeView === 'gateway',
      icon: Globe,
      id: 'gateway',
      label: t.settings.nav.gateway,
      onSelect: () => setActiveView('gateway')
    },
    {
      active: activeView === 'keys',
      children: [
        {
          active: activeView === 'keys' && keysView === 'tools',
          icon: Wrench,
          id: 'kview:tools',
          label: t.settings.nav.keysTools,
          onSelect: () => openKeysView('tools')
        },
        {
          active: activeView === 'keys' && keysView === 'settings',
          icon: Settings2,
          id: 'kview:settings',
          label: t.settings.nav.keysSettings,
          onSelect: () => openKeysView('settings')
        }
      ],
      icon: KeyRound,
      id: 'keys',
      label: t.settings.nav.apiKeys,
      onSelect: () => setActiveView('keys')
    },
    {
      active: activeView === 'sessions',
      icon: Archive,
      id: 'sessions',
      label: t.settings.nav.archivedChats,
      onSelect: () => setActiveView('sessions')
    },
    {
      active: activeView === 'about',
      gapBefore: true,
      icon: Info,
      id: 'about',
      label: t.settings.nav.about,
      onSelect: () => setActiveView('about')
    }
  ]

  const navFooter = (
    <>
      <Tip label={t.settings.exportConfig}>
        <OverlayIconButton onClick={() => void exportConfig()}>
          <Download />
        </OverlayIconButton>
      </Tip>
      <Tip label={t.settings.importConfig}>
        <OverlayIconButton
          onClick={() => {
            triggerHaptic('open')
            importInputRef.current?.click()
          }}
        >
          <Upload />
        </OverlayIconButton>
      </Tip>
      <Tip label={t.settings.resetToDefaults}>
        <OverlayIconButton
          className="hover:text-destructive"
          onClick={() => {
            triggerHaptic('warning')
            void resetConfig()
          }}
        >
          <RefreshCw />
        </OverlayIconButton>
      </Tip>
    </>
  )

  return (
    <OverlayView closeLabel={t.settings.closeSettings} onClose={onClose}>
      <OverlaySplitLayout>
        <OverlayNav footer={navFooter} groups={navGroups} />

        <OverlayMain className="px-0 pb-0">
          {activeView === 'config:appearance' ? (
            <AppearanceSettings />
          ) : activeView === 'about' ? (
            <AboutSettings />
          ) : activeView === 'gateway' ? (
            <GatewaySettings />
          ) : activeView.startsWith('config:') ? (
            <ConfigSettings
              activeSectionId={activeView.slice('config:'.length)}
              importInputRef={importInputRef}
              onConfigSaved={onConfigSaved}
              onMainModelChanged={onMainModelChanged}
            />
          ) : activeView.startsWith('peeka:') ? (
            peekaIdent ? (
              (() => {
                const tab = activeView.slice('peeka:'.length)
                if (tab === 'profile') return <ProfileTab identity={peekaIdent} rq={rq} onUpdate={id => { saveIdentity(id); refreshPeeka(); }} />
                if (tab === 'accounts') return <AccountsTab currentUid={peekaIdent.uid} onSwitch={id => { saveIdentity(id); window.location.reload() }} />
                if (tab === 'password') return <PasswordTab uid={peekaIdent.uid} rq={rq} />
                if (tab === 'organization') return <OrganizationTab uid={peekaIdent.uid} rq={rq} />
                if (tab === 'devices') return <DevicesTab uid={peekaIdent.uid} rq={rq} />
                if (tab === 'agents') return <AgentsTab uid={peekaIdent.uid} rq={rq} />
                return null
              })()
            ) : (
              <PeekaLoginPanel onLogin={refreshPeeka} />
            )
          ) : activeView === 'providers' ? (
            <ProvidersSettings onClose={onClose} onViewChange={setProviderView} view={providerView} />
          ) : activeView === 'keys' ? (
            <KeysSettings view={keysView} />
          ) : activeView === 'notifications' ? (
            <NotificationsSettings />
          ) : (
            <SessionsSettings />
          )}
        </OverlayMain>
      </OverlaySplitLayout>
    </OverlayView>
  )
}

export { SettingsView as SettingsPage }
