import { store } from 'quasar/wrappers'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

/*
 * When adding new properties to stores, you should also
 * add them here so they can be type-inferred
 */
export type StateInterface = Record<string, unknown>

export default store((/* { ssrContext } */) => {
  const pinia = createPinia()
  pinia.use(piniaPluginPersistedstate)
  return pinia
})
