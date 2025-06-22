import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import datetime
import re

from backend.models.chat import ChatSession, ChatMessage
from backend.utils.async_openai_client import AsyncOpenAIClient
from backend.services.new_rag_service import NewRagService

class ChatService:
    """Serviço para gerenciar conversas de chat."""
    
    def __init__(self, db: Session):
        """Inicializa o serviço de chat.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.openai_client = AsyncOpenAIClient(db)
        self.rag_agent = NewRagService(db)
    
    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista todas as sessões de chat de um usuário específico.
        
        Args:
            user_id: ID do usuário para filtrar sessões
        
        Returns:
            Lista de sessões no formato {session_id, created_at, title}
        """
        sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.created_at.desc()).all()
        
        return [
            {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "title": self._generate_session_title(session.id)
            } 
            for session in sessions
        ]
    
    def _generate_session_title(self, session_db_id: int) -> Optional[str]:
        """Gera um título para a sessão baseado na primeira mensagem do usuário.
        
        Args:
            session_db_id: ID interno da sessão no banco de dados
            
        Returns:
            Título da sessão ou None
        """
        # Obter a primeira mensagem do usuário
        first_message = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_db_id,
            ChatMessage.role == "user"
        ).order_by(ChatMessage.created_at).first()
        
        if not first_message:
            return None
        
        # Limitar o conteúdo da mensagem a 30 caracteres
        title = first_message.content[:30]
        if len(first_message.content) > 30:
            title += "..."
            
        return title
    
    def create_session(self, user_id: str) -> str:
        """Cria uma nova sessão de chat.
        
        Args:
            user_id: ID do usuário que está criando a sessão
            
        Returns:
            ID da sessão criada
        """
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id=session_id, user_id=user_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session_id
    
    def get_session(self, session_id: str, user_id: str = None) -> Optional[ChatSession]:
        """Obtém uma sessão de chat pelo ID.
        
        Args:
            session_id: ID da sessão
            user_id: ID do usuário (opcional, para validação)
            
        Returns:
            Sessão de chat ou None se não existir
        """
        query = self.db.query(ChatSession).filter(ChatSession.session_id == session_id)
        
        # Se um user_id for fornecido, garante que a sessão pertence a este usuário
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
            
        return query.first()
    
    def get_messages(self, session_id: str, include_timestamps: bool = False, user_id: str = None) -> List[Dict[str, Any]]:
        """Obtém todas as mensagens de uma sessão de chat.
        
        Args:
            session_id: ID da sessão
            include_timestamps: Se True, inclui timestamps das mensagens
            user_id: ID do usuário (opcional, para validação)
            
        Returns:
            Lista de mensagens no formato {role, content, timestamp?}
        """
        session = self.get_session(session_id, user_id)
        if not session:
            return []
        
        messages = self.db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at).all()
        
        if include_timestamps:
            return [
                {
                    "role": msg.role, 
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                } 
                for msg in messages
            ]
        else:
            return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def add_message(self, session_id: str, role: str, content: str, user_id: str = None) -> ChatMessage:
        """Adiciona uma mensagem a uma sessão de chat.
        
        Args:
            session_id: ID da sessão
            role: Papel do remetente ('user' ou 'assistant')
            content: Conteúdo da mensagem
            user_id: ID do usuário (opcional, para validação)
            
        Returns:
            Mensagem criada
        """
        session = self.get_session(session_id, user_id)
        if not session:
            if not user_id:
                raise ValueError("user_id é obrigatório para criar uma nova sessão")
            session_id = self.create_session(user_id)
            session = self.get_session(session_id)
        
        message = ChatMessage(
            session_id=session.id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    async def send_message(self, session_id: str, content: str, user_id: str = None) -> Dict[str, Any]:
        """Envia uma mensagem de usuário e obtém resposta.
        
        Args:
            session_id: ID da sessão
            content: Conteúdo da mensagem
            user_id: ID do usuário (opcional, para validação)
            
        Returns:
            Resposta com o texto e detalhes do processamento
        """
        # Adicionar mensagem do usuário
        self.add_message(session_id, "user", content, user_id)
        
        # Obter todas as mensagens da sessão para contexto
        messages = self.get_messages(session_id, user_id=user_id)
        
        # Adicionar sistema inicial se não existe
        if not any(msg["role"] == "system" for msg in messages):
            system_message = {
                "role": "system", 
                "content": (
                    "Você é um assistente de documentação para programadores. "
                    "Forneça respostas precisas e concisas sobre Python, FastAPI e Streamlit. "
                    "Inclua exemplos de código quando apropriado. "
                    "Para exemplos de código, utilize a seguinte formatação: "
                    "```linguagem\ncódigo aqui\n```"
                    "Por exemplo: ```python\nprint('Hello World')\n```"
                    "Se não souber a resposta, diga que não tem essa informação na documentação disponível."
                )
            }
            messages.insert(0, system_message)
            # Adicionar ao banco, mas não ao contexto atual
            self.add_message(session_id, "system", system_message["content"], user_id)
        
        # Determinar se a pergunta é sobre documentação
        use_rag = self._is_documentation_question(content)
        response = None
        rag_error = None
        
        if use_rag:
            try:
                # Usar o novo agente RAG para perguntas de documentação
                response = await self.rag_agent.answer_question(content, messages)
                
                # Adicionar fonte à resposta
                if response.get("sources"):
                    try:
                        # Instead of adding sources as text, we'll keep them structured separately
                        # This way the frontend can display them as bubbles
                        # Add a special marker that our component can recognize
                        response["text"] += "\n\n<sources-list>" 
                        
                        # Add structured information about each source
                        for source in response["sources"]:
                            # Check if source is a string or a dict
                            if isinstance(source, str):
                                # Extract title and URL from source - typically in format "Title: URL"
                                parts = source.split(":", 1)
                                if len(parts) > 1:
                                    title = parts[0].strip()
                                    url = parts[1].strip()
                                else:
                                    title = "Fonte de documentação"
                                    url = source.strip()
                            else:
                                # Handle dict case - use title and url if available or set defaults
                                title = source.get("title", "Fonte de documentação")
                                url = source.get("url", "#")
                                
                            # Add formatted source information
                            response["text"] += f"\n<source title=\"{title}\" url=\"{url}\"></source>"
                        
                        response["text"] += "\n</sources-list>"
                    except Exception as source_error:
                        # If there's an error processing sources, log it but continue
                        import traceback
                        print(f"Error processing sources: {str(source_error)}")
                        print(traceback.format_exc())
                
                # Adicionar resposta ao histórico - moved outside the try block
            except Exception as e:
                # Log do erro e continuar com o modelo normal
                import traceback
                rag_error = str(e)
                print(f"Error in RAG system: {rag_error}")
                print(traceback.format_exc())
                # Não propagar o erro, apenas continuar com o modelo normal
        
        # Save the AI response to the database regardless of where it came from
        try:
            # Usar o modelo normal para outras perguntas ou se o RAG falhou
            if response is None:
                response = await self.openai_client.async_chat_completion(
                    messages=messages,
                    endpoint="chat",
                    temperature=0.7
                )
                
                # Adicionar formatação de código se a pergunta é sobre código mas não usou RAG
                if not use_rag and any(code_term in content.lower() for code_term in ["código", "function", "example", "exemplo", "como"]):
                    # Garantir que a resposta inclua formatação markdown para blocos de código
                    if "```" not in response["text"]:
                        # Adicionar uma dica com exemplo de código formatado corretamente
                        code_example = """
                        
### Exemplo de código Python:

```python
def hello_world():
    print('Olá, mundo!')
    return 'Hello, World!'

# Chamando a função
result = hello_world()
print(result)
```

Você pode copiar o código acima e executá-lo diretamente em um ambiente Python.
"""
                        response["text"] += code_example
            
            # If RAG had an error, add a note about this in the response
            if rag_error:
                response["text"] += f"\n\n*Nota: Houve um erro ao processar fontes de documentação: {rag_error}*"
            
            # Always save the AI response to the database
            self.add_message(session_id, "assistant", response["text"], user_id)
        except Exception as final_error:
            # If everything fails, at least save a generic error message
            error_msg = f"Ocorreu um erro ao processar sua mensagem: {str(final_error)}"
            self.add_message(session_id, "assistant", error_msg, user_id)
            # Create a basic response if it doesn't exist
            if response is None:
                response = {
                    "text": error_msg,
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "tokens_total": 0,
                    "duration_ms": 0
                }
        
        return response
    
    def _is_documentation_question(self, question: str) -> bool:
        """Verifica se a pergunta é sobre documentação de Python, FastAPI ou Streamlit.
        
        Args:
            question: A pergunta do usuário
            
        Returns:
            True se a pergunta for sobre documentação, False caso contrário
        """
        # Palavras-chave que indicam uma pergunta de documentação
        keywords = [
            "python", "fastapi", "streamlit", "documentação", "como usar", "como fazer",
            "exemplo", "código", "tutorial", "função", "método", "classe", "módulo", 
            "import", "api", "web", "http", "request", "response", "app", "dashboard"
        ]
        
        # Verificar se a pergunta contém alguma palavra-chave
        question_lower = question.lower()
        for keyword in keywords:
            if keyword in question_lower:
                return True
        
        # Verificar padrões de perguntas técnicas
        patterns = [
            r"como (eu )?fa[çz]o",
            r"como (eu )?posso",
            r"como (eu )?devo",
            r"como (eu )?utilizo",
            r"como (eu )?implemento",
            r"como (eu )?defino",
            r"qual a maneira",
            r"qual a forma",
            r"existe (um|uma|alguma)",
            r"o que é",
        ]
        
        for pattern in patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    def delete_all_sessions(self, user_id: str) -> None:
        """Deleta todas as sessões de chat e suas mensagens para um usuário específico.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            None
        """
        # Encontra todas as sessões do usuário
        sessions = self.db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
        
        # Delete all messages first to maintain referential integrity
        for session in sessions:
            self.db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
        
        # Then delete all sessions
        self.db.query(ChatSession).filter(ChatSession.user_id == user_id).delete()
        self.db.commit() 