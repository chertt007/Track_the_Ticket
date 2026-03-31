import { useEffect, useRef } from 'react'

// Generates a soft MacBook-like keyboard click using the Web Audio API.
// No external files needed — the sound is synthesised on the fly.
function playMacClick(ctx: AudioContext) {
  const now = ctx.currentTime
  const duration = 0.055

  // Short noise burst — mimics the physical key impact
  const bufferSize = Math.ceil(ctx.sampleRate * duration)
  const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
  const data = buffer.getChannelData(0)
  for (let i = 0; i < bufferSize; i++) {
    // Exponential decay envelope on white noise
    const t = i / bufferSize
    data[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, 6)
  }

  const noise = ctx.createBufferSource()
  noise.buffer = buffer

  // Band-pass filter: warm mid-range, not too clicky or harsh
  const filter = ctx.createBiquadFilter()
  filter.type = 'bandpass'
  filter.frequency.value = 3200
  filter.Q.value = 0.6

  // Master gain — keep it subtle
  const gain = ctx.createGain()
  gain.gain.setValueAtTime(0.14, now)
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration)

  noise.connect(filter)
  filter.connect(gain)
  gain.connect(ctx.destination)
  noise.start(now)
  noise.stop(now + duration)
}

// Attaches a document-level click listener that plays the sound
// only when the click target is an interactive element.
export function useClickSound() {
  const ctxRef = useRef<AudioContext | null>(null)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      // Only play for buttons, links, and explicitly interactive elements
      const isInteractive = target.closest(
        'button, a, [role="button"], [role="tab"], [role="option"], label, input, select, textarea'
      )
      if (!isInteractive) return

      // AudioContext must be created (or resumed) inside a user gesture
      if (!ctxRef.current) {
        ctxRef.current = new AudioContext()
      } else if (ctxRef.current.state === 'suspended') {
        ctxRef.current.resume()
      }

      playMacClick(ctxRef.current)
    }

    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])
}
