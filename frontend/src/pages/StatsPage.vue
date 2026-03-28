<template>
  <q-page class="q-pa-md stats-page">
    <!-- Not authenticated -->
    <div v-if="!authStore.isAuthenticated" class="column items-center justify-center q-mt-xl">
      <q-icon name="lock" size="4rem" color="grey-5" />
      <div class="text-h6 q-mt-md text-grey-5">Login to track your progress</div>
      <q-btn to="/login" color="primary" label="Sign In" class="q-mt-md" no-caps />
    </div>

    <!-- Authenticated -->
    <template v-else>
      <!-- Loading -->
      <div v-if="loading" class="column items-center q-mt-xl">
        <q-spinner color="primary" size="3rem" />
        <div class="q-mt-sm text-grey-5">Loading stats…</div>
      </div>

      <!-- Error -->
      <q-banner v-else-if="error" class="bg-negative text-white" rounded>
        {{ error }}
      </q-banner>

      <!-- Content -->
      <template v-else>
        <!-- ── Summary cards ──────────────────────────── -->
        <div class="row q-col-gutter-md q-mb-lg">
          <div class="col-12 col-sm-6 col-md-2">
            <q-card class="summary-card">
              <q-card-section class="text-center">
                <div class="text-h2 text-orange">{{ stats?.streak_days ?? 0 }}</div>
                <div class="text-caption text-grey-5 q-mt-xs">🔥 Day Streak</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-card class="summary-card">
              <q-card-section class="text-center">
                <div class="text-h2 text-primary">{{ stats?.best_cpm?.toFixed(0) ?? '—' }}</div>
                <div class="text-caption text-grey-5 q-mt-xs">Best CPM</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-card class="summary-card">
              <q-card-section class="text-center">
                <div class="text-h2 text-blue-4">{{ stats?.avg_cpm?.toFixed(0) ?? '—' }}</div>
                <div class="text-caption text-grey-5 q-mt-xs">Avg CPM</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-card class="summary-card">
              <q-card-section class="text-center">
                <div class="text-h2 text-purple-4">{{ stats?.best_wpm?.toFixed(1) ?? '—' }}</div>
                <div class="text-caption text-grey-5 q-mt-xs">Best WPM</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-card class="summary-card">
              <q-card-section class="text-center">
                <div class="text-h2 text-positive">{{ stats?.avg_accuracy?.toFixed(1) ?? '—' }}%</div>
                <div class="text-caption text-grey-5 q-mt-xs">Avg Accuracy</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-sm-6 col-md-2">
            <q-card class="summary-card">
              <q-card-section class="text-center">
                <div class="text-h2 text-secondary">{{ stats?.total_sessions ?? 0 }}</div>
                <div class="text-caption text-grey-5 q-mt-xs">Total Sessions</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- ── CPM / WPM Chart ────────────────────────── -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="row items-center q-mb-md">
              <div class="text-subtitle1">Speed History (last {{ chartSessions.length }} sessions)</div>
              <q-space />
              <q-btn-toggle
                v-model="chartMetric"
                :options="[{ label: 'CPM', value: 'cpm' }, { label: 'WPM', value: 'wpm' }]"
                color="primary"
                text-color="white"
                toggle-color="deep-orange"
                unelevated
                dense
              />
            </div>
            <div v-if="chartSessions.length === 0" class="text-grey-5 text-center q-pa-md">
              No sessions yet — start typing!
            </div>
            <div v-else class="wpm-chart-wrapper" ref="chartWrapper">
              <svg
                :width="svgWidth"
                :height="svgHeight"
                class="wpm-chart"
                @mousemove="onChartMouseMove"
                @mouseleave="tooltipVisible = false"
              >
                <!-- Y-axis gridlines -->
                <g v-for="tick in yTicks" :key="tick">
                  <line
                    :x1="PADDING_LEFT"
                    :y1="yScale(tick)"
                    :x2="svgWidth - PADDING_RIGHT"
                    :y2="yScale(tick)"
                    stroke="#333"
                    stroke-width="1"
                  />
                  <text
                    :x="PADDING_LEFT - 6"
                    :y="yScale(tick) + 4"
                    text-anchor="end"
                    font-size="11"
                    fill="#666"
                  >{{ tick }}</text>
                </g>

                <!-- Line path -->
                <polyline
                  :points="linePoints"
                  fill="none"
                  stroke="#1976d2"
                  stroke-width="2"
                  stroke-linejoin="round"
                  stroke-linecap="round"
                />

                <!-- Dots -->
                <circle
                  v-for="(pt, idx) in pointCoords"
                  :key="idx"
                  :cx="pt.x"
                  :cy="pt.y"
                  r="4"
                  fill="#1976d2"
                  stroke="#121212"
                  stroke-width="1.5"
                />

                <!-- Hover tooltip line -->
                <line
                  v-if="tooltipVisible"
                  :x1="tooltipX"
                  :y1="PADDING_TOP"
                  :x2="tooltipX"
                  :y2="svgHeight - PADDING_BOTTOM"
                  stroke="#ffffff33"
                  stroke-width="1"
                  stroke-dasharray="4 2"
                />
              </svg>

              <!-- Tooltip -->
              <div
                v-if="tooltipVisible && tooltipItem"
                class="wpm-tooltip"
                :style="{ left: tooltipLeft + 'px', top: '8px' }"
              >
                <div class="text-weight-bold">{{ chartMetric === 'cpm' ? tooltipItem.cpm.toFixed(0) + ' CPM' : tooltipItem.wpm.toFixed(1) + ' WPM' }}</div>
                <div class="text-caption">{{ formatDate(tooltipItem.created_at) }}</div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- ── Keyboard Heatmap ───────────────────────── -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Error Heatmap</div>
            <div class="text-caption text-grey-5 q-mb-sm">
              Keys highlighted by error frequency. Green = few errors, Red = many errors.
            </div>
            <HeatmapChart :keyErrors="heatmap?.keys ?? {}" :layout="settings.lang as 'en' | 'ru'" />
          </q-card-section>
        </q-card>

        <!-- ── Achievements ───────────────────────────── -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Achievements</div>
            <div class="row q-col-gutter-md">
              <div
                v-for="ach in achievements"
                :key="ach.id"
                class="col-12 col-sm-6 col-md-4"
              >
                <q-card
                  class="achievement-card"
                  :class="ach.unlocked ? 'achievement-unlocked' : 'achievement-locked'"
                >
                  <q-card-section class="row items-center no-wrap">
                    <div class="achievement-icon-wrap q-mr-md">
                      <q-icon
                        :name="ach.icon"
                        size="2rem"
                        :color="ach.unlocked ? 'amber' : 'grey-7'"
                      />
                      <q-icon
                        v-if="ach.unlocked"
                        name="check_circle"
                        size="0.9rem"
                        color="positive"
                        class="achievement-badge"
                      />
                      <q-icon
                        v-else
                        name="lock"
                        size="0.9rem"
                        color="grey-6"
                        class="achievement-badge"
                      />
                    </div>
                    <div>
                      <div class="text-weight-bold" :class="ach.unlocked ? 'text-white' : 'text-grey-6'">
                        {{ ach.title }}
                      </div>
                      <div class="text-caption" :class="ach.unlocked ? 'text-grey-4' : 'text-grey-7'">
                        {{ ach.description }}
                      </div>
                      <div v-if="ach.unlocked && ach.unlocked_at" class="text-caption text-positive q-mt-xs">
                        Unlocked {{ formatDate(ach.unlocked_at) }}
                      </div>
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- ── Certificate ────────────────────────────── -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Certificate</div>

            <template v-if="certificate?.eligible">
              <div class="row items-center q-gutter-md">
                <q-chip
                  :color="tierColor(certificate.tier)"
                  text-color="white"
                  icon="emoji_events"
                  class="text-weight-bold"
                  size="lg"
                >
                  {{ certificate.tier?.toUpperCase() }} Certificate
                </q-chip>
                <div>
                  <span class="text-primary text-weight-bold">{{ certificate.wpm.toFixed(1) }} WPM</span>
                  &nbsp;·&nbsp;
                  <span class="text-positive text-weight-bold">{{ certificate.accuracy.toFixed(1) }}% accuracy</span>
                  &nbsp;·&nbsp;
                  <span class="text-grey-5">{{ certificate.language.toUpperCase() }}</span>
                  &nbsp;·&nbsp;
                  <span class="text-grey-5">{{ formatDate(certificate.date ?? '') }}</span>
                </div>
              </div>
              <q-btn
                class="q-mt-md"
                color="primary"
                icon="download"
                label="Download Certificate"
                no-caps
                @click="downloadCertificate"
              />
            </template>

            <template v-else>
              <div class="text-grey-5">
                Keep practicing! You need
                <strong class="text-white">40 WPM at 96% accuracy</strong>
                for a Silver certificate.
              </div>
              <div class="q-mt-sm text-caption text-grey-7">
                Tiers: Silver (40 WPM / 96%) · Gold (50 WPM / 97.8%) · Platinum (70 WPM / 99.5%)
              </div>
            </template>
          </q-card-section>
        </q-card>
      </template>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { statsApi } from '../api'
