<template>
  <div class="quiz-view">
    <div class="quiz-container">
      <div v-if="!activeQuiz" class="quiz-generator content-card futura-card">
        <div class="generator-header">
          <h1>Gerar <span class="accent-text">Quiz</span> Personalizado</h1>
          <p class="generator-description">
            Crie um quiz sobre qualquer tópico da documentação de Python, FastAPI ou Streamlit.
          </p>
        </div>
        
        <div class="generator-form">
          <div class="form-group">
            <label for="topic">Tema escolhido</label>
            <div class="input-wrapper">
              <input 
                id="topic" 
                v-model="quizTopic" 
                type="text" 
                class="futura-input" 
                placeholder="Ex: Funções Decoradoras em Python"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="questions">Número de Perguntas</label>
              <div class="quantity-selector">
                <button 
                  class="quantity-btn" 
                  @click="questionCount = Math.max(1, questionCount - 1)"
                  type="button"
                >
                  -
                </button>
                <input 
                  id="questions" 
                  v-model="questionCount" 
                  type="number" 
                  min="1" 
                  max="10" 
                  class="futura-input quantity-input"
                />
                <button 
                  class="quantity-btn" 
                  @click="questionCount = Math.min(10, questionCount + 1)"
                  type="button"
                >
                  +
                </button>
              </div>
            </div>
            
            <div class="form-group">
              <label for="difficulty">Dificuldade</label>
              <div class="select-wrapper">
                <select id="difficulty" v-model="difficulty" class="futura-input">
                  <option value="beginner">Iniciante</option>
                  <option value="intermediate">Intermediário</option>
                  <option value="advanced">Avançado</option>
                </select>
              </div>
            </div>
          </div>
          
          <div class="limited-divider"></div>
        </div>
        
        <div class="suggested-topics-section">
          <div class="suggested-topics">
            <h3>Tópicos sugeridos</h3>
            <div class="topic-chips">
              <button 
                v-for="topic in suggestedTopics" 
                :key="topic"
                class="topic-chip"
                @click="quizTopic = topic"
              >
                {{ topic }}
              </button>
            </div>
          </div>
        </div>
        
        <div class="form-actions">
          <button 
            class="futura-button" 
            @click="generateQuiz" 
            :disabled="!quizTopic || isGenerating"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span v-if="isGenerating">Gerando quiz...</span>
            <span v-else>Gerar Quiz</span>
          </button>
        </div>
        
        <div v-if="lastError" class="error-message">
          <div class="error-title">Erro ao gerar quiz:</div>
          <div class="error-details">{{ lastError }}</div>
          <button class="error-dismiss" @click="lastError = null">X</button>
        </div>
      </div>
      
      <div v-else class="active-quiz content-card futura-card">
        <div class="quiz-header">
          <h2>Quiz: {{ activeQuiz.title }}</h2>
          <div class="quiz-progress">
            <div class="progress-text">
              Pergunta {{ currentQuestionIndex + 1 }} de {{ activeQuiz.questions.length }}
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${((currentQuestionIndex + 1) / activeQuiz.questions.length) * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
        
        <div v-if="!quizCompleted" class="question-container">
          <div class="current-question futura-hologram">
            <h3>{{ currentQuestion.question }}</h3>
          </div>
          
          <div class="answer-options">
            <div 
              v-for="(option, index) in currentQuestion.options" 
              :key="index"
              class="answer-option"
              :class="{
                'selected': selectedAnswer === index,
                'correct': showFeedback && index === currentQuestion.correctIndex,
                'incorrect': showFeedback && selectedAnswer === index && index !== currentQuestion.correctIndex
              }"
              @click="selectAnswer(index)"
            >
              <div class="option-letter">{{ ['A', 'B', 'C', 'D'][index] }}</div>
              <div class="option-text">{{ option }}</div>
            </div>
          </div>
          
          <div v-if="showFeedback" class="feedback-container">
            <div class="feedback-content futura-card" :class="isCorrect ? 'correct-feedback' : 'incorrect-feedback'">
              <div class="feedback-icon">
                <svg v-if="isCorrect" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
              </div>
              <div class="feedback-message">
                <h4>{{ isCorrect ? 'Correto!' : 'Incorreto!' }}</h4>
                <p>{{ currentQuestion.explanation }}</p>
              </div>
            </div>
          </div>
          
          <div class="question-actions">
            <button 
              v-if="!showFeedback" 
              class="futura-button check-btn" 
              @click="checkAnswer"
              :disabled="selectedAnswer === null"
            >
              Verificar Resposta
            </button>
            <button 
              v-else 
              class="futura-button next-btn" 
              @click="nextQuestion"
            >
              {{ isLastQuestion ? 'Ver Resultados' : 'Próxima Pergunta' }}
            </button>
          </div>
        </div>
        
        <div v-else class="quiz-results">
          <div class="results-header">
            <div class="futura-hologram hologram-ring pulse">
              <div class="hologram-circle circle-inner"></div>
              <div class="hologram-circle circle-middle"></div>
            </div>
            <h2>Quiz Concluído!</h2>
            <p class="score-display">
              Pontuação: <span class="accent-text">{{ score }}</span> de {{ activeQuiz.questions.length }}
            </p>
          </div>
          
          <div class="results-details">
            <h3>Desempenho por Pergunta</h3>
            <div class="question-results">
              <div 
                v-for="(answer, index) in userAnswers" 
                :key="index"
                class="question-result futura-card"
                :class="{ 'correct': answer.isCorrect, 'expanded': expandedResults[index] }"
              >
                <div class="result-header" @click="toggleResultExpand(index)">
                  <div class="result-status">
                    <svg v-if="answer.isCorrect" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                      <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="15" y1="9" x2="9" y2="15"></line>
                      <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                    <span>Pergunta {{ index + 1 }}</span>
                  </div>
                  <button type="button" class="expand-btn">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline v-if="expandedResults[index]" points="18 15 12 9 6 15"></polyline>
                      <polyline v-else points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>
                </div>
                <transition name="slide-fade">
                  <div v-show="expandedResults[index]" class="result-details">
                    <p class="result-question">{{ activeQuiz.questions[index].question }}</p>
                    <p class="result-answer">
                      <span class="label">Sua resposta:</span> 
                      {{ activeQuiz.questions[index].options[answer.selectedIndex] }}
                    </p>
                    <p v-if="!answer.isCorrect" class="result-correct">
                      <span class="label">Resposta correta:</span> 
                      {{ activeQuiz.questions[index].options[activeQuiz.questions[index].correctIndex] }}
                    </p>
                    <p class="result-explanation">
                      <span class="label">Explicação:</span>
                      {{ activeQuiz.questions[index].explanation }}
                    </p>
                  </div>
                </transition>
              </div>
            </div>
          </div>
          
          <div class="results-actions">
            <button class="futura-button secondary" @click="resetQuiz">Novo Quiz</button>
            <button class="futura-button" @click="restartQuiz">Tentar Novamente</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api';

