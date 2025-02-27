<template>
  <div class="app">
    <header class="header">
      <h1>{{ telegramUser ? `Привет, ${telegramUser.first_name}!` : 'Загрузка...' }}</h1>
    </header>
    <main class="content">
      <p>Добро пожаловать в Telegram Mini App!</p>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      telegramUser: null
    }
  },
  mounted() {
    // Получаем данные пользователя из Telegram WebApp
    this.telegramUser = this.$telegram.initDataUnsafe?.user || null
    
    // Устанавливаем основной цвет темы Telegram
    document.documentElement.style.setProperty(
      '--tg-theme-bg-color', 
      this.$telegram.backgroundColor || '#ffffff'
    )
  }
}
</script>

<style>
.app {
  min-height: 100vh;
  background-color: var(--tg-theme-bg-color);
  padding: 16px;
}

.header {
  text-align: center;
  margin-bottom: 20px;
}

.content {
  max-width: 800px;
  margin: 0 auto;
}
</style>