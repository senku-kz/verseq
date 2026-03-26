<template>
  <q-page class="onboarding-page column items-center justify-center q-pa-lg">
    <q-stepper
      v-model="step"
      vertical
      color="primary"
      animated
      flat
      class="onboarding-stepper full-width"
      style="max-width: 700px"
    >
      <!-- Step 1: Welcome -->
      <q-step :name="1" title="Welcome to VerseQ" icon="keyboard" :done="step > 1">
        <div class="column items-center text-center q-py-lg">
          <div class="row items-center justify-center q-mb-md">
            <q-icon name="keyboard" size="5rem" color="primary" />
          </div>
          <div class="text-h3 text-weight-bold text-primary q-mb-sm">VerseQ</div>
          <div class="text-h6 text-grey-4 q-mb-lg">
            Master touch typing in English and Russian
          </div>
          <q-chip color="primary" text-color="white" icon="timer" class="q-mb-md">
            Takes 10–15 min/day for 2–4 weeks
          </q-chip>
          <p class="text-body1 text-grey-5" style="max-width: 480px">
            VerseQ teaches you to type without looking at your keyboard using structured lessons
            and adaptive exercises that target your weak spots.
          </p>
        </div>

        <q-stepper-navigation>
          <q-btn color="primary" label="Next" unelevated @click="step = 2" />
          <q-btn flat color="grey" label="Skip" class="q-ml-sm" @click="finish" />
        </q-stepper-navigation>
      </q-step>

      <!-- Step 2: Posture -->
      <q-step :name="2" title="Sit correctly" icon="straighten" :done="step > 2">
        <div class="column q-py-md">
          <div class="text-h5 text-weight-bold q-mb-lg">Posture matters</div>
          <q-list>
            <q-item>
              <q-item-section avatar>
                <q-icon name="chair" color="primary" size="2rem" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-subtitle1 text-weight-medium">Back straight, feet flat</q-item-label>
                <q-item-label caption>Sit upright with both feet flat on the floor</q-item-label>
              </q-item-section>
            </q-item>
            <q-separator spaced />
            <q-item>
              <q-item-section avatar>
                <q-icon name="visibility" color="secondary" size="2rem" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-subtitle1 text-weight-medium">Eyes on screen, not keyboard</q-item-label>
                <q-item-label caption>Train your muscle memory — resist looking down</q-item-label>
              </q-item-section>
            </q-item>
            <q-separator spaced />
            <q-item>
              <q-item-section avatar>
                <q-icon name="straighten" color="positive" size="2rem" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-subtitle1 text-weight-medium">Elbows at ~90°, wrists floating</q-item-label>
                <q-item-label caption>Keep elbows at a right angle; wrists should float freely</q-item-label>
              </q-item-section>
            </q-item>
            <q-separator spaced />
            <q-item>
              <q-item-section avatar>
                <q-icon name="do_not_touch" color="negative" size="2rem" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-subtitle1 text-weight-medium">Never look at your hands</q-item-label>
                <q-item-label caption>This is the most important rule — trust your fingers</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <q-stepper-navigation>
          <q-btn color="primary" label="Next" unelevated @click="step = 3" />
          <q-btn flat color="grey" label="Back" @click="step = 1" class="q-ml-sm" />
          <q-btn flat color="grey" label="Skip" class="q-ml-sm" @click="finish" />
        </q-stepper-navigation>
      </q-step>

      <!-- Step 3: Home Row -->
      <q-step :name="3" title="The home row" icon="home" :done="step > 3">
        <div class="column q-py-md">
          <div class="text-h5 text-weight-bold q-mb-sm">Your anchor: the home row</div>
          <p class="text-body1 text-grey-4 q-mb-lg">
            Always return fingers here. Feel the bumps on <strong class="text-primary">F</strong> and
            <strong class="text-primary">J</strong> — they are your anchor without looking.
          </p>

          <!-- Home row SVG visualization -->
          <div class="home-row-viz q-mb-lg">
            <div class="row justify-center q-gutter-xs">
              <div
                v-for="key in homeRowKeys"
                :key="key.char"
                class="home-key"
                :style="{ backgroundColor: key.color }"
              >
                <span class="home-key-label">{{ key.char.toUpperCase() }}</span>
                <span v-if="key.bump" class="home-key-bump" />
              </div>
            </div>
            <div class="row justify-center q-mt-xs">
              <div class="text-caption text-grey-5 text-center" style="max-width: 400px">
                Left hand: A S D F &nbsp;|&nbsp; Right hand: J K L ;
              </div>
            </div>
          </div>

          <q-banner class="bg-dark-page rounded-borders q-pa-md" rounded>
            <template #avatar>
              <q-icon name="info" color="primary" />
            </template>
            The <strong class="text-primary">F</strong> and <strong class="text-primary">J</strong>
            keys have a small raised bump so you can find the home row by touch. Your left index
            finger rests on F, your right index finger on J.
          </q-banner>
        </div>

        <q-stepper-navigation>
          <q-btn color="primary" label="Next" unelevated @click="step = 4" />
          <q-btn flat color="grey" label="Back" @click="step = 2" class="q-ml-sm" />
          <q-btn flat color="grey" label="Skip" class="q-ml-sm" @click="finish" />
        </q-stepper-navigation>
      </q-step>

      <!-- Step 4: Finger Zones -->
      <q-step :name="4" title="One finger per zone" icon="pan_tool" :done="step > 4">
        <div class="column q-py-md">
          <div class="text-h5 text-weight-bold q-mb-sm">One finger per zone</div>
          <p class="text-body1 text-grey-4 q-mb-lg">
            Each color represents one finger. Never use the wrong finger — even if it's slower.
            Consistent technique builds lasting speed.
          </p>

          <!-- Finger zone legend -->
          <div class="row q-gutter-sm q-mb-lg flex-wrap">
            <div
              v-for="finger in fingerLegend"
              :key="finger.name"
              class="finger-chip row items-center q-px-sm q-py-xs rounded-borders"
              :style="{ backgroundColor: finger.color + '33', border: '1px solid ' + finger.color }"
            >
              <div class="finger-dot q-mr-xs" :style="{ backgroundColor: finger.color }" />
              <span class="text-caption text-weight-medium">{{ finger.name }}</span>
            </div>
          </div>

          <!-- Full keyboard -->
          <KeyboardViz
            layout="en"
            next-key=""
            :error-key="null"
          />

          <p class="text-caption text-grey-6 q-mt-md text-center">
            Each color = one finger. Memorize this and your fingers will fly.
          </p>
        </div>

        <q-stepper-navigation>
          <q-btn color="positive" label="Start Practicing" icon="play_arrow" unelevated @click="finish" />
          <q-btn flat color="grey" label="Back" @click="step = 3" class="q-ml-sm" />
        </q-stepper-navigation>
      </q-step>
    </q-stepper>

    <!-- Skip link (always visible) -->
    <div class="text-right q-mt-md" style="max-width: 700px; width: 100%">
      <q-btn
        flat
        no-caps
        size="sm"
        color="grey-6"
        label="Skip intro"
        @click="finish"
      />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import KeyboardViz from '../components/KeyboardViz.vue'

