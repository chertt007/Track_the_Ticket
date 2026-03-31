import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import LinkIcon from '@mui/icons-material/Link'
import { useT } from '../hooks/useT'
import { useAppDispatch } from '../hooks'
import { addSubscription } from '../store/slices/subscriptionsSlice'
import { modalStyles as s } from './AddSubscriptionModal.styles'

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddSubscriptionModal({ open, onClose }: Props) {
  const t = useT()
  const dispatch = useAppDispatch()
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const validate = () => {
    if (!url.trim()) return t('urlRequired')
    if (!url.startsWith('http')) return t('urlInvalid')
    return ''
  }

  const handleSubmit = () => {
    const err = validate()
    if (err) { setError(err); return }
    dispatch(addSubscription({ url }))
    setUrl('')
    setError('')
    onClose()
  }

  const handleClose = () => {
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
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          InputProps={{ sx: s.inputProps }}
        />
      </DialogContent>

      <DialogActions sx={s.dialogActions}>
        <Button variant="outlined" onClick={handleClose}>{t('cancel')}</Button>
        <Button variant="contained" onClick={handleSubmit}>{t('add')}</Button>
      </DialogActions>
    </Dialog>
  )
}
