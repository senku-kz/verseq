<template>
  <q-page class="practice-page q-pa-md">
    <!-- Header controls -->
    <div class="row items-center q-gutter-sm q-mb-md flex-wrap">
      <!-- Language toggle -->
      <q-btn-toggle
        v-model="settings.lang"
        :options="[
          { label: 'EN', value: 'en' },
          { label: 'RU', value: 'ru' },
        ]"
        color="primary"
        text-color="white"
        toggle-color="deep-orange"
        unelevated
        @update:model-value="fetchNewText"
      />

      <!-- Mode selector -->
      <q-btn-toggle
        v-model="settings.practiceMode"
        :options="[
          { label: 'Free', value: 'free' },
          { label: 'Adaptive', value: 'adaptive' },
          { label: 'Bigrams', value: 'bigrams' },
        ]"
        color="primary"
        text-color="white"
        toggle-color="deep-orange"
        unelevated
        @update:model-value="fetchNewText"
      />

      <!-- Length slider (hidden on xs) -->
      <div v-if="!$q.screen.lt.sm" class="row items-center q-gutter-sm" style="min-width: 200px">
        <q-icon name="short_text" />
        <q-slider
          v-model="settings.practiceLength"
          :min="100"
          :max="600"
          :step="50"
          color="primary"
          style="flex: 1; min-width: 100px"
          @change="fetchNewText"
        />
        <span class="text-caption">{{ settings.practiceLength }}ch</span>
      </div>

      <!-- Keyboard toggle (hidden on mobile) -->
      <q-btn
        v-if="!$q.screen.lt.sm"
        :icon="settings.showKeyboard ? 'keyboard' : 'keyboard_hide'"
        :color="settings.showKeyboard ? 'primary' : 'grey'"
        flat
        round
        @click="settings.showKeyboard = !settings.showKeyboard"
      >
        <q-tooltip>Toggle keyboard visualization</q-tooltip>
      </q-btn>

      <!-- Spacer -->
      <q-space />

      <!-- New text button -->
      <q-btn
        icon="refresh"
        :label="$q.screen.lt.sm ? '' : 'New Text'"
        color="secondary"
        unelevated
        :loading="loading"
        @click="fetchNewText"
      />
    </div>

    <!-- Loading state -->
    <div v-if="loading && !currentText" class="column items-center q-pa-xl">
      <q-spinner-dots color="primary" size="48px" />
      <p class="q-mt-md text-grey">Loading text...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="loadError" class="column items-center q-pa-xl">
      <q-icon name="error" color="negative" size="3rem" />
      <p class="q-mt-md text-negative">{{ loadError }}</p>
      <q-btn color="primary" label="Retry" @click="fetchNewText" class="q-mt-sm" />
    </div>

    <!-- Typing zone -->
    <template v-else-if="currentText">
      <div class="training-area">
        <TypingZone
          ref="typingZoneRef"
          :text="currentText"
          :disabled="showResults"
          :mobile-font-large="$q.screen.lt.sm"
          :style="{ width: tzWidth }"
          @finished="onFinished"
          @key-pressed="pressedKey = $event"
          @next-char="nextKey = $event"
        />

        <!-- Keyboard visualization (desktop/tablet only) -->
        <div
          v-if="settings.showKeyboard && !$q.screen.lt.sm"
          ref="kbWrapperRef"
          class="q-mt-sm"
        >
          <KeyboardViz
            :layout="settings.lang"
            :next-key="nextKey"
            :error-key="errorKey"
            :pressed-key="pressedKey"
            :compact="$q.screen.lt.md"
          />
        </div>
      </div>
    </template>

    <!-- Results overlay -->
    <ResultsCard
      v-if="showResults && finishedStats"
      :stats="finishedStats"
      mode="practice"
      @retry="onRetry"
      @next="onNext"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useQuasar } from 'quasar'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'
