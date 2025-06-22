from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class ChatSession(Base):
    """Modelo para armazenar sessões de chat."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    user_id = Column(String(100), index=True)  # User identifier from cookie
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com as mensagens
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id={self.session_id}, user_id={self.user_id})>"


class ChatMessage(Base):
    """Modelo para armazenar mensagens de chat."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String(50))  # 'user' ou 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com a sessão
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role})>" 