import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from backend.chains import get_rag_chain
from sqlalchemy.orm import Session
from backend.models.logging import APILog

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RagAgentService:
    """Serviço de agente que utiliza o sistema RAG para responder perguntas."""
    
    def __init__(self, db: Session):
        """Inicializa o serviço de agente RAG.
        
        Args:
            db: Sessão do banco de dados para logging
        """
        self.db = db
        self.rag_chain = get_rag_chain()
        
    def answer_question(self, question: str, chat_context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Responde a uma pergunta usando o sistema RAG.
        
        Args:
            question: A pergunta do usuário
            chat_context: O contexto da conversa (histórico)
            
        Returns:
            Um dicionário contendo o texto da resposta, fontes e detalhes de tokens
        """
        logger.info(f"RAG Agent question: {question}")
        
        try:
            # Obter resposta do RAG
            response = self.rag_chain.answer_question(question)
            
            # Log na base de dados
            if self.db:
                log = APILog(
                    endpoint="rag_agent",
                    prompt=question,
                    response=response["text"],
                    tokens_prompt=response.get("tokens_prompt", 0),
                    tokens_completion=response.get("tokens_completion", 0),
                    tokens_total=response.get("tokens_total", 0),
                    model=os.getenv("CHAT_MODEL", "gpt-4.1-mini"),
                    duration_ms=0  # O RAG chain não fornece duração atualmente
                )
                self.db.add(log)
                self.db.commit()
            
            return {
                "text": response["text"],
                "sources": response.get("sources", []),
                "tokens_prompt": response.get("tokens_prompt", 0),
                "tokens_completion": response.get("tokens_completion", 0),
                "tokens_total": response.get("tokens_total", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG Agent: {e}")
            
            # Log do erro também
            if self.db:
                log = APILog(
                    endpoint="rag_agent",
                    prompt=question,
                    response=str(e),
                    tokens_prompt=0,
                    tokens_completion=0,
                    tokens_total=0,
                    model=os.getenv("CHAT_MODEL", "gpt-4.1-mini"),
                    duration_ms=0
                )
                self.db.add(log)
                self.db.commit()
            
            raise
    
    def get_context_for_faq(self, topic: str, max_docs: int = 5) -> List[Dict[str, str]]:
        """Obtém contexto relevante para um tópico de FAQ.
        
        Args:
            topic: O tópico ou pergunta para buscar contexto
            max_docs: Número máximo de documentos a retornar
            
        Returns:
            Lista de documentos relevantes com conteúdo e fonte
        """
        logger.info(f"Getting context for FAQ: {topic}")
        
        try:
            return self.rag_chain.get_relevant_context(topic, max_docs)
        except Exception as e:
            logger.error(f"Error getting FAQ context: {e}")
            return []
    
    def generate_quiz_context(self, topic: str, max_docs: int = 3) -> List[Dict[str, str]]:
        """Obtém contexto relevante para geração de quiz.
        
        Args:
            topic: O tópico para o quiz
            max_docs: Número máximo de documentos a retornar
            
        Returns:
            Lista de documentos relevantes com conteúdo e fonte
        """
        logger.info(f"Getting context for quiz: {topic}")
        
        try:
            return self.rag_chain.get_relevant_context(topic, max_docs)
        except Exception as e:
            logger.error(f"Error getting quiz context: {e}")
            return [] 