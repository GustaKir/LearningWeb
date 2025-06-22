import os
import sys
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.agents import AgentExecutor, Tool
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.base import BaseTool
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define constants
INDEX_DIR = os.path.join(project_root, "data/index")
API_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
TEMPERATURE = 0.0  # Low temperature for factual responses

class RagAgentTools:
    """Tools for the RAG Agent."""
    
    def __init__(self):
        """Initialize the RAG agent tools."""
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.vector_store = self._load_vector_store()
        self.last_retrieved_docs = []  # Store the last retrieved documents
        
    def _load_vector_store(self) -> FAISS:
        """Load the FAISS vector store with embeddings."""
        logger.info(f"Loading FAISS index from {INDEX_DIR}")
        
        if not os.path.exists(INDEX_DIR):
            raise FileNotFoundError(f"RAG index not found at {INDEX_DIR}. Please run build_rag.py first.")
        
        try:
            vector_store = FAISS.load_local(
                INDEX_DIR,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("FAISS index loaded successfully")
            return vector_store
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            raise
    
    def _filter_low_quality_documents(self, docs: List[Document]) -> List[Document]:
        """Filter out low-quality documents like 404 pages or very short content."""
        filtered_docs = []
        
        for doc in docs:
            content = doc.page_content.lower()
            
            # Skip documents that appear to be 404 pages
            if "page not found" in content or "404" in content:
                continue
                
            # Skip very short documents
            if len(content.split()) < 20:  # At least 20 words
                continue
                
            # Skip documents with suspicious patterns of being non-content
            suspicious_patterns = ["cookie policy", "contact us", "home", "search", "documentation"]
            if sum(1 for pattern in suspicious_patterns if pattern in content) >= 3:
                continue
                
            filtered_docs.append(doc)
        
        # If we've filtered everything, return the original set rather than nothing
        if not filtered_docs and docs:
            logger.warning("All documents were filtered out. Using original documents as fallback.")
            return docs
            
        return filtered_docs
    
    def get_retrieval_tool(self) -> Tool:
        """Get a tool for retrieving relevant documentation."""
        return Tool(
            name="retrieve_relevant_documents",
            description="Retrieve relevant documentation chunks based on the query. Use this to find information about Python, FastAPI, and Streamlit.",
            func=self.retrieve_relevant_documents
        )
    
    def get_search_tool(self) -> Tool:
        """Get a tool for searching the vector store directly."""
        return Tool(
            name="semantic_search",
            description="Search for information in the documentation using a semantic query.",
            func=self.semantic_search
        )
    
    def retrieve_relevant_documents(self, query: str, k: int = 5) -> str:
        """
        Retrieve relevant documents based on the query and format them for the agent.
        
        Args:
            query: The query to retrieve documents for
            k: The number of documents to retrieve
            
        Returns:
            A formatted string containing the retrieved documents with metadata
        """
        try:
            # Retrieve more documents than needed to then filter
            initial_k = max(10, k * 2)
            
            if not self.vector_store:
                logger.error("Vector store initialization failed.")
                return "Error: Vector store not available"
            
            documents = self.vector_store.similarity_search(query, k=initial_k)
            
            # Filter low-quality documents
            filtered_docs = self._filter_low_quality_documents(documents)
            
            # If all documents were filtered out, use the original documents as fallback
            if not filtered_docs and documents:
                logger.warning("All documents were filtered out. Using original documents as fallback.")
                filtered_docs = documents[:k]  # Use only the top k original documents
            else:
                # Limit to the requested k documents
                filtered_docs = filtered_docs[:k]
            
            # Log source information with metadata
            for doc in filtered_docs:
                source = doc.metadata.get("source", "Unknown")
                title = doc.metadata.get("title", "No title")
                url = doc.metadata.get("url", "No URL")
                summary = doc.metadata.get("summary", "No summary")
                logger.info(f"Retrieved document: {title} | {url}")
            
            # Store the documents for later use in process_query
            self.last_retrieved_docs = filtered_docs
            
            # Format the documents into a prompt
            return self._create_prompt_with_sources(filtered_docs)
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return f"Error retrieving relevant documents: {str(e)}"
    
    def semantic_search(self, query: str) -> str:
        """
        Search for information in the vector store using a semantic query.
        
        Args:
            query: The search query
            
        Returns:
            A string containing the search results
        """
        try:
            # Get more documents initially since we'll filter some out
            docs = self.vector_store.similarity_search(query, k=8)
            
            # Filter out low-quality documents
            filtered_docs = self._filter_low_quality_documents(docs)
            
            # Store the documents for later use in process_query
            self.last_retrieved_docs = filtered_docs[:3]
            
            # Take the top 3 remaining docs
            filtered_docs = filtered_docs[:3]
            
            if not filtered_docs:
                return "No relevant information found in our knowledge base. I'll answer based on my general knowledge."
                
            return self._create_prompt_with_sources(filtered_docs)
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return f"Error searching documentation: {str(e)}"

    def _create_prompt_with_sources(self, documents: List[Document]) -> str:
        """
        Create a prompt with sources for the LLM.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            A prompt with sources
        """
        if not documents:
            return "No relevant documentation was found for this query."
            
        prompt_parts = ["I found the following relevant information:"]
        
        for i, doc in enumerate(documents, 1):
            # Extract metadata
            title = doc.metadata.get("title", f"Document {i}")
            url = doc.metadata.get("url", "No URL provided")
            summary = doc.metadata.get("summary", "")
            source = doc.metadata.get("source", "Unknown source")
            
            # Format the document with metadata
            doc_header = f"## Source {i}: {title}"
            doc_url = f"URL: {url}"
            doc_source = f"File: {source}"
            doc_summary = f"Summary: {summary}" if summary else ""
            
            prompt_parts.append(doc_header)
            prompt_parts.append(doc_url)
            prompt_parts.append(doc_source)
            if doc_summary:
                prompt_parts.append(doc_summary)
            prompt_parts.append("Content:")
            prompt_parts.append(doc.page_content.strip())
            prompt_parts.append("\n---\n")
        
        prompt_parts.append("\nUse the above information to answer the user's question. Include relevant source URLs in your response when providing specific information from the documentation.")
        
        # Create the final prompt
        prompt = "\n".join(prompt_parts)
        return prompt

class ChatRagAgent:
    """
    Agent that uses RAG to answer questions about Python, FastAPI, and Streamlit.
    Uses LangChain and FAISS for vector search instead of Pydantic AI and Supabase.
    """
    
    def __init__(self):
        """Initialize the Chat RAG Agent."""
        self.tools = RagAgentTools()
        self.llm = ChatOpenAI(model_name=API_MODEL, temperature=TEMPERATURE)
        self.agent_executor = self._create_agent()
        
    def _create_agent(self) -> AgentExecutor:
        """Create and configure the RAG agent."""
        # Define the tools
        tools = [
            self.tools.get_retrieval_tool(),
            self.tools.get_search_tool()
        ]
        
        # Define the prompt template
        system_prompt = """
You are an expert technical assistant specializing in Python, FastAPI, and Streamlit.
Your responses should be clear, concise, and accurate.

APPROACH TO ANSWERING QUESTIONS:
1. First, determine if the question is related to Python, FastAPI, or Streamlit
2. If it is, always use your tools to search for relevant information in the documentation
3. If you find relevant information in the documentation, base your answer primarily on that
4. If you don't find relevant documentation or the information is incomplete, you can supplement with your general knowledge but clearly indicate this
5. Always provide code examples when appropriate
6. Be direct and to the point in your answers

QUALITY AND STANDARDS:
- Format code blocks properly using ```python markup
- Prefer specific, actionable information over general advice
- Always be honest about what you know from documentation vs. general knowledge
- If the documentation genuinely doesn't cover a topic, it's okay to say "The documentation doesn't cover this specific topic, but based on my general knowledge..."
- When you cite information from sources, include the relevant URL in your answer

You have access to the following tools:
- retrieve_relevant_documents: Use this to find detailed documentation chunks about Python, FastAPI, or Streamlit
- semantic_search: Use this for more specific queries to find information

Remember that your primary goal is to provide accurate, helpful answers based on the documentation first, and your general knowledge second.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create memory for conversation history
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Create the agent
        agent = OpenAIFunctionsAgent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    async def process_query(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a user query using the RAG agent.
        
        Args:
            query: The user's question
            chat_history: Optional chat history for context
            
        Returns:
            A dictionary containing the response text and metadata
        """
        logger.info(f"Processing query with RAG agent: {query}")
        
        try:
            # Convert chat history to the format expected by the agent
            formatted_history = []
            if chat_history:
                for msg in chat_history:
                    if msg["role"] != "system":  # Skip system messages
                        formatted_history.append({"type": msg["role"], "content": msg["content"]})
            
            # Run the agent
            start_time = __import__('time').time()
            response = await self.agent_executor.ainvoke(
                {
                    "input": query,
                    "chat_history": formatted_history
                }
            )
            end_time = __import__('time').time()
            
            duration_ms = (end_time - start_time) * 1000
            
            # Extract response text
            output = response.get("output", "I couldn't process that request.")
            
            # Get token usage if available
            token_usage = {
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "tokens_total": 0
            }
            
            # Extract sources from the last retrieved documents
            sources = []
            for doc in self.tools.last_retrieved_docs:
                source = {
                    "title": doc.metadata.get("title", "Unknown"),
                    "url": doc.metadata.get("url", ""),
                    "source": doc.metadata.get("source", ""),
                    "summary": doc.metadata.get("summary", "")
                }
                sources.append(source)
            
            return {
                "text": output,
                "sources": sources,
                "tokens_prompt": token_usage["tokens_prompt"],
                "tokens_completion": token_usage["tokens_completion"],
                "tokens_total": token_usage["tokens_total"],
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "text": f"I encountered an error while processing your question. Please try again or rephrase your question.",
                "sources": [],
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "tokens_total": 0,
                "duration_ms": 0
            }

# Singleton instance
_agent_instance = None

def get_rag_agent():
    """Get a singleton instance of the ChatRagAgent."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ChatRagAgent()
    return _agent_instance 