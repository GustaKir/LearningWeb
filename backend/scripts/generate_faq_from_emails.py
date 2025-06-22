#!/usr/bin/env python3
"""
Script to generate FAQs from emails in a database.

This script demonstrates the complete process of importing emails,
extracting questions, and generating a FAQ based on the most common questions.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy.orm import Session
from backend.models.base import get_db, SessionLocal, init_db
from backend.services.email_faq_service import EmailFAQService
from backend.models.email import EmailQuestion

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_complete_process(email_dir: str, num_faq_entries: int = 10):
    """
    Run the complete process of importing emails, extracting questions,
    and generating a FAQ.
    
    Args:
        email_dir: Directory containing email files (.json or .eml)
        num_faq_entries: Number of FAQ entries to generate
    """
    # Initialize database
    init_db()
    
    # Create a database session
    db: Session = SessionLocal()
    
    try:
        # Create service
        service = EmailFAQService(db)
        
        # Step 1: Import emails
        logger.info(f"Importing emails from {email_dir}")
        imported_count = service.import_emails_from_directory(email_dir)
        logger.info(f"Imported {imported_count} emails")
        
        if imported_count == 0:
            logger.warning("No emails imported. Please check the directory path.")
            return
        
        # Display the imported emails before processing
        imported_emails = db.query(EmailQuestion).filter(
            EmailQuestion.processed == False
        ).all()
        
        logger.info(f"\nImported {len(imported_emails)} emails:")
        for i, email in enumerate(imported_emails):
            logger.info(f"\n--- Email {i+1} ---")
            logger.info(f"Subject: {email.email_subject}")
            logger.info(f"Body: {email.email_body[:150]}..." if len(email.email_body) > 150 else f"Body: {email.email_body}")
            
        # Step 2: Extract questions
        logger.info("\nExtracting questions from emails")
        processed_count = service.extract_questions_from_emails()
        logger.info(f"Processed {processed_count} emails")
        
        if processed_count == 0:
            logger.warning("No emails processed. Please check the database.")
            return
        
        # Display the extracted questions
        processed_emails = db.query(EmailQuestion).filter(
            EmailQuestion.processed == True
        ).all()
        
        logger.info(f"\nExtracted questions from {len(processed_emails)} emails:")
        for i, email in enumerate(processed_emails):
            logger.info(f"{i+1}. Original subject: {email.email_subject}")
            logger.info(f"   Extracted question: {email.extracted_question}")
            
        # Step 3: Identify common questions
        logger.info("\nIdentifying common questions")
        common_questions = service.identify_common_questions()
        
        if not common_questions:
            logger.warning("No common questions identified.")
            return
        
        logger.info(f"\nIdentified {len(common_questions)} common question clusters:")
        for i, (question, frequency) in enumerate(common_questions):
            logger.info(f"{i+1}. '{question}' (frequency: {frequency})")
        
        # Step 4: Generate FAQ entries
        logger.info(f"\nGenerating {num_faq_entries} FAQ entries")
        entries = service.generate_faq_from_common_questions(num_faq_entries)
        
        # Print results
        logger.info(f"\nGenerated {len(entries)} FAQ entries:")
        for i, entry in enumerate(entries):
            logger.info(f"\n--- FAQ Entry {i+1} ---")
            logger.info(f"Question: {entry.question}")
            logger.info(f"Answer: {entry.answer[:150]}..." if len(entry.answer) > 150 else f"Answer: {entry.answer}")
            logger.info(f"Category: {entry.category}")
            logger.info(f"Source: {entry.source}")
        
        logger.info("\nFAQ generation complete!")
        
    except Exception as e:
        logger.error(f"Error generating FAQ: {str(e)}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    # Default directory for email files
    default_email_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "emails")
    
    # Get directory from command line arguments or use default
    email_dir = sys.argv[1] if len(sys.argv) > 1 else default_email_dir
    
    # Get number of FAQ entries from command line arguments or use default
    num_entries = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Run the process
    run_complete_process(email_dir, num_entries) 