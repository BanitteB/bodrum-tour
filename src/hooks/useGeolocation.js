import { useState, useEffect } from 'react'

// One shared GPS watch for the whole app.
// - Survives screen changes (hub ↔ mission), so the position doesn't vanish
//   and the slow first fix isn't repeated on every screen.
// - If high-accuracy GPS times out or is unavailable (common indoors, on some
//   Android phones and with battery saver), it falls back to network location
//   and keeps retrying high accuracy in the background.
// - Restarts when the app comes back to the foreground, because iOS/Android
//   silently stop location updates while the browser is in the background.

const listeners = new Set()
let state = { position: null, error: null }
let watchId = null
let highAccuracy = true
let retryTimer = null
let started = false

function emit(patch) {
  state = { ...state, ...patch }
  listeners.forEach(fn => fn(state))
}

function stopWatch() {
  if (watchId != null) navigator.geolocation.clearWatch(watchId)
  watchId = null
  clearTimeout(retryTimer)
  retryTimer = null
}

function onPosition(pos) {
  emit({
    position: {
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      accuracy: pos.coords.accuracy,
    },
    error: null,
  })
}

function onError(err) {
  if (err.code === 1) {
    // Permission denied – nothing will work until the user allows it.
    emit({ error: 'denied' })
    stopWatch()
    return
  }
  // Timeout / unavailable: keep the last known position, switch accuracy mode and retry.
  if (!state.position) emit({ error: 'unavailable' })
  stopWatch()
  highAccuracy = !highAccuracy
  retryTimer = setTimeout(startWatch, 2000)
}

function startWatch() {
  if (!navigator?.geolocation) {
    emit({ error: 'unsupported' })
    return
  }
  stopWatch()
  watchId = navigator.geolocation.watchPosition(onPosition, onError, {
    enableHighAccuracy: highAccuracy,
    maximumAge: 5000,
    timeout: highAccuracy ? 20000 : 10000,
  })
  // While on the network-location fallback, try precise GPS again after a while.
  if (!highAccuracy) {
    retryTimer = setTimeout(() => { highAccuracy = true; startWatch() }, 30000)
  }
}

function ensureStarted() {
  if (started) return
  started = true
  startWatch()
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      highAccuracy = true
      startWatch()
    }
  })
}

// Lets the UI offer a "try again" button (e.g. after the user changed permissions).
export function retryGeolocation() {
  highAccuracy = true
  emit({ error: null })
  startWatch()
}

export function useGeolocation() {
  const [snap, setSnap] = useState(state)

  useEffect(() => {
    listeners.add(setSnap)
    ensureStarted()
    setSnap(state)
    return () => { listeners.delete(setSnap) }
  }, [])

  return snap
}
