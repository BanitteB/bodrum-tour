import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { X, Play, Pause, RotateCcw, ChevronRight, CheckCircle2, Star, Bell, MapPin } from 'lucide-react'
import { playArrivalSound } from '../../lib/arrivalSound'

// "How to play" — a short, auto-playing animated walkthrough (like a mini
// video / story). Built from CSS animations so it works offline, in all four
// languages, and needs no video file. Keyframes live in index.css (htp-*).

const SCENE_MS = 4500

/* ── Scene illustrations ───────────────────────────────────────────── */

function PhoneFrame({ children }) {
  return (
    <div className="relative mx-auto rounded-[28px] overflow-hidden"
      style={{ width: 190, height: 250, background: '#06142a', border: '3px solid rgba(255,255,255,0.15)', boxShadow: '0 12px 40px rgba(0,0,0,0.5)' }}>
      {children}
    </div>
  )
}

function SceneTour() {
  return (
    <PhoneFrame>
      <div className="p-3 flex flex-col gap-2 pt-5">
        {['🏛️', '⚓', '🌅'].map((e, i) => (
          <div key={e} className={`rounded-xl p-2.5 flex items-center gap-2 ${i === 1 ? 'htp-pick' : ''}`}
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg" style={{ background: 'rgba(34,211,238,0.15)' }}>{e}</div>
            <div className="flex-1">
              <div className="h-2 rounded bg-white/40 w-20 mb-1.5" />
              <div className="h-1.5 rounded bg-white/15 w-14" />
            </div>
          </div>
        ))}
      </div>
      <div className="htp-finger absolute text-2xl" style={{ left: 120, top: 150 }}>👆</div>
    </PhoneFrame>
  )
}

function SceneWalk() {
  return (
    <PhoneFrame>
      <svg viewBox="0 0 190 250" className="absolute inset-0 w-full h-full">
        <rect width="190" height="250" fill="#0b2340" />
        {[40, 95, 150, 205].map(y => <line key={y} x1="0" y1={y} x2="190" y2={y + 20} stroke="rgba(255,255,255,0.06)" strokeWidth="10" />)}
        <path id="htp-route" d="M30 215 C 60 170, 40 130, 95 115 S 140 70, 145 55" fill="none" stroke="#22d3ee" strokeWidth="3" strokeDasharray="6 6" opacity="0.7" />
        <circle cx="145" cy="55" r="22" fill="rgba(34,211,238,0.12)" stroke="#22d3ee" strokeWidth="1.5" />
      </svg>
      <div className="absolute" style={{ left: 133, top: 30 }}><MapPin className="w-6 h-6 text-cyan-300" fill="#0e7490" /></div>
      <div className="htp-walker absolute w-4 h-4 rounded-full"
        style={{ background: '#3b82f6', border: '3px solid white', boxShadow: '0 0 0 6px rgba(59,130,246,0.25)', offsetPath: "path('M30 215 C 60 170, 40 130, 95 115 S 140 70, 145 55')" }} />
    </PhoneFrame>
  )
}

function SceneArrive({ t }) {
  return (
    <PhoneFrame>
      <svg viewBox="0 0 190 250" className="absolute inset-0 w-full h-full">
        <rect width="190" height="250" fill="#0b2340" />
        <circle className="htp-ring" cx="95" cy="95" r="40" fill="rgba(34,197,94,0.15)" stroke="#22c55e" strokeWidth="2" />
      </svg>
      <div className="absolute" style={{ left: 83, top: 70 }}><MapPin className="w-6 h-6 text-green-300" fill="#15803d" /></div>
      <div className="absolute w-4 h-4 rounded-full" style={{ left: 88, top: 100, background: '#3b82f6', border: '3px solid white' }} />
      <div className="htp-bell absolute rounded-full w-10 h-10 flex items-center justify-center" style={{ right: 12, top: 14, background: 'rgba(251,191,36,0.2)' }}>
        <Bell className="w-5 h-5 text-amber-300" />
      </div>
      <div className="htp-cta absolute left-3 right-3 rounded-xl py-3 text-center text-white font-bold text-sm"
        style={{ bottom: 14, background: 'linear-gradient(135deg,#16a34a,#22c55e)', boxShadow: '0 4px 18px rgba(34,197,94,0.45)' }}>
        {t('hub_start_challenge')} ›
      </div>
    </PhoneFrame>
  )
}

