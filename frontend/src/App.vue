<template>
  <div class="futura-app">
    <header class="futura-header">
      <div class="futura-container header-container">
        <div class="logo-container">
          <div class="logo futura-glow">
            <div class="logo-hologram pulse">
              <div class="logo-circle circle-inner"></div>
              <div class="logo-circle circle-middle"></div>
            </div>
          </div>
          <h1 class="app-title">EdTech <span class="accent-text">Futura</span></h1>
        </div>
        <nav class="main-nav">
          <router-link to="/" class="nav-link">Home</router-link>
          <router-link to="/chat" class="nav-link">Chat</router-link>
          <router-link to="/faq" class="nav-link">FAQ</router-link>
          <router-link to="/quiz" class="nav-link">Quiz</router-link>
        </nav>
      </div>
    </header>

    <main class="futura-main">
      <div class="background-elements">
        <div class="bg-circle circle-1"></div>
        <div class="bg-circle circle-2"></div>
        <div class="bg-circle circle-3"></div>
        <div class="grid-overlay"></div>
      </div>
      <div class="futura-container">
        <router-view />
      </div>
    </main>

    <footer class="futura-footer">
      <div class="futura-container">
        <p>&copy; {{ new Date().getFullYear() }} EdTech Futura. Todos os direitos reservados.</p>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
@import './assets/main.css';

.futura-app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
}

/* Header styling */
.futura-header {
  background-color: var(--bg-secondary);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--card-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(19, 26, 41, 0.8), rgba(30, 42, 69, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.logo-hologram {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo-circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid var(--accent-primary);
}

.logo .circle-inner {
  width: 12px;
  height: 12px;
  background: rgba(0, 184, 217, 0.1);
}

.logo .circle-middle {
  width: 24px;
  height: 24px;
  border: 1px dashed var(--accent-primary);
}

.app-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.main-nav {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 0;
  position: relative;
  transition: all 0.3s ease;
}

.nav-link:hover, .nav-link.router-link-active {
  color: var(--text-primary);
}

.nav-link:after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
  transition: width 0.3s ease;
}

.nav-link:hover:after, .nav-link.router-link-active:after {
  width: 100%;
}

/* Main content area */
.futura-main {
  flex: 1;
  padding: 2rem 0;
  position: relative;
  overflow: hidden;
}

/* Background elements */
.background-elements {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.1;
}

.circle-1 {
  background-color: var(--accent-primary);
  width: 500px;
  height: 500px;
  top: -200px;
  right: -100px;
}

.circle-2 {
  background-color: var(--accent-secondary);
  width: 600px;
  height: 600px;
  bottom: -300px;
  left: -200px;
}

.circle-3 {
  background-color: var(--accent-primary);
  width: 400px;
  height: 400px;
  bottom: 10%;
  right: 15%;
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 184, 217, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 184, 217, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  z-index: -1;
}

/* Footer styling */
.futura-footer {
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--card-border);
  padding: 1.5rem 0;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .main-nav {
    width: 100%;
    justify-content: space-around;
    gap: 0.5rem;
  }
}
</style> 