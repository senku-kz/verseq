<template>
  <q-layout view="lHh Lpr lFf">
    <!-- Mobile drawer -->
    <q-drawer
      v-if="$q.screen.lt.sm"
      v-model="drawerOpen"
      side="left"
      overlay
      bordered
      :width="240"
    >
      <q-list padding>
        <q-item-label header class="text-primary text-weight-bold">VerseQ</q-item-label>

        <q-item clickable v-ripple to="/practice" @click="drawerOpen = false">
          <q-item-section avatar>
            <q-icon name="play_arrow" />
          </q-item-section>
          <q-item-section>Practice</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/course" @click="drawerOpen = false">
          <q-item-section avatar>
            <q-icon name="school" />
          </q-item-section>
          <q-item-section>Course</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/stats" @click="drawerOpen = false">
          <q-item-section avatar>
            <q-icon name="insights" />
          </q-item-section>
          <q-item-section>Stats</q-item-section>
        </q-item>

        <q-separator spaced />

        <q-item clickable v-ripple to="/settings" @click="drawerOpen = false">
          <q-item-section avatar>
            <q-icon name="settings" />
          </q-item-section>
          <q-item-section>Settings</q-item-section>
        </q-item>

        <template v-if="authStore.isAuthenticated">
          <q-item clickable v-ripple @click="logout">
            <q-item-section avatar>
              <q-icon name="logout" color="negative" />
            </q-item-section>
            <q-item-section class="text-negative">Sign Out</q-item-section>
          </q-item>
        </template>
        <template v-else>
          <q-item clickable v-ripple to="/login" @click="drawerOpen = false">
            <q-item-section avatar>
              <q-icon name="login" />
            </q-item-section>
            <q-item-section>Sign In</q-item-section>
          </q-item>
        </template>
      </q-list>
    </q-drawer>

    <q-header elevated class="bg-dark">
      <q-toolbar>
        <!-- Hamburger on mobile -->
        <q-btn
          v-if="$q.screen.lt.sm"
          flat
          round
          icon="menu"
          @click="drawerOpen = !drawerOpen"
          class="q-mr-xs"
        />

        <!-- Logo / App name -->
        <q-btn to="/" flat no-caps class="q-mr-sm">
          <q-icon name="keyboard" size="1.5rem" color="primary" class="q-mr-xs" />
          <span class="text-h6 text-weight-bold text-primary">VerseQ</span>
        </q-btn>

        <!-- Language badge -->
        <q-badge
          :color="settings.lang === 'en' ? 'blue' : 'deep-orange'"
          class="q-mr-sm text-weight-bold"
          style="font-size: 0.75rem; padding: 4px 8px"
        >
          {{ settings.lang.toUpperCase() }}
        </q-badge>

        <q-separator dark vertical inset class="q-mx-sm" v-if="!$q.screen.lt.sm" />

        <!-- Nav links (desktop only) -->
        <q-tabs v-if="!$q.screen.lt.sm" dense align="left" class="q-mx-sm">
          <q-route-tab to="/practice" label="Practice" icon="play_arrow" no-caps />
          <q-route-tab to="/course" label="Course" icon="school" no-caps />
          <q-route-tab to="/stats" label="Stats" icon="insights" no-caps />
        </q-tabs>

        <q-space />

        <!-- Streak indicator (authenticated + streak > 0) -->
        <div v-if="authStore.isAuthenticated && streak > 0" class="row items-center q-mr-md">
          <span style="font-size: 1rem">🔥</span>
          <span class="text-weight-bold text-orange q-ml-xs">{{ streak }}</span>
        </div>

        <!-- Settings icon (desktop) -->
        <q-btn
          v-if="!$q.screen.lt.sm"
          to="/settings"
          flat
          round
          icon="settings"
          size="sm"
          class="q-mr-xs"
        >
          <q-tooltip>Settings</q-tooltip>
        </q-btn>

        <!-- User menu (desktop) -->
        <template v-if="!$q.screen.lt.sm">
          <template v-if="authStore.isAuthenticated">
            <q-btn-dropdown flat no-caps :label="authStore.user?.username ?? 'User'" icon="account_circle">
              <q-list>
                <q-item clickable v-close-popup to="/stats">
                  <q-item-section avatar>
                    <q-icon name="insights" />
                  </q-item-section>
                  <q-item-section>My Stats</q-item-section>
                </q-item>
                <q-item clickable v-close-popup to="/settings">
                  <q-item-section avatar>
                    <q-icon name="settings" />
                  </q-item-section>
                  <q-item-section>Settings</q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable v-close-popup @click="logout">
                  <q-item-section avatar>
                    <q-icon name="logout" color="negative" />
                  </q-item-section>
                  <q-item-section class="text-negative">Sign Out</q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </template>
          <template v-else>
            <q-btn
              to="/login"
              flat
              no-caps
              icon="login"
              label="Sign In"
            />
          </template>
        </template>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { statsApi } from '../api'

const $q = useQuasar()
const authStore = useAuthStore()
const settings = useSettingsStore()
const router = useRouter()

const drawerOpen = ref(false)
const streak = ref(0)

// Redirect to onboarding on first visit
onMounted(async () => {
  const onboarded = localStorage.getItem('verseq_onboarded')
  if (!onboarded && router.currentRoute.value.path === '/') {
    router.push('/onboarding')
  }

  // Fetch streak if authenticated
  if (authStore.isAuthenticated) {
    try {
      const data = await statsApi.getStreak()
      streak.value = data.current_streak
    } catch {
      // ignore
    }
  }
})

function logout() {
  authStore.logout()
  drawerOpen.value = false
  router.push('/')
}
</script>
