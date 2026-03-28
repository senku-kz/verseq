<template>
  <q-page class="lesson-page q-pa-md">
    <!-- Header bar -->
    <div class="row items-center q-mb-md">
      <q-btn
        flat
        round
        icon="arrow_back"
        color="grey"
        @click="router.push('/course')"
      >
        <q-tooltip>Back to Course</q-tooltip>
      </q-btn>

      <div class="q-ml-sm">
        <div class="text-overline text-grey">Lesson {{ lessonId }}</div>
        <div class="text-subtitle1 text-weight-bold">{{ lessonData?.title ?? '' }}</div>
      </div>

      <q-space />

      <!-- Exercise progress dots -->
      <div class="row q-gutter-xs items-center">
        <q-btn
          v-for="(ex, idx) in lessonData?.exercises ?? []"
          :key="ex.id"
          :icon="getExerciseDotIcon(idx, ex)"
          :color="getExerciseDotColor(idx, ex)"
          round
          flat
          size="sm"
          @click="jumpToExercise(idx)"
        >
          <q-tooltip>{{ ex.title }}</q-tooltip>
        </q-btn>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="column items-center q-pa-xl">
      <q-spinner-dots color="primary" size="48px" />
      <p class="q-mt-md text-grey">Loading exercise...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="loadError" class="column items-center q-pa-xl">
      <q-icon name="error" color="negative" size="3rem" />
      <p class="q-mt-md text-negative">{{ loadError }}</p>
      <q-btn color="primary" label="Retry" @click="loadExercise" class="q-mt-sm" />
    </div>

    <!-- Exercise content -->
    <template v-else-if="exerciseText && currentExercise">
      <!-- Exercise info bar -->
      <div class="row items-center q-mb-sm q-gutter-sm">
        <q-badge color="primary" outline>
          {{ currentExercise.title }}
        </q-badge>
        <q-badge v-if="currentExercise.min_wpm > 0" color="orange" outline>
          Target: {{ currentExercise.min_wpm }} WPM
        </q-badge>
        <q-badge color="teal" outline>
          Accuracy: {{ currentExercise.min_accuracy }}%
        </q-badge>
        <!-- Previous best -->
        <q-badge
          v-if="currentExercise.progress?.completed"
          color="positive"
          outline
        >
          Best: {{ currentExercise.progress.best_wpm.toFixed(0) }} WPM /
          {{ currentExercise.progress.best_accuracy.toFixed(0) }}%
          <q-icon name="star" size="0.7rem" class="q-ml-xs" />
          {{ currentExercise.progress.stars }}
        </q-badge>
      </div>

      <div class="training-area">
        <TypingZone
          ref="typingZoneRef"
          :text="exerciseText"
          :disabled="showResults"
          :style="{ width: tzWidth }"
          @finished="onFinished"
          @key-pressed="pressedKey = $event"
          @next-char="nextKey = $event"
        />

        <!-- Keyboard visualization (hidden on mobile, compact on tablet) -->
        <div
          v-if="!$q.screen.lt.sm"
          ref="kbWrapperRef"
          class="q-mt-sm"
        >
          <KeyboardViz
            :layout="lang"
            :next-key="nextKey"
            :error-key="errorKey"
            :pressed-key="pressedKey"
            :compact="$q.screen.lt.md"
          />
        </div>
      </div>
    </template>

    <!-- Results overlay -->
    <div v-if="showResults && finishedStats" class="results-overlay">
      <q-card class="results-card q-pa-lg" dark>
        <q-card-section class="text-center">
          <div class="text-h5 q-mb-md text-weight-bold">
            {{ currentExercise?.title }} Complete!
          </div>

          <!-- Stars earned this attempt -->
          <div class="star-rating q-mb-sm">
            <span v-for="n in 3" :key="n">
              <q-icon
                :name="n <= starsEarned ? 'star' : 'star_border'"
                :color="n <= starsEarned ? 'amber' : 'grey-6'"
                size="2rem"
              />
            </span>
          </div>
          <div class="text-caption text-grey q-mb-lg">{{ starsEarned }} / 3 stars</div>

          <!-- Stats -->
          <div class="row justify-center q-gutter-md q-mb-lg">
            <div class="stat-block">
              <div class="stat-value text-primary">{{ finishedStats.wpm }}</div>
              <div class="stat-label text-grey-4">WPM</div>
            </div>
            <div class="stat-block">
              <div class="stat-value text-secondary">{{ finishedStats.cpm }}</div>
              <div class="stat-label text-grey-4">CPM</div>
            </div>
            <div class="stat-block">
              <div
                class="stat-value"
                :class="finishedStats.accuracy >= 95 ? 'text-positive' : finishedStats.accuracy >= 80 ? 'text-warning' : 'text-negative'"
              >
                {{ finishedStats.accuracy }}%
              </div>
              <div class="stat-label text-grey-4">Accuracy</div>
            </div>
            <div class="stat-block">
              <div class="stat-value text-info">{{ formatTime(finishedStats.elapsedSeconds) }}</div>
              <div class="stat-label text-grey-4">Time</div>
            </div>
          </div>

          <div class="text-body2 text-grey-5 q-mb-md">
            Total errors: {{ finishedStats.totalErrors }}
          </div>
        </q-card-section>

        <q-card-actions align="center" class="q-gutter-md">
          <q-btn
            color="orange"
            unelevated
            icon="replay"
            label="Try Again"
            @click="onRetry"
          />
          <q-btn
            v-if="!isLastExercise"
            color="primary"
            unelevated
            icon="arrow_forward"
            label="Next Exercise"
            @click="onNext"
          />
          <q-btn
            v-else
            color="positive"
            unelevated
            icon="school"
            label="Finish Lesson"
            @click="onFinishLesson"
          />
        </q-card-actions>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/auth'
