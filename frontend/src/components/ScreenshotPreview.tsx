import { useState } from 'react'
import Box from '@mui/material/Box'
import Dialog from '@mui/material/Dialog'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import ZoomInIcon from '@mui/icons-material/ZoomIn'
import CloseIcon from '@mui/icons-material/Close'
import { useT } from '../hooks/useT'
import { screenshotStyles as s } from './ScreenshotPreview.styles'

interface Props {
  src: string
}

export default function ScreenshotPreview({ src }: Props) {
  const t = useT()
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Thumbnail */}
      <Box onClick={() => setOpen(true)} sx={s.wrapper}>
        <Box component="img" src={src} alt={t('screenshotAlt')} sx={s.image} />

        <Box className="overlay" sx={s.overlay}>
          <ZoomInIcon sx={{ color: '#fff', fontSize: 28 }} />
          <Typography variant="caption" color="white" fontWeight={600}>
            {t('clickToEnlarge')}
          </Typography>
        </Box>

      </Box>

      {/* Lightbox */}
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="md"
        PaperProps={{ sx: s.dialogPaper }}
      >
        <Box sx={s.dialogInner}>
          <Tooltip title={t('close')}>
            <IconButton onClick={() => setOpen(false)} sx={s.closeButton}>
              <CloseIcon />
            </IconButton>
          </Tooltip>
          <Box component="img" src={src} alt={t('screenshotAlt')} sx={s.fullImage} />
        </Box>
      </Dialog>
    </>
  )
}
