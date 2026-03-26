<template>
  <q-page class="landing-page column items-center justify-center q-pa-xl">
    <div class="text-center q-mb-xl">
      <!-- Logo / Name -->
      <div class="row items-center justify-center q-mb-md">
        <q-icon name="keyboard" size="4rem" color="primary" />
        <span class="text-h2 text-weight-bold q-ml-sm text-primary">VerseQ</span>
      </div>

      <p class="text-h6 text-grey-5 q-mb-xl">
        Train touch typing in English and Russian
      </p>

      <!-- CTA Buttons -->
      <div class="row justify-center q-gutter-md">
        <q-btn
          v-if="isOnboarded"
          to="/practice"
          color="primary"
          unelevated
          size="lg"
          icon="play_arrow"
          label="Continue Practicing"
          no-caps
        />
        <q-btn
          v-else
          to="/onboarding"
          color="primary"
          unelevated
          size="lg"
          icon="play_arrow"
          label="Get Started"
          no-caps
        />
        <q-btn
          color="grey-7"
          unelevated
          size="lg"
          icon="school"
          label="Take a Course"
          no-caps
          disabled
        >
          <q-tooltip>Coming soon!</q-tooltip>
        </q-btn>
      </div>

      <!-- Auth links -->
      <div class="q-mt-xl text-body2">
        <template v-if="!authStore.isAuthenticated">
          <span class="text-grey-5">Track your progress — </span>
          <router-link to="/login" class="text-primary">Sign in</router-link>
          <span class="text-grey-5"> or </span>
          <router-link to="/login" class="text-primary">Create account</router-link>
        </template>
        <template v-else>
          <span class="text-grey-5">Welcome back, </span>
          <span class="text-primary text-weight-bold">{{ authStore.user?.username }}</span>
          <span class="text-grey-5">! </span>
          <router-link to="/stats" class="text-primary">View your stats →</router-link>
        </template>
      </div>
    </div>

    <!-- Feature highlights -->
    <div class="row q-gutter-lg justify-center q-mt-xl">
      <q-card dark flat bordered class="feature-card">
        <q-card-section class="text-center">
          <q-icon name="language" size="2rem" color="primary" class="q-mb-sm" />
          <div class="text-subtitle1 text-weight-bold">Bilingual</div>
          <div class="text-caption text-grey-5">English & Russian</div>
        </q-card-section>
      </q-card>
      <q-card dark flat bordered class="feature-card">
        <q-card-section class="text-center">
          <q-icon name="psychology" size="2rem" color="secondary" class="q-mb-sm" />
          <div class="text-subtitle1 text-weight-bold">Adaptive</div>
          <div class="text-caption text-grey-5">Targets your weak spots</div>
        </q-card-section>
      </q-card>
      <q-card dark flat bordered class="feature-card">
        <q-card-section class="text-center">
          <q-icon name="insights" size="2rem" color="positive" class="q-mb-sm" />
          <div class="text-subtitle1 text-weight-bold">Analytics</div>
          <div class="text-caption text-grey-5">Track WPM & accuracy</div>
        </q-card-section>
      </q-card>
    </div>

    <!-- How it works section -->
    <div class="how-it-works q-mt-xl q-pt-xl full-width" style="max-width: 700px">
      <div class="text-h5 text-weight-bold text-center q-mb-xl">How it works</div>
      <div class="row q-gutter-lg justify-center">
        <div class="how-step text-center">
          <div class="how-step-number bg-primary">1</div>
          <q-icon name="school" size="2rem" color="primary" class="q-my-sm" />
          <div class="text-subtitle1 text-weight-bold">Learn</div>
          <div class="text-caption text-grey-5">Start with the home row. Each lesson introduces new keys one at a time.</div>
        </div>
        <div class="how-step text-center">
          <div class="how-step-number bg-secondary">2</div>
          <q-icon name="keyboard" size="2rem" color="secondary" class="q-my-sm" />
          <div class="text-subtitle1 text-weight-bold">Practice</div>
          <div class="text-caption text-grey-5">Type real words and sentences. Adaptive mode focuses on your mistakes.</div>
        </div>
        <div class="how-step text-center">
          <div class="how-step-number bg-positive">3</div>
          <q-icon name="trending_up" size="2rem" color="positive" class="q-my-sm" />
          <div class="text-subtitle1 text-weight-bold">Improve</div>
          <div class="text-caption text-grey-5">Track your WPM and accuracy. Most users reach 50+ WPM in 4 weeks.</div>
        </div>
      </div>

      <div class="text-center q-mt-xl">
        <q-chip icon="emoji_events" color="primary" text-color="white" class="text-body2">
          Average typist reaches 50+ WPM after just 4 weeks of daily practice
        </q-chip>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const isOnboarded = computed(() => !!localStorage.getItem('verseq_onboarded'))
</script>

<style scoped lang="scss">
.landing-page {
  min-height: 100vh;
}

.feature-card {
  width: 150px;
}

.how-it-works {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.how-step {
  flex: 1;
  min-width: 160px;
  max-width: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.how-step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
}
</style>
