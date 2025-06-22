from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime

from .base import Base

class FAQEntry(Base):
    """Modelo para armazenar entradas de FAQ."""
    
    __tablename__ = "faq_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, index=True)
    answer = Column(Text)
    source = Column(Text, nullable=True)  # Fonte da documentação
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = Column(Boolean, default=True)
    category = Column(String(100), nullable=True)  # Python, FastAPI ou Streamlit
    
    def __repr__(self):
        return f"<FAQEntry(id={self.id}, question={self.question[:30]}...)>" 