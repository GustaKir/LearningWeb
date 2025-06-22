<template>
  <div class="chat-view">
    <div class="chat-container futura-card">
      <div class="chat-sessions">
        <div class="sessions-header">
          <h2>Sessões</h2>
          <button @click="createNewSession" class="futura-button small">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Nova
          </button>
        </div>
        <div class="sessions-list">
          <div 
            v-for="session in sessions" 
            :key="session.session_id" 
            class="session-item"
            :class="{ active: session.session_id === currentSessionId }"
            @click="switchSession(session.session_id)"
          >
            <div class="session-title">{{ session.title || 'Nova conversa' }}</div>
            <div class="session-time">{{ formatDate(session.created_at) }}</div>
          </div>
          <div v-if="sessions.length === 0" class="no-sessions">
            Nenhuma sessão encontrada
          </div>
        </div>
        <div class="sessions-footer">
          <button @click="clearSessions" class="futura-button small full-width" :disabled="sessions.length === 0">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
            </svg>
            Limpar Todas as Sessões
          </button>
        </div>
      </div>
      
      <div class="chat-main">
        <div class="chat-header">
          <h2>{{ currentSessionTitle || 'Nova conversa' }}</h2>
          <div class="chat-status" :class="{ 'status-active': isTyping }">
            <div class="status-indicator"></div>
            <span>{{ isTyping ? 'EdTech está digitando...' : 'Online' }}</span>
          </div>
        </div>
        
        <div class="chat-messages" ref="messagesContainer">
          <div class="welcome-message" v-if="messages.length === 0">
            <div class="futura-hologram hologram-ring pulse">
              <div class="hologram-circle circle-inner"></div>
              <div class="hologram-circle circle-middle"></div>
              <div class="hologram-circle circle-outer"></div>
            </div>
            <h3>Como posso ajudar?</h3>
            <p>Faça perguntas sobre Python, FastAPI ou Streamlit</p>
            <div class="suggested-questions">
              <button @click="useQuestion('Como faço para criar uma aplicação FastAPI?')" class="question-chip">
                Como faço para criar uma aplicação FastAPI?
              </button>
              <button @click="useQuestion('O que é list comprehension em Python?')" class="question-chip">
                O que é list comprehension em Python?
              </button>
              <button @click="useQuestion('Como exibir um dataframe no Streamlit?')" class="question-chip">
                Como exibir um dataframe no Streamlit?
              </button>
            </div>
          </div>
          
          <div v-for="(message, index) in messages" :key="index" class="message-container">
            <div :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']">
              <div class="message-content">
                <div v-if="message.role !== 'user'" class="message-avatar">
                  <div class="futura-holo hologram-ring pulse">
                    <div class="avatar-circle avatar-inner"></div>
                    <div class="avatar-circle avatar-middle"></div>
                    <div class="avatar-circle avatar-outer"></div>
                  </div>
                </div>
                <div class="message-text" v-if="message.role === 'user'">{{ message.content }}</div>
                <div v-else>
                  <div v-if="!message.content || message.content.length === 0" class="message-text">
                    <em>Esta mensagem não contém conteúdo</em>
                  </div>
                  <code-highlighter v-else :content="message.content" class="message-text"></code-highlighter>
                </div>
              </div>
              <div class="message-time">{{ formatMessageTime(message.timestamp) }}</div>
            </div>
          </div>
          
          <div v-if="isTyping" class="message-container">
            <div class="message assistant-message typing">
              <div class="message-content">
                <div class="message-avatar">
                  <div class="futura-holo hologram-ring pulse">
                    <div class="avatar-circle avatar-inner"></div>
                    <div class="avatar-circle avatar-middle"></div>
                    <div class="avatar-circle avatar-outer"></div>
                  </div>
                </div>
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="chat-input">
          <form @submit.prevent="sendMessage" class="input-form">
            <input 
              v-model="newMessage" 
              type="text" 
              placeholder="Digite sua pergunta..."
              class="futura-input message-input"
              :disabled="isLoading"
            />
            <button type="submit" class="futura-button send-button" :disabled="isLoading || !newMessage">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import CodeHighlighter from '../components/CodeHighlighter.vue';

