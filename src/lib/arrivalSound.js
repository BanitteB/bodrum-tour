// Short, pleasant arrival chime, synthesised with the Web Audio API (no asset
// to load or cache). Only plays while the page is open.
//
// iOS Safari only lets audio play after a user gesture has "unlocked" an
// AudioContext. Call unlockArrivalSound() from a tap handler (e.g. "Begin the
// Journey"). As a fallback — the app resumes straight into the hub after a
// reload, skipping the welcome screen — the very first tap anywhere on the page
// also unlocks it.

let ctx = null

function getCtx() {
  if (ctx) return ctx
  const AC = typeof window !== 'undefined' && (window.AudioContext || window.webkitAudioContext)
  if (!AC) return null
  try { ctx = new AC() } catch { ctx = null }
  return ctx
}

export function unlockArrivalSound() {
  const c = getCtx()
  if (!c) return
  try {
    if (c.state === 'suspended') c.resume()
    // Play one silent sample inside the gesture — required on older iOS.
    const buf = c.createBuffer(1, 1, 22050)
    const src = c.createBufferSource()
    src.buffer = buf
    src.connect(c.destination)
    src.start(0)
  } catch { /* ignore */ }
}

// Global fallback: unlock on the first interaction anywhere.
if (typeof window !== 'undefined') {
  const once = () => {
    unlockArrivalSound()
    window.removeEventListener('pointerdown', once, true)
    window.removeEventListener('touchend', once, true)
    window.removeEventListener('click', once, true)
  }
  window.addEventListener('pointerdown', once, true)
  window.addEventListener('touchend', once, true)
  window.addEventListener('click', once, true)
}

// Two soft bell-like notes (E5 → A5), ~0.9 s total.
export function playArrivalSound() {
  const c = getCtx()
  if (!c) return
  try {
    if (c.state === 'suspended') c.resume()
    const now = c.currentTime + 0.02
    const notes = [
      { freq: 659.25, start: 0 },
      { freq: 880.0,  start: 0.18 },
    ]
    const master = c.createGain()
    master.gain.value = 0.35
    master.connect(c.destination)

    for (const { freq, start } of notes) {
      const t0 = now + start
      // Fundamental + a quiet octave overtone for a bell-ish timbre
      for (const [mult, level] of [[1, 1], [2, 0.25]]) {
        const osc = c.createOscillator()
        const g = c.createGain()
        osc.type = 'sine'
        osc.frequency.value = freq * mult
        g.gain.setValueAtTime(0.0001, t0)
        g.gain.exponentialRampToValueAtTime(level, t0 + 0.015)
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.7)
        osc.connect(g)
        g.connect(master)
        osc.start(t0)
        osc.stop(t0 + 0.75)
      }
    }
  } catch { /* ignore — sound is a nice-to-have */ }
}
