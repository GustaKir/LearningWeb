from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.models.base import get_db
from backend.services.quiz_service import QuizService
from pydantic import BaseModel

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"],
    responses={404: {"description": "Not found"}},
)

# Helper function to convert datetime to string
def format_quiz_dates(quiz):
    """Converte datetime objects para strings no formato ISO e preserva relationships."""
    if not quiz:
        return None
        
    # Create a dictionary with all quiz attributes
    result = {}
    
    # Copy basic fields
    for key, value in quiz.__dict__.items():
        if key != '_sa_instance_state':
            if key == 'created_at' and isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
    
    # Preserve relationships
    if hasattr(quiz, 'questions'):
        result['questions'] = [
            {
                'id': q.id,
                'question_text': q.question_text,
                'explanation': q.explanation,
                'alternatives': [
                    {
                        'id': a.id,
                        'text': a.text,
                        'is_correct': a.is_correct,
                        'explanation': a.explanation
                    } 
                    for a in q.alternatives
                ]
            }
            for q in quiz.questions
        ]
    
    return result

class QuizCreate(BaseModel):
    """Modelo para criação de quiz."""
    title: str
    topic: str
    
class QuizGenerateRequest(BaseModel):
    """Modelo para requisição de geração de quiz."""
    topic: str
    num_questions: Optional[int] = 5
    num_alternatives: Optional[int] = 4
    
class AlternativeResponse(BaseModel):
    """Modelo para resposta de alternativa."""
    id: int
    text: str
    is_correct: Optional[bool] = None  # Opcional para não revelar a resposta correta antes do usuário escolher
    explanation: Optional[str] = None  # Opcional pela mesma razão
    
    class Config:
        orm_mode = True
    
class QuestionResponse(BaseModel):
    """Modelo para resposta de pergunta."""
    id: int
    question_text: str
    explanation: Optional[str] = None
    alternatives: List[AlternativeResponse]
    
    class Config:
        orm_mode = True
    
class QuizResponse(BaseModel):
    """Modelo para resposta de quiz."""
    id: int
    title: str
    topic: str
    created_at: str
    questions: List[QuestionResponse]
    
    class Config:
        orm_mode = True
        
class CheckAnswerRequest(BaseModel):
    """Modelo para requisição de verificação de resposta."""
    alternative_id: int
    
class CheckAnswerResponse(BaseModel):
    """Modelo para resposta de verificação de resposta."""
    is_correct: bool
    explanation: Optional[str] = None

@router.get("/quizzes", response_model=List[QuizResponse])
def get_all_quizzes(db: Session = Depends(get_db)):
    """Obtém todos os quizzes."""
    service = QuizService(db)
    quizzes = service.get_all_quizzes()
    # Convert datetime to string for each quiz
    return [format_quiz_dates(quiz) for quiz in quizzes]

@router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Obtém um quiz pelo ID."""
    service = QuizService(db)
    quiz = service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz com ID {quiz_id} não encontrado"
        )
    return format_quiz_dates(quiz)

@router.post("/quizzes", response_model=QuizResponse)
def create_quiz(request: QuizCreate, db: Session = Depends(get_db)):
    """Cria um novo quiz."""
    service = QuizService(db)
    quiz = service.create_quiz(request.title, request.topic)
    return format_quiz_dates(quiz)

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizGenerateRequest, db: Session = Depends(get_db)):
    """Gera um quiz sobre um tópico específico."""
    service = QuizService(db)
    
    try:
        quiz = await service.generate_quiz(
            topic=request.topic,
            num_questions=request.num_questions,
            num_alternatives=request.num_alternatives
        )
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível gerar o quiz"
            )
        return format_quiz_dates(quiz)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/check-answer", response_model=CheckAnswerResponse)
def check_answer(request: CheckAnswerRequest, db: Session = Depends(get_db)):
    """Verifica se uma alternativa está correta."""
    service = QuizService(db)
    result = service.check_answer(request.alternative_id)
    return result

@router.delete("/quizzes/{quiz_id}", response_model=Dict[str, bool])
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Remove um quiz."""
    service = QuizService(db)
    success = service.delete_quiz(quiz_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz com ID {quiz_id} não encontrado"
        )
    return {"success": True} 