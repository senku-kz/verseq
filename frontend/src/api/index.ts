import axios, { type AxiosInstance } from 'axios'
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from '../tokenManager'
import type {
  TextResponse,
  SessionSubmit,
  SessionResponse,
  TokenResponse,
  UserResponse,
  LessonListItem,
  LessonDetail,
  ExerciseText,
  StatsData,
  HeatmapData,
  Achievement,
  CertificateData,
  StreakData,
} from '../types'

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach Bearer token
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        try {
          const response = await authApi.refresh(refreshToken)
          setTokens(response.access_token, response.refresh_token)
          // Also sync back to Pinia's persisted localStorage so the store
          // stays consistent across page reloads
          _syncTokensToStorage(response.access_token, response.refresh_token)
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`
          return api(originalRequest)
        } catch {
          clearTokens()
          window.dispatchEvent(new CustomEvent('verseq:auth-expired'))
        }
      }
    }
    return Promise.reject(error)
  }
)

// Sync refreshed tokens back into Pinia's persisted localStorage entry so
// the Pinia store and tokenManager stay consistent across page reloads.
function _syncTokensToStorage(access: string, refresh: string): void {
  try {
    const raw = localStorage.getItem('auth')
    const parsed = raw ? JSON.parse(raw) : {}
    parsed.accessToken = access
    parsed.refreshToken = refresh
    localStorage.setItem('auth', JSON.stringify(parsed))
  } catch {
    // ignore
  }
}

// Practice API
export const practiceApi = {
  async getText(
    lang: string,
    mode: string,
    length: number,
    weakBigrams?: Record<string, number>
  ): Promise<TextResponse> {
    const params: Record<string, unknown> = { lang, mode, length }
    if (weakBigrams && Object.keys(weakBigrams).length > 0) {
      params.weak_bigrams = JSON.stringify(weakBigrams)
    }
    const response = await api.get<TextResponse>('/practice/text', { params })
    return response.data
  },
}

// Sessions API
export const sessionsApi = {
  async submit(data: SessionSubmit): Promise<SessionResponse> {
    const response = await api.post<SessionResponse>('/sessions', data)
    return response.data
  },
}

// Auth API
export const authApi = {
  async register(data: {
    username: string
    email: string
    password: string
  }): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/register', data)
    return response.data
  },

  async login(data: { username: string; password: string }): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', data)
    return response.data
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  async me(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('/auth/me')
    return response.data
  },
}

// Lessons API
export const lessonsApi = {
  async list(lang: string): Promise<LessonListItem[]> {
    const response = await api.get<LessonListItem[]>('/lessons/', {
      params: { lang },
    })
    return response.data
  },

  async get(lessonId: number, lang: string): Promise<LessonDetail> {
    const response = await api.get<LessonDetail>(`/lessons/${lessonId}`, {
      params: { lang },
    })
    return response.data
  },

  async getExerciseText(lessonId: number, exerciseId: string, lang: string): Promise<ExerciseText> {
    const response = await api.get<ExerciseText>(
      `/lessons/${lessonId}/exercises/${exerciseId}/text`,
      { params: { lang } }
    )
    return response.data
  },
}

// Stats API
export const statsApi = {
  async getSummary(lang?: string): Promise<StatsData> {
    const response = await api.get<StatsData>('/stats/', {
      params: lang ? { lang } : {},
    })
    return response.data
  },

  async getHeatmap(): Promise<HeatmapData> {
    const response = await api.get<HeatmapData>('/stats/heatmap')
    return response.data
  },

  async getAchievements(): Promise<{ achievements: Achievement[] }> {
    const response = await api.get<{ achievements: Achievement[] }>('/stats/achievements')
    return response.data
  },

  async getCertificate(): Promise<CertificateData> {
    const response = await api.get<CertificateData>('/stats/certificate')
    return response.data
  },

  async getStreak(): Promise<StreakData> {
    const response = await api.get<StreakData>('/stats/streak')
    return response.data
  },
}

export default api