export default {
  name: 'QuizView',
  data() {
    return {
      // Quiz generator
      quizTopic: '',
      questionCount: 5,
      difficulty: 'intermediate',
      isGenerating: false,
      lastError: null,
      
      // Active quiz
      activeQuiz: null,
      currentQuestionIndex: 0,
      selectedAnswer: null,
      showFeedback: false,
      userAnswers: [],
      quizCompleted: false,
      expandedResults: {},
      
      // Suggested topics
      suggestedTopics: [
        'List Comprehension em Python',
        'Classes e Herança em Python',
        'Dependências e Injeção de Dependência no FastAPI',
        'Criação de APIs RESTful com FastAPI',
        'Widgets Interativos no Streamlit',
        'Visualização de Dados com Streamlit'
      ]
    };
  },
  computed: {
    currentQuestion() {
      if (!this.activeQuiz) return null;
      return this.activeQuiz.questions[this.currentQuestionIndex];
    },
    isLastQuestion() {
      if (!this.activeQuiz) return false;
      return this.currentQuestionIndex === this.activeQuiz.questions.length - 1;
    },
    isCorrect() {
      if (!this.showFeedback || this.selectedAnswer === null) return false;
      return this.selectedAnswer === this.currentQuestion.correctIndex;
    },
    score() {
      return this.userAnswers.filter(answer => answer.isCorrect).length;
    }
  },
  methods: {
    async generateQuiz() {
      if (!this.quizTopic.trim() || this.isGenerating) return;
      
      this.isGenerating = true;
      this.lastError = null; // Clear previous errors
      console.log(`Starting quiz generation for topic: "${this.quizTopic}"`);
      
      try {
        // Log request parameters
        const requestData = {
          topic: this.quizTopic,
          num_questions: this.questionCount,
          num_alternatives: 4
        };
        console.log('Quiz API request:', requestData);
        
        // Call the backend RAG service API
        console.log('Sending request to /quiz/generate endpoint...');
        const response = await api.post('/quiz/generate', requestData);
        
        console.log('Quiz API response received:', response);
        
        // Check if we received a valid response
        if (!response.data) {
          throw new Error('Resposta vazia recebida do servidor.');
        }
        
        // Check if the quiz has questions
        if (!response.data.questions || response.data.questions.length === 0) {
          throw new Error('O quiz foi gerado, mas não contém perguntas. Por favor, tente novamente com outro tópico.');
        }
        
        // Process the quiz data to match frontend format
        const processedQuiz = this.processQuizData(response.data);
        console.log('Processed quiz data:', processedQuiz);
        
        // Verify we have valid questions after processing
        if (!processedQuiz.questions || processedQuiz.questions.length === 0) {
          throw new Error('Erro ao processar as perguntas do quiz. Por favor, tente novamente.');
        }
        
        // Set the active quiz
        this.activeQuiz = processedQuiz;
        
        // Reset quiz state
        this.currentQuestionIndex = 0;
        this.selectedAnswer = null;
        this.showFeedback = false;
        this.userAnswers = [];
        this.quizCompleted = false;
        this.expandedResults = {};
        
      } catch (error) {
        console.error('Error generating quiz:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
          this.lastError = `Erro ${error.response.status}: ${error.response.data.detail || JSON.stringify(error.response.data)}`;
        } else if (error.code === 'ECONNABORTED') {
          this.lastError = 'A geração do quiz demorou muito tempo e atingiu o timeout. Por favor, tente novamente ou escolha um tópico mais específico.';
        } else {
          this.lastError = error.message || 'Ocorreu um erro desconhecido.';
        }
        alert('Não foi possível gerar o quiz. Por favor, tente novamente.');
      } finally {
        this.isGenerating = false;
      }
    },
    
    processQuizData(quizData) {
      console.log('Processing quiz data:', JSON.stringify(quizData));
      
      try {
        // Create a new quiz object with the correct structure
        const processedQuiz = {
          id: quizData.id,
          title: quizData.title || `Quiz sobre ${quizData.topic}`,
          topic: quizData.topic,
          created_at: quizData.created_at,
          questions: []
        };
        
        // Process each question
        if (quizData.questions && quizData.questions.length > 0) {
          console.log(`Processing ${quizData.questions.length} questions`);
          
          processedQuiz.questions = quizData.questions.map((q, index) => {
            console.log(`Processing question ${index + 1}:`, q);
            
            try {
              // Find the correct alternative
              const correctIndex = q.alternatives.findIndex(alt => alt.is_correct);
              console.log(`Question ${index + 1} correct index:`, correctIndex);
              
              if (correctIndex === -1) {
                console.warn(`No correct alternative found for question ${index + 1}. Setting first as correct.`);
              }
              
              // Map alternatives to options
              const options = q.alternatives.map(alt => alt.text);
              
              return {
                id: q.id,
                question: q.question_text,
                explanation: q.explanation,
                options: options,
                correctIndex: correctIndex >= 0 ? correctIndex : 0, // Default to first if none marked correct
                // Store the original alternatives for reference
                originalAlternatives: q.alternatives
              };
            } catch (qError) {
              console.error(`Error processing question ${index + 1}:`, qError);
              // Return a default question to prevent the entire quiz from failing
              return {
                id: q.id || index + 1,
                question: q.question_text || "Erro ao carregar pergunta",
                explanation: "Houve um erro ao processar esta pergunta.",
                options: ["Opção A", "Opção B", "Opção C", "Opção D"],
                correctIndex: 0,
                originalAlternatives: []
              };
            }
          });
        } else {
          console.error('No questions found in quiz data:', quizData);
        }
        
        console.log('Processed quiz:', processedQuiz);
        return processedQuiz;
      } catch (error) {
        console.error('Error processing quiz data:', error);
        // Return a minimal valid quiz structure to prevent UI errors
        return {
          id: 0,
          title: 'Erro ao processar quiz',
          topic: quizData.topic || 'Desconhecido',
          created_at: new Date().toISOString(),
          questions: [{
            id: 1,
            question: 'Ocorreu um erro ao processar o quiz. Por favor, tente novamente.',
            explanation: 'Erro técnico.',
            options: ['Tentar novamente'],
            correctIndex: 0
          }]
        };
      }
    },
    selectAnswer(index) {
      if (this.showFeedback) return; // Prevent changing answer after checking
      this.selectedAnswer = index;
    },
    checkAnswer() {
      if (this.selectedAnswer === null) return;
      
      this.showFeedback = true;
      const isCorrect = this.selectedAnswer === this.currentQuestion.correctIndex;
      
      // Record user's answer
      this.userAnswers.push({
        selectedIndex: this.selectedAnswer,
        isCorrect
      });
    },
    nextQuestion() {
      if (this.isLastQuestion) {
        this.completeQuiz();
        return;
      }
      
      this.currentQuestionIndex++;
      this.selectedAnswer = null;
      this.showFeedback = false;
    },
    completeQuiz() {
      this.quizCompleted = true;
      
      // Create a fresh expandedResults object
      const newExpandedResults = {};
      
      // Initialize all results as collapsed
      this.userAnswers.forEach((_, index) => {
        newExpandedResults[index] = false;
      });
      
      // Replace the entire object for better reactivity
      this.expandedResults = newExpandedResults;
      
      console.log('Quiz completed, expandedResults initialized:', this.expandedResults);
    },
    toggleResultExpand(index) {
      console.log(`Toggling question ${index} expansion state:`, 
        `Current state = ${this.expandedResults[index] ? 'expanded' : 'collapsed'}`);
      
      // Create a new object with the updated state for better reactivity
      const updatedResults = { ...this.expandedResults };
      updatedResults[index] = !updatedResults[index];
      
      // Replace the entire object
      this.expandedResults = updatedResults;
      
      console.log(`Question ${index} expansion updated to: ${this.expandedResults[index] ? 'expanded' : 'collapsed'}`);
    },
    resetQuiz() {
      this.activeQuiz = null;
      this.quizTopic = '';
      this.currentQuestionIndex = 0;
      this.selectedAnswer = null;
      this.showFeedback = false;
      this.userAnswers = [];
      this.quizCompleted = false;
    },
    restartQuiz() {
      this.currentQuestionIndex = 0;
      this.selectedAnswer = null;
      this.showFeedback = false;
      this.userAnswers = [];
      this.quizCompleted = false;
    }
  }
};
</script>

