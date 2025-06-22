from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from backend.models.base import get_db
from backend.services.faq_service import FAQService
from backend.services.email_faq_service import EmailFAQService
from backend.services.email_rag_service import EmailRagService
from pydantic import BaseModel

router = APIRouter(
    prefix="/faq",
    tags=["faq"],
    responses={404: {"description": "Not found"}},
)

class FAQEntryBase(BaseModel):
    """Modelo base para entrada de FAQ."""
    question: str
    answer: str
    source: Optional[str] = None
    category: Optional[str] = None
    
class FAQEntryCreate(FAQEntryBase):
    """Modelo para criação de entrada de FAQ."""
    pass
    
class FAQEntryResponse(FAQEntryBase):
    """Modelo para resposta de entrada de FAQ."""
    id: int
    is_published: bool
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True
        
class EmailsRequest(BaseModel):
    """Modelo para requisição de emails para gerar FAQ."""
    emails: List[str]
    num_entries: Optional[int] = 5

class EmailImportRequest(BaseModel):
    """Modelo para requisição de importação de emails."""
    directory_path: str
    
class EmailFAQGenerateRequest(BaseModel):
    """Modelo para requisição de geração de FAQ a partir de emails importados."""
    num_entries: Optional[int] = 10
    
class FAQGenerateResponse(BaseModel):
    """Modelo para resposta de geração de FAQ."""
    entries: List[FAQEntryResponse]
    
class ImportResponse(BaseModel):
    """Modelo para resposta de importação de emails."""
    imported_count: int
    
class ProcessResponse(BaseModel):
    """Modelo para resposta de processamento de emails."""
    processed_count: int
    
class CommonQuestionsResponse(BaseModel):
    """Modelo para resposta de perguntas comuns."""
    questions: List[Dict[str, Any]]

# New models for email RAG FAQ generation
class EmailQuestionResponse(BaseModel):
    """Model for email question response."""
    id: int
    question: str
    email_filename: str
    email_subject: Optional[str] = None

class EmailAnswerRequest(BaseModel):
    """Model for email answer request."""
    question_id: int

class EmailAnswerResponse(BaseModel):
    """Model for email answer response."""
    question_id: int
    question_text: str
    answer: str
    email_filename: str
    sources: Optional[List[Dict[str, Any]]] = None

class EmailGenerateFAQRequest(BaseModel):
    """Model for request to generate FAQ entries from email questions."""
    limit: Optional[int] = None

@router.get("/entries", response_model=List[FAQEntryResponse])
def get_faq_entries(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Obtém todas as entradas de FAQ."""
    service = FAQService(db)
    entries = service.get_all_entries(category)
    return entries

@router.get("/entries/{entry_id}", response_model=FAQEntryResponse)
def get_faq_entry(entry_id: int, db: Session = Depends(get_db)):
    """Obtém uma entrada de FAQ pelo ID."""
    service = FAQService(db)
    entry = service.get_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entrada de FAQ com ID {entry_id} não encontrada"
        )
    return entry

@router.post("/entries", response_model=FAQEntryResponse)
def create_faq_entry(request: FAQEntryCreate, db: Session = Depends(get_db)):
    """Cria uma nova entrada de FAQ."""
    service = FAQService(db)
    entry = service.create_entry(
        question=request.question,
        answer=request.answer,
        source=request.source,
        category=request.category
    )
    return entry

@router.delete("/entries/{entry_id}", response_model=Dict[str, bool])
def delete_faq_entry(entry_id: int, db: Session = Depends(get_db)):
    """Remove uma entrada de FAQ."""
    service = FAQService(db)
    success = service.delete_entry(entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entrada de FAQ com ID {entry_id} não encontrada"
        )
    return {"success": True}

@router.post("/generate", response_model=FAQGenerateResponse)
def generate_faq(request: EmailsRequest, db: Session = Depends(get_db)):
    """Gera entradas de FAQ a partir de emails de suporte."""
    service = FAQService(db)
    
    try:
        entries = service.generate_faq_from_emails(request.emails, request.num_entries)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# New routes for email-based FAQ generation

@router.post("/emails/import", response_model=ImportResponse) 
def import_emails(request: EmailImportRequest, db: Session = Depends(get_db)):
    """Importa emails de um diretório para análise e geração de FAQ."""
    service = EmailFAQService(db)
    
    try:
        imported_count = service.import_emails_from_directory(request.directory_path)
        return {"imported_count": imported_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao importar emails: {str(e)}"
        )

@router.post("/emails/process", response_model=ProcessResponse)
def process_emails(batch_size: Optional[int] = 50, db: Session = Depends(get_db)):
    """Processa emails importados para extrair questões."""
    service = EmailFAQService(db)
    
    try:
        processed_count = service.extract_questions_from_emails(batch_size)
        return {"processed_count": processed_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar emails: {str(e)}"
        )

@router.get("/emails/common-questions", response_model=CommonQuestionsResponse)
def get_common_questions(limit: Optional[int] = 20, min_similarity: Optional[float] = 0.85, 
                        db: Session = Depends(get_db)):
    """Obtém as perguntas mais comuns dos emails processados."""
    service = EmailFAQService(db)
    
    try:
        questions = service.identify_common_questions(min_similarity, limit)
        return {
            "questions": [
                {"question": q, "frequency": f} for q, f in questions
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao identificar perguntas comuns: {str(e)}"
        )

@router.post("/emails/generate-faq", response_model=FAQGenerateResponse)
def generate_faq_from_emails(request: EmailFAQGenerateRequest, db: Session = Depends(get_db)):
    """Gera FAQ a partir de perguntas comuns identificadas nos emails importados."""
    service = EmailFAQService(db)
    
    try:
        entries = service.generate_faq_from_common_questions(request.num_entries)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar FAQ: {str(e)}"
        )

# New routes for email RAG FAQ generation
@router.get("/email-questions", response_model=List[EmailQuestionResponse])
def get_email_questions(db: Session = Depends(get_db)):
    """Get all questions extracted from emails."""
    service = EmailRagService(db)
    questions = service.get_all_questions()
    return questions

@router.post("/email-questions/{question_id}/answer", response_model=EmailAnswerResponse)
async def generate_answer_for_email_question(question_id: int, db: Session = Depends(get_db)):
    """Generate an answer for a specific email question using RAG."""
    service = EmailRagService(db)
    
    try:
        answer = await service.generate_faq_answer(question_id)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found or could not be answered"
            )
        return answer
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )

@router.post("/email-questions/{question_id}/create-faq", response_model=FAQEntryResponse)
async def create_faq_from_email_question(question_id: int, db: Session = Depends(get_db)):
    """Create a FAQ entry from a specific email question."""
    service = EmailRagService(db)
    
    try:
        entry = await service.generate_faq_entry(question_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create FAQ entry for question ID {question_id}"
            )
        return entry
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating FAQ entry: {str(e)}"
        )

@router.post("/email-questions/generate-all", response_model=FAQGenerateResponse)
async def generate_all_faq_from_emails(request: EmailGenerateFAQRequest, db: Session = Depends(get_db)):
    """Generate FAQ entries for all or a limited number of email questions."""
    service = EmailRagService(db)
    
    try:
        entries = await service.generate_all_faq_entries(request.limit)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating FAQ entries: {str(e)}"
        )