<template>
  <q-page class="settings-page q-pa-lg">
    <div style="max-width: 600px; margin: 0 auto">
      <div class="text-h5 text-weight-bold q-mb-lg">
        <q-icon name="settings" class="q-mr-sm" />
        Settings
      </div>

      <!-- Interface Section -->
      <q-card dark flat bordered class="q-mb-md">
        <q-card-section>
          <div class="text-overline text-primary q-mb-md">Interface</div>

          <!-- Language -->
          <div class="row items-center justify-between q-mb-md">
            <div>
              <div class="text-subtitle2">Language</div>
              <div class="text-caption text-grey-5">Practice language</div>
            </div>
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
              dense
            />
          </div>

          <q-separator dark class="q-mb-md" />

          <!-- Dark mode -->
          <div class="row items-center justify-between q-mb-md">
            <div>
              <div class="text-subtitle2">Dark mode</div>
              <div class="text-caption text-grey-5">Toggle dark / light theme</div>
            </div>
            <q-toggle
              :model-value="$q.dark.isActive"
              color="primary"
              @update:model-value="$q.dark.toggle()"
            />
          </div>

          <q-separator dark class="q-mb-md" />

          <!-- Show keyboard -->
          <div class="row items-center justify-between">
            <div>
              <div class="text-subtitle2">Show keyboard</div>
              <div class="text-caption text-grey-5">Display keyboard visualization</div>
            </div>
            <q-toggle
              v-model="settings.showKeyboard"
              color="primary"
            />
          </div>
        </q-card-section>
      </q-card>

      <!-- Practice Section -->
      <q-card dark flat bordered class="q-mb-md">
        <q-card-section>
          <div class="text-overline text-primary q-mb-md">Practice</div>

          <!-- Practice mode -->
          <div class="row items-center justify-between q-mb-md">
            <div>
              <div class="text-subtitle2">Practice mode</div>
              <div class="text-caption text-grey-5">Free or adaptive text generation</div>
            </div>
            <q-select
              v-model="settings.practiceMode"
              :options="practiceModeOptions"
              emit-value
              map-options
              dense
              outlined
              dark
              style="min-width: 140px"
            />
          </div>

          <q-separator dark class="q-mb-md" />

          <!-- Text length -->
          <div class="q-mb-md">
            <div class="row items-center justify-between q-mb-sm">
              <div>
                <div class="text-subtitle2">Text length</div>
                <div class="text-caption text-grey-5">Characters per practice session</div>
              </div>
              <q-badge color="primary" outline>{{ settings.practiceLength }} chars</q-badge>
            </div>
            <q-slider
              v-model="settings.practiceLength"
              :min="100"
              :max="600"
              :step="50"
              color="primary"
              label
              :label-value="settings.practiceLength + ' ch'"
            />
            <div class="row justify-between text-caption text-grey-6">
              <span>100</span>
              <span>600</span>
            </div>
          </div>

          <q-separator dark class="q-mb-md" />

          <!-- Sound effects -->
          <div class="row items-center justify-between q-mb-md">
            <div>
              <div class="text-subtitle2">Sound effects</div>
              <div class="text-caption text-grey-5">Audio feedback on keypress</div>
            </div>
            <q-toggle
              v-model="settings.soundEnabled"
              color="primary"
            />
          </div>

          <q-separator dark class="q-mb-md" />

          <!-- Live stats -->
          <div class="row items-center justify-between q-mb-md">
            <div>
              <div class="text-subtitle2">Live stats</div>
              <div class="text-caption text-grey-5">Show WPM, CPM, accuracy and time while typing</div>
            </div>
            <q-toggle
              v-model="settings.showLiveStats"
              color="primary"
            />
          </div>

          <q-separator dark class="q-mb-md" />

          <!-- Advanced mode -->
          <div class="row items-center justify-between">
            <div>
              <div class="text-subtitle2">Advanced mode</div>
              <div class="text-caption text-grey-5">Hide keyboard hints (for experienced typists)</div>
            </div>
            <q-toggle
              v-model="settings.advancedMode"
              color="deep-orange"
            />
          </div>
        </q-card-section>
      </q-card>

      <!-- Account Section -->
      <q-card dark flat bordered class="q-mb-md">
        <q-card-section>
          <div class="text-overline text-primary q-mb-md">Account</div>

          <template v-if="authStore.isAuthenticated">
            <div class="row items-center q-mb-md">
              <q-icon name="account_circle" size="2.5rem" color="primary" class="q-mr-md" />
              <div>
                <div class="text-subtitle1 text-weight-bold">{{ authStore.user?.username }}</div>
                <div class="text-caption text-grey-5">{{ authStore.user?.email }}</div>
              </div>
            </div>
            <q-btn
              color="negative"
              unelevated
              icon="logout"
              label="Sign out"
              no-caps
              @click="logout"
            />
          </template>
          <template v-else>
            <p class="text-grey-5 q-mb-md">
              Sign in to save your progress, track stats, and sync across devices.
            </p>
            <q-btn
              color="primary"
              unelevated
              icon="login"
              label="Login / Register"
              no-caps
              to="/login"
            />
          </template>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'

const $q = useQuasar()
const router = useRouter()
const settings = useSettingsStore()
const authStore = useAuthStore()

const practiceModeOptions = [
  { label: 'Free', value: 'free' },
  { label: 'Adaptive', value: 'adaptive' },
  { label: 'Bigrams', value: 'bigrams' },
]

function logout() {
  authStore.logout()
  router.push('/')
}
</script>

<style scoped lang="scss">
.settings-page {
  min-height: 100vh;
}
</style>