<style scoped>
.quiz-view {
  min-height: calc(100vh - 180px);
}

.quiz-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 0;
}

/* Content Card - Matching FAQ card style */
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

/* Quiz Generator */
.quiz-generator {
  overflow: hidden;
  position: relative;
}

.generator-header {
  margin: 0;
  text-align: center;
  padding: 2rem;
  border-bottom: 1px solid var(--card-border);
}

.generator-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, var(--text-primary), var(--accent-primary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.generator-description {
  color: var(--text-secondary);
  font-size: 1.1rem;
  max-width: 600px;
  margin: 0 auto;
}

.generator-form {
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem 2rem 0;
}

.form-group {
  margin-bottom: 2rem;
  text-align: center;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.input-wrapper {
  display: flex;
  justify-content: center;
  max-width: 500px;
  margin: 0 auto;
  padding: 0.5rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--card-border);
}

.select-wrapper {
  display: flex;
  justify-content: center;
  width: 180px;
  margin: 0 auto;
  padding: 0;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--card-border);
  overflow: hidden;
  height: 40px;
}

.input-wrapper:focus-within, .select-wrapper:focus-within {
  border-color: var(--accent-primary);
  box-shadow: 0 0 10px var(--accent-glow);
}

.futura-input {
  flex: 1;
  font-size: 1rem;
  border: none;
  outline: none;
  background: transparent;
  max-width: 100%;
  text-align: center;
}

