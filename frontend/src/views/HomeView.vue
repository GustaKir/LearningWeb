<template>
  <div class="home-view">
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">EdTech <span class="accent-text">Futura</span></h1>
        <p class="hero-subtitle">Seu assistente de IA para programação</p>
        <div class="hero-description">
          <p>Um portal inteligente para consultas sobre Python, FastAPI e Streamlit com respostas em tempo real.</p>
        </div>
        <div class="cta-buttons">
          <router-link to="/chat" class="futura-button pulse">Iniciar Chat</router-link>
          <router-link to="/faq" class="futura-button secondary">Ver FAQ</router-link>
          <router-link to="/quiz" class="futura-button secondary">Gerar Quiz</router-link>
        </div>
      </div>
      <div class="hero-visual">
        <div class="futura-hologram hologram-ring pulse">
          <div class="hologram-circle circle-inner"></div>
          <div class="hologram-circle circle-middle"></div>
          <div class="hologram-circle circle-outer"></div>
        </div>
      </div>
    </section>

    <section class="features-section">
      <h2 class="section-title">Recursos <span class="accent-text">Inteligentes</span></h2>
      
      <div class="features-grid">
        <div class="feature-card futura-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <h3 class="feature-title">Chat Inteligente</h3>
          <p class="feature-description">Faça perguntas sobre Python, FastAPI ou Streamlit e receba respostas detalhadas com referências à documentação oficial.</p>
        </div>
        
        <div class="feature-card futura-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <h3 class="feature-title">FAQ Automatizado</h3>
          <p class="feature-description">Um FAQ automatizado para perguntas frequentes que foram geradas a partir de emails recebidos pelo nosso suporte.</p>
        </div>
        
        <div class="feature-card futura-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </div>
          <h3 class="feature-title">Quiz Inteligente</h3>
          <p class="feature-description">Crie quizzes personalizados sobre qualquer capítulo do material para uso em sala de aula.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 5rem;
  padding-bottom: 5rem;
}

/* Hero section */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  margin-top: 2rem;
}

.hero-content {
  flex: 1;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  line-height: 1.1;
  background: linear-gradient(90deg, var(--text-primary), var(--accent-primary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: var(--accent-primary);
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.hero-description {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
  max-width: 600px;
  line-height: 1.6;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
}

.cta-buttons a {
  text-decoration: none;
}

.futura-button.secondary {
  background: transparent;
  border: 1px solid var(--accent-primary);
}

.hero-visual {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  height: 400px;
}

.hologram-ring {
  position: relative;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.hologram-circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid var(--accent-primary);
}

.circle-inner {
  width: 100px;
  height: 100px;
  background: rgba(0, 184, 217, 0.05);
  animation: rotate 10s linear infinite;
}

.circle-middle {
  width: 200px;
  height: 200px;
  border: 1px dashed var(--accent-primary);
  animation: rotate 20s linear infinite reverse;
}

.circle-outer {
  width: 300px;
  height: 300px;
  border: 1px solid var(--accent-secondary);
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Features section */
.features-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section-title {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 1rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.3s ease;
  height: 100%;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, rgba(0, 184, 217, 0.2), rgba(0, 82, 204, 0.2));
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  color: var(--accent-primary);
}

.feature-title {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.feature-description {
  color: var(--text-secondary);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
  }

  .hero-content {
    order: 2;
  }

  .hero-visual {
    order: 1;
    height: 300px;
  }

  .hero-description {
    margin-left: auto;
    margin-right: auto;
  }

  .cta-buttons {
    justify-content: center;
  }
}
</style> 