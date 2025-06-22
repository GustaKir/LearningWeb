import os
import logging
import time
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from backend.services.new_rag_service import NewRagService
from backend.utils.openai_client import OpenAIClient
from backend.models.faq import FAQEntry
from backend.models.logging import APILog

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailRagService:
    """
    Service for generating FAQ answers from email questions using RAG.
    """
    
    def __init__(self, db: Session):
        """Initialize the email RAG service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.rag_service = NewRagService(db)
        self.openai_client = OpenAIClient(db)
        
        # Get the path to the emails.db file
        base_dir = Path(__file__).resolve().parent.parent
        self.emails_db_path = base_dir / "db" / "emails.db"
        
        if not os.path.exists(self.emails_db_path):
            logger.error(f"Email database not found at {self.emails_db_path}")
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """Get all questions from the emails database.
        
        Returns:
            List of dictionaries containing question data
        """
        if not os.path.exists(self.emails_db_path):
            logger.error(f"Email database not found at {self.emails_db_path}")
            return []
        
        try:
            conn = sqlite3.connect(self.emails_db_path)
            cursor = conn.cursor()
            
            # Query the questions with email filenames
            cursor.execute("""
                SELECT q.id, q.question_text, e.filename, e.subject
                FROM questions q
                JOIN emails e ON q.email_id = e.id
                ORDER BY q.id;
            """)
            
            questions = []
            for row in cursor.fetchall():
                q_id, question_text, filename, subject = row
                questions.append({
                    "id": q_id,
                    "question": question_text,
                    "email_filename": filename,
                    "email_subject": subject
                })
            
            conn.close()
            return questions
            
        except Exception as e:
            logger.error(f"Error retrieving questions from emails.db: {e}")
            return []
    
    async def generate_faq_answer(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Generate an answer for a specific question using RAG.
        
        Args:
            question_id: ID of the question to answer
            
        Returns:
            Dictionary with generated answer and metadata
        """
        if not os.path.exists(self.emails_db_path):
            logger.error(f"Email database not found at {self.emails_db_path}")
            return None
        
        try:
            # Get the question text
            conn = sqlite3.connect(self.emails_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT q.question_text, e.filename, e.subject
                FROM questions q
                JOIN emails e ON q.email_id = e.id
                WHERE q.id = ?;
            """, (question_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                logger.error(f"Question with ID {question_id} not found")
                return None
            
            question_text, filename, subject = result
            
            # Use the RAG service to answer the question
            response = await self.rag_service.answer_question(question_text)
            
            # Create a formatted response
            answer = {
                "question_id": question_id,
                "question_text": question_text,
                "email_filename": filename,
                "email_subject": subject,
                "answer": response["text"],
                "sources": response.get("sources", []),
                "tokens_total": response.get("tokens_total", 0),
                "duration_ms": response.get("duration_ms", 0)
            }
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating FAQ answer: {e}")
            return None
    
    async def generate_faq_entry(self, question_id: int) -> Optional[FAQEntry]:
        """Generate a FAQ entry for a specific question using RAG and save it to the database.
        
        Args:
            question_id: ID of the question to answer
            
        Returns:
            Created FAQEntry object or None if failed
        """
        answer_data = await self.generate_faq_answer(question_id)
        
        if not answer_data:
            return None
        
        try:
            # Determine the category of the question
            category = self._determine_category(answer_data["question_text"], answer_data["answer"])
            
            # Create a new FAQ entry
            faq_entry = FAQEntry(
                question=answer_data["question_text"],
                answer=answer_data["answer"],
                source=f"Email: {answer_data['email_filename']}",
                category=category,
                is_published=True
            )
            
            # Save to database
            self.db.add(faq_entry)
            self.db.commit()
            self.db.refresh(faq_entry)
            
            return faq_entry
            
        except Exception as e:
            logger.error(f"Error creating FAQ entry: {e}")
            self.db.rollback()
            return None
    
    async def generate_all_faq_entries(self, limit: int = None) -> List[FAQEntry]:
        """Generate FAQ entries for all or a limited number of questions.
        
        Args:
            limit: Optional limit on the number of entries to generate
            
        Returns:
            List of created FAQEntry objects
        """
        questions = self.get_all_questions()
        
        if limit:
            questions = questions[:limit]
        
        faq_entries = []
        
        for question in questions:
            try:
                entry = await self.generate_faq_entry(question["id"])
                if entry:
                    faq_entries.append(entry)
            except Exception as e:
                logger.error(f"Error generating FAQ entry for question {question['id']}: {e}")
        
        return faq_entries
    
    def _determine_category(self, question: str, answer: str) -> str:
        """Determine the category of a question and answer pair.
        
        Args:
            question: The question text
            answer: The generated answer
            
        Returns:
            Category string (Python, FastAPI, Streamlit, or Other)
        """
        try:
            # Combine question and answer for context
            content = f"{question}\n\n{answer}"
            
            # Check for category keywords
            content_lower = content.lower()
            
            if "fastapi" in content_lower:
                return "FastAPI"
            elif "streamlit" in content_lower or "st." in content_lower:
                return "Streamlit"
            elif "python" in content_lower or "def " in content_lower or "class " in content_lower:
                return "Python"
            
            # If no keywords found, ask the AI
            prompt = f"""
            Determine the primary category for this question and answer:
            
            Question: {question}
            Answer: {answer}
            
            Choose ONE category from: Python, FastAPI, Streamlit, or Other.
            Respond with ONLY the category name.
            """
            
            response = self.openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                endpoint="categorize_faq",
                temperature=0
            )
            
            category = response["text"].strip()
            
            # Validate and normalize the category
            valid_categories = ["Python", "FastAPI", "Streamlit", "Other"]
            for valid in valid_categories:
                if valid.lower() in category.lower():
                    return valid
            
            return "Other"
            
        except Exception as e:
            logger.error(f"Error determining category: {e}")
            return "Other" 