export default {
  name: 'ChatView',
  components: {
    CodeHighlighter
  },
  data() {
    return {
      currentSessionId: null,
      currentSessionTitle: null,
      sessions: [],
      messages: [],
      newMessage: '',
      isLoading: false,
      isTyping: false,
    };
  },
  async created() {
    // Try to restore session from localStorage
    const savedSessionId = localStorage.getItem('currentSessionId');
    
    await this.loadSessions();
    
    // Create new session if none exists or if saved session doesn't exist anymore
    if (this.sessions.length === 0) {
      await this.createNewSession();
    } else if (savedSessionId && this.sessions.some(session => session.session_id === savedSessionId)) {
      // If we have a saved session and it still exists, use that
      this.switchSession(savedSessionId);
    } else {
      // Otherwise use the first available session
      this.switchSession(this.sessions[0].session_id);
    }
  },
  methods: {
    async loadSessions() {
      try {
        const response = await axios.get('/api/chat/sessions');
        this.sessions = response.data.sessions || [];
      } catch (error) {
        console.error('Error loading sessions:', error);
      }
    },
    async switchSession(sessionId) {
      this.currentSessionId = sessionId;
      // Save session ID to localStorage for persistence
      localStorage.setItem('currentSessionId', sessionId);
      
      try {
        const response = await axios.get(`/api/chat/sessions/${sessionId}`);
        
        // Process messages to ensure they have the correct format
        this.messages = response.data.messages.map(msg => {
          return {
            role: msg.role || 'assistant',
            content: msg.content || '',
            timestamp: msg.timestamp || new Date().toISOString()
          };
        });
        
        this.currentSessionTitle = response.data.title;
        this.scrollToBottom();
      } catch (error) {
        console.error('Error loading session messages:', error);
      }
    },
    async createNewSession() {
      try {
        const response = await axios.post('/api/chat/sessions', {
          title: 'Nova conversa'
        });
        console.log('Created new session with ID:', response.data.session_id);
        
        // Set the current session ID immediately
        this.currentSessionId = response.data.session_id;
        localStorage.setItem('currentSessionId', response.data.session_id);
        
        // Refresh the sessions list
        await this.loadSessions();
        
        // Clear messages for the new session
        this.messages = [];
        this.scrollToBottom();
      } catch (error) {
        console.error('Error creating new session:', error);
      }
    },
    async sendMessage() {
      if (!this.newMessage || this.isLoading) return;
      
      // Add user message locally
      const userMessage = {
        role: 'user',
        content: this.newMessage,
        timestamp: new Date()
      };
      this.messages.push(userMessage);
      
      const messageText = this.newMessage;
      this.newMessage = '';
      this.isTyping = true;
      this.scrollToBottom();
      
      try {
        const response = await axios.post(`/api/chat/sessions/${this.currentSessionId}/messages`, {
          content: messageText
        });
        
        // Add assistant message from response
        this.isTyping = false;
        const assistantMessage = {
          role: 'assistant',
          content: response.data.text,
          timestamp: new Date()
        };
        this.messages.push(assistantMessage);
        this.scrollToBottom();
        
        // Update session title if it's the first message
        if (this.messages.length === 2) {
          await this.loadSessions();
        }
      } catch (error) {
        this.isTyping = false;
        console.error('Error sending message:', error);
        this.messages.push({
          role: 'assistant',
          content: 'Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.',
          timestamp: new Date()
        });
      }
    },
    useQuestion(question) {
      this.newMessage = question;
      this.sendMessage();
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR', { 
        day: '2-digit', 
        month: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    },
    formatMessageTime(timestamp) {
      if (!timestamp) return '';
      try {
        const date = new Date(timestamp);
        if (isNaN(date.getTime())) {
          return ''; // Invalid date
        }
        return date.toLocaleTimeString('pt-BR', { 
          hour: '2-digit', 
          minute: '2-digit' 
        });
      } catch (error) {
        console.error('Error formatting timestamp:', error, timestamp);
        return '';
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight;
        }
      });
    },
    async clearSessions() {
      if (confirm('Tem certeza que deseja limpar todas as sessões de chat?')) {
        try {
          await axios.delete('/api/chat/sessions');
          this.sessions = [];
          this.currentSessionId = null;
          // Also clear from localStorage
          localStorage.removeItem('currentSessionId');
          this.messages = [];
          await this.createNewSession();
        } catch (error) {
          console.error('Error clearing sessions:', error);
          alert('Ocorreu um erro ao limpar as sessões.');
        }
      }
    }
  }
};
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 180px);
  display: flex;
  justify-content: center;
  align-items: center;
}

