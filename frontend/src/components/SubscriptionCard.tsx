import { useState } from 'react'
import Card from '@mui/material/Card'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import SyncIcon from '@mui/icons-material/Sync'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import FlightLandIcon from '@mui/icons-material/FlightLand'
import LuggageIcon from '@mui/icons-material/Luggage'
import CloseIcon from '@mui/icons-material/Close'
import ButtonBase from '@mui/material/ButtonBase'
import { useNavigate } from 'react-router-dom'
import { useT } from '../hooks/useT'
import { useLocale } from '../hooks/useLocale'
import { useAppDispatch, useAppSelector } from '../hooks'
import { setCheckingId, checkSubscriptionApi, deleteSubscriptionApi } from '../store/slices/subscriptionsSlice'
import { cardStyles as s } from './SubscriptionCard.styles'
import type { Subscription } from '../types'

interface Props {
  subscription: Subscription
}

export default function SubscriptionCard({ subscription: sub }: Props) {
  const t = useT()
  const locale = useLocale()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const checkingId = useAppSelector(st => st.subscriptions.checkingId)
  const isChecking = checkingId === sub.id

  const [confirmOpen, setConfirmOpen] = useState(false)
  const [lightboxOpen, setLightboxOpen] = useState(false)

  const handleCheck = (e: React.MouseEvent) => {
    e.stopPropagation()
    dispatch(setCheckingId(sub.id))
    dispatch(checkSubscriptionApi(sub.id))
  }

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setConfirmOpen(true)
  }

  const handleConfirmDelete = () => {
    setConfirmOpen(false)
    dispatch(deleteSubscriptionApi(sub.id))
  }

  const handleCancelDelete = () => setConfirmOpen(false)

  const handleThumbnailClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setLightboxOpen(true)
  }

  const handleLightboxClose = () => setLightboxOpen(false)

  const formattedPrice = sub.lastPrice !== null && sub.currency
    ? `${sub.lastPrice.toLocaleString(locale)} ${sub.currency}`
    : null

  const formattedDate = sub.departureDate !== '—'
    ? new Date(sub.departureDate).toLocaleDateString(locale, {
        day: 'numeric', month: 'short', year: 'numeric',
      })
    : '—'

  return (
    <Card elevation={0} sx={s.card(sub.isActive)} onClick={() => navigate(`/subscription/${sub.id}`)}>
      {/* ── Flight info ──────────────────────────────────────────────────── */}
      <Box sx={s.infoBox}>
        <Box sx={s.routeRow}>
          <Typography variant="h6" fontWeight={700} color="primary.dark" noWrap>
            {sub.originIata}
          </Typography>
          <FlightTakeoffIcon sx={s.takeoffIcon} />
          <Typography variant="h6" fontWeight={700} color="text.secondary">→</Typography>
          <FlightLandIcon sx={s.landIcon} />
          <Typography variant="h6" fontWeight={700} color="primary.dark" noWrap>
            {sub.destinationIata}
          </Typography>
          <Chip
            label={sub.isActive ? t('active') : t('inactive')}
            size="small"
            color={sub.isActive ? 'primary' : 'default'}
            sx={s.chip}
          />
        </Box>

        <Box sx={s.detailsRow}>
          <Box>
            <Typography variant="caption" color="text.secondary">{t('airline')}</Typography>
            <Typography variant="body2" fontWeight={600}>{sub.airline}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">{t('departure')}</Typography>
            <Typography variant="body2" fontWeight={600}>{formattedDate} · {sub.departureTime}</Typography>
          </Box>
          <Box sx={s.baggageBox}>
            <LuggageIcon sx={s.luggageIcon} />
            <Typography variant="body2" color="text.secondary">{sub.baggageInfo}</Typography>
          </Box>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={s.metaText}>
          #{sub.id} · {t('lastChecked')}: {sub.lastCheckedAt
            ? new Date(sub.lastCheckedAt).toLocaleString(locale, {
                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
              })
            : t('never')}
        </Typography>
      </Box>

      {/* ── Last check (price + screenshot thumbnail) ──────────────────── */}
      <Box sx={s.lastCheckBox}>
        <Box sx={s.priceBox}>
          {formattedPrice ? (
            <Typography sx={s.priceText}>{formattedPrice}</Typography>
          ) : (
            <Typography sx={s.pricePlaceholder}>—</Typography>
          )}
        </Box>
        {sub.lastScreenshotUrl && (
          <ButtonBase onClick={handleThumbnailClick} sx={s.thumbnailButton}>
            <Box
              component="img"
              src={sub.lastScreenshotUrl}
              alt={t('lastChecked')}
              sx={s.thumbnailImg}
            />
          </ButtonBase>
        )}
      </Box>

      {/* ── Actions ──────────────────────────────────────────────────────── */}
      <Box sx={s.actionBox}>
        <Tooltip title={isChecking ? t('checking') : t('checkNow')}>
          <span>
            <IconButton onClick={handleCheck} disabled={isChecking} size="large" sx={s.checkButton}>
              {isChecking
                ? <CircularProgress size={22} sx={s.spinner} />
                : <SyncIcon />}
            </IconButton>
          </span>
        </Tooltip>
        <Tooltip title={t('deleteSubscription')}>
          <IconButton onClick={handleDeleteClick} size="small" sx={s.deleteButton}>
            <DeleteOutlineIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* ── Lightbox (full-screen screenshot) ──────────────────────────── */}
      {sub.lastScreenshotUrl && (
        <Dialog
          open={lightboxOpen}
          onClose={handleLightboxClose}
          onClick={e => e.stopPropagation()}
          PaperProps={{ sx: s.lightboxPaper }}
          BackdropProps={{ sx: s.lightboxBackdrop }}
          maxWidth={false}
        >
          <DialogContent sx={s.lightboxContent}>
            <Box
              component="img"
              src={sub.lastScreenshotUrl}
              alt={t('lastChecked')}
              onClick={handleLightboxClose}
              sx={s.lightboxImg}
            />
            <IconButton onClick={handleLightboxClose} sx={s.lightboxCloseButton}>
              <CloseIcon />
            </IconButton>
          </DialogContent>
        </Dialog>
      )}

      {/* ── Delete confirm dialog ──────────────────────────────────────── */}
      <Dialog
        open={confirmOpen}
        onClose={handleCancelDelete}
        onClick={e => e.stopPropagation()}
        PaperProps={{ sx: s.dialogPaper }}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={s.dialogTitleRow}>
          <Box sx={s.dialogIconCircle}>
            <DeleteOutlineIcon fontSize="small" />
          </Box>
          {t('deleteSubscription')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>{t('deleteConfirm')}</DialogContentText>
        </DialogContent>
        <DialogActions sx={s.dialogActions}>
          <Button onClick={handleCancelDelete} sx={s.dialogCancelButton}>
            {t('cancel')}
          </Button>
          <Button onClick={handleConfirmDelete} variant="contained" sx={s.dialogDeleteButton}>
            {t('delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  )
}
