<template>
  <div class="faq-view">
    <div class="faq-container">
      <div class="content-card futura-card">
        <div class="faq-header">
          <h1 class="page-title">Perguntas <span class="accent-text">Frequentes</span> (FAQ)</h1>
          <p class="subtitle">Perguntas e respostas geradas automaticamente com base em emails de suporte.</p>
        </div>

        <div class="search-container">
          <input 
            type="text" 
            v-model="searchQuery" 
            class="futura-input search-input" 
            placeholder="Buscar perguntas frequentes..."
            @input="searchFAQs"
          />
          <button class="search-button futura-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </button>
        </div>

        <div class="categories-container">
          <button 
            v-for="category in categories" 
            :key="category.id"
            class="category-button"
            :class="{ active: activeCategory === category.id }"
            @click="activeCategory = category.id"
          >
            {{ category.name }}
          </button>
        </div>

        <div class="faq-content">
          <div v-if="loading" class="loading-state">
            <div class="futura-hologram hologram-ring pulse">
              <div class="hologram-circle circle-inner"></div>
              <div class="hologram-circle circle-middle"></div>
              <div class="hologram-circle circle-outer"></div>
            </div>
            <p>Carregando perguntas frequentes...</p>
          </div>
          
          <div v-else-if="filteredFaqs.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <h2>Nenhuma pergunta encontrada</h2>
            <p>Não há perguntas disponíveis nesta categoria no momento.</p>
          </div>
          
          <div v-else class="faq-list">
            <div 
              v-for="(faq, index) in filteredFaqs" 
              :key="index"
              class="faq-item"
              :class="{ 'expanded': expandedIndex === index }"
            >
              <div class="faq-question" @click="toggleFaq(index)">
                <h3>{{ faq.question }}</h3>
                <div class="expand-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline v-if="expandedIndex === index" points="18 15 12 9 6 15"></polyline>
                    <polyline v-else points="6 9 12 15 18 9"></polyline>
                  </svg>
                </div>
              </div>
              <div class="faq-answer" v-show="expandedIndex === index">
                <div class="answer-content">
                  <p>{{ faq.answer }}</p>
                </div>
                <a 
                  v-if="faq.sourceUrl" 
                  :href="faq.sourceUrl" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  class="answer-source"
                >
                  <h4>Fonte:</h4>
                  <p>{{ faq.source }}</p>
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </a>
                <div v-else class="answer-source">
                  <h4>Fonte:</h4>
                  <p>{{ faq.source || 'Conhecimento base do modelo' }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="faq-actions">
          <button @click="showGeneratorModal = true" class="futura-button">
            Gerar Nova FAQ
          </button>
        </div>
      </div>
    </div>
    
    <!-- Generator Modal -->
    <div class="modal-overlay" v-if="showGeneratorModal" @click.self="showGeneratorModal = false">
      <div class="modal-content futura-card">
        <div class="modal-header">
          <h2>Gerar FAQ a partir de e-mails</h2>
          <button class="close-button" @click="showGeneratorModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p class="modal-description">Cole as mensagens de e-mail abaixo para gerar automaticamente perguntas frequentes.</p>
          
          <textarea 
            v-model="emailContent" 
            class="futura-input email-input" 
            placeholder="Cole aqui o conteúdo dos e-mails..."
            rows="8"
          ></textarea>
          
          <div class="category-selection">
            <label>Categoria:</label>
            <select v-model="selectedCategory" class="futura-input">
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="futura-button secondary" @click="showGeneratorModal = false">Cancelar</button>
          <button 
            class="futura-button" 
            @click="generateFAQ" 
            :disabled="!emailContent.trim() || isGenerating"
          >
            <span v-if="isGenerating">Gerando...</span>
            <span v-else>Gerar FAQ</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'FaqView',
  data() {
    return {
      categories: [
        { id: 'all', name: 'Todos' },
        { id: 'python', name: 'Python' },
        { id: 'fastapi', name: 'FastAPI' },
        { id: 'streamlit', name: 'Streamlit' },
        { id: 'installation', name: 'Instalação' },
        { id: 'errors', name: 'Erros comuns' }
      ],
      activeCategory: 'all',
      faqs: [],
      expandedIndex: null,
      loading: true,
      showGeneratorModal: false,
      emailContent: '',
      selectedCategory: 'python',
      isGenerating: false,
      searchQuery: ''
    };
  },
  computed: {
    filteredFaqs() {
      let result = this.faqs;
      
      // Filter by category
      if (this.activeCategory !== 'all') {
        result = result.filter(faq => faq.category === this.activeCategory);
      }
      
      // Filter by search query
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(faq => 
          faq.question.toLowerCase().includes(query) || 
          faq.answer.toLowerCase().includes(query)
        );
      }
      
      return result;
    }
  },
  async created() {
    await this.loadFAQs();
  },
  methods: {
    async loadFAQs() {
      try {
        this.loading = true;
        // Simulating API call with a timeout for now
        // TODO: Replace with actual API call
        setTimeout(() => {
          this.faqs = [
            {
              question: 'Como faço uma requisição HTTP com Python?',
              answer: 'Você pode usar a biblioteca requests para fazer requisições HTTP em Python. Exemplo: import requests; response = requests.get("https://api.example.com/data")',
              category: 'python',
              source: 'Python Documentation - requests module',
              sourceUrl: 'https://docs.python-requests.org/en/latest/'
            },
            {
              question: 'Como criar uma rota com parâmetros no FastAPI?',
              answer: 'No FastAPI, você pode criar rotas com parâmetros usando chaves {}. Exemplo: @app.get("/items/{item_id}") def read_item(item_id: int): return {"item_id": item_id}',
              category: 'fastapi',
              source: 'FastAPI Documentation - Path Parameters',
              sourceUrl: 'https://fastapi.tiangolo.com/tutorial/path-params/'
            },
            {
              question: 'Como exibir um gráfico no Streamlit?',
              answer: 'O Streamlit oferece funções como st.line_chart(), st.bar_chart() e st.altair_chart() para visualização de dados. Exemplo: import streamlit as st; import pandas as pd; chart_data = pd.DataFrame(...); st.line_chart(chart_data)',
              category: 'streamlit',
              source: 'Streamlit Documentation - API Reference',
              sourceUrl: 'https://docs.streamlit.io/library/api-reference/charts/'
            },
            {
              question: 'Como instalar FastAPI em um ambiente virtual Python?',
              answer: 'Para instalar FastAPI em um ambiente virtual Python, primeiro crie um ambiente com "python -m venv venv", ative o ambiente e execute "pip install fastapi uvicorn[standard]".',
              category: 'installation',
              source: 'FastAPI Documentation - Installation',
              sourceUrl: 'https://fastapi.tiangolo.com/#installation'
            },
            {
              question: 'O que fazer quando recebo o erro "ModuleNotFoundError" no Python?',
              answer: 'O erro "ModuleNotFoundError" ocorre quando o Python não consegue encontrar um módulo importado. Verifique se o nome está correto e se o pacote está instalado usando "pip install nome-do-pacote".',
              category: 'errors',
              source: 'Python Documentation - Common Errors',
              sourceUrl: 'https://docs.python.org/3/tutorial/errors.html'
            }
          ];
          this.loading = false;
        }, 1500);
      } catch (error) {
        console.error('Error loading FAQs:', error);
        this.loading = false;
      }
    },
    toggleFaq(index) {
      if (this.expandedIndex === index) {
        this.expandedIndex = null;
      } else {
        this.expandedIndex = index;
      }
    },
    async generateFAQ() {
      if (!this.emailContent.trim()) return;
      
      this.isGenerating = true;
      try {
        // Simulating API call with a timeout for now
        // TODO: Replace with actual API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Add new generated FAQ items
        const newFaqs = [
          {
            question: 'Como instalo pacotes específicos de uma versão no Python?',
            answer: 'Você pode especificar a versão de um pacote usando o operador == seguido da versão desejada. Exemplo: pip install requests==2.25.1',
            category: this.selectedCategory,
            source: 'Gerado a partir de e-mails',
            sourceUrl: ''
          },
          {
            question: 'Qual é a diferença entre list e tuple em Python?',
            answer: 'Lists são mutáveis (podem ser alteradas) enquanto tuples são imutáveis (não podem ser alteradas após criação). Lists usam colchetes [] e tuples usam parênteses ().',
            category: this.selectedCategory,
            source: 'Gerado a partir de e-mails',
            sourceUrl: ''
          }
        ];
        
        this.faqs = [...this.faqs, ...newFaqs];
        this.showGeneratorModal = false;
        this.emailContent = '';
      } catch (error) {
        console.error('Error generating FAQ:', error);
      } finally {
        this.isGenerating = false;
      }
    }
  }
};
</script>

