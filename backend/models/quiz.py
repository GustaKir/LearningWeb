from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Quiz(Base):
    """Modelo para armazenar quizzes."""
    
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    topic = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com as questões
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quiz(id={self.id}, title={self.title})>"


class QuizQuestion(Base):
    """Modelo para armazenar questões de quiz."""
    
    __tablename__ = "quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_text = Column(Text)
    explanation = Column(Text, nullable=True)  # Explicação da resposta correta
    
    # Relacionamento com o quiz
    quiz = relationship("Quiz", back_populates="questions")
    
    # Relacionamento com as alternativas
    alternatives = relationship("QuizAlternative", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuizQuestion(id={self.id}, quiz_id={self.quiz_id})>"


class QuizAlternative(Base):
    """Modelo para armazenar alternativas de questões de quiz."""
    
    __tablename__ = "quiz_alternatives"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"))
    text = Column(Text)
    is_correct = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)  # Explicação do porquê essa alternativa está correta ou incorreta
    
    # Relacionamento com a questão
    question = relationship("QuizQuestion", back_populates="alternatives")
    
    def __repr__(self):
        return f"<QuizAlternative(id={self.id}, is_correct={self.is_correct})>" 