import { lessonsApi, sessionsApi } from '../api'
import TypingZone from '../components/TypingZone.vue'
import KeyboardViz from '../components/KeyboardViz.vue'
import type { LessonDetail, ExerciseDetail, TypingStats } from '../types'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const authStore = useAuthStore()

const lessonId = computed(() => Number(route.params.lessonId))
const lang = computed(() => (route.query.lang as string) || 'en')

const lessonData = ref<LessonDetail | null>(null)
const currentExerciseIndex = ref(0)
const exerciseText = ref('')
const loading = ref(false)
const loadError = ref<string | null>(null)
const showResults = ref(false)
const finishedStats = ref<TypingStats | null>(null)
const starsEarned = ref(0)

const typingZoneRef = ref<InstanceType<typeof TypingZone> | null>(null)
const nextKey = ref('')
const errorKey = ref<string | null>(null)
const pressedKey = ref<string | null>(null)

const kbWrapperRef = ref<HTMLElement | null>(null)
const tzWidth = ref<string>('100%')
let resizeObserver: ResizeObserver | null = null

function syncWidth() {
  if (kbWrapperRef.value) tzWidth.value = kbWrapperRef.value.offsetWidth + 'px'
}

const currentExercise = computed<ExerciseDetail | null>(() => {
  if (!lessonData.value) return null
  return lessonData.value.exercises[currentExerciseIndex.value] ?? null
})

const isLastExercise = computed(() => {
  if (!lessonData.value) return true
  return currentExerciseIndex.value >= lessonData.value.exercises.length - 1
})

function computeStars(wpm: number, accuracy: number, exercise: ExerciseDetail): number {
  let stars = 1
  if (accuracy >= 95) stars += 1
  if (exercise.min_wpm > 0 && wpm >= exercise.min_wpm) {
    stars += 1
  } else if (exercise.min_wpm === 0) {
    stars += 1
  }
  return stars
}

async function fetchLesson() {
  loading.value = true
  loadError.value = null
  try {
    lessonData.value = await lessonsApi.get(lessonId.value, lang.value)
    await loadExercise()
  } catch (err) {
    console.error('Failed to load lesson:', err)
    loadError.value = 'Failed to load lesson. Please try again.'
    loading.value = false
  }
}

async function loadExercise() {
  if (!lessonData.value) return
  const exercise = lessonData.value.exercises[currentExerciseIndex.value]
  if (!exercise) return

  loading.value = true
  loadError.value = null
  showResults.value = false
  finishedStats.value = null

  try {
    const result = await lessonsApi.getExerciseText(
      lessonId.value,
      exercise.id,
      lang.value,
    )
    exerciseText.value = result.text
    nextKey.value = ''
  } catch (err) {
    console.error('Failed to load exercise text:', err)
    loadError.value = 'Failed to load exercise text. Please try again.'
  } finally {
    loading.value = false
  }
}

async function onFinished(stats: TypingStats) {
  finishedStats.value = stats
  const exercise = currentExercise.value
  if (exercise) {
    starsEarned.value = computeStars(stats.wpm, stats.accuracy, exercise)
  }
  showResults.value = true

  if (authStore.isAuthenticated && exercise) {
    const tokenOk = await authStore.ensureFreshToken()
    if (!tokenOk) return
    sessionsApi
      .submit({
        exercise_id: exercise.id,
        language: lang.value,
        wpm: stats.wpm,
        cpm: stats.cpm,
        accuracy: stats.accuracy,
        duration_ms: stats.elapsedSeconds * 1000,
        error_matrix_delta: stats.errorMatrix,
      })
      .catch((err) => console.error('Failed to save session:', err))
  }
}

function onRetry() {
  showResults.value = false
  finishedStats.value = null
  typingZoneRef.value?.reset()
  nextKey.value = ''
}

async function onNext() {
  if (!isLastExercise.value) {
    currentExerciseIndex.value++
    await loadExercise()
    typingZoneRef.value?.reset()
  }
}

function onFinishLesson() {
  router.push('/course')
}

function jumpToExercise(idx: number) {
  if (idx === currentExerciseIndex.value) return
  currentExerciseIndex.value = idx
  showResults.value = false
  finishedStats.value = null
  loadExercise().then(() => {
    typingZoneRef.value?.reset()
  })
}

function getExerciseDotIcon(idx: number, ex: ExerciseDetail): string {
  if (ex.progress?.completed) return 'check_circle'
  if (idx === currentExerciseIndex.value) return 'radio_button_checked'
  return 'radio_button_unchecked'
}

function getExerciseDotColor(idx: number, ex: ExerciseDetail): string {
  if (ex.progress?.completed) return 'positive'
  if (idx === currentExerciseIndex.value) return 'primary'
  return 'grey'
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

onMounted(() => {
  fetchLesson()
  resizeObserver = new ResizeObserver(syncWidth)
  if (kbWrapperRef.value) resizeObserver.observe(kbWrapperRef.value)
})

onUnmounted(() => resizeObserver?.disconnect())
</script>

<style scoped lang="scss">
.lesson-page {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
}

.training-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 auto;
}

.results-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.results-card {
  background: #1e1e1e;
  border-radius: 12px;
  min-width: 340px;
  max-width: 500px;
  width: 90vw;
}

.stat-block {
  text-align: center;
  min-width: 80px;
}

.stat-value {
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.1;
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.star-rating {
  display: flex;
  justify-content: center;
  gap: 4px;
}
</style>
