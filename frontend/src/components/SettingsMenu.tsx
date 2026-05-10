import { useState } from 'react'
import IconButton from '@mui/material/IconButton'
import Menu from '@mui/material/Menu'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import Tooltip from '@mui/material/Tooltip'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import SettingsIcon from '@mui/icons-material/Settings'
import LanguageIcon from '@mui/icons-material/Language'
import TelegramIcon from '@mui/icons-material/Telegram'
import { useT } from '../hooks/useT'
import { useAppDispatch, useAppSelector } from '../hooks'
import { useTelegramConnect } from '../hooks/useTelegramConnect'
import { setLanguage, type Language } from '../store/slices/settingsSlice'
import TelegramConnectModal from './TelegramConnectModal'
import { settingsStyles as s } from './SettingsMenu.styles'

export default function SettingsMenu() {
  const t = useT()
  const dispatch = useAppDispatch()
  const language = useAppSelector(st => st.settings.language)
  const linked = useAppSelector(st => st.telegram.linked)
  const { connect, issuing } = useTelegramConnect()
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)
  const [tgOpen, setTgOpen] = useState(false)

  // Not linked → one-click connect (open Telegram + modal with countdown).
  // Linked   → just open the modal so the user can see status / unlink.
  const handleTelegramClick = async () => {
    setAnchor(null)
    setTgOpen(true)
    if (!linked) await connect()
  }

  return (
    <>
      <Tooltip title={t('settings')}>
        <IconButton color="inherit" onClick={e => setAnchor(e.currentTarget)} sx={s.iconButton}>
          <SettingsIcon />
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchor}
        open={Boolean(anchor)}
        onClose={() => setAnchor(null)}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{ sx: s.menuPaper }}
      >
        <Box sx={s.headerBox}>
          <Typography variant="subtitle2" fontWeight={700} color="primary.dark">
            {t('settings')}
          </Typography>
        </Box>

        <Divider sx={s.divider} />

        <Box sx={s.sectionBox}>
          <Box sx={s.langLabelRow}>
            <LanguageIcon sx={s.langIcon} />
            <Typography variant="body2" color="text.secondary">{t('language')}</Typography>
          </Box>
          <ToggleButtonGroup
            value={language}
            exclusive
            size="small"
            onChange={(_, val) => { if (val) dispatch(setLanguage(val as Language)) }}
            fullWidth
          >
            <ToggleButton value="ru" sx={s.toggleButton}>🇷🇺 {t('russian')}</ToggleButton>
            <ToggleButton value="en" sx={s.toggleButton}>🇬🇧 {t('english')}</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Divider sx={s.divider} />

        <Box sx={s.sectionBox}>
          <Box sx={s.telegramRow}>
            <TelegramIcon sx={s.telegramIcon} />
            <Typography variant="body2" color="text.secondary">{t('telegram')}</Typography>
          </Box>
          <Button
            variant="outlined"
            size="small"
            fullWidth
            disabled={issuing}
            sx={s.telegramButton}
            onClick={handleTelegramClick}
          >
            {linked ? t('telegramConnected') : t('connectTelegram')}
          </Button>
        </Box>
      </Menu>

      <TelegramConnectModal open={tgOpen} onClose={() => setTgOpen(false)} />
    </>
  )
}
