import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import CloseIcon from '@mui/icons-material/Close'
import { useT } from '../hooks/useT'
import { installStyles as s } from './InstallPromptBanner.styles'

// BeforeInstallPromptEvent is not in standard TS lib yet
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISSED_KEY = 'pwa_install_dismissed'

export default function InstallPromptBanner() {
  const t = useT()
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Do not show if the user already dismissed it this session
    if (sessionStorage.getItem(DISMISSED_KEY)) return

    const handler = (e: Event) => {
      e.preventDefault()
      setPromptEvent(e as BeforeInstallPromptEvent)
      setVisible(true)
    }

    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = async () => {
    if (!promptEvent) return
    await promptEvent.prompt()
    const { outcome } = await promptEvent.userChoice
    if (outcome === 'accepted') setVisible(false)
  }

  const handleDismiss = () => {
    sessionStorage.setItem(DISMISSED_KEY, '1')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <Box sx={s.banner}>
      {/* App icon */}
      <Box sx={s.iconBox} component="img" src="/icons/icon-192x192.png" alt="icon" />

      {/* Text */}
      <Box sx={s.textBox}>
        <Typography variant="body2" fontWeight={700} color="#fff" lineHeight={1.3}>
          {t('installTitle')}
        </Typography>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.75)' }}>
          {t('installHint')}
        </Typography>
      </Box>

      {/* Install button */}
      <Button onClick={handleInstall} sx={s.installButton} disableElevation>
        {t('installAction')}
      </Button>

      {/* Dismiss */}
      <IconButton onClick={handleDismiss} size="small" sx={s.closeButton}>
        <CloseIcon fontSize="small" />
      </IconButton>
    </Box>
  )
}
