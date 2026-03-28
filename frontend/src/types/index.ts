export interface CharState {
  char: string
  state: 'pending' | 'correct' | 'error' | 'corrected'
}

export interface TypingStats {
  wpm: number
  cpm: number
  accuracy: number
  elapsedSeconds: number
  totalErrors: number
  errorMatrix: Record<string, number>
}

export interface TextResponse {
  text: string
  word_count: number
  char_count: number
  mode: string
  language: string
}

export interface SessionSubmit {
  exercise_id?: string
  language: string
  wpm: number
  cpm: number
  accuracy: number
  duration_ms: number
  error_matrix_delta: Record<string, number>
}

export interface SessionResponse {
  id: number
  wpm: number
  cpm: number
  accuracy: number
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: number
  username: string
  email: string
  created_at: string
}

export interface ExerciseProgress {
  exercise_id: string
  completed: boolean
  stars: number
  best_wpm: number
  best_accuracy: number
}

export interface ExerciseDetail {
  id: string
  title: string
  min_wpm: number
  min_accuracy: number
  target_length: number
  progress: ExerciseProgress | null
}

export interface LessonListItem {
  id: number
  title: string
  description: string
  is_unlocked: boolean
  is_completed: boolean
  stars_total: number
  exercises_completed: number
}

export interface LessonDetail extends LessonListItem {
  allowed_chars: string[]
  exercises: ExerciseDetail[]
}

export interface ExerciseText {
  text: string
  exercise_id: string
  lesson_id: number
}

export interface SessionHistoryItem {
  wpm: number
  cpm: number
  accuracy: number
  created_at: string
  language: string
}

export interface StatsData {
  sessions: SessionHistoryItem[]
  avg_wpm: number
  best_wpm: number
  avg_cpm: number
  best_cpm: number
  avg_accuracy: number
  total_sessions: number
  total_chars_typed: number
  streak_days: number
}

export interface HeatmapData {
  keys: Record<string, number>
}

export interface Achievement {
  id: string
  title: string
  description: string
  icon: string
  unlocked: boolean
  unlocked_at: string | null
}

export interface CertificateData {
  eligible: boolean
  tier: string | null
  wpm: number
  accuracy: number
  language: string
  date: string | null
}

export interface StreakData {
  current_streak: number
  longest_streak: number
}
