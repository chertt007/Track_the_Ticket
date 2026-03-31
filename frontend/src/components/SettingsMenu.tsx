import { useState } from 'react'
import IconButton from '@mui/material/IconButton'
import Menu from '@mui/material/Menu'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Divider from '@mui/material/Divider'
import Tooltip from '@mui/material/Tooltip'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import SettingsIcon from '@mui/icons-material/Settings'
import LanguageIcon from '@mui/icons-material/Language'
import { useT } from '../hooks/useT'
import { useAppDispatch, useAppSelector } from '../hooks'
import { setLanguage, type Language } from '../store/slices/settingsSlice'
import { settingsStyles as s } from './SettingsMenu.styles'

export default function SettingsMenu() {
  const t = useT()
  const dispatch = useAppDispatch()
  const language = useAppSelector(st => st.settings.language)
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)

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
      </Menu>
    </>
  )
}