const router = useRouter()
const step = ref(1)

const homeRowKeys = [
  { char: 'a', color: '#e74c3c', bump: false },
  { char: 's', color: '#e67e22', bump: false },
  { char: 'd', color: '#f1c40f', bump: false },
  { char: 'f', color: '#2ecc71', bump: true },
  { char: ' ', color: 'transparent', bump: false }, // separator
  { char: 'j', color: '#3498db', bump: true },
  { char: 'k', color: '#9b59b6', bump: false },
  { char: 'l', color: '#e91e63', bump: false },
  { char: ';', color: '#1abc9c', bump: false },
]

const fingerLegend = [
  { name: 'Left Pinky', color: '#e74c3c' },
  { name: 'Left Ring', color: '#e67e22' },
  { name: 'Left Middle', color: '#f1c40f' },
  { name: 'Left Index', color: '#2ecc71' },
  { name: 'Right Index', color: '#3498db' },
  { name: 'Right Middle', color: '#9b59b6' },
  { name: 'Right Ring', color: '#e91e63' },
  { name: 'Right Pinky', color: '#1abc9c' },
]

function finish() {
  localStorage.setItem('verseq_onboarded', 'true')
  router.push('/practice')
}
</script>

<style scoped lang="scss">
.onboarding-page {
  min-height: 100vh;
}

.onboarding-stepper {
  background: transparent;
}

.home-row-viz {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.home-key {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 8px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  position: relative;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.home-key-label {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.home-key-bump {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 3px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
}

.finger-chip {
  cursor: default;
}

.finger-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bg-dark-page {
  background: rgba(255, 255, 255, 0.05);
}
</style>