.form-row {
  display: flex;
  gap: 2rem;
  margin-bottom: 2.5rem;
  justify-content: center;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.quantity-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--card-border);
  width: 180px;
  margin: 0 auto;
  overflow: hidden;
  height: 40px;
}

.quantity-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.quantity-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--accent-primary);
}

.quantity-input {
  width: 100px;
  text-align: center;
  margin: 0;
  border-left: 1px solid var(--card-border);
  border-right: 1px solid var(--card-border);
  height: 40px;
  padding: 0;
  flex: 1;
  line-height: 40px;
  font-size: 1rem;
  -moz-appearance: textfield;
}

.quantity-input::-webkit-outer-spin-button,
.quantity-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

select.futura-input {
  width: 100%;
  height: 40px;
  padding: 0 30px 0 10px;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="%239fa6b2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>');
  background-repeat: no-repeat;
  background-position: right 10px center;
  cursor: pointer;
}

select.futura-input option {
  color: black;
  background-color: white;
  padding: 10px;
}

select.futura-input:hover option:hover {
  background-color: var(--accent-glow);
  color: var(--text-primary);
}

.limited-divider {
  height: 1px;
  background-color: var(--card-border);
  width: 100%;
  margin: 2.5rem auto;
}

.suggested-topics-section {
  padding: 0 2rem;
}

