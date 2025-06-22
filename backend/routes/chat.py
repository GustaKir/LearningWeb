from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from backend.models.base import get_db
from backend.services.chat_service import ChatService
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

class ChatMessageRequest(BaseModel):
    """Modelo para requisição de mensagem de chat."""
    content: str
    
class ChatMessageResponse(BaseModel):
    """Modelo para resposta de mensagem de chat."""
    text: str
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    duration_ms: float
    
class ChatSessionResponse(BaseModel):
    """Modelo para resposta de sessão de chat."""
    session_id: str
    
class ChatHistoryMessage(BaseModel):
    """Modelo para mensagem no histórico de chat."""
    role: str
    content: str
    timestamp: Optional[str] = Field(None, description="ISO format timestamp of the message")

class ChatSessionInfo(BaseModel):
    """Modelo para informações de sessão de chat."""
    session_id: str
    created_at: str
    title: Optional[str] = None
    
class ChatSessionListResponse(BaseModel):
    """Modelo para resposta de lista de sessões de chat."""
    sessions: List[ChatSessionInfo]
    
class ChatHistoryResponse(BaseModel):
    """Modelo para resposta de histórico de chat."""
    messages: List[ChatHistoryMessage]
    title: Optional[str] = None

def get_or_create_user_id(response: Response, user_id: Optional[str] = Cookie(None)) -> str:
    """Obtém ou cria um ID de usuário único usando cookies.
    
    Args:
        response: Objeto de resposta para definir o cookie
        user_id: ID do usuário existente do cookie
        
    Returns:
        ID do usuário (existente ou novo)
    """
    if not user_id:
        # Cria um novo ID de usuário se não existir
        user_id = str(uuid.uuid4())
        # Define o cookie para expirar em 1 ano (em segundos)
        expires_in = 60 * 60 * 24 * 365
        # Define o cookie como HTTP-only para maior segurança
        response.set_cookie(key="user_id", value=user_id, max_age=expires_in, httponly=True)
    
    return user_id

@router.get("/sessions", response_model=ChatSessionListResponse)
def list_sessions(
    response: Response, 
    db: Session = Depends(get_db),
    user_id: Optional[str] = Cookie(None)
):
    """Lista todas as sessões de chat do usuário."""
    user_id = get_or_create_user_id(response, user_id)
    service = ChatService(db)
    sessions = service.list_sessions(user_id)
    return {"sessions": sessions}

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    response: Response,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Cookie(None)
):
    """Cria uma nova sessão de chat."""
    user_id = get_or_create_user_id(response, user_id)
    service = ChatService(db)
    session_id = service.create_session(user_id)
    return {"session_id": session_id}

@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str, 
    response: Response,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Cookie(None)
):
    """Obtém o histórico de mensagens de uma sessão de chat."""
    user_id = get_or_create_user_id(response, user_id)
    service = ChatService(db)
    messages = service.get_messages(session_id, include_timestamps=True, user_id=user_id)
    # Filter out system messages when returning to frontend
    user_assistant_messages = [msg for msg in messages if msg["role"] != "system"]
    
    # Get session title from the first user message
    session = service.get_session(session_id, user_id)
    title = service._generate_session_title(session.id) if session else None
    
    # Ensure all messages have all required fields properly formatted
    formatted_messages = []
    for msg in user_assistant_messages:
        formatted_messages.append(
            ChatHistoryMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp")
            )
        )
    
    return {
        "messages": formatted_messages,
        "title": title
    }

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str, 
    request: ChatMessageRequest, 
    response: Response,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Cookie(None)
):
    """Envia uma mensagem para o chat e obtém a resposta."""
    user_id = get_or_create_user_id(response, user_id)
    service = ChatService(db)
    
    try:
        chat_response = await service.send_message(session_id, request.content, user_id)
        return ChatMessageResponse(
            text=chat_response["text"],
            tokens_prompt=chat_response["tokens_prompt"],
            tokens_completion=chat_response["tokens_completion"],
            tokens_total=chat_response["tokens_total"],
            duration_ms=chat_response["duration_ms"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_sessions(
    response: Response,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Cookie(None)
):
    """Deleta todas as sessões de chat do usuário atual."""
    user_id = get_or_create_user_id(response, user_id)
    service = ChatService(db)
    service.delete_all_sessions(user_id)
    return None 