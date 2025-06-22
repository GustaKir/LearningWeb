from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime

from .base import Base

class APILog(Base):
    """Modelo para armazenar logs de uso da API da OpenAI."""
    
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    endpoint = Column(String(255))  # Qual endpoint foi chamado (chat, faq, quiz)
    prompt = Column(Text)  # Prompt enviado para a API
    response = Column(Text)  # Resposta recebida da API
    tokens_prompt = Column(Integer)  # Número de tokens no prompt
    tokens_completion = Column(Integer)  # Número de tokens na resposta
    tokens_total = Column(Integer)  # Total de tokens utilizados
    model = Column(String(100))  # Modelo utilizado (gpt-4.1-mini)
    duration_ms = Column(Float)  # Duração da chamada em milissegundos
    
    def __repr__(self):
        return f"<APILog(id={self.id}, endpoint={self.endpoint}, model={self.model})>" 