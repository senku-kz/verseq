<template>
  <div class="typing-zone-wrapper">
    <!-- Hidden input for desktop key capture -->
    <input
      v-if="!$q.platform.is.mobile"
      ref="hiddenInput"
      class="hidden-input"
      :disabled="disabled"
      @keydown="onKeydown"
      autocomplete="off"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
      aria-label="Typing input"
    />

    <!-- Mobile textarea -->
    <textarea
      v-else
      ref="mobileInput"
      class="mobile-input"
      :disabled="disabled"
      @input="onMobileInput"
      @keydown="onKeydown"
      autocomplete="off"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
      placeholder="Tap here to type..."
      rows="3"
    />

    <!-- Text display — single scrolling line -->
    <div
      ref="scrollContainer"
      class="typing-zone q-pa-md rounded-borders"
      :class="{ 'typing-zone-mobile': mobileFontLarge }"
      @click="focusInput"
    >
      <div ref="textInner" class="typing-zone-inner">
        <template v-for="(charState, index) in engine.chars.value" :key="index">
          <span
            v-if="index === engine.cursor.value"
            ref="cursorSpan"
            class="cursor"
          />
          <span :class="charClass(charState.state)">{{ charState.char === ' ' ? '\u00A0' : charState.char }}</span>
        </template>
        <span
          v-if="engine.cursor.value >= engine.chars.value.length"
          ref="cursorSpan"
          class="cursor"
        />
      </div>
    </div>

    <!-- Live stats -->
    <div v-if="settings.showLiveStats" class="row q-gutter-md q-pa-sm">
      <div class="stat-chip">
        <span class="stat-number">{{ engine.stats.value.wpm }}</span>
        <span class="stat-unit">WPM</span>
      </div>
      <div class="stat-chip">
        <span class="stat-number">{{ engine.stats.value.cpm }}</span>
        <span class="stat-unit">CPM</span>
      </div>
      <div class="stat-chip">
        <span class="stat-number">{{ engine.stats.value.accuracy }}%</span>
        <span class="stat-unit">Accuracy</span>
      </div>
      <div class="stat-chip">
        <span class="stat-number">{{ formatTime(engine.stats.value.elapsedSeconds) }}</span>
        <span class="stat-unit">Time</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, type Ref } from 'vue'
import { useQuasar } from 'quasar'
import { useTypingEngine } from '../composables/useTypingEngine'
import { useSound } from '../composables/useSound'
import { useSettingsStore } from '../stores/settings'
import type { TypingStats } from '../types'

const props = defineProps<{
  text: string
  disabled?: boolean
  mobileFontLarge?: boolean
}>()

const emit = defineEmits<{
  (e: 'finished', stats: TypingStats): void
  (e: 'keyPressed', key: string): void
  (e: 'nextChar', char: string): void
}>()

const $q = useQuasar()
const settings = useSettingsStore()
const { playCorrect, playError, playFinish } = useSound()

const hiddenInput = ref<HTMLInputElement | null>(null)
const mobileInput = ref<HTMLTextAreaElement | null>(null)
const scrollContainer = ref<HTMLElement | null>(null)
const cursorSpan = ref<HTMLElement | HTMLElement[] | null>(null)

// Initialize engine
const engine = useTypingEngine(props.text)

// Watch for text changes
watch(
  () => props.text,
  (newText) => {
    if (newText) {
      engine.loadText(newText)
      emit('nextChar', newText[0] ?? '')
    }
  }
)

// Emit next char whenever cursor moves
watch(engine.cursor, (pos) => {
  emit('nextChar', engine.chars.value[pos]?.char ?? '')
})

// Scroll so cursor stays at ~30% from left
watch(
  () => engine.cursor.value,
  () => {
    nextTick(() => {
      if (!scrollContainer.value) return
      const el = Array.isArray(cursorSpan.value)
        ? cursorSpan.value[0]
        : cursorSpan.value
      if (!el) return
      const containerWidth = scrollContainer.value.clientWidth
      const cursorLeft = (el as HTMLElement).offsetLeft
      scrollContainer.value.scrollLeft = Math.max(0, cursorLeft - containerWidth * 0.3)
    })
  }
)

// Watch for finish
watch(
  () => engine.isFinished.value,
  (finished) => {
    if (finished) {
      emit('finished', engine.stats.value)
    }
  }
)

function charClass(state: string): string {
  switch (state) {
    case 'correct': return 'char-correct'
    case 'error': return 'char-error'
    case 'corrected': return 'char-corrected'
    default: return 'char-pending'
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onKeydown(event: KeyboardEvent) {
  if (props.disabled) return
  if (event.key === 'Tab') {
    event.preventDefault()
    return
  }

  const cursorBefore = engine.cursor.value
  const errorsBefore = engine.stats.value.totalErrors

  engine.handleKeydown(event)

  // Emit pressed key for keyboard visualization
  if (event.key.length === 1 || event.key === 'Backspace') {
    emit('keyPressed', event.key === ' ' ? ' ' : event.key.toLowerCase())
  }

  // Sound feedback
  if (settings.soundEnabled) {
    if (engine.isFinished.value) {
      playFinish()
    } else if (engine.stats.value.totalErrors > errorsBefore) {
      playError()
    } else if (engine.cursor.value > cursorBefore) {
      playCorrect()
    }
  }
}

let mobileLastValue = ''
function onMobileInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  const newVal = target.value
  // Detect what was typed by comparing with last value
  if (newVal.length > mobileLastValue.length) {
    const newChars = newVal.slice(mobileLastValue.length)
    for (const ch of newChars) {
      const syntheticEvent = new KeyboardEvent('keydown', { key: ch })
      engine.handleKeydown(syntheticEvent)
    }
  } else if (newVal.length < mobileLastValue.length) {
    // Backspace
    const syntheticEvent = new KeyboardEvent('keydown', { key: 'Backspace' })
    engine.handleKeydown(syntheticEvent)
  }
  mobileLastValue = newVal
}

function focusInput() {
  if (!props.disabled) {
    const input = hiddenInput.value ?? mobileInput.value
    input?.focus()
  }
}

// Expose reset for parent
defineExpose({
  reset: () => engine.reset(),
  focusInput,
})

onMounted(() => {
  focusInput()
  // Prevent context menu on typing area
  document.addEventListener('contextmenu', preventContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('contextmenu', preventContextMenu)
})

function preventContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.closest('.typing-zone-wrapper')) {
    e.preventDefault()
  }
}
</script>

<style scoped lang="scss">
.hidden-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
  border: none;
  outline: none;
  padding: 0;
  margin: 0;
  overflow: hidden;
}

.mobile-input {
  width: 100%;
  font-size: 16px; // prevent iOS zoom
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px;
  margin-bottom: 8px;
  resize: none;
}

.typing-zone {
  background: #1e1e1e;
  border-radius: 10px;
  cursor: text;
  overflow-x: hidden;
  overflow-y: hidden;
  height: 120px;
  display: flex;
  align-items: center;
  // hide scrollbar
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

.typing-zone-inner {
  display: inline-block;
  white-space: nowrap;
  line-height: 1;
  padding: 0 4px;
}

.typing-zone-mobile {
  font-size: 1.8rem;
}

.stat-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(128, 128, 128, 0.1);
  border-radius: 8px;
  padding: 8px 16px;
  min-width: 70px;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
}

.stat-unit {
  font-size: 0.8rem;
  text-transform: uppercase;
  opacity: 0.6;
}
</style>
