import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { createCareerRouter } from './app/router'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(createCareerRouter(undefined, pinia))
app.mount('#app')