.suggested-topics {
  text-align: center;
  max-width: 700px;
  margin: 0 auto;
}

.suggested-topics h3 {
  font-size: 1.2rem;
  margin-bottom: 1.5rem;
  color: var(--accent-primary);
}

.topic-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  margin: 0 auto 2.5rem;
}

.topic-chip {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--card-border);
  border-radius: 50px;
  padding: 0.75rem 1.25rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
}

.topic-chip:hover {
  background-color: var(--bg-secondary);
  border-color: var(--accent-primary);
  color: var(--text-primary);
  box-shadow: 0 0 10px var(--accent-glow);
}

.form-actions {
  display: flex;
  justify-content: center;
  padding: 2rem;
  border-top: 1px solid var(--card-border);
}

.form-actions .futura-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spin-icon {
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Active Quiz */
.active-quiz {
  overflow: hidden;
}

.quiz-header {
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid var(--card-border);
}

.quiz-header h2 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  background: linear-gradient(90deg, var(--text-primary), var(--accent-primary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.quiz-progress {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.progress-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.progress-bar {
  height: 6px;
  background-color: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Question Container */
.question-container {
  padding: 2rem;
}

.current-question {
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: center;
  border-radius: 8px;
  border: 1px solid var(--card-border);
  background: rgba(0, 184, 217, 0.05);
}

.current-question h3 {
  margin: 0;
  font-size: 1.25rem;
  line-height: 1.5;
}

.answer-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.answer-option {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.answer-option:hover {
  background-color: var(--bg-tertiary);
  border-color: var(--accent-primary);
  box-shadow: 0 0 10px var(--accent-glow);
}

.answer-option.selected {
  background-color: rgba(0, 184, 217, 0.1);
  border-color: var(--accent-primary);
  box-shadow: 0 0 15px var(--accent-glow);
}

.answer-option.correct {
  background-color: rgba(45, 212, 191, 0.1);
  border-color: var(--success);
}

.answer-option.incorrect {
  background-color: rgba(244, 63, 94, 0.1);
  border-color: var(--error);
}

.option-letter {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-tertiary);
  border-radius: 50%;
  margin-right: 1rem;
  font-weight: bold;
}

.selected .option-letter, .correct .option-letter {
  background-color: var(--accent-primary);
  color: white;
}

.incorrect .option-letter {
  background-color: var(--error);
  color: white;
}

.option-text {
  flex: 1;
}

.feedback-container {
  margin-bottom: 2rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.feedback-content {
  display: flex;
  padding: 1.5rem;
}

.correct-feedback {
  border-left: 4px solid var(--success);
}

.incorrect-feedback {
  border-left: 4px solid var(--error);
}

.feedback-icon {
  margin-right: 1rem;
}

.correct-feedback .feedback-icon {
  color: var(--success);
}

.incorrect-feedback .feedback-icon {
  color: var(--error);
}

.feedback-message h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
}

.correct-feedback .feedback-message h4 {
  color: var(--success);
}

.incorrect-feedback .feedback-message h4 {
  color: var(--error);
}

.feedback-message p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.question-actions {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--card-border);
}

.check-btn, .next-btn {
  min-width: 180px;
}

/* Quiz Results */
.quiz-results {
  padding: 2rem;
}

.results-header {
  text-align: center;
  margin-bottom: 3rem;
}

.results-header h2 {
  margin: 1rem 0 0.5rem;
  font-size: 2rem;
  background: linear-gradient(90deg, var(--text-primary), var(--accent-primary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.score-display {
  font-size: 1.25rem;
}

.results-details {
  margin-bottom: 3rem;
}

.results-details h3 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  text-align: center;
  color: var(--accent-primary);
}

.question-results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.question-result {
  margin-bottom: 1rem;
  overflow: hidden;
  transition: all 0.3s ease;
}

.question-result.correct {
  border-left: 4px solid var(--success);
}

.question-result:not(.correct) {
  border-left: 4px solid var(--error);
}

.question-result.expanded {
  box-shadow: 0 8px 32px rgba(0, 184, 217, 0.2);
}

.result-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background-color: var(--bg-secondary);
  transition: background-color 0.2s ease;
  border-bottom: 1px solid transparent;
}

.expanded .result-header {
  border-bottom-color: var(--card-border);
}

.result-header:hover {
  background-color: var(--bg-tertiary);
}

.result-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.correct .result-status svg {
  color: var(--success);
}

.question-result:not(.correct) .result-status svg {
  color: var(--error);
}

.expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.expanded .expand-btn {
  transform: rotate(180deg);
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
  opacity: 1;
  overflow: hidden;
}

.slide-fade-enter-from, .slide-fade-leave-to {
  max-height: 0;
  opacity: 0;
  padding: 0 1rem;
  overflow: hidden;
}

.result-details {
  padding: 1rem;
  background-color: var(--bg-primary);
  border-radius: 0 0 8px 8px;
}

.result-question {
  font-weight: 500;
  margin-bottom: 1rem;
}

.result-answer, .result-correct, .result-explanation {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.label {
  font-weight: 500;
  color: var(--text-primary);
}

.results-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  padding-top: 2rem;
  margin-top: 2rem;
  border-top: 1px solid var(--card-border);
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .quiz-container, .question-container, .quiz-results {
    padding: 1rem;
  }
  
  .feedback-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .feedback-icon {
    margin-right: 0;
    margin-bottom: 0.5rem;
  }
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 0.25rem;
  position: relative;
}

.error-title {
  font-weight: bold;
  color: #dc3545;
  margin-bottom: 0.5rem;
}

.error-details {
  font-size: 0.9rem;
  overflow-wrap: break-word;
  white-space: pre-wrap;
}

.error-dismiss {
  position: absolute;
  top: 0.25rem;
  right: 0.5rem;
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
}
</style> 