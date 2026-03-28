import { ref, computed, type Ref } from 'vue'
import type { CharState, TypingStats } from '../types'

const IGNORED_KEYS = new Set([
  'Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab', 'Escape',
  'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
  'Home', 'End', 'PageUp', 'PageDown', 'Insert', 'Delete',
  'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
  'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
  'NumLock', 'ScrollLock', 'Pause', 'PrintScreen', 'ContextMenu',
])

function makeStats(): TypingStats {
  return {
    wpm: 0,
    cpm: 0,
    accuracy: 100,
    elapsedSeconds: 0,
    totalErrors: 0,
    errorMatrix: {},
  }
}

function textToChars(text: string): CharState[] {
  return text.split('').map((char) => ({ char, state: 'pending' as const }))
}

export function useTypingEngine(initialText: string) {
  const chars: Ref<CharState[]> = ref(textToChars(initialText))
  const cursor: Ref<number> = ref(0)
  const isStarted: Ref<boolean> = ref(false)
  const isFinished: Ref<boolean> = ref(false)
  const stats: Ref<TypingStats> = ref(makeStats())
  const lastErrorKey: Ref<string | null> = ref(null)

  // Internal timing state
  let startTime: number | null = null
  let timerHandle: ReturnType<typeof setInterval> | null = null
  let totalAttempted = 0

  function startTimer() {
    startTime = Date.now()
  }

  function stopTimer() {
    if (timerHandle !== null) {
      clearInterval(timerHandle)
      timerHandle = null
    }
  }

  function countCorrect(): number {
    return chars.value.filter((c) => c.state === 'correct').length
  }

  function updateStats() {
    if (!startTime) return
    const elapsedMs = Date.now() - startTime
    const elapsedMin = elapsedMs / 60000
    const elapsedSec = elapsedMs / 1000
    const correct = countCorrect()

    const wpm = elapsedMin > 0 ? Math.round(correct / 5 / elapsedMin) : 0
    const cpm = elapsedMin > 0 ? Math.round(correct / elapsedMin) : 0
    const accuracy =
      totalAttempted > 0
        ? Math.round(((totalAttempted - stats.value.totalErrors) / totalAttempted) * 100)
        : 100

    stats.value = {
      ...stats.value,
      wpm,
      cpm,
      accuracy: Math.max(0, Math.min(100, accuracy)),
      elapsedSeconds: Math.floor(elapsedSec),
    }
  }

  function handleKeydown(event: KeyboardEvent): void {
    if (isFinished.value) return
    if (event.ctrlKey || event.altKey || event.metaKey) return
    if (IGNORED_KEYS.has(event.key)) return

    const key = event.key

    // Start timer on first real keypress
    if (!isStarted.value) {
      isStarted.value = true
      startTimer()
    }

    if (key === 'Backspace') {
      if (cursor.value > 0) {
        cursor.value--
        const prev = chars.value[cursor.value]
        if (prev.state === 'error') {
          chars.value[cursor.value] = { ...prev, state: 'corrected' }
        } else if (prev.state === 'correct') {
          chars.value[cursor.value] = { ...prev, state: 'pending' }
        } else {
          chars.value[cursor.value] = { ...prev, state: 'pending' }
        }
      }
      updateStats()
      return
    }

    // Only process single printable characters
    if (key.length !== 1) return

    const currentChar = chars.value[cursor.value]
    if (!currentChar) return

    totalAttempted++

    if (key === currentChar.char) {
      // Correct keypress
      chars.value[cursor.value] = { ...currentChar, state: 'correct' }
      cursor.value++
      lastErrorKey.value = null
      updateStats()

      // Check if finished
      if (cursor.value >= chars.value.length) {
        isFinished.value = true
        stopTimer()
      }
    } else {
      // Wrong keypress
      chars.value[cursor.value] = { ...currentChar, state: 'error' }
      stats.value = { ...stats.value, totalErrors: stats.value.totalErrors + 1 }
      lastErrorKey.value = key

      // Track bigram error
      if (cursor.value > 0) {
        const prevChar = chars.value[cursor.value - 1].char
        const bigram = prevChar + currentChar.char
        const matrix = { ...stats.value.errorMatrix }
        matrix[bigram] = (matrix[bigram] ?? 0) + 1
        stats.value = { ...stats.value, errorMatrix: matrix }
      }

      updateStats()
    }
  }

  function reset(): void {
    stopTimer()
    startTime = null
    totalAttempted = 0
    cursor.value = 0
    isStarted.value = false
    isFinished.value = false
    lastErrorKey.value = null
    stats.value = makeStats()
    chars.value = chars.value.map((c) => ({ ...c, state: 'pending' }))
  }

  function loadText(newText: string): void {
    stopTimer()
    startTime = null
    totalAttempted = 0
    cursor.value = 0
    isStarted.value = false
    isFinished.value = false
    lastErrorKey.value = null
    stats.value = makeStats()
    chars.value = textToChars(newText)
  }

  return {
    chars,
    cursor,
    isStarted,
    isFinished,
    stats,
    lastErrorKey,
    handleKeydown,
    reset,
    loadText,
  }
}
