import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import TelegramIcon from '@mui/icons-material/Telegram'
import { useAppDispatch, useAppSelector } from '../hooks'
import { useT } from '../hooks/useT'
import { useTelegramConnect } from '../hooks/useTelegramConnect'
import { fetchTelegramStatus } from '../store/slices/telegramSlice'
import TelegramConnectModal from './TelegramConnectModal'
import { telegramBannerStyles as s } from './TelegramConnectBanner.styles'

export default function TelegramConnectBanner() {
  const t = useT()
  const dispatch = useAppDispatch()
  const linked = useAppSelector(st => st.telegram.linked)
  const { connect, issuing } = useTelegramConnect()
  const [modalOpen, setModalOpen] = useState(false)

  // Resolve status once on mount. The modal also refreshes on its own open;
  // the slice de-dupes via thunk semantics so the cost is negligible.
  useEffect(() => {
    if (linked === null) dispatch(fetchTelegramStatus())
  }, [linked, dispatch])

  // Hide the banner while we don't yet know the status (avoids a flash) and
  // once the user is linked.
  if (linked === null || linked === true) return null

  // One-click flow: open Telegram immediately AND surface the modal so the
  // user sees "waiting for confirmation" + countdown.
  const handleConnect = async () => {
    setModalOpen(true)
    await connect()
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
          disabled={issuing}
          startIcon={issuing ? <CircularProgress size={14} color="inherit" /> : null}
          onClick={handleConnect}
          sx={s.button}
        >
          {t('connectTelegram')}
        </Button>
      </Box>

      <TelegramConnectModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  )
}
