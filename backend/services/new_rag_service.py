import os
import logging
import time
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from backend.models.logging import APILog
from backend.scripts.agents.chat_rag_agent import get_rag_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewRagService:
    """
    Service that uses the LangChain-based RAG agent to answer questions.
    This implements a similar interface to the existing RagAgentService for
    smooth integration with the chat system.
    """
    
    def __init__(self, db: Session):
        """Initialize the RAG service.
        
        Args:
            db: SQLAlchemy database session for logging
        """
        self.db = db
        # Lazy initialization of the agent when needed
        self._rag_agent = None
    
    @property
    def rag_agent(self):
        """Get the RAG agent instance."""
        if self._rag_agent is None:
            self._rag_agent = get_rag_agent()
        return self._rag_agent
    
    async def answer_question(self, question: str, chat_context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Answers a question using the RAG agent.
        
        Args:
            question: The user's question
            chat_context: Optional chat history for context
            
        Returns:
            Dict containing the response text, sources, and token usage
        """
        logger.info(f"Processing question with new RAG agent: {question}")
        
        start_time = time.time()
        
        try:
            # Process the query with our RAG agent
            response = await self.rag_agent.process_query(question, chat_context)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            response["duration_ms"] = duration_ms
            
            # Log the request and response
            if self.db:
                try:
                    log = APILog(
                        endpoint="new_rag_agent",
                        prompt=question,
                        response=response["text"],
                        tokens_prompt=response.get("tokens_prompt", 0),
                        tokens_completion=response.get("tokens_completion", 0),
                        tokens_total=response.get("tokens_total", 0),
                        model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
                        duration_ms=duration_ms
                    )
                    self.db.add(log)
                    self.db.commit()
                except Exception as e:
                    logger.error(f"Error logging API request: {e}")
            
            return response
        
        except Exception as e:
            logger.error(f"Error in RAG service: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log the error
            if self.db:
                try:
                    log = APILog(
                        endpoint="new_rag_agent",
                        prompt=question,
                        response=str(e),
                        tokens_prompt=0,
                        tokens_completion=0,
                        tokens_total=0,
                        model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
                        duration_ms=(time.time() - start_time) * 1000
                    )
                    self.db.add(log)
                    self.db.commit()
                except Exception as log_err:
                    logger.error(f"Error logging API error: {log_err}")
            
            # Return a graceful error response
            return {
                "text": f"I encountered an error while processing your question. Please try again or rephrase your question.",
                "sources": [],
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "tokens_total": 0,
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def get_relevant_context(self, topic: str, max_docs: int = 5) -> List[Dict[str, str]]:
        """Gets relevant context for a topic.
        
        Args:
            topic: The topic to search for
            max_docs: Maximum number of documents to return
            
        Returns:
            List of documents with content and source
        """
        logger.info(f"Getting context for topic with new RAG service: {topic}")
        
        try:
            # Get the RAG agent tools
            tools = self.rag_agent.tools
            
            # Use the semantic search to get context
            docs = tools.vector_store.similarity_search(topic, k=max_docs)
            
            # Format into the expected response structure
            context = []
            for doc in docs:
                context.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown")
                })
            
            return context
        
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return [] 