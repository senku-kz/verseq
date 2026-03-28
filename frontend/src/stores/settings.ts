import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useSettingsStore = defineStore(
  'settings',
  () => {
    const lang = ref<'en' | 'ru'>('en')
    const showKeyboard = ref(true)
    const practiceMode = ref<'free' | 'adaptive'>('free')
    const practiceLength = ref(300)
    const soundEnabled = ref(false)
    const advancedMode = ref(false)
    const showLiveStats = ref(true)

    return { lang, showKeyboard, practiceMode, practiceLength, soundEnabled, advancedMode, showLiveStats }
  },
  { persist: true }
)
