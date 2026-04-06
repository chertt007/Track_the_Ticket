import { useState, useEffect, useRef } from 'react'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import IconButton from '@mui/material/IconButton'
import Typography from '@mui/material/Typography'
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew'
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos'
import CloseIcon from '@mui/icons-material/Close'
import ZoomInIcon from '@mui/icons-material/ZoomIn'
import { useT } from '../hooks/useT'
import { useLocale } from '../hooks/useLocale'
import type { ScreenshotItem } from '../types'
import { sliderStyles as s } from './ScreenshotSlider.styles'

interface Props {
  screenshots: ScreenshotItem[]
  loading: boolean
}

export default function ScreenshotSlider({ screenshots, loading }: Props) {
  const t = useT()
  const locale = useLocale()

  // Reverse so oldest is at index 0 and newest is at the end.
  // Default active = last item (newest). Left arrow = older, right arrow = newer.
  const items = [...screenshots].reverse()

  const lastIdx = Math.max(0, items.length - 1)
  const [activeIdx, setActiveIdx] = useState(lastIdx)
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const activeThumbRef = useRef<HTMLDivElement | null>(null)

  // When the screenshot list changes, reset to the newest item
  useEffect(() => {
    setActiveIdx(Math.max(0, items.length - 1))
  }, [screenshots.length]) // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll the active thumbnail into the visible area of the strip
  useEffect(() => {
    activeThumbRef.current?.scrollIntoView({
      behavior: 'smooth',
      inline: 'center',
      block: 'nearest',
    })
  }, [activeIdx])

  if (loading) {
    return (
      <Box sx={s.center}>
        <CircularProgress size={28} color="primary" />
      </Box>
    )
  }

  if (items.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t('noScreenshots')}
      </Typography>
    )
  }

  const active = items[activeIdx]
  const canPrev = activeIdx > 0                   // can go to older
  const canNext = activeIdx < items.length - 1    // can go to newer

  return (
    <>
      {/* Main large image */}
      <Box sx={s.mainWrapper} onClick={() => setLightboxOpen(true)}>
        <Box
          component="img"
          src={active.url}
          alt={t('screenshotAlt')}
          sx={s.mainImage}
        />
        <Box className="overlay" sx={s.overlay}>
          <ZoomInIcon sx={{ color: '#fff', fontSize: 32 }} />
          <Typography variant="caption" color="white" fontWeight={600}>
            {t('clickToEnlarge')}
          </Typography>
        </Box>
      </Box>

      {/* Date + price row */}
      <Box sx={s.metaRow}>
        <Typography variant="caption" color="text.secondary">
          {new Date(active.checkedAt).toLocaleString(locale, {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </Typography>
        {active.status === 'ok' && (
          <Typography variant="caption" fontWeight={700} color="primary.dark">
            {active.price.toLocaleString('ru-RU')} {active.currency}
          </Typography>
        )}
      </Box>

      {/* Thumbnail strip with prev/next arrows */}
      <Box sx={s.navRow}>
        {/* Left = go to older screenshot */}
        <IconButton
          onClick={() => setActiveIdx(i => i - 1)}
          disabled={!canPrev}
          sx={s.arrowBtn}
          size="small"
        >
          <ArrowBackIosNewIcon fontSize="small" />
        </IconButton>

        <Box sx={s.thumbnailStrip}>
          {items.map((sc, idx) => (
            <Box
              key={sc.checkedAt}
              ref={idx === activeIdx ? activeThumbRef : null}
              onClick={() => setActiveIdx(idx)}
              sx={s.thumbnail(idx === activeIdx)}
            >
              <Box
                component="img"
                src={sc.url}
                alt=""
                sx={s.thumbImage}
              />
            </Box>
          ))}
        </Box>

        {/* Right = go to newer screenshot */}
        <IconButton
          onClick={() => setActiveIdx(i => i + 1)}
          disabled={!canNext}
          sx={s.arrowBtn}
          size="small"
        >
          <ArrowForwardIosIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Lightbox */}
      <Dialog
        open={lightboxOpen}
        onClose={() => setLightboxOpen(false)}
        maxWidth="md"
        PaperProps={{ sx: s.dialogPaper }}
      >
        <Box sx={s.dialogInner}>
          <IconButton onClick={() => setLightboxOpen(false)} sx={s.closeBtn}>
            <CloseIcon />
          </IconButton>
          <Box
            component="img"
            src={active.url}
            alt={t('screenshotAlt')}
            sx={s.fullImage}
          />
        </Box>
      </Dialog>
    </>
  )
}
