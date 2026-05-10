import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import TelegramIcon from '@mui/icons-material/Telegram'
import { useAppDispatch, useAppSelector } from '../hooks'
import { useT } from '../hooks/useT'
import {
  isLinkExpired,
  useTelegramConnect,
} from '../hooks/useTelegramConnect'
import { fetchTelegramStatus } from '../store/slices/telegramSlice'
import TelegramConnectModal from './TelegramConnectModal'
import { telegramBannerStyles as s } from './TelegramConnectBanner.styles'

export default function TelegramConnectBanner() {
  const t = useT()
  const dispatch = useAppDispatch()
  const linked = useAppSelector(st => st.telegram.linked)
  const pendingLink = useAppSelector(st => st.telegram.pendingLink)
  const { prefetchToken, launchNow, connectFallback, issuing } = useTelegramConnect()
  const [modalOpen, setModalOpen] = useState(false)

  // Resolve status once on mount.
  useEffect(() => {
    if (linked === null) dispatch(fetchTelegramStatus())
  }, [linked, dispatch])

  // Pre-issue a token as soon as we know the user is not linked. This
  // keeps the click handler synchronous so the `tg://` launch retains
  // user-activation context (Chromium drops it across `await` boundaries).
  useEffect(() => {
    if (linked === false && (pendingLink === null || isLinkExpired(pendingLink))) {
      void prefetchToken()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [linked, pendingLink])

  // Hide while we don't know the status (avoids a flash) and once linked.
  if (linked === null || linked === true) return null

  const handleClick = () => {
    setModalOpen(true)
    if (pendingLink && !isLinkExpired(pendingLink)) {
      // Fresh token — fire tg:// synchronously inside the click handler.
      launchNow(pendingLink)
    } else {
      // No usable token (network slow, prefetch failed). Best-effort async.
      void connectFallback()
    }
  }

  return (
    <>
      <Box sx={s.root}>
        <Box sx={s.iconCircle}>
          <TelegramIcon />
        </Box>
        <Box sx={s.textColumn}>
          <Typography sx={s.title}>{t('telegramBannerTitle')}</Typography>
          <Typography sx={s.subtitle}>{t('telegramBannerSubtitle')}</Typography>
        </Box>
        <Button
          variant="contained"
          size="small"
          disabled={issuing && !pendingLink}
          startIcon={issuing && !pendingLink ? <CircularProgress size={14} color="inherit" /> : null}
          onClick={handleClick}
          sx={s.button}
        >
          {t('connectTelegram')}
        </Button>
      </Box>

      <TelegramConnectModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  )
}
