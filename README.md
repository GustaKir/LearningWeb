
### Funcionalidades

- **Alteração do Frontend**: Substituído o Streamlit pelo Vue.js para uma experiência de usuário mais moderna e dinâmica
- **Estrutura do Frontend**: Configuração da estrutura do frontend utilizando Vue.js 3 e Vite
- **Paginação Básica**: Implementação de roteamento básico para as páginas: Home, Chat, FAQ e Quiz
- **Estilização básica da interface**: Estilização básica da interface com Tailwind CSS
- **Chat Interface**: Interface de chat funcional com criação de sessões, envio de mensagens e exibição de respostas
- **API Integration**: Configuração do proxy Vite para conectar o frontend ao backend corretamente
- **Backend API**: Implementação de endpoints para gerenciar sessões de chat e mensagens
- **Banco de Dados**: Modelos SQLAlchemy para armazenar sessões de chat e histórico de mensagens
- **Sitema do FAQ**: Sistema para gerar FAQ a partir de emails de suporte, com exibição em formato acordeão
- **Streaming de texto**: A implementação atual não utiliza streaming de texto no chat, enviando respostas completas após processamento
- **Sistema do Quiz**: Gerador de quiz com perguntas de múltipla escolha, feedback de respostas e explicações (u acabei estragando o código do Quiz ao implementar o sistema de RAG, e acabei não tendo tempo para consertar)
- **API Logging**: Sistema para logging de todas as interações com a API da OpenAI, incluindo tokens utilizados
- **RAG**: Implementação de RAG para a documentação do FastAPI, Python e Streamlit, com busca por similaridade de vetores e uso de embeddings




### Novas bibliotecas adicionadas

#### Frontend
| Lib | Motivo |
|-----|--------|
| Vue.js 3 | Framework frontend para construção da interface |
| Vue Router | Roteamento da aplicação Vue.js |
| Vite | Build tool e dev server para desenvolvimento frontend |
| Axios | Cliente HTTP para comunicação com o backend |

#### Backend
| Lib | Motivo |
|-----|--------|
| Pydantic | Validação de dados e gerenciamento de configurações |
| SQLAlchemy | ORM para interação com banco de dados |
| OpenAI | Integração com a API da OpenAI |
| python-dotenv | Carregamento de variáveis de ambiente do arquivo .env |
| LangChain | Framework para desenvolvimento de aplicações com LLMs |
| LangChain-OpenAI | Integração do LangChain com OpenAI |
| tiktoken | Contagem de tokens para modelos da OpenAI |
| pandas | Manipulação de dados estruturados |
| FAISS | Busca por similaridade de vetores para RAG |
| tenacity | Lógica de retry para chamadas de APIs externas |
| pytest | Framework para testes unitários |
| httpx | Cliente HTTP assíncrono |


# Sistema RAG de Documentação FastAPI + Streamlit

Este projeto implementa um sistema de Recuperação-Geração Aumentada (RAG) para consultar documentação sobre Python, FastAPI e Streamlit.

## Recursos

- **Pesquisa de Vetores**: Utiliza embeddings OpenAI e FAISS para uma busca de vetores eficiente
- **Processamento de Documentos**: Processa automaticamente arquivos HTML e de texto da documentação
- **Filtragem Avançada**: Filtra conteúdo de baixa qualidade e prioriza resultados relevantes
- **Rastreamento de Fontes**: Monitora as fontes usadas nas respostas
- **Interação Baseada em Agentes**: Utiliza agentes LangChain para tratamento inteligente de consultas
- **Geração de FAQs por E-mail**: Gera FAQs automaticamente a partir de e-mails de usuários, extraindo perguntas comuns

## Configuração

1. **Clone o repositório**

```bash
git clone <url-do-repositório>
cd <diretório-do-repositório>
```

2. **Crie um ambiente virtual e instale as dependências**

```bash
python -m venv .venv
source .venv/bin/activate # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configurar variáveis ​​de ambiente**

Crie um arquivo `.env` no diretório raiz com o seguinte conteúdo:

```
OPENAI_API_KEY=sua_chave_de_api_openai
CHAT_MODEL=gpt-4o-mini # Ou outro modelo OpenAI
EMBEDDINGS_MODEL=text-embedding-3-small
```

## Uso

### Construindo o Índice RAG

Antes de consultar, você precisa construir o índice a partir da sua documentação:

```bash
python -m backend.chains.scripts.build_rag
```

### Geração de FAQ por e-mail

O sistema pode gerar automaticamente entradas de FAQ a partir de perguntas de e-mail usando o RAG:

1. **Extrair perguntas de arquivos de e-mail**

Coloque seus arquivos de e-mail (formato .eml) no diretório `data/emails` e execute:

```bash
python -m backend.scripts.extract_email_questions
```

Este script extrai perguntas dos arquivos de e-mail e as armazena em `backend/db/emails.db`.

2. **Gerar entradas de FAQ a partir das perguntas extraídas**

Você pode gerar entradas de FAQ de várias maneiras:

**Usando os endpoints da API:**

- Listar todas as perguntas extraídas:
```
GET /faq/email-questions
```

- Gerar uma resposta para uma pergunta específica:
```
POST /faq/email-questions/{question_id}/answer
```

- Criar uma entrada de FAQ para uma pergunta específica:
```
POST /faq/email-questions/{question_id}/create-faq
```

- Gerar entradas de FAQ para todas as perguntas:
```
POST /faq/email-questions/generate-all
```

**Usando o script de teste:**

```bash
python -m backend.scripts.test_email_rag
```

Este script demonstra como:
- Recuperar perguntas do banco de dados
- Gerar uma resposta para Uma pergunta usando o RAG
- Crie uma entrada de FAQ no banco de dados

3. **Como funciona**

- As perguntas são extraídas de arquivos de e-mail usando padrões regex
- O sistema RAG recupera o contexto relevante da documentação
- As respostas são geradas usando o contexto e o LLM
- As entradas de FAQ são categorizadas automaticamente com base no conteúdo
- Todas as entradas são armazenadas no banco de dados principal e podem ser recuperadas via API

## Estrutura do Projeto

- `backend/chains/scripts/build_rag.py`: Script para construir o índice RAG
- `backend/chains/scripts/query_rag.py`: Script para consultar o sistema RAG
- `backend/scripts/agents/chat_rag_agent.py`: Implementação do agente RAG
- `backend/scripts/extract_email_questions.py`: Script para extrair perguntas de e-mails
- `backend/scripts/test_email_rag.py`: Script para testar a geração de FAQs por e-mail
- `data/corpus/`: Diretório contendo arquivos de documentação
- `data/emails/`: Diretório contendo arquivos de e-mail para geração de FAQ
- `data/index/`: Diretório onde o índice FAISS é salvo

## Adicionando Mais Documentação

Para adicionar mais documentação:

1. Adicione arquivos HTML ou de texto ao diretório `data/corpus`
2. Para arquivos de texto, você pode adicionar metadados estruturados no seguinte formato:
```
Título: Título do Documento
URL: https://example.com/doc
Resumo: Um breve resumo do documento
---

O conteúdo do documento vai aqui...
```

3. Reconstrua o índice executando `python -m backend.chains.scripts.build_rag`

Adendo. O vue.js é executado a partir da porta http://localhost:5173/
