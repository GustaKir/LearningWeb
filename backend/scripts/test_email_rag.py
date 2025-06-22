import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from backend.models.base import SessionLocal, engine, Base
from backend.services.email_rag_service import EmailRagService

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

async def test_email_rag():
    """Test the email RAG functionality."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Initialize the service
        service = EmailRagService(db)
        
        # 1. List all questions
        print("Getting all questions from emails.db...")
        questions = service.get_all_questions()
        
        if not questions:
            print("No questions found in the database.")
            return
        
        print(f"Found {len(questions)} questions in the database.")
        
        # Display first 3 questions
        print("\nFirst 3 questions:")
        for i, q in enumerate(questions[:3], 1):
            print(f"{i}. {q['question']} (from {q['email_filename']})")
        
        # 2. Generate an answer for the first question
        if questions:
            first_question = questions[0]
            print(f"\nGenerating answer for question ID {first_question['id']}:")
            print(f"Question: {first_question['question']}")
            
            answer = await service.generate_faq_answer(first_question['id'])
            
            if answer:
                print("\nGenerated answer:")
                print(f"{answer['answer']}")
                
                if answer.get('sources'):
                    print("\nSources used:")
                    for source in answer['sources']:
                        print(f"- {source.get('title')} ({source.get('source')})")
            else:
                print("Failed to generate an answer.")
        
        # 3. Create a FAQ entry
        if questions:
            print("\nCreating FAQ entry for the question...")
            faq_entry = await service.generate_faq_entry(questions[0]['id'])
            
            if faq_entry:
                print(f"Created FAQ entry with ID {faq_entry.id}")
                print(f"Category: {faq_entry.category}")
            else:
                print("Failed to create FAQ entry.")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_email_rag()) 