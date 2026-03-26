<template>
  <div class="keyboard-container" :class="{ 'keyboard-compact': compact }">
    <div v-for="(row, rowIndex) in keyboardRows" :key="rowIndex" class="keyboard-row">
      <div
        v-for="key in row"
        :key="key.id"
        class="key"
        :class="[
          key.extraClass,
          isNextKey(key) ? 'next-key' : '',
          isErrorKey(key) ? 'error-flash' : '',
          isPressedKey(key) ? 'pressed-key' : '',
        ]"
        :style="{ backgroundColor: key.color }"
      >
        <span v-if="key.labelShift" class="key-shift-label">{{ key.labelShift }}</span>
        <span class="key-main-label">{{ key.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useKeyboard, type Layout } from '../composables/useKeyboard'

const props = defineProps<{
  layout: Layout
  nextKey: string
  errorKey: string | null
  pressedKey?: string | null
  compact?: boolean
}>()

const { getFingerColor, getLayoutMap } = useKeyboard()

// Error flash
const errorFlashKey = ref<string | null>(null)
const errorFlashActive = ref(false)

watch(
  () => props.errorKey,
  (newKey) => {
    if (newKey) {
      errorFlashKey.value = newKey
      errorFlashActive.value = true
      setTimeout(() => {
        errorFlashActive.value = false
        errorFlashKey.value = null
      }, 350)
    }
  }
)

// Pressed key visual feedback
const pressedKeyActive = ref<string | null>(null)

watch(
  () => props.pressedKey,
  (newKey) => {
    if (newKey) {
      pressedKeyActive.value = newKey
      setTimeout(() => {
        pressedKeyActive.value = null
      }, 120)
    }
  }
)

interface KeyDef {
  id: string
  label: string
  labelShift?: string
  color: string
  extraClass?: string
  // The logical key value(s) this key represents
  logicalKey: string[]
}

// Define keyboard rows for EN layout
// Row 0: ` 1 2 3 4 5 6 7 8 9 0 - = Backspace
// Row 1: Tab Q W E R T Y U I O P [ ] \
// Row 2: CapsLock A S D F G H J K L ; ' Enter
// Row 3: Shift Z X C V B N M , . / Shift
// Row 4: Space

const EN_ROWS: Array<Array<{ key: string; extraClass?: string; label?: string; labelShift?: string }>> = [
  [
    { key: '`' }, { key: '1' }, { key: '2' }, { key: '3' }, { key: '4' },
    { key: '5' }, { key: '6' }, { key: '7' }, { key: '8' }, { key: '9' },
    { key: '0' }, { key: '-' }, { key: '=' },
    { key: 'backspace', label: '⌫', extraClass: 'key-wide' },
  ],
  [
    { key: 'tab', label: 'Tab', extraClass: 'key-wide' },
    { key: 'q' }, { key: 'w' }, { key: 'e' }, { key: 'r' }, { key: 't' },
    { key: 'y' }, { key: 'u' }, { key: 'i' }, { key: 'o' }, { key: 'p' },
    { key: '[' }, { key: ']' }, { key: '\\' },
  ],
  [
    { key: 'caps', label: 'Caps', extraClass: 'key-wider' },
    { key: 'a' }, { key: 's' }, { key: 'd' }, { key: 'f' }, { key: 'g' },
    { key: 'h' }, { key: 'j' }, { key: 'k' }, { key: 'l' },
    { key: ';' }, { key: "'" },
    { key: 'enter', label: '↵', extraClass: 'key-wider' },
  ],
  [
    { key: 'lshift', label: '⇧ Shift', extraClass: 'key-wider' },
    { key: 'z' }, { key: 'x' }, { key: 'c' }, { key: 'v' }, { key: 'b' },
    { key: 'n' }, { key: 'm' }, { key: ',' }, { key: '.' }, { key: '/' },
    { key: 'rshift', label: '⇧ Shift', extraClass: 'key-wider' },
  ],
  [
    { key: ' ', label: 'Space', extraClass: 'key-widest' },
  ],
]

// Russian ЙЦУКЕН rows (logical key values are Cyrillic)
const RU_ROWS: Array<Array<{ key: string; extraClass?: string; label?: string; labelShift?: string }>> = [
  [
    { key: '1' }, { key: '2' }, { key: '3' }, { key: '4' }, { key: '5' },
    { key: '6' }, { key: '7' }, { key: '8' }, { key: '9' }, { key: '0' },
    { key: '-' }, { key: '=' },
    { key: 'backspace', label: '⌫', extraClass: 'key-wide' },
  ],
  [
    { key: 'tab', label: 'Tab', extraClass: 'key-wide' },
    { key: 'й' }, { key: 'ц' }, { key: 'у' }, { key: 'к' }, { key: 'е' },
    { key: 'н' }, { key: 'г' }, { key: 'ш' }, { key: 'щ' }, { key: 'з' },
    { key: 'х' }, { key: 'ъ' },
  ],
  [
    { key: 'caps', label: 'Caps', extraClass: 'key-wider' },
    { key: 'ф' }, { key: 'ы' }, { key: 'в' }, { key: 'а' }, { key: 'п' },
    { key: 'р' }, { key: 'о' }, { key: 'л' }, { key: 'д' }, { key: 'ж' }, { key: 'э' },
    { key: 'enter', label: '↵', extraClass: 'key-wider' },
  ],
  [
    { key: 'lshift', label: '⇧ Shift', extraClass: 'key-wider' },
    { key: 'я' }, { key: 'ч' }, { key: 'с' }, { key: 'м' }, { key: 'и' },
    { key: 'т' }, { key: 'ь' }, { key: 'б' }, { key: 'ю' }, { key: '.' },
    { key: 'rshift', label: '⇧ Shift', extraClass: 'key-wider' },
  ],
  [
    { key: ' ', label: 'Space', extraClass: 'key-widest' },
  ],
]

// Special key colors (non-finger-mapped)
const SPECIAL_KEY_COLOR = '#546e7a'

const keyboardRows = computed<KeyDef[][]>(() => {
  const layoutMap = getLayoutMap(props.layout)
  const rows = props.layout === 'en' ? EN_ROWS : RU_ROWS

  return rows.map((row) =>
    row.map((keyDef) => {
      const info = layoutMap[keyDef.key]
      const label = keyDef.label ?? (info?.label ?? keyDef.key.toUpperCase())
      const labelShift = keyDef.labelShift ?? info?.labelShift
      const color = info ? info.color : SPECIAL_KEY_COLOR

      return {
        id: keyDef.key,
        label,
        labelShift,
        color,
        extraClass: keyDef.extraClass,
        logicalKey: [keyDef.key, keyDef.key.toLowerCase(), keyDef.key.toUpperCase()].filter(Boolean),
      }
    })
  )
})

function isNextKey(key: KeyDef): boolean {
  const nk = props.nextKey?.toLowerCase()
  if (!nk) return false
  return key.logicalKey.some((k) => k.toLowerCase() === nk)
}

function isErrorKey(key: KeyDef): boolean {
  if (!errorFlashActive.value || !errorFlashKey.value) return false
  const ek = errorFlashKey.value.toLowerCase()
  return key.logicalKey.some((k) => k.toLowerCase() === ek)
}

function isPressedKey(key: KeyDef): boolean {
  if (!pressedKeyActive.value) return false
  const pk = pressedKeyActive.value.toLowerCase()
  return key.logicalKey.some((k) => k.toLowerCase() === pk)
}
</script>

<style scoped lang="scss">
.keyboard-compact {
  transform: scale(0.82);
  transform-origin: top center;
}
</style>
