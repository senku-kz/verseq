<template>
  <div class="heatmap-keyboard">
    <div v-for="(row, rowIndex) in keyboardRows" :key="rowIndex" class="heatmap-row">
      <div
        v-for="key in row"
        :key="key.id"
        class="heatmap-key"
        :class="key.extraClass"
        :style="{ backgroundColor: getKeyColor(key.id) }"
      >
        <q-tooltip v-if="key.isTypeable">
          {{ key.label }}: {{ props.keyErrors[key.id] ?? 0 }} errors
        </q-tooltip>
        <span class="heatmap-key-label">{{ key.label }}</span>
      </div>
    </div>

    <!-- Legend -->
    <div class="heatmap-legend q-mt-md">
      <span class="legend-label">0 errors</span>
      <div class="legend-bar"></div>
      <span class="legend-label">{{ maxErrors }}+ errors</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  keyErrors: Record<string, number>
  layout: 'en' | 'ru'
}>()

const maxErrors = computed(() => Math.max(...Object.values(props.keyErrors), 1))

function getKeyColor(key: string): string {
  const count = props.keyErrors[key] ?? 0
  if (count === 0) return '#2ecc71'
  const ratio = Math.min(count / maxErrors.value, 1)
  if (ratio < 0.5) {
    // green (#2ecc71) to yellow (#f1c40f)
    const t = ratio / 0.5
    const r = Math.round(46 + (241 - 46) * t)
    const g = Math.round(204 + (196 - 204) * t)
    const b = Math.round(113 + (15 - 113) * t)
    return `rgb(${r},${g},${b})`
  } else {
    // yellow (#f1c40f) to red (#e74c3c)
    const t = (ratio - 0.5) / 0.5
    const r = Math.round(241 + (231 - 241) * t)
    const g = Math.round(196 + (76 - 196) * t)
    const b = Math.round(15 + (60 - 15) * t)
    return `rgb(${r},${g},${b})`
  }
}

interface KeyDef {
  id: string
  label: string
  extraClass?: string
  isTypeable: boolean
}

const EN_ROWS: Array<Array<{ key: string; extraClass?: string; label?: string; typeable?: boolean }>> = [
  [
    { key: '`', typeable: true }, { key: '1', typeable: true }, { key: '2', typeable: true },
    { key: '3', typeable: true }, { key: '4', typeable: true }, { key: '5', typeable: true },
    { key: '6', typeable: true }, { key: '7', typeable: true }, { key: '8', typeable: true },
    { key: '9', typeable: true }, { key: '0', typeable: true }, { key: '-', typeable: true },
    { key: '=', typeable: true }, { key: 'backspace', label: '⌫', extraClass: 'key-wide' },
  ],
  [
    { key: 'tab', label: 'Tab', extraClass: 'key-wide' },
    { key: 'q', typeable: true }, { key: 'w', typeable: true }, { key: 'e', typeable: true },
    { key: 'r', typeable: true }, { key: 't', typeable: true }, { key: 'y', typeable: true },
    { key: 'u', typeable: true }, { key: 'i', typeable: true }, { key: 'o', typeable: true },
    { key: 'p', typeable: true }, { key: '[', typeable: true }, { key: ']', typeable: true },
    { key: '\\', typeable: true },
  ],
  [
    { key: 'caps', label: 'Caps', extraClass: 'key-wider' },
    { key: 'a', typeable: true }, { key: 's', typeable: true }, { key: 'd', typeable: true },
    { key: 'f', typeable: true }, { key: 'g', typeable: true }, { key: 'h', typeable: true },
    { key: 'j', typeable: true }, { key: 'k', typeable: true }, { key: 'l', typeable: true },
    { key: ';', typeable: true }, { key: "'", typeable: true },
    { key: 'enter', label: '↵', extraClass: 'key-wider' },
  ],
  [
    { key: 'lshift', label: '⇧', extraClass: 'key-wider' },
    { key: 'z', typeable: true }, { key: 'x', typeable: true }, { key: 'c', typeable: true },
    { key: 'v', typeable: true }, { key: 'b', typeable: true }, { key: 'n', typeable: true },
    { key: 'm', typeable: true }, { key: ',', typeable: true }, { key: '.', typeable: true },
    { key: '/', typeable: true }, { key: 'rshift', label: '⇧', extraClass: 'key-wider' },
  ],
  [
    { key: ' ', label: 'Space', extraClass: 'key-widest', typeable: true },
  ],
]

