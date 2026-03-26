<template>
  <div class="results-overlay">
    <q-card class="results-card q-pa-lg" dark>
      <q-card-section class="text-center">
        <div class="text-h5 q-mb-md text-weight-bold">
          Session Complete!
        </div>

        <!-- Stars -->
        <div class="star-rating q-mb-lg">
          <span v-for="n in 3" :key="n">
            <q-icon
              :name="n <= starCount ? 'star' : 'star_border'"
              :color="n <= starCount ? 'amber' : 'grey-6'"
              size="2rem"
            />
          </span>
        </div>

        <!-- Main stats grid -->
        <div class="row justify-center q-gutter-md q-mb-lg">
          <div class="stat-block">
            <div class="stat-value text-primary">{{ stats.wpm }}</div>
            <div class="stat-label text-grey-4">WPM</div>
          </div>
          <div class="stat-block">
            <div class="stat-value text-secondary">{{ stats.cpm }}</div>
            <div class="stat-label text-grey-4">CPM</div>
          </div>
          <div class="stat-block">
            <div class="stat-value" :class="accuracyColor">{{ stats.accuracy }}%</div>
            <div class="stat-label text-grey-4">Accuracy</div>
          </div>
          <div class="stat-block">
            <div class="stat-value text-info">{{ formattedTime }}</div>
            <div class="stat-label text-grey-4">Time</div>
          </div>
        </div>

        <!-- Error count -->
        <div class="text-body2 text-grey-5 q-mb-md">
          Total errors: {{ stats.totalErrors }}
        </div>
      </q-card-section>

      <q-card-actions align="center" class="q-gutter-md">
        <q-btn
          color="orange"
          unelevated
          icon="replay"
          label="Try Again"
          @click="emit('retry')"
        />
        <q-btn
          color="primary"
          unelevated
          :icon="mode === 'lesson' ? 'arrow_forward' : 'refresh'"
          :label="mode === 'lesson' ? 'Next Exercise' : 'New Text'"
          @click="emit('next')"
        />
      </q-card-actions>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TypingStats } from '../types'

const props = defineProps<{
  stats: TypingStats
  mode: 'lesson' | 'practice'
}>()

const emit = defineEmits<{
  (e: 'retry'): void
  (e: 'next'): void
}>()

const starCount = computed(() => {
  if (props.stats.accuracy >= 95 && props.stats.wpm >= 30) return 3
  if (props.stats.accuracy >= 95) return 2
  return 1
})

const accuracyColor = computed(() => {
  if (props.stats.accuracy >= 95) return 'text-positive'
  if (props.stats.accuracy >= 80) return 'text-warning'
  return 'text-negative'
})

const formattedTime = computed(() => {
  const s = props.stats.elapsedSeconds
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
})
</script>

<style scoped lang="scss">
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
</style>