<style scoped>
.faq-view {
  min-height: calc(100vh - 180px);
  position: relative;
  overflow: hidden;
}

.faq-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 0;
  position: relative;
  z-index: 1;
}

.faq-header {
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid var(--card-border);
}

.page-title {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, var(--text-primary), var(--accent-primary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
  max-width: 600px;
  margin: 0 auto;
}

/* Content Card - Matching Quiz card style */
.content-card {
  background: var(--card-glass);
  backdrop-filter: blur(10px);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
  padding: 0;
}

.content-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, rgba(0, 184, 217, 0.1), transparent);
  z-index: -1;
}

.content-card:hover {
  box-shadow: 0 8px 32px rgba(0, 184, 217, 0.1);
  border-color: var(--accent-primary);
}

/* Search styles */
.search-container {
  display: flex;
  margin: 1.5rem;
  padding: 0.5rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--card-border);
}

.search-input {
  flex: 1;
  font-size: 1rem;
  border: none;
  outline: none;
  background: transparent;
}

.search-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  padding: 0;
}

/* Categories styles */
.categories-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin: 0 1.5rem 1.5rem;
  justify-content: center;
}

.category-button {
  padding: 0.75rem 1.25rem;
  border-radius: 50px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--card-border);
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-button:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
  box-shadow: 0 0 10px var(--accent-glow);
}

