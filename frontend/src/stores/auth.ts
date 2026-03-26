import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api'

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
      await fetchMe()
    }

    async function register(username: string, email: string, password: string): Promise<void> {
      const response = await authApi.register({ username, email, password })
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      await fetchMe()
    }

    function logout(): void {
      accessToken.value = null
      refreshToken.value = null
      user.value = null
    }

    async function fetchMe(): Promise<void> {
      if (!accessToken.value) return
      try {
        const me = await authApi.me()
        user.value = { id: me.id, username: me.username, email: me.email }
      } catch {
        // token might be invalid
        logout()
      }
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
    }
  },
  { persist: true }
)
