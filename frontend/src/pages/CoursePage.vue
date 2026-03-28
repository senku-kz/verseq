<template>
  <q-page class="q-pa-md course-page">
    <!-- Header -->
    <div class="row items-center q-mb-lg">
      <div class="text-h5 text-weight-bold q-mr-auto">Course</div>
      <q-btn-toggle
        v-model="lang"
        :options="[
          { label: 'EN', value: 'en' },
          { label: 'RU', value: 'ru' },
        ]"
        color="primary"
        text-color="white"
        toggle-color="deep-orange"
        unelevated
        @update:model-value="fetchLessons"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="column items-center q-pa-xl">
      <q-spinner-dots color="primary" size="48px" />
      <p class="q-mt-md text-grey">Loading lessons...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="column items-center q-pa-xl">
      <q-icon name="error" color="negative" size="3rem" />
      <p class="q-mt-md text-negative">{{ error }}</p>
      <q-btn color="primary" label="Retry" @click="fetchLessons" class="q-mt-sm" />
    </div>

    <!-- Lessons grid -->
    <div v-else class="row q-col-gutter-md">
      <div
        v-for="lesson in lessons"
        :key="lesson.id"
        class="col-12 col-sm-6 col-md-4"
      >
        <q-card
          class="lesson-card full-height"
          :class="{ 'lesson-locked': !lesson.is_unlocked }"
          @click="navigateToLesson(lesson)"
          clickable
          v-ripple="lesson.is_unlocked"
        >
          <!-- Colored header band -->
          <div
            class="lesson-header q-pa-md"
            :style="{ background: getLessonGradient(lesson.id) }"
          >
            <div class="row items-center">
              <div class="text-overline text-white opacity-80 q-mr-auto">
                Lesson {{ lesson.id }}
              </div>
              <q-icon
                v-if="!lesson.is_unlocked"
                name="lock"
                color="white"
                size="1.2rem"
              />
              <q-badge
                v-else-if="lesson.is_completed"
                color="positive"
                rounded
              >
                <q-icon name="check" size="0.9rem" />
              </q-badge>
            </div>
            <div class="text-subtitle1 text-white text-weight-bold q-mt-xs">
              {{ lesson.title }}
            </div>
          </div>

          <q-card-section class="q-pt-sm">
            <p class="text-caption text-grey q-mb-sm">{{ lesson.description }}</p>

            <!-- Stars progress bar -->
            <div class="row items-center q-gutter-xs q-mb-sm">
              <q-icon
                v-for="n in 15"
                :key="n"
                :name="n <= lesson.stars_total ? 'star' : 'star_border'"
                :color="n <= lesson.stars_total ? 'amber' : 'grey-7'"
                size="0.8rem"
              />
            </div>

            <q-linear-progress
              :value="lesson.stars_total / 15"
              :color="lesson.is_completed ? 'positive' : 'primary'"
              track-color="grey-8"
              rounded
              size="6px"
              class="q-mb-xs"
            />

            <div class="text-caption text-grey-5">
              {{ lesson.exercises_completed }}/5 exercises
              &nbsp;&bull;&nbsp;
              {{ lesson.stars_total }}/15 stars
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { lessonsApi } from '../api'
import type { LessonListItem } from '../types'

const router = useRouter()

const lang = ref('en')
const lessons = ref<LessonListItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function fetchLessons() {
  loading.value = true
  error.value = null
  try {
    lessons.value = await lessonsApi.list(lang.value)
  } catch (err) {
    console.error('Failed to load lessons:', err)
    error.value = 'Failed to load lessons. Please try again.'
  } finally {
    loading.value = false
  }
}

function navigateToLesson(lesson: LessonListItem) {
  if (!lesson.is_unlocked) return
  router.push({ path: `/lesson/${lesson.id}`, query: { lang: lang.value } })
}

function getLessonGradient(id: number): string {
  if (id <= 4) {
    return 'linear-gradient(135deg, #e53935, #c62828)'
  } else if (id <= 9) {
    return 'linear-gradient(135deg, #fb8c00, #e65100)'
  } else if (id <= 12) {
    return 'linear-gradient(135deg, #1e88e5, #0d47a1)'
  } else {
    return 'linear-gradient(135deg, #8e24aa, #4a148c)'
  }
}

onMounted(() => {
  fetchLessons()
})
</script>

<style scoped lang="scss">
.course-page {
  max-width: 1100px;
  margin: 0 auto;
}

.lesson-card {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  background: #1e1e1e;

  &:hover:not(.lesson-locked) {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  }

  &.lesson-locked {
    opacity: 0.5;
    cursor: default;
  }
}

.lesson-header {
  border-radius: 4px 4px 0 0;
}
</style>
