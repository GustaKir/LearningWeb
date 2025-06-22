from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Definir caminho para o banco de dados SQLite
DATABASE_URL = "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "app.db")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar base para os modelos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para inicializar o banco de dados
def init_db():
    """Initialize database by creating all tables."""
    # Import all models here to ensure they are registered with Base
    from backend.models import (
        ChatSession, ChatMessage,
        FAQEntry,
        Quiz, QuizQuestion, QuizAlternative,
        APILog,
        EmailQuestion
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine) 