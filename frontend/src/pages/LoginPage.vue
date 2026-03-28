<template>
  <q-page class="login-page column items-center justify-center q-pa-md">
    <q-card style="min-width: 380px; max-width: 420px; width: 100%" dark>
      <q-card-section class="text-center q-pb-none">
        <q-icon name="keyboard" size="2.5rem" color="primary" />
        <div class="text-h5 text-weight-bold q-mt-sm">VerseQ</div>
        <div class="text-caption text-grey-5 q-mt-xs">
          {{ isRegistering ? 'Create your account' : 'Sign in to track progress' }}
        </div>
      </q-card-section>

      <!-- Toggle tabs -->
      <q-card-section class="q-pb-none">
        <q-tabs
          v-model="activeTab"
          dense
          align="justify"
          active-color="primary"
          indicator-color="primary"
        >
          <q-tab name="login" label="Sign In" />
          <q-tab name="register" label="Register" />
        </q-tabs>
      </q-card-section>

      <q-separator dark />

      <q-card-section>
        <!-- Login form -->
        <q-form v-if="activeTab === 'login'" @submit.prevent="doLogin" class="column q-gutter-md">
          <q-input
            v-model="loginForm.username"
            dark
            outlined
            label="Username"
            autocomplete="username"
            :rules="[(v) => !!v || 'Required']"
            hide-bottom-space
          >
            <template #prepend><q-icon name="person" /></template>
          </q-input>
          <q-input
            v-model="loginForm.password"
            dark
            outlined
            label="Password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            :rules="[(v) => !!v || 'Required']"
            hide-bottom-space
          >
            <template #prepend><q-icon name="lock" /></template>
            <template #append>
              <q-icon
                :name="showPassword ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="showPassword = !showPassword"
              />
            </template>
          </q-input>

          <q-banner v-if="errorMsg" dense rounded class="bg-negative text-white q-py-sm">
            <template #avatar><q-icon name="error_outline" /></template>
            {{ errorMsg }}
          </q-banner>

          <q-btn
            type="submit"
            color="primary"
            unelevated
            label="Sign In"
            :loading="submitting"
            no-caps
          />
        </q-form>

        <!-- Register form -->
        <q-form v-else @submit.prevent="doRegister" class="column q-gutter-md">
          <q-input
            v-model="registerForm.username"
            dark
            outlined
            label="Username"
            autocomplete="username"
            :rules="[
              (v) => !!v || 'Required',
              (v) => v.length >= 3 || 'Minimum 3 characters',
            ]"
            hide-bottom-space
          >
            <template #prepend><q-icon name="person" /></template>
          </q-input>
          <q-input
            v-model="registerForm.email"
            dark
            outlined
            label="Email"
            type="email"
            autocomplete="email"
            :rules="[
              (v) => !!v || 'Required',
              (v) => /.+@.+\..+/.test(v) || 'Invalid email',
            ]"
            hide-bottom-space
          >
            <template #prepend><q-icon name="email" /></template>
          </q-input>
          <q-input
            v-model="registerForm.password"
            dark
            outlined
            label="Password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            :rules="[
              (v) => !!v || 'Required',
              (v) => v.length >= 6 || 'Minimum 6 characters',
            ]"
            hide-bottom-space
          >
            <template #prepend><q-icon name="lock" /></template>
            <template #append>
              <q-icon
                :name="showPassword ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="showPassword = !showPassword"
              />
            </template>
          </q-input>

          <q-banner v-if="errorMsg" dense rounded class="bg-negative text-white q-py-sm">
            <template #avatar><q-icon name="error_outline" /></template>
            {{ errorMsg }}
          </q-banner>

          <q-btn
            type="submit"
            color="primary"
            unelevated
            label="Create Account"
            :loading="submitting"
            no-caps
          />
        </q-form>
      </q-card-section>

      <q-card-section class="text-center q-pt-none">
        <q-btn to="/" flat dense no-caps color="grey-5" label="← Back to home" />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref<'login' | 'register'>('login')
const isRegistering = computed(() => activeTab.value === 'register')

const showPassword = ref(false)
const submitting = ref(false)
const errorMsg = ref('')

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', email: '', password: '' })

async function doLogin() {
  submitting.value = true
  errorMsg.value = ''
  try {
    await authStore.login(loginForm.value.username, loginForm.value.password)
    router.push('/practice')
  } catch (err: unknown) {
    errorMsg.value = extractErrorMsg(err, 'Invalid credentials. Please try again.')
  } finally {
    submitting.value = false
  }
}

async function doRegister() {
  submitting.value = true
  errorMsg.value = ''
  try {
    await authStore.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password
    )
    router.push('/practice')
  } catch (err: unknown) {
    errorMsg.value = extractErrorMsg(err, 'Registration failed. Please try again.')
  } finally {
    submitting.value = false
  }
}

function extractErrorMsg(err: unknown, fallback: string): string {
  if (err && typeof err === 'object') {
    const resp = (err as Record<string, unknown>).response as Record<string, unknown> | undefined
    const data = resp?.data as Record<string, unknown> | undefined
    if (data) {
      // Simple string detail (e.g. "Incorrect username or password")
      if (typeof data.detail === 'string') return data.detail
      // Pydantic validation array: [{msg: "Value error, ...", loc: [...]}]
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        const msg = (data.detail[0] as Record<string, unknown>).msg as string ?? ''
        // Strip Pydantic "Value error, " prefix
        return msg.replace(/^Value error,\s*/i, '')
      }
    }
  }
  return fallback
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
}
</style>
