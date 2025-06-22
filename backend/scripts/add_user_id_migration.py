"""
Script de migração para adicionar a coluna user_id à tabela chat_sessions.
"""
import uuid
import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, Column, String, text
from sqlalchemy.orm import sessionmaker

from backend.models.base import get_db, Base
from backend.models.chat import ChatSession, ChatMessage

def run_migration():
    """Executa a migração para adicionar a coluna user_id."""
    
    print("Iniciando migração para adicionar coluna user_id...")
    
    try:
        # Cria uma sessão do banco de dados
        db = next(get_db())
        
        # Verifica se a coluna já existe
        try:
            # Tenta executar uma consulta que use a coluna user_id
            db.execute(text("SELECT user_id FROM chat_sessions LIMIT 1"))
            print("A coluna user_id já existe na tabela chat_sessions.")
            return
        except Exception:
            print("A coluna user_id não existe. Adicionando...")
        
        # Adiciona a coluna user_id
        db.execute(text("ALTER TABLE chat_sessions ADD COLUMN user_id VARCHAR(100)"))
        
        # Cria um índice para melhorar o desempenho de consultas
        db.execute(text("CREATE INDEX ix_chat_sessions_user_id ON chat_sessions (user_id)"))
        
        # Atribui um valor padrão (mesmo ID) a todas as sessões existentes
        # Primeiro, gera um ID aleatório para aplicar a todas as sessões existentes
        default_user_id = str(uuid.uuid4())
        db.execute(text(f"UPDATE chat_sessions SET user_id = '{default_user_id}' WHERE user_id IS NULL"))
        
        # Confirma as alterações
        db.commit()
        
        print(f"Migração concluída! Todas as sessões existentes foram atribuídas ao ID de usuário: {default_user_id}")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        raise
    
if __name__ == "__main__":
    run_migration() 