const RU_ROWS: Array<Array<{ key: string; extraClass?: string; label?: string; typeable?: boolean }>> = [
  [
    { key: '1', typeable: true }, { key: '2', typeable: true }, { key: '3', typeable: true },
    { key: '4', typeable: true }, { key: '5', typeable: true }, { key: '6', typeable: true },
    { key: '7', typeable: true }, { key: '8', typeable: true }, { key: '9', typeable: true },
    { key: '0', typeable: true }, { key: '-', typeable: true }, { key: '=', typeable: true },
    { key: 'backspace', label: '⌫', extraClass: 'key-wide' },
  ],
  [
    { key: 'tab', label: 'Tab', extraClass: 'key-wide' },
    { key: 'й', typeable: true }, { key: 'ц', typeable: true }, { key: 'у', typeable: true },
    { key: 'к', typeable: true }, { key: 'е', typeable: true }, { key: 'н', typeable: true },
    { key: 'г', typeable: true }, { key: 'ш', typeable: true }, { key: 'щ', typeable: true },
    { key: 'з', typeable: true }, { key: 'х', typeable: true }, { key: 'ъ', typeable: true },
  ],
  [
    { key: 'caps', label: 'Caps', extraClass: 'key-wider' },
    { key: 'ф', typeable: true }, { key: 'ы', typeable: true }, { key: 'в', typeable: true },
    { key: 'а', typeable: true }, { key: 'п', typeable: true }, { key: 'р', typeable: true },
    { key: 'о', typeable: true }, { key: 'л', typeable: true }, { key: 'д', typeable: true },
    { key: 'ж', typeable: true }, { key: 'э', typeable: true },
    { key: 'enter', label: '↵', extraClass: 'key-wider' },
  ],
  [
    { key: 'lshift', label: '⇧', extraClass: 'key-wider' },
    { key: 'я', typeable: true }, { key: 'ч', typeable: true }, { key: 'с', typeable: true },
    { key: 'м', typeable: true }, { key: 'и', typeable: true }, { key: 'т', typeable: true },
    { key: 'ь', typeable: true }, { key: 'б', typeable: true }, { key: 'ю', typeable: true },
    { key: '.', typeable: true }, { key: 'rshift', label: '⇧', extraClass: 'key-wider' },
  ],
  [
    { key: ' ', label: 'Space', extraClass: 'key-widest', typeable: true },
  ],
]

const keyboardRows = computed<KeyDef[][]>(() => {
  const rows = props.layout === 'en' ? EN_ROWS : RU_ROWS
  return rows.map((row) =>
    row.map((k) => ({
      id: k.key,
      label: k.label ?? k.key.toUpperCase(),
      extraClass: k.extraClass,
      isTypeable: k.typeable ?? false,
    }))
  )
})
</script>

<style scoped lang="scss">
.heatmap-keyboard {
  font-family: monospace;
  user-select: none;
}

.heatmap-row {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

.heatmap-key {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 5px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #1a1a1a;
  border: 1px solid rgba(0,0,0,0.2);
  cursor: default;
  transition: transform 0.1s;

  &:hover {
    transform: scale(1.1);
    z-index: 1;
  }

  &.key-wide { width: 56px; }
  &.key-wider { width: 70px; }
  &.key-widest { width: 220px; }
}

.heatmap-key-label {
  pointer-events: none;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.legend-bar {
  flex: 1;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(to right, #2ecc71, #f1c40f, #e74c3c);
  border: 1px solid rgba(0,0,0,0.15);
}

.legend-label {
  font-size: 0.75rem;
  color: #aaa;
  white-space: nowrap;
}
</style>
