import os
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

def get_openai_api_key() -> str:
    """Retorna a chave da API OpenAI das variáveis de ambiente."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
    return api_key

def get_embeddings_model() -> str:
    """Retorna o modelo de embeddings das variáveis de ambiente."""
    return os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")

def get_chat_model() -> str:
    """Retorna o modelo de chat das variáveis de ambiente."""
    return os.getenv("CHAT_MODEL", "gpt-4.1-mini") 