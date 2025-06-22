from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
import traceback

from backend.models.base import Base, engine
from backend.routes import chat, faq, quiz
from backend.chains import get_rag_chain

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar as tabelas do banco de dados
Base.metadata.create_all(bind=engine)

# Initialize RAG chain
try:
    logger.info("Initializing RAG chain...")
    rag_chain = get_rag_chain()
    logger.info("RAG chain initialized successfully")
except Exception as e:
    logger.error(f"Error initializing RAG chain: {e}")
    logger.warning("API will start, but RAG functionality may not work properly")

app = FastAPI(
    title="EdTech Futura API",
    description="API para o portal educacional da EdTech Futura",
    version="1.0.0"
)

# Exception handler for detailed error logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and log them with traceback."""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde."}
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, isto deve ser restrito para origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(chat.router)
app.include_router(faq.router)
app.include_router(quiz.router)

@app.get("/health", tags=["Utils"])
def health_check():
    """Verifica a saúde da API."""
    return {"status": "ok"}

@app.get("/", tags=["Utils"])
def root():
    """Rota raiz da API."""
    return {
        "message": "Bem-vindo à API do portal educacional da EdTech Futura",
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat",
            "faq": "/faq",
            "quiz": "/quiz"
        }
    }