function SceneSolve() {
  return (
    <PhoneFrame>
      <div className="p-4 pt-6 flex flex-col items-center gap-3">
        <div className="flex gap-2">
          {['📸', '🧩', '🔢', '🔍'].map((e, i) => (
            <div key={e} className="htp-chip w-10 h-10 rounded-xl flex items-center justify-center text-lg"
              style={{ background: 'rgba(255,255,255,0.08)', animationDelay: `${i * 0.35}s` }}>{e}</div>
          ))}
        </div>
        <div className="w-full rounded-xl p-3 mt-1" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <div className="h-2 rounded bg-white/35 w-24 mb-2" />
          <div className="h-1.5 rounded bg-white/15 w-full mb-1.5" />
          <div className="h-1.5 rounded bg-white/15 w-3/4" />
        </div>
        <div className="w-full rounded-xl px-3 py-2.5 text-left text-white/80 text-xs" style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(34,211,238,0.4)' }}>
          <span className="htp-typing">castle</span>
        </div>
        <CheckCircle2 className="htp-check w-12 h-12 text-green-400" />
      </div>
    </PhoneFrame>
  )
}

function SceneProgress({ t }) {
  return (
    <PhoneFrame>
      <div className="p-4 pt-8 flex flex-col items-center">
        <div className="htp-points flex items-center gap-1.5 text-amber-400 font-black text-2xl mb-5">
          <Star className="w-6 h-6 fill-amber-400" /> +100
        </div>
        <div className="flex items-center gap-1.5">
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="flex items-center gap-1.5">
              <div className={`htp-step w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold`}
                style={{ animationDelay: `${0.6 + i * 0.5}s` }}>{i + 1}</div>
              {i < 3 && <div className="w-3 h-0.5 bg-white/20" />}
            </div>
          ))}
        </div>
        <div className="htp-finger2 text-2xl mt-2 self-start" style={{ marginLeft: 30 }}>👆</div>
        <div className="text-white/45 text-[10px] text-center mt-1 leading-snug px-1">{t('hub_steps_hint')}</div>
      </div>
    </PhoneFrame>
  )
}

const SCENES = [
  { key: 's1', Comp: SceneTour, emoji: '🗺️' },
  { key: 's2', Comp: SceneWalk, emoji: '🚶' },
  { key: 's3', Comp: SceneArrive, emoji: '🔔', chime: true },
  { key: 's4', Comp: SceneSolve, emoji: '🧩' },
  { key: 's5', Comp: SceneProgress, emoji: '⭐' },
]

/* ── Player ────────────────────────────────────────────────────────── */

