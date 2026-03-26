// Minimal sound feedback using Web Audio API (no external files needed)

let audioContext: AudioContext | null = null

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioContext) {
    try {
      audioContext = new AudioContext()
    } catch {
      return null
    }
  }
  return audioContext
}

function playTone(frequency: number, durationMs: number, volume = 0.15): void {
  const ctx = getAudioContext()
  if (!ctx) return

  const oscillator = ctx.createOscillator()
  const gainNode = ctx.createGain()

  oscillator.connect(gainNode)
  gainNode.connect(ctx.destination)

  oscillator.type = 'sine'
  oscillator.frequency.setValueAtTime(frequency, ctx.currentTime)

  gainNode.gain.setValueAtTime(volume, ctx.currentTime)
  gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + durationMs / 1000)

  oscillator.start(ctx.currentTime)
  oscillator.stop(ctx.currentTime + durationMs / 1000)
}

export function useSound() {
  function playCorrect() {
    // Short high beep: 800Hz, 50ms, low volume
    playTone(800, 50, 0.1)
  }

  function playError() {
    // Short low buzz: 200Hz, 80ms
    playTone(200, 80, 0.15)
  }

  function playFinish() {
    // Three ascending tones: C-E-G (523Hz, 659Hz, 784Hz), 100ms each
    const ctx = getAudioContext()
    if (!ctx) return

    const notes = [523, 659, 784]
    notes.forEach((freq, i) => {
      const oscillator = ctx.createOscillator()
      const gainNode = ctx.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(ctx.destination)

      oscillator.type = 'sine'
      oscillator.frequency.setValueAtTime(freq, ctx.currentTime)

      const startTime = ctx.currentTime + i * 0.12
      gainNode.gain.setValueAtTime(0.0001, startTime)
      gainNode.gain.exponentialRampToValueAtTime(0.2, startTime + 0.01)
      gainNode.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.1)

      oscillator.start(startTime)
      oscillator.stop(startTime + 0.12)
    })
  }

  return { playCorrect, playError, playFinish }
}
