import axios, { type AxiosInstance } from 'axios'
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
  // Dynamically import to avoid circular dependency
  // Access pinia store at request time
  const token = getStoredToken()
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
      const refreshToken = getStoredRefreshToken()
      if (refreshToken) {
        try {
          const response = await authApi.refresh(refreshToken)
          setStoredToken(response.access_token)
          setStoredRefreshToken(response.refresh_token)
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`
          return api(originalRequest)
        } catch {
          clearStoredTokens()
        }
      }
    }
    return Promise.reject(error)
  }
)

// Token storage helpers (localStorage directly to avoid circular pinia imports)
function getStoredToken(): string | null {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed.accessToken ?? null
  } catch {
    return null
  }
}

function getStoredRefreshToken(): string | null {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed.refreshToken ?? null
  } catch {
    return null
  }
}

function setStoredToken(token: string): void {
  try {
    const raw = localStorage.getItem('auth')
    const parsed = raw ? JSON.parse(raw) : {}
    parsed.accessToken = token
    localStorage.setItem('auth', JSON.stringify(parsed))
  } catch {
    // ignore
  }
}

function setStoredRefreshToken(token: string): void {
  try {
    const raw = localStorage.getItem('auth')
    const parsed = raw ? JSON.parse(raw) : {}
    parsed.refreshToken = token
    localStorage.setItem('auth', JSON.stringify(parsed))
  } catch {
    // ignore
  }
}

function clearStoredTokens(): void {
  try {
    const raw = localStorage.getItem('auth')
    const parsed = raw ? JSON.parse(raw) : {}
    delete parsed.accessToken
    delete parsed.refreshToken
    delete parsed.user
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
    // OAuth2 form format
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)
    const response = await api.post<TokenResponse>('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  async me(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('/users/me')
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