export default function HowToPlay({ open, onClose }) {
  const { t } = useTranslation()
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const last = useRef(null)

  useEffect(() => { if (open) { setIdx(0); setElapsed(0); setPlaying(true) } }, [open])

  // Timeline clock
  useEffect(() => {
    if (!open || !playing) { last.current = null; return }
    let raf
    const tick = (ts) => {
      if (last.current != null) {
        const dt = ts - last.current
        setElapsed(e => e + dt)
      }
      last.current = ts
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => { cancelAnimationFrame(raf); last.current = null }
  }, [open, playing])

  // Advance scenes
  useEffect(() => {
    if (elapsed < SCENE_MS) return
    if (idx < SCENES.length - 1) { setIdx(i => i + 1); setElapsed(0) }
    else { setPlaying(false); setElapsed(SCENE_MS) }
  }, [elapsed, idx])

  // Demo the arrival chime on the "you've arrived" scene
  useEffect(() => {
    if (!open || !SCENES[idx].chime) return
    const tm = setTimeout(() => playArrivalSound(), 900)
    return () => clearTimeout(tm)
  }, [open, idx])

  if (!open) return null

  const atEnd = idx === SCENES.length - 1 && !playing && elapsed >= SCENE_MS
  const go = (n) => { setIdx(Math.max(0, Math.min(SCENES.length - 1, n))); setElapsed(0); setPlaying(true) }
  const { Comp, key, emoji } = SCENES[idx]

  return createPortal(
    <div className="fixed inset-0 flex items-center justify-center p-4" style={{ zIndex: 10000, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(6px)' }}>
      <div className="relative w-full max-w-[400px] rounded-3xl overflow-hidden"
        style={{ background: 'linear-gradient(160deg, #041a3d 0%, #072b5c 55%, #0e7490 100%)', border: '1px solid rgba(255,255,255,0.12)' }}>

        {/* Story-style progress bars */}
        <div className="flex gap-1.5 px-4 pt-4">
          {SCENES.map((s, i) => (
            <div key={s.key} className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.18)' }}>
              <div className="h-full bg-white rounded-full"
                style={{ width: i < idx ? '100%' : i === idx ? `${Math.min(100, (elapsed / SCENE_MS) * 100)}%` : '0%' }} />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between px-4 pt-3">
          <div className="text-cyan-300 text-xs font-semibold tracking-[0.2em] uppercase">{t('howto_title')}</div>
          <button onClick={onClose} aria-label={t('howto_close')}
            className="w-9 h-9 rounded-full flex items-center justify-center active:scale-90 transition-transform"
            style={{ background: 'rgba(255,255,255,0.1)' }}>
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Scene — tap left/right half to go back/forward */}
        <div className="relative px-4 pt-3 pb-2 select-none">
          <div key={`${key}-${idx}`} className="animate-fade-in">
            <Comp t={t} />
          </div>
          <button aria-label="back" className="absolute inset-y-0 left-0 w-1/3" onClick={() => go(idx - 1)} />
          <button aria-label="next" className="absolute inset-y-0 right-0 w-1/3" onClick={() => go(idx + 1)} />
        </div>

        <div key={`txt-${idx}`} className="px-6 pt-2 pb-4 text-center animate-slide-up" style={{ minHeight: 104 }}>
          <div className="text-white/40 text-xs font-semibold mb-1">{idx + 1} / {SCENES.length}</div>
          <h3 className="text-white font-bold text-lg leading-tight mb-1.5">{emoji} {t(`howto_${key}_title`)}</h3>
          <p className="text-white/65 text-sm leading-relaxed">{t(`howto_${key}_body`)}</p>
        </div>

        {/* Controls */}
        <div className="flex gap-2 px-4 pb-5">
          {atEnd ? (
            <button onClick={() => go(0)}
              className="w-14 rounded-xl flex items-center justify-center active:scale-95 transition-transform"
              style={{ background: 'rgba(255,255,255,0.1)' }} aria-label={t('howto_replay')}>
              <RotateCcw className="w-5 h-5 text-white" />
            </button>
          ) : (
            <button onClick={() => setPlaying(p => !p)}
              className="w-14 rounded-xl flex items-center justify-center active:scale-95 transition-transform"
              style={{ background: 'rgba(255,255,255,0.1)' }}>
              {playing ? <Pause className="w-5 h-5 text-white" /> : <Play className="w-5 h-5 text-white" />}
            </button>
          )}
          <button onClick={atEnd ? onClose : () => go(idx + 1)}
            className="flex-1 py-4 rounded-xl font-bold text-white text-base flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
            style={{ background: 'linear-gradient(135deg, #06b6d4, #0ea5e9, #2563eb)', boxShadow: '0 4px 20px rgba(6,182,212,0.35)' }}>
            {atEnd ? t('howto_done') : t('howto_next')} <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