import type { StatsData, HeatmapData, Achievement, CertificateData } from '../types'
import HeatmapChart from '../components/HeatmapChart.vue'

const authStore = useAuthStore()
const settings = useSettingsStore()
const router = useRouter()

const loading = ref(false)
const error = ref<string | null>(null)

const stats = ref<StatsData | null>(null)
const heatmap = ref<HeatmapData | null>(null)
const achievements = ref<Achievement[]>([])
const certificate = ref<CertificateData | null>(null)

// ── SVG chart constants ──────────────────────────────────────────────────────
const PADDING_LEFT = 40
const PADDING_RIGHT = 16
const PADDING_TOP = 16
const PADDING_BOTTOM = 24
const svgWidth = ref(600)
const svgHeight = 200
const chartWrapper = ref<HTMLElement | null>(null)
const chartMetric = ref<'cpm' | 'wpm'>('cpm')

const chartSessions = computed(() => {
  if (!stats.value) return []
  return [...stats.value.sessions].reverse().slice(-30)
})

const chartValues = computed(() =>
  chartSessions.value.map((s) => chartMetric.value === 'cpm' ? s.cpm : s.wpm)
)

const maxValue = computed(() => Math.max(...chartValues.value, chartMetric.value === 'cpm' ? 50 : 10))