.category-button.active {
  background-color: var(--accent-glow);
  border-color: var(--accent-primary);
  color: var(--text-primary);
  box-shadow: 0 0 15px var(--accent-glow);
}

/* FAQ content styles */
.faq-content {
  padding: 0 2rem 2rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  color: var(--text-secondary);
}

.futura-hologram {
  position: relative;
  width: 150px;
  height: 150px;
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
  width: 50px;
  height: 50px;
  background: rgba(0, 184, 217, 0.05);
  animation: rotate 10s linear infinite;
}

.circle-middle {
  width: 100px;
  height: 100px;
  border: 1px dashed var(--accent-primary);
  animation: rotate 20s linear infinite reverse;
}

.circle-outer {
  width: 150px;
  height: 150px;
  border: 1px solid var(--accent-secondary);
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.empty-icon {
  color: var(--accent-primary);
  margin-bottom: 1rem;
}

.empty-state h2 {
  color: var(--text-primary);
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: var(--text-secondary);
  max-width: 400px;
}

.faq-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.faq-item {
  border: 1px solid var(--card-border);
  transition: all 0.3s ease;
  background: linear-gradient(135deg, rgba(0, 184, 217, 0.03), transparent);
  border-radius: 8px;
}

.faq-item.expanded {
  border-color: var(--accent-primary);
  box-shadow: 0 8px 32px rgba(0, 184, 217, 0.1);
  background: linear-gradient(135deg, rgba(0, 184, 217, 0.1), rgba(0, 82, 204, 0.05));
}

.faq-question {
  padding: 1.5rem;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.faq-question h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 500;
}

.expand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
}

.expanded .expand-icon {
  color: var(--accent-primary);
}

.faq-answer {
  padding: 0 1.5rem 1.5rem;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.answer-content {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.answer-source {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--card-border);
  width: auto;
  max-width: 100%;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.answer-source:hover {
  border-color: var(--accent-primary);
  background: rgba(0, 184, 217, 0.1);
}

a.answer-source {
  color: inherit;
}

a.answer-source svg {
  color: var(--accent-primary);
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

a.answer-source:hover svg {
  opacity: 1;
}

.answer-source::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: repeating-linear-gradient(
    transparent,
    transparent 5px,
    rgba(0, 184, 217, 0.03) 5px,
    rgba(0, 184, 217, 0.03) 10px
  );
  transform: rotate(30deg);
  pointer-events: none;
}

.answer-source h4 {
  margin: 0;
  font-size: 0.85rem;
  color: var(--accent-primary);
  white-space: nowrap;
}

.answer-source p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}

.faq-actions {
  display: flex;
  justify-content: center;
  padding: 2rem;
  border-top: 1px solid var(--card-border);
}

.faq-actions .futura-button {
  margin-top: 1rem;
}

.futura-button.secondary {
  background: transparent;
  border: 1px solid var(--accent-primary);
  color: var(--accent-primary);
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  width: 600px;
  max-width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: modalFadeIn 0.3s ease;
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
  box-shadow: 0 0 30px var(--accent-glow);
}

@keyframes modalFadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--card-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--accent-primary);
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
}

.close-button:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
}

.modal-description {
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

.email-input {
  width: 100%;
  resize: vertical;
  font-family: inherit;
  margin-bottom: 1.5rem;
  background-color: var(--bg-secondary);
}

.category-selection {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.category-selection label {
  color: var(--text-secondary);
}

.category-selection select {
  background-color: var(--bg-secondary);
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--card-border);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

@media (max-width: 768px) {
  .content-card {
    padding: 1.5rem 1rem;
  }

  .faq-question {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .expand-icon {
    align-self: flex-end;
  }
  
  .category-selection {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .category-selection select {
    width: 100%;
  }
}
</style> 