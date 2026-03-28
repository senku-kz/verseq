/**
 * Single source of truth for auth tokens in memory.
 * Used by both the axios interceptor (api/index.ts) and the auth store
 * to avoid circular imports and localStorage sync issues.
 *
 * Falls back to Pinia's persisted localStorage entry ('auth') so that
 * token availability is guaranteed even before afterRestore fires.
 */

const PINIA_KEY = 'auth'

let _accessToken: string | null = null
let _refreshToken: string | null = null

function _readFromStorage(field: 'accessToken' | 'refreshToken'): string | null {
  try {
    const raw = localStorage.getItem(PINIA_KEY)
    if (!raw) return null
    return JSON.parse(raw)[field] ?? null
  } catch {
    return null
  }
}

export function getAccessToken(): string | null {
  return _accessToken ?? _readFromStorage('accessToken')
}

export function getRefreshToken(): string | null {
  return _refreshToken ?? _readFromStorage('refreshToken')
}

export function setTokens(access: string, refresh: string): void {
  _accessToken = access
  _refreshToken = refresh
}

export function clearTokens(): void {
  _accessToken = null
  _refreshToken = null
}
