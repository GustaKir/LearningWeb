import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import api from './services/api'

const app = createApp(App)

// Make api available globally
app.config.globalProperties.$api = api

app.use(router)
app.mount('#app') 