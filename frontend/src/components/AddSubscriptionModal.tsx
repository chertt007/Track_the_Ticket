import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import Fade from '@mui/material/Fade'
import LinkIcon from '@mui/icons-material/Link'
import { useT } from '../hooks/useT'
import { modalStyles as s } from './AddSubscriptionModal.styles'

const AVIASALES_DOMAINS = ['aviasales.ru', 'aviasales.com', 'avs.io']

type Step = 'input' | 'parsing'

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddSubscriptionModal({ open, onClose }: Props) {
  const t = useT()

  const [step, setStep] = useState<Step>('input')
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const validate = (): string => {
    const trimmed = url.trim()
    if (!trimmed) return t('urlRequired')
    if (!trimmed.startsWith('http')) return t('urlInvalid')
    const isAviasales = AVIASALES_DOMAINS.some(d => trimmed.includes(d))
    if (!isAviasales) return t('urlNotAviasales')
    return ''
  }

  const handleCheck = () => {
    const err = validate()
    if (err) { setError(err); return }
    setStep('parsing')
    // TODO: trigger backend Playwright parsing here
  }

  const handleClose = () => {
    if (step === 'parsing') return
    setStep('input')
    setUrl('')
    setError('')
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth PaperProps={{ sx: s.paper }}>
      <DialogTitle sx={s.dialogTitle}>
        <Box sx={s.titleRow}>
          <Box sx={s.iconCircle}>
            <LinkIcon sx={{ color: '#fff', fontSize: 18 }} />
          </Box>
          <Typography variant="h6" fontWeight={700} color="primary.dark">
            {step === 'input' ? t('addSubscriptionTitle') : t('previewLoading')}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={s.dialogContent}>

        {/* ── Step: URL input ─────────────────────────────────────────── */}
        {step === 'input' && (
          <Fade in>
            <Box>
              <Typography variant="body2" color="text.secondary" sx={s.hintText}>
                {t('urlHint')}
              </Typography>
              <TextField
                fullWidth
                autoFocus
                label={t('urlLabel')}
                placeholder={t('urlPlaceholder')}
                value={url}
                onChange={e => { setUrl(e.target.value); setError('') }}
                error={!!error}
                helperText={error}
                onKeyDown={e => e.key === 'Enter' && handleCheck()}
                InputProps={{ sx: s.inputProps }}
              />
            </Box>
          </Fade>
        )}

        {/* ── Step: parsing (Playwright running on backend) ───────────── */}
        {step === 'parsing' && (
          <Fade in>
            <Box sx={s.parsingBox}>
              <CircularProgress size={44} thickness={3} color="primary" />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                {t('previewLoading')}
              </Typography>
            </Box>
          </Fade>
        )}

      </DialogContent>

      <DialogActions sx={s.dialogActions}>
        {step === 'input' && (
          <>
            <Button variant="outlined" onClick={handleClose}>
              {t('cancel')}
            </Button>
            <Button variant="contained" onClick={handleCheck}>
              {t('previewCheck')}
            </Button>
          </>
        )}

        {step === 'parsing' && (
          <Button variant="outlined" disabled>
            {t('previewLoading')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}