const yTicks = computed(() => {
  const step = chartMetric.value === 'cpm' ? 50 : 10
  const top = Math.ceil((maxValue.value + step) / step) * step
  const ticks: number[] = []
  for (let v = 0; v <= top; v += step) ticks.push(v)
  return ticks
})

function yScale(value: number): number {
  const step = chartMetric.value === 'cpm' ? 50 : 10
  const top = Math.ceil((maxValue.value + step) / step) * step
  const chartH = svgHeight - PADDING_TOP - PADDING_BOTTOM
  return PADDING_TOP + chartH - (value / top) * chartH
}

function xScale(idx: number): number {
  const chartW = svgWidth.value - PADDING_LEFT - PADDING_RIGHT
  const n = Math.max(chartSessions.value.length - 1, 1)
  return PADDING_LEFT + (idx / n) * chartW
}

const pointCoords = computed(() =>
  chartValues.value.map((v, i) => ({ x: xScale(i), y: yScale(v) }))
)

const linePoints = computed(() =>
  pointCoords.value.map((p) => `${p.x},${p.y}`).join(' ')
)

// ── Tooltip ──────────────────────────────────────────────────────────────────
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipLeft = ref(0)
const tooltipItem = ref<typeof chartSessions.value[0] | null>(null)

function onChartMouseMove(event: MouseEvent) {
  if (chartSessions.value.length === 0) return
  const rect = (event.currentTarget as SVGSVGElement).getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const chartW = svgWidth.value - PADDING_LEFT - PADDING_RIGHT
  const n = chartSessions.value.length - 1
  const idx = Math.round(((mouseX - PADDING_LEFT) / chartW) * n)
  const clampedIdx = Math.max(0, Math.min(idx, chartSessions.value.length - 1))
  tooltipItem.value = chartSessions.value[clampedIdx]
  tooltipX.value = xScale(clampedIdx)
  tooltipLeft.value = xScale(clampedIdx) + 8
  tooltipVisible.value = true
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function tierColor(tier: string | null | undefined): string {
  switch (tier) {
    case 'platinum': return 'cyan-7'
    case 'gold': return 'amber-8'
    case 'silver': return 'grey-5'
    default: return 'grey'
  }
}

function downloadCertificate() {
  if (!certificate.value) return
  const c = certificate.value
  const content = [
    '╔══════════════════════════════════════════╗',
    '║         VerseQ Typing Certificate        ║',
    '╠══════════════════════════════════════════╣',
    `║  Tier:     ${(c.tier ?? '').toUpperCase().padEnd(31)}║`,
    `║  WPM:      ${c.wpm.toFixed(1).padEnd(31)}║`,
    `║  Accuracy: ${c.accuracy.toFixed(1).padEnd(30)}%║`,
    `║  Language: ${c.language.toUpperCase().padEnd(31)}║`,
    `║  Date:     ${formatDate(c.date ?? '').padEnd(31)}║`,
    '╚══════════════════════════════════════════╝',
  ].join('\n')
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `verseq-certificate-${c.tier}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadStats() {
  if (!authStore.isAuthenticated) return
  loading.value = true
  error.value = null
  try {
    const [summaryResult, heatmapResult, achievementsResult, certificateResult] = await Promise.all([
      statsApi.getSummary(),
      statsApi.getHeatmap(),
      statsApi.getAchievements(),
      statsApi.getCertificate(),
    ])
    stats.value = summaryResult
    heatmap.value = heatmapResult
    achievements.value = achievementsResult.achievements
    certificate.value = certificateResult
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Failed to load stats'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  // Measure wrapper width for responsive SVG
  setTimeout(() => {
    if (chartWrapper.value) {
      svgWidth.value = chartWrapper.value.clientWidth || 600
    }
  }, 50)
})
</script>

<style scoped lang="scss">
.stats-page {
  max-width: 1100px;
  margin: 0 auto;
}

.summary-card {
  background: #1e1e2e;
  border: 1px solid #2a2a3e;
}

.wpm-chart-wrapper {
  position: relative;
  overflow: hidden;
}

.wpm-chart {
  display: block;
  width: 100%;
  height: 200px;
}

.wpm-tooltip {
  position: absolute;
  background: #1e1e2e;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.8rem;
  pointer-events: none;
  z-index: 10;
  color: #eee;
}

.achievement-card {
  transition: transform 0.15s;
  &:hover { transform: translateY(-2px); }
}

.achievement-unlocked {
  background: #1a2a1a;
  border: 1px solid #2d5a2d;
}

.achievement-locked {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  opacity: 0.7;
}

.achievement-icon-wrap {
  position: relative;
  flex-shrink: 0;
}

.achievement-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
}
</style>
