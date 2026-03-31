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
import LinkIcon from '@mui/icons-material/Link'
import { useT } from '../hooks/useT'
import { useAppDispatch } from '../hooks'
import { addSubscription } from '../store/slices/subscriptionsSlice'
import { modalStyles as s } from './AddSubscriptionModal.styles'

const AVIASALES_DOMAINS = ['aviasales.ru', 'aviasales.com']

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddSubscriptionModal({ open, onClose }: Props) {
  const t = useT()
  const dispatch = useAppDispatch()
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const validate = (): string => {
    const trimmed = url.trim()
    if (!trimmed) return t('urlRequired')
    if (!trimmed.startsWith('http')) return t('urlInvalid')
    const isAviasales = AVIASALES_DOMAINS.some(domain => trimmed.includes(domain))
    if (!isAviasales) return t('urlNotAviasales')
    return ''
  }

  const handleSubmit = () => {
    const err = validate()
    if (err) { setError(err); return }

    setSubmitting(true)
    // Simulate async submission (will be replaced by real API call in FE-07)
    setTimeout(() => {
      dispatch(addSubscription({ url: url.trim() }))
      setUrl('')
      setError('')
      setSubmitting(false)
      onClose()
    }, 800)
  }

  const handleClose = () => {
    if (submitting) return
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
            {t('addSubscriptionTitle')}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={s.dialogContent}>
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
          disabled={submitting}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          InputProps={{ sx: s.inputProps }}
        />
      </DialogContent>

      <DialogActions sx={s.dialogActions}>
        <Button variant="outlined" onClick={handleClose} disabled={submitting}>
          {t('cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={submitting}
          startIcon={submitting ? <CircularProgress size={16} color="inherit" /> : undefined}
        >
          {submitting ? t('checking') : t('add')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
