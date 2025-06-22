import os
import sys
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Path to the FAISS index
INDEX_DIR = os.path.join(project_root, "data/index")

class TokenCounterCallback(BaseCallbackHandler):
    """Callback handler for counting tokens."""
    
    def __init__(self):
        self.tokens_prompt = 0
        self.tokens_completion = 0
        self.tokens_total = 0
    
    def on_llm_start(self, *args, **kwargs):
        self.tokens_prompt = kwargs.get("prompts", [""])[0].count(" ") // 3  # Rough estimate
    
    def on_llm_end(self, response, **kwargs):
        usage = getattr(response, "llm_output", {}).get("token_usage", {})
        self.tokens_completion = usage.get("completion_tokens", 0)
        self.tokens_total = usage.get("total_tokens", 0)
        self.tokens_prompt = usage.get("prompt_tokens", self.tokens_prompt)

class RagChain:
    """Chain para recuperação de informações da documentação."""
    
    def __init__(self):
        """Inicializa o chain de RAG."""
        self.vectorstore = self._load_index()
        self.qa_chain = self._create_qa_chain()
    
    def _load_index(self):
        """Carrega o índice FAISS."""
        logger.info("Loading FAISS index...")
        
        if not os.path.exists(INDEX_DIR):
            logger.error(f"Index directory {INDEX_DIR} does not exist.")
            raise FileNotFoundError(f"RAG index not found at {INDEX_DIR}. Please run build_rag.py first.")
        
        # Initialize embeddings model
        embeddings_model = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
        logger.info(f"Using embedding model: {embeddings_model}")
        
        try:
            # Initialize embeddings model
            embeddings = OpenAIEmbeddings(
                model=embeddings_model
            )
            
            # Load the vector store
            vectorstore = FAISS.load_local(
                INDEX_DIR,
                embeddings,
                allow_dangerous_deserialization=True  # Allow deserialization as this is a local file we created
            )
            
            logger.info("Index loaded successfully!")
            return vectorstore
        
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def _create_qa_chain(self):
        """Cria o chain de perguntas e respostas."""
        # Initialize the language model
        chat_model = os.getenv("CHAT_MODEL", "gpt-4.1-mini")
        logger.info(f"Using chat model: {chat_model}")
        
        try:
            llm = ChatOpenAI(
                model_name=chat_model,
                temperature=0
            )
            
            # Define the prompt template
            prompt_template = """Você é um assistente de documentação para programadores. 
Use as seguintes partes do contexto para responder à pergunta ao final.
Se não souber a resposta com base no contexto fornecido, diga que não tem essa informação na documentação disponível.
Forneça respostas precisas e concisas. Inclua exemplos de código quando apropriado.

Contexto:
{context}

Pergunta: {question}
Resposta:"""

            prompt = ChatPromptTemplate.from_template(prompt_template)
            
            # Create the chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                ),
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )
            
            return qa_chain
        
        except Exception as e:
            logger.error(f"Error creating QA chain: {e}")
            raise
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Responde a uma pergunta usando a documentação.
        
        Args:
            question: Pergunta do usuário
            
        Returns:
            Resposta com o texto, fontes e detalhes de tokens
        """
        logger.info(f"RAG Question: {question}")
        
        try:
            # Create callback for token tracking
            callback = TokenCounterCallback()
            
            # Query the chain
            result = self.qa_chain.invoke(
                {"query": question},
                callbacks=[callback]
            )
            
            sources = []
            for doc in result.get("source_documents", []):
                if "source" in doc.metadata:
                    sources.append(doc.metadata["source"])
            
            return {
                "text": result["result"],
                "sources": sources,
                "tokens_prompt": callback.tokens_prompt,
                "tokens_completion": callback.tokens_completion,
                "tokens_total": callback.tokens_total
            }
        
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise
    
    def get_relevant_context(self, question: str, max_docs: int = 3) -> List[Dict[str, str]]:
        """Recupera o contexto relevante para uma pergunta.
        
        Args:
            question: Pergunta ou tema
            max_docs: Número máximo de documentos a retornar
            
        Returns:
            Lista de documentos relevantes com conteúdo e fonte
        """
        logger.info(f"Getting context for: {question}")
        
        try:
            docs = self.vectorstore.similarity_search(question, k=max_docs)
            
            context = []
            for doc in docs:
                context.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown")
                })
            
            return context
        
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            raise 