import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api'
import { setTokens, clearTokens } from '../tokenManager'

export const useAuthStore = defineStore(
  'auth',
  () => {
    const accessToken = ref<string | null>(null)
    const refreshToken = ref<string | null>(null)
    const user = ref<{ id: number; username: string; email: string } | null>(null)

    const isAuthenticated = computed(() => !!accessToken.value)

    // Anonymous error matrix stored in localStorage
    const anonErrorMatrix = ref<Record<string, number>>(
      JSON.parse(localStorage.getItem('verseq_error_matrix') || '{}')
    )

    function updateAnonErrorMatrix(delta: Record<string, number>) {
      for (const [bigram, count] of Object.entries(delta)) {
        anonErrorMatrix.value[bigram] = (anonErrorMatrix.value[bigram] ?? 0) + count
      }
      localStorage.setItem('verseq_error_matrix', JSON.stringify(anonErrorMatrix.value))
    }

    function getAnonWeakBigrams(): Record<string, number> {
      return Object.fromEntries(
        Object.entries(anonErrorMatrix.value)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 20)
      )
    }

    async function login(username: string, password: string): Promise<void> {
      const response = await authApi.login({ username, password })
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      setTokens(response.access_token, response.refresh_token)
      await fetchMe()
    }

    async function register(username: string, email: string, password: string): Promise<void> {
      const response = await authApi.register({ username, email, password })
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      setTokens(response.access_token, response.refresh_token)
      await fetchMe()
    }

    function logout(): void {
      accessToken.value = null
      refreshToken.value = null
      user.value = null
      clearTokens()
    }

    async function fetchMe(): Promise<void> {
      if (!accessToken.value) return
      try {
        const me = await authApi.me()
        user.value = { id: me.id, username: me.username, email: me.email }
      } catch {
        logout()
      }
    }

    function isAccessTokenValid(): boolean {
      if (!accessToken.value) return false
      try {
        const payload = JSON.parse(atob(accessToken.value.split('.')[1]!))
        if (!payload.exp) return true
        // Refresh if less than 60 seconds remain
        return payload.exp * 1000 > Date.now() + 60_000
      } catch {
        return false
      }
    }

    async function ensureFreshToken(): Promise<boolean> {
      if (isAccessTokenValid()) return true
      if (!refreshToken.value) { logout(); return false }
      try {
        const response = await authApi.refresh(refreshToken.value)
        accessToken.value = response.access_token
        refreshToken.value = response.refresh_token
        setTokens(response.access_token, response.refresh_token)
        return true
      } catch {
        logout()
        return false
      }
    }

    // When the API interceptor clears tokens (refresh failed), sync Pinia state
    if (typeof window !== 'undefined') {
      window.addEventListener('verseq:auth-expired', () => {
        accessToken.value = null
        refreshToken.value = null
        user.value = null
        clearTokens()
      })
    }

    return {
      accessToken,
      refreshToken,
      user,
      isAuthenticated,
      anonErrorMatrix,
      updateAnonErrorMatrix,
      getAnonWeakBigrams,
      login,
      register,
      logout,
      fetchMe,
      ensureFreshToken,
    }
  },
  {
    persist: {
      afterRestore: (ctx) => {
        // Seed tokenManager from persisted Pinia state on app startup
        const { accessToken: at, refreshToken: rt } = ctx.store
        if (at && rt) setTokens(at, rt)
      },
    },
  }
)
