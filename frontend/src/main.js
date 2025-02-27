import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'

const app = createApp(App)

// Добавляем Telegram WebApp в глобальные свойства Vue
app.config.globalProperties.$telegram = window.Telegram.WebApp

app.mount('#app')

// Сообщаем Telegram, что приложение готово
window.Telegram.WebApp.ready()