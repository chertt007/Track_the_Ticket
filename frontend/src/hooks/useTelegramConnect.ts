import { useState } from 'react'
import { requestTelegramLinkToken, type TelegramLinkToken } from '../api'
import { setPendingLink } from '../store/slices/telegramSlice'
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
 * Fire the `tg://` URL via a hidden iframe. If Telegram Desktop is
 * installed and registered as the protocol handler, the OS launches it
 * silently — our page stays put, no blank tab, no t.me detour. If the
 * scheme is unhandled the iframe fails quietly; we offer a manual web
 * fallback button in the modal for that case.
 */
export function launchTelegramDesktop(tgUrl: string): void {
  const iframe = document.createElement('iframe')
  iframe.style.display = 'none'
  iframe.src = tgUrl
  document.body.appendChild(iframe)
  window.setTimeout(() => iframe.remove(), 3000)
}

/**
 * One-click connect flow used by the Dashboard banner and the Settings
 * menu item. Issues a deep-link token and immediately attempts to launch
 * Telegram Desktop. The modal that consumes `pendingLink` from Redux
 * shows the "waiting for confirmation" state and offers a web fallback.
 */
export function useTelegramConnect() {
  const dispatch = useAppDispatch()
  const [issuing, setIssuing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const connect = async (): Promise<boolean> => {
    setError(null)
    setIssuing(true)
    try {
      const link = await requestTelegramLinkToken()
      dispatch(setPendingLink(link))
      launchTelegramDesktop(buildTgDeepLink(link))
      return true
    } catch (e) {
      setError(e instanceof Error ? e.message : 'failed')
      return false
    } finally {
      setIssuing(false)
    }
  }

  return { connect, issuing, error }
}
