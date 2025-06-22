from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from datetime import datetime

from .base import Base

class EmailQuestion(Base):
    """Model for storing user emails with questions and extracted question content."""
    
    __tablename__ = "email_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    email_subject = Column(String(255), nullable=True)
    email_body = Column(Text, nullable=False)
    extracted_question = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    frequency = Column(Integer, default=1)  # For tracking similar questions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create index on extracted_question for faster clustering and searching
    __table_args__ = (
        Index('idx_extracted_question', extracted_question),
    )
    
    def __repr__(self):
        return f"<EmailQuestion(id={self.id}, extracted_question={self.extracted_question[:30]}...)>" 