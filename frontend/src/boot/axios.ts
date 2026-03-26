import { boot } from 'quasar/wrappers'
import api from '../api'

// Quasar boot file for axios
// The api instance is already configured in src/api/index.ts
// This boot file can be used for any additional setup

export default boot(({ app }) => {
  // Make api available as $api on the app instance (optional)
  app.config.globalProperties.$api = api
})

export { api }