.chat-container {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* Sessions sidebar */
.chat-sessions {
  width: 250px;
  border-right: 1px solid var(--card-border);
  display: flex;
  flex-direction: column;
  background-color: var(--bg-tertiary);
}

.sessions-header {
  height: 60px;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--card-border);
}

.sessions-header h2 {
  margin: 0;
  font-size: 1.2rem;
}

.sessions-footer {
  padding: 0.75rem;
  border-top: 1px solid var(--card-border);
}

.futura-button.small {
  padding: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.futura-button.full-width {
  width: 100%;
  justify-content: center;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.session-item {
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.session-item:hover {
  background-color: var(--bg-secondary);
}

.session-item.active {
  background-color: rgba(0, 184, 217, 0.1);
  border-color: var(--accent-primary);
}

.session-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.no-sessions {
  padding: 1rem;
  text-align: center;
  color: var(--text-tertiary);
}

/* Main chat area */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-secondary);
}

.chat-header {
  height: 60px;
  padding: 0 1rem;
  border-bottom: 1px solid var(--card-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  margin: 0;
  font-size: 1.2rem;
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--success);
}

.status-active .status-indicator {
  animation: pulse 1.5s infinite;
}

/* Messages area */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  text-align: center;
  height: 100%;
  overflow: hidden;
}

.welcome-message h3 {
  font-size: 1.5rem;
  margin: 1rem 0 0.5rem;
  color: var(--accent-primary);
}

.welcome-message p {
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.hologram-ring {
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

.suggested-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  max-width: 600px;
  margin-bottom: 0;
}

.question-chip {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);
}

.question-chip:hover {
  background-color: var(--bg-primary);
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.message-container {
  display: flex;
  flex-direction: column;
}

.message {
  max-width: 80%;
  padding: 1rem;
  border-radius: 12px;
  position: relative;
  display: inline-block;
  width: auto;
}

.user-message {
  align-self: flex-end;
  background-color: var(--accent-glow);
  border: 1px solid var(--accent-primary);
  margin-left: auto;
}

.assistant-message {
  align-self: flex-start;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--card-border);
}

.message-content {
  display: flex;
  gap: 0.75rem;
  max-width: 100%;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(19, 26, 41, 0.8), rgba(30, 42, 69, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.avatar-hologram {
  position: relative;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid var(--accent-primary);
}

.avatar-inner {
  width: 10px;
  height: 10px;
  background: rgba(0, 184, 217, 0.1);
}

.avatar-middle {
  width: 20px;
  height: 20px;
  border: 1px dashed var(--accent-primary);
  animation: rotate 20s linear infinite reverse;
}

.avatar-outer {
  width: 28px;
  height: 28px;
  border: 1px solid var(--accent-primary);
  animation: rotate 30s linear infinite;
}

.avatar-text {
  font-weight: bold;
  font-size: 0.75rem;
  color: white;
  position: absolute;
  z-index: 2;
}

.message-text {
  white-space: pre-wrap;
  line-height: 1.5;
  max-width: 100%;
  overflow-wrap: break-word;
  word-break: break-word;
  width: 100%;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.5rem;
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--accent-primary);
  display: inline-block;
  animation: typing 1.4s infinite both;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0% {
    opacity: 0.4;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-5px);
  }
  100% {
    opacity: 0.4;
    transform: translateY(0);
  }
}

/* Input area */
.chat-input {
  padding: 1rem;
  border-top: 1px solid var(--card-border);
}

.input-form {
  display: flex;
  gap: 0.5rem;
}

.message-input {
  flex: 1;
  padding: 0.75rem 1rem;
  font-size: 1rem;
}

.send-button {
  padding: 0.75rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.source-bubble:hover .source-external-icon {
  opacity: 1;
  color: var(--accent-primary);
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }
  
  .chat-sessions {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--card-border);
  }
  
  .chat-view {
    height: calc(100vh - 150px);
  }
}
</style> 