import { practiceApi, sessionsApi } from '../api'
import TypingZone from '../components/TypingZone.vue'
import KeyboardViz from '../components/KeyboardViz.vue'
import ResultsCard from '../components/ResultsCard.vue'
import type { TypingStats } from '../types'

const $q = useQuasar()
const settings = useSettingsStore()
const authStore = useAuthStore()

const currentText = ref('')
const loading = ref(false)
const loadError = ref<string | null>(null)
const showResults = ref(false)
const finishedStats = ref<TypingStats | null>(null)

const typingZoneRef = ref<InstanceType<typeof TypingZone> | null>(null)

const nextKey = ref('')
const errorKey = ref<string | null>(null)
const pressedKey = ref<string | null>(null)

// Sync TypingZone width to keyboard width
const kbWrapperRef = ref<HTMLElement | null>(null)
const tzWidth = ref<string>('100%')
let resizeObserver: ResizeObserver | null = null

function syncWidth() {
  if (kbWrapperRef.value) {
    tzWidth.value = kbWrapperRef.value.offsetWidth + 'px'
  }
}

async function fetchNewText() {
  loading.value = true
  loadError.value = null
  showResults.value = false
  finishedStats.value = null

  try {
    // Pass anonymous weak bigrams for adaptive mode when not authenticated
    let weakBigrams: Record<string, number> | undefined
    if (settings.practiceMode === 'adaptive' && !authStore.isAuthenticated) {
      weakBigrams = authStore.getAnonWeakBigrams()
    }

    const response = await practiceApi.getText(
      settings.lang,
      settings.practiceMode,
      settings.practiceLength,
      weakBigrams
    )
    currentText.value = response.text
    nextKey.value = ''
  } catch (err: unknown) {
    console.error('Failed to fetch text:', err)
    const sampleEn = 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.'
    const sampleRu = 'Съешь же ещё этих мягких французских булок да выпей чаю. В чащах юга жил бы цитрус.'
    currentText.value = settings.lang === 'en' ? sampleEn : sampleRu
    nextKey.value = ''
    loadError.value = null
  } finally {
    loading.value = false
  }
}

async function onFinished(stats: TypingStats) {
  finishedStats.value = stats
  showResults.value = true

  if (authStore.isAuthenticated) {
    const tokenOk = await authStore.ensureFreshToken()
    if (!tokenOk) {
      $q.notify({ type: 'warning', message: 'Session not saved — please sign in again' })
      return
    }
    sessionsApi
      .submit({
        language: settings.lang,
        wpm: stats.wpm,
        cpm: stats.cpm,
        accuracy: stats.accuracy,
        duration_ms: stats.elapsedSeconds * 1000,
        error_matrix_delta: stats.errorMatrix,
      })
      .then(() => {
        $q.notify({ type: 'positive', message: 'Session saved', timeout: 1500 })
      })
      .catch((err) => {
        console.error('Failed to save session:', err)
        $q.notify({ type: 'negative', message: 'Failed to save session — check your connection' })
      })
  } else {
    // Store error matrix locally for anonymous adaptive mode
    if (Object.keys(stats.errorMatrix).length > 0) {
      authStore.updateAnonErrorMatrix(stats.errorMatrix)
    }
  }
}

function onRetry() {
  showResults.value = false
  finishedStats.value = null
  typingZoneRef.value?.reset()
  nextKey.value = currentText.value[0] ?? ''
}

function onNext() {
  fetchNewText()
}

onMounted(() => {
  fetchNewText()
  resizeObserver = new ResizeObserver(syncWidth)
  if (kbWrapperRef.value) resizeObserver.observe(kbWrapperRef.value)
})

onUnmounted(() => resizeObserver?.disconnect())
</script>

<style scoped lang="scss">
.practice-page {
  max-width: 1400px;
  margin: 0 auto;
}

// Контейнер подстраивается под ширину клавиатуры,
// TypingZone растягивается до той же ширины
.training-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 auto;
}
</style>
