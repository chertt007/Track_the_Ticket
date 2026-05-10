import { useState } from 'react'
import { type TelegramLinkToken } from '../api'
import { issueLinkToken } from '../store/slices/telegramSlice'
import { useAppDispatch } from '.'

/**
 * Build a `tg://` deep-link that the OS hands directly to Telegram Desktop
 * (or the mobile app) when the protocol handler is registered.
 *
 * `https://t.me/...` lands in a browser tab and only sometimes redirects
 * into the desktop client; `tg://` is unambiguous.
 */
export function buildTgDeepLink(link: TelegramLinkToken): string {
  return `tg://resolve?domain=${link.bot_username}&start=${link.token}`
}

/**
 * Trigger the `tg://` URL via a programmatic anchor click. This is more
 * reliable than a hidden iframe for protocol-handler launches: browsers
 * treat it as a regular link click, fully passing query parameters
 * (domain, start) to the OS handler. Our page stays put — the browser
 * defers to the OS for the unknown scheme. If no app is registered the
 * click fails quietly; the modal shows a manual web fallback.
 */
export function launchTelegramDesktop(tgUrl: string): void {
  const a = document.createElement('a')
  a.href = tgUrl
  a.style.position = 'fixed'
  a.style.left = '-9999px'
  a.style.top = '-9999px'
  document.body.appendChild(a)
  a.click()
  window.setTimeout(() => a.remove(), 500)
}

export function isLinkExpired(link: TelegramLinkToken | null): boolean {
  if (!link) return true
  return new Date(link.expires_at).getTime() <= Date.now()
}

/**
 * One-click connect flow used by the Dashboard banner and the Settings
 * menu item.
 *
 * Browsers strip "transient user activation" once a click handler `await`s,
 * which causes Chromium to silently drop subsequent `tg://` protocol
 * launches. To keep the launch in-gesture, we pre-issue the token via
 * `prefetchToken()` (called from a `useEffect`, no gesture needed) and
 * then `launchNow()` synchronously inside the click handler — no `await`
 * between the user click and the protocol fire.
 *
 * `connectFallback()` is the async path used when no fresh token is
 * available; the launch is best-effort and the modal shows a manual
 * "Open in Telegram" anchor button as a guaranteed fallback.
 */
export function useTelegramConnect() {
  const dispatch = useAppDispatch()
  const [issuing, setIssuing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const prefetchToken = async (): Promise<void> => {
    setError(null)
    setIssuing(true)
    try {
      await dispatch(issueLinkToken()).unwrap()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'failed')
    } finally {
      setIssuing(false)
    }
  }

  const launchNow = (link: TelegramLinkToken): void => {
    launchTelegramDesktop(buildTgDeepLink(link))
  }

  const connectFallback = async (): Promise<TelegramLinkToken | null> => {
    setError(null)
    setIssuing(true)
    try {
      const link = await dispatch(issueLinkToken()).unwrap()
      launchTelegramDesktop(buildTgDeepLink(link))
      return link
    } catch (e) {
      setError(e instanceof Error ? e.message : 'failed')
      return null
    } finally {
      setIssuing(false)
    }
  }

  return { prefetchToken, launchNow, connectFallback, issuing, error }
}
