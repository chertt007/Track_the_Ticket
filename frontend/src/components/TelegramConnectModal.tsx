import { useEffect, useRef, useState } from 'react'
import Dialog from '@mui/material/Dialog'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import TelegramIcon from '@mui/icons-material/Telegram'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import { useAppDispatch, useAppSelector } from '../hooks'
import { useT } from '../hooks/useT'
import {
  buildTgDeepLink,
  isLinkExpired,
  useTelegramConnect,
} from '../hooks/useTelegramConnect'
import {
  fetchTelegramStatus,
  setPendingLink,
  unlinkTelegramThunk,
} from '../store/slices/telegramSlice'
import { telegramModalStyles as s } from './TelegramConnectModal.styles'

interface Props {
  open: boolean
  onClose: () => void
}

export default function TelegramConnectModal({ open, onClose }: Props) {
  const t = useT()
  const dispatch = useAppDispatch()
  const linked = useAppSelector(st => st.telegram.linked)
  const chatIdMasked = useAppSelector(st => st.telegram.chatIdMasked)
  const pendingLink = useAppSelector(st => st.telegram.pendingLink)
  const initialLoading = useAppSelector(st => st.telegram.loading)
  const { connectFallback, issuing, error } = useTelegramConnect()

  const [unlinking, setUnlinking] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)

  const pollRef = useRef<number | null>(null)
  const tickRef = useRef<number | null>(null)

  // Refresh status every time the modal opens — Redux state may be stale.
  useEffect(() => {
    if (open) dispatch(fetchTelegramStatus())
  }, [open, dispatch])

  // Poll status every 3s while we have an unfulfilled token. Stops when
  // the user gets linked, the modal closes, or no pending token exists.
  useEffect(() => {
    if (!open || !pendingLink || linked === true) {
      if (pollRef.current) { window.clearInterval(pollRef.current); pollRef.current = null }
      return
    }
    pollRef.current = window.setInterval(() => {
      dispatch(fetchTelegramStatus())
    }, 3000)
    return () => {
      if (pollRef.current) { window.clearInterval(pollRef.current); pollRef.current = null }
    }
  }, [open, pendingLink, linked, dispatch])

  // Countdown for the visible expiry hint.
  useEffect(() => {
    if (!pendingLink) {
      if (tickRef.current) { window.clearInterval(tickRef.current); tickRef.current = null }
      setSecondsLeft(0)
      return
    }
    const expiresMs = new Date(pendingLink.expires_at).getTime()
    const update = () => {
      const remaining = Math.max(0, Math.round((expiresMs - Date.now()) / 1000))
      setSecondsLeft(remaining)
      if (remaining === 0 && tickRef.current) {
        window.clearInterval(tickRef.current); tickRef.current = null
      }
    }
    update()
    tickRef.current = window.setInterval(update, 1000)
    return () => {
      if (tickRef.current) { window.clearInterval(tickRef.current); tickRef.current = null }
    }
  }, [pendingLink])

  // Drop the stale link when the user successfully links — the chat id is
  // now in users.telegram_chat_id and the pending row was used.
  useEffect(() => {
    if (linked === true && pendingLink) dispatch(setPendingLink(null))
  }, [linked, pendingLink, dispatch])

  // Web fallback: open https://t.me/... in a new tab. Used when Telegram
  // Desktop is not installed or the protocol handler isn't registered.
  const handleOpenWeb = () => {
    if (!pendingLink) return
    window.open(pendingLink.deep_link, '_blank', 'noopener,noreferrer')
  }

  const handleRefresh = () => { void connectFallback() }

  const tgUrl = pendingLink ? buildTgDeepLink(pendingLink) : ''

  const handleUnlink = async () => {
    setUnlinking(true)
    try {
      await dispatch(unlinkTelegramThunk()).unwrap()
    } finally {
      setUnlinking(false)
    }
  }

  // Computed from the absolute expiry timestamp — `secondsLeft` cannot be
  // used here because it starts at 0 before the countdown effect runs,
  // which would cause a brief "expired" flash right after a fresh issue.
  const expired = isLinkExpired(pendingLink)

  return (
    <Dialog open={open} onClose={onClose} PaperProps={{ sx: s.paper }}>
      <Box sx={s.iconCircle}>
        <TelegramIcon sx={s.icon} />
      </Box>

      {error && <Alert severity="error" sx={s.errorAlert}>{t('telegramErrorIssue')}</Alert>}

      {/* Initial /telegram/status fetch */}
      {linked === null && initialLoading && (
        <Box sx={s.loadingBox}><CircularProgress /></Box>
      )}

      {/* Linked state */}
      {linked === true && (
        <>
          <Typography variant="h6" fontWeight={700} sx={s.title}>
            {t('telegramConnected')}
          </Typography>
          <Box sx={s.successRow}>
            <CheckCircleIcon fontSize="small" />
            <Typography component="span" sx={s.chatIdMono}>
              {chatIdMasked ?? ''}
            </Typography>
          </Box>
          <Button
            variant="outlined"
            color="error"
            fullWidth
            disabled={unlinking}
            onClick={handleUnlink}
            sx={s.unlinkButton}
          >
            {unlinking ? t('telegramUnlinking') : t('telegramUnlink')}
          </Button>
        </>
      )}

      {/* Not linked, no token yet — entered modal directly via Settings.
          Offer a single button that issues + opens Telegram. */}
      {linked === false && !pendingLink && (
        <>
          <Typography variant="h6" fontWeight={700} sx={s.title}>
            {t('telegramBannerTitle')}
          </Typography>
          <Typography variant="body2" sx={s.subtitle}>
            {t('telegramBannerSubtitle')}
          </Typography>
          <Button
            variant="contained"
            fullWidth
            disabled={issuing}
            startIcon={issuing ? <CircularProgress size={16} color="inherit" /> : <OpenInNewIcon />}
            onClick={handleRefresh}
            sx={s.primaryButton}
          >
            {t('telegramOpenApp')}
          </Button>
        </>
      )}

      {/* Pending — token issued, desktop app launched (or attempted), polling for claim */}
      {linked === false && pendingLink && !expired && (
        <>
          <Typography variant="h6" fontWeight={700} sx={s.title}>
            {t('telegramBannerTitle')}
          </Typography>
          <Box sx={s.waiting}>
            <CircularProgress size={14} />
            <span>{t('telegramWaitingClaim')}</span>
          </Box>
          <Typography sx={s.expiryText}>
            {t('telegramExpiresIn').replace('{n}', String(secondsLeft))}
          </Typography>
          <Button
            variant="contained"
            fullWidth
            component="a"
            href={tgUrl}
            startIcon={<OpenInNewIcon />}
            sx={{ ...s.primaryButton, mt: 2 }}
          >
            {t('telegramOpenApp')}
          </Button>
          <Button
            variant="text"
            fullWidth
            size="small"
            onClick={handleOpenWeb}
            sx={{ mt: 1 }}
          >
            {t('telegramOpenWeb')}
          </Button>
        </>
      )}

      {/* Token expired without claim — issue a fresh one + reopen Telegram */}
      {linked === false && pendingLink && expired && (
        <>
          <Typography variant="h6" fontWeight={700} sx={s.title}>
            {t('telegramLinkExpired')}
          </Typography>
          <Button
            variant="contained"
            fullWidth
            disabled={issuing}
            startIcon={issuing ? <CircularProgress size={16} color="inherit" /> : <OpenInNewIcon />}
            onClick={handleRefresh}
            sx={s.primaryButton}
          >
            {t('telegramRefresh')}
          </Button>
        </>
      )}
    </Dialog>
  )
}
