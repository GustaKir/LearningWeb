from typing import List, Dict, Any, Optional, Tuple
import os
import json
import email
import re
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc
import logging

from backend.models.email import EmailQuestion
from backend.models.faq import FAQEntry
from backend.utils.openai_client import OpenAIClient
from backend.services.new_rag_service import NewRagService

class EmailFAQService:
    """Service for managing email import, question extraction, and FAQ generation."""
    
    def __init__(self, db: Session):
        """Initialize the email FAQ service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.openai_client = OpenAIClient(db)
        self.rag_agent = NewRagService(db)
        self.logger = logging.getLogger(__name__)
    
    def import_emails_from_directory(self, directory_path: str) -> int:
        """Import emails from JSON files and .eml files in a directory.
        
        Args:
            directory_path: Path to directory containing email files
            
        Returns:
            Number of emails imported
        """
        email_dir = Path(directory_path)
        if not email_dir.exists() or not email_dir.is_dir():
            self.logger.error(f"Directory not found: {directory_path}")
            return 0
        
        imported_count = 0
        
        # Process JSON files
        for file_path in email_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    emails_data = json.load(f)
                
                # Handle either single email or list of emails
                if isinstance(emails_data, dict):
                    emails_data = [emails_data]
                
                for email_data in emails_data:
                    # Basic validation
                    if "body" not in email_data:
                        self.logger.warning(f"Skipping email without body in {file_path}")
                        continue
                    
                    # Create email record
                    email_record = EmailQuestion(
                        email_subject=email_data.get("subject", ""),
                        email_body=email_data["body"],
                        processed=False
                    )
                    self.db.add(email_record)
                    imported_count += 1
                
                self.db.commit()
                
            except Exception as e:
                self.logger.error(f"Error importing emails from JSON {file_path}: {str(e)}")
                self.db.rollback()
        
        # Process .eml files
        for file_path in email_dir.glob("*.eml"):
            try:
                email_record = self._parse_eml_file(file_path)
                if email_record:
                    self.db.add(email_record)
                    imported_count += 1
                    self.db.commit()
            except Exception as e:
                self.logger.error(f"Error importing email from EML {file_path}: {str(e)}")
                self.db.rollback()
        
        return imported_count
    
    def _parse_eml_file(self, file_path: Path) -> Optional[EmailQuestion]:
        """Parse an .eml file and extract email data.
        
        Args:
            file_path: Path to the .eml file
            
        Returns:
            EmailQuestion object or None if parsing failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                msg = email.message_from_file(f)
            
            subject = msg.get("Subject", "")
            # Decode any encoded subject
            if subject.startswith("=?") and "?=" in subject:
                subject = self._decode_mime_header(subject)
            
            # Extract body from either plain text or html part
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        charset = self._get_charset(part)
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(charset or 'utf-8', errors='replace')
                            break
                    elif content_type == "text/html" and not body:
                        # Use HTML part only if we don't have plain text
                        charset = self._get_charset(part)
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_body = payload.decode(charset or 'utf-8', errors='replace')
                            # Strip HTML tags for a simple text representation
                            body = re.sub(r'<[^>]+>', '', html_body)
                            body = re.sub(r'\s+', ' ', body).strip()
            else:
                charset = self._get_charset(msg)
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset or 'utf-8', errors='replace')
            
            if not body:
                self.logger.warning(f"Could not extract body from {file_path}")
                return None
            
            return EmailQuestion(
                email_subject=subject,
                email_body=body,
                processed=False
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing EML file {file_path}: {str(e)}")
            return None
    
    def _get_charset(self, message_part) -> Optional[str]:
        """Get charset from a message part.
        
        Args:
            message_part: Email message part
            
        Returns:
            Charset string or None
        """
        charset = message_part.get_charset()
        if charset:
            return str(charset)
        
        content_type = message_part.get("Content-Type", "")
        match = re.search(r'charset="?([^";]+)"?', content_type)
        if match:
            return match.group(1)
        
        return None
    
    def _decode_mime_header(self, header: str) -> str:
        """Decode MIME encoded email headers.
        
        Args:
            header: MIME encoded header
            
        Returns:
            Decoded header
        """
        try:
            decoded_header = email.header.decode_header(header)
            parts = []
            for part, encoding in decoded_header:
                if isinstance(part, bytes):
                    if encoding:
                        parts.append(part.decode(encoding, errors='replace'))
                    else:
                        parts.append(part.decode('utf-8', errors='replace'))
                else:
                    parts.append(part)
            return ''.join(parts)
        except Exception as e:
            self.logger.warning(f"Error decoding header: {str(e)}")
            return header
    
    def extract_questions_from_emails(self, batch_size: int = 50) -> int:
        """Extract questions from unprocessed emails.
        
        Args:
            batch_size: Number of emails to process in one batch
            
        Returns:
            Number of emails processed
        """
        # Get unprocessed emails
        unprocessed_emails = self.db.query(EmailQuestion).filter(
            EmailQuestion.processed == False
        ).limit(batch_size).all()
        
        if not unprocessed_emails:
            return 0
        
        processed_count = 0
        batch_items = []
        
        for i, email in enumerate(unprocessed_emails):
            batch_items.append(email)
            
            # Process in smaller batches for the AI
            if len(batch_items) >= 10 or i == len(unprocessed_emails) - 1:
                self._process_email_batch(batch_items)
                processed_count += len(batch_items)
                batch_items = []
        
        return processed_count
    
    def _process_email_batch(self, emails: List[EmailQuestion]) -> None:
        """Process a batch of emails to extract questions.
        
        Args:
            emails: List of email questions to process
        """
        if not emails:
            return
        
        email_texts = [
            f"Email {i+1}:\nSubject: {email.email_subject}\nBody: {email.email_body}"
            for i, email in enumerate(emails)
        ]
        
        prompt = f"""
        Extract the main question or query from each of the following emails.
        For each email, identify ONLY the primary question that the sender is asking.
        If there is no clear question, extract the main request or issue.
        
        {"\n\n".join(email_texts)}
        
        Respond with ONLY the extracted questions, one per line, in the exact same order as the emails:
        1. [Extracted question 1]
        2. [Extracted question 2]
        ...
        """
        
        try:
            response = self.openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                endpoint="extract_questions",
                temperature=0.1
            )
            
            # Process the response
            extracted_questions = []
            for line in response["text"].strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                # Remove numbering
                parts = line.split(".", 1)
                if len(parts) > 1 and parts[0].strip().isdigit():
                    question = parts[1].strip()
                else:
                    question = line
                
                extracted_questions.append(question)
            
            # Update the emails with extracted questions
            for i, email in enumerate(emails):
                if i < len(extracted_questions):
                    email.extracted_question = extracted_questions[i]
                    email.processed = True
            
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Error extracting questions: {str(e)}")
            self.db.rollback()
    
    def identify_common_questions(self, min_similarity: float = 0.85, limit: int = 100) -> List[Tuple[str, int]]:
        """Identify common questions using semantic similarity.
        
        Args:
            min_similarity: Minimum similarity score (0-1) to consider questions as similar
            limit: Maximum number of question clusters to return
            
        Returns:
            List of tuples with (representative_question, frequency)
        """
        # Get all processed emails with extracted questions
        questions = self.db.query(EmailQuestion).filter(
            EmailQuestion.processed == True,
            EmailQuestion.extracted_question.isnot(None)
        ).all()
        
        if not questions:
            return []
        
        # Use OpenAI to cluster similar questions
        question_texts = [q.extracted_question for q in questions]
        
        prompt = f"""
        Analyze the following list of {len(question_texts)} user questions and group them by similarity.
        For each group of similar questions, provide:
        1. A representative question that best captures the intent
        2. The number of questions in that group
        
        Questions:
        {json.dumps(question_texts)}
        
        Group similar questions even if they use different wording but ask about the same topic.
        The minimum similarity threshold is {min_similarity} (on a scale of 0-1).
        
        Return ONLY the results in JSON format:
        [
          {{"representative_question": "How do I reset my password?", "frequency": 15}},
          {{"representative_question": "What's the deadline for submitting assignments?", "frequency": 8}},
          ...
        ]
        """
        
        try:
            response = self.openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                endpoint="cluster_questions",
                temperature=0.1
            )
            
            # Parse the JSON response
            result_text = response["text"].strip()
            
            # Handle if response has markdown code block
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:].strip()
            
            clusters = json.loads(result_text)
            
            # Sort by frequency in descending order
            clusters.sort(key=lambda x: x["frequency"], reverse=True)
            
            # Return the top clusters
            return [(c["representative_question"], c["frequency"]) for c in clusters[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error clustering questions: {str(e)}")
            return []
    
    def generate_faq_from_common_questions(self, num_entries: int = 10) -> List[FAQEntry]:
        """Generate FAQ entries from the most common questions.
        
        Args:
            num_entries: Number of FAQ entries to generate
            
        Returns:
            List of created FAQ entries
        """
        # Get common questions
        common_questions = self.identify_common_questions(limit=num_entries)
        
        if not common_questions:
            return []
        
        # Create FAQ entries
        created_entries = []
        
        for question, frequency in common_questions:
            # Get context from RAG
            try:
                context = self.rag_agent.get_relevant_context(question)
                
                # Generate answer
                answer, category, source = self._generate_faq_answer(question, context)
                
                # Create entry
                if answer:
                    entry = FAQEntry(
                        question=question,
                        answer=answer,
                        source=source,
                        category=category,
                        is_published=True
                    )
                    self.db.add(entry)
                    self.db.commit()
                    self.db.refresh(entry)
                    created_entries.append(entry)
            
            except Exception as e:
                self.logger.error(f"Error generating FAQ for question '{question}': {str(e)}")
                self.db.rollback()
        
        return created_entries
    
    def _generate_faq_answer(self, question: str, context: List[Dict[str, str]]) -> Tuple[str, str, str]:
        """Generate an answer for a FAQ question using RAG context.
        
        Args:
            question: The question to answer
            context: List of context documents
            
        Returns:
            Tuple of (answer, category, source)
        """
        # Format the context
        context_text = ""
        source = ""
        
        if context:
            context_text = "Context from documentation:\n\n"
            for i, doc in enumerate(context):
                context_text += f"Document {i+1}:\nContent: {doc['content']}\nSource: {doc['source']}\n\n"
            # Use the first source as the primary source
            source = context[0].get('source', '')
        
        prompt = f"""
        Based on the following question and context, create a comprehensive answer:
        
        Question: {question}
        
        {context_text if context else "No specific documentation found. Please use your knowledge about Python, FastAPI, and Streamlit to provide an accurate answer."}
        
        Provide:
        1. A comprehensive answer that directly addresses the question
        2. Determine the category (Python, FastAPI, or Streamlit)
        
        Respond in the following format:
        ANSWER: [Your comprehensive answer]
        CATEGORY: [Python/FastAPI/Streamlit]
        """
        
        response = self.openai_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            endpoint="faq_answer",
            temperature=0.3
        )
        
        # Process the response
        answer_text = response["text"].strip()
        
        # Extract answer and category
        answer = ""
        category = ""
        
        for line in answer_text.split("\n"):
            if line.startswith("ANSWER:"):
                answer = line[len("ANSWER:"):].strip()
            elif line.startswith("CATEGORY:"):
                category = line[len("CATEGORY:"):].strip()
        
        return answer, category, source 