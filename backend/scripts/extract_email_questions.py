import os
import re
import email
import sqlite3
from pathlib import Path
from email import policy
from email.parser import BytesParser

def extract_questions_from_email(email_file_path):
    """Extract questions from an email file."""
    with open(email_file_path, 'rb') as fp:
        msg = BytesParser(policy=policy.default).parse(fp)
    
    # Get the email body
    body = ""
    if msg.is_multipart():
        for part in msg.get_payload():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                break
    else:
        body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')
    
    # Extract the main question from the email
    main_question = ""
    
    # Strategy 1: Look for numbered question lists and combine them
    numbered_pattern = r'\d+\.\s+(.+?[?])'
    numbered_questions = re.findall(numbered_pattern, body)
    
    if numbered_questions:
        # If we have a numbered list, it's likely a single topic with multiple parts
        main_question = " ".join(numbered_questions)
    else:
        # Strategy 2: Find the most substantial question in the email
        question_pattern = r'([A-Z][^.!?]*\?)'
        question_sentences = re.findall(question_pattern, body)
        
        if question_sentences:
            # Filter short questions (likely follow-up questions without context)
            substantial_questions = [q for q in question_sentences if len(q.strip()) > 15]
            
            if substantial_questions:
                # Use the longest question as the main one
                main_question = max(substantial_questions, key=len)
                
                # Look for related questions that might be follow-ups
                for q in question_sentences:
                    if q != main_question and len(q.strip()) < 30:
                        # If it's a short question, it might be a follow-up
                        if "como" in q.lower() or "qual" in q.lower() or "quando" in q.lower():
                            main_question += " " + q
            else:
                # If no substantial questions found, combine all questions
                main_question = " ".join(question_sentences)
    
    # If no questions found in body, check the subject
    if not main_question:
        subject = msg.get('Subject', '')
        if '?' in subject:
            main_question = subject
    
    return {
        'email_file': os.path.basename(email_file_path),
        'subject': msg.get('Subject', ''),
        'questions': [main_question] if main_question else []
    }

def setup_database(db_path):
    """Create the SQLite database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        subject TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER,
        question_text TEXT NOT NULL,
        FOREIGN KEY (email_id) REFERENCES emails (id)
    )
    ''')
    
    conn.commit()
    return conn

def process_emails(emails_dir, db_path):
    """Process all emails in the directory and store questions in the database."""
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = setup_database(db_path)
    cursor = conn.cursor()
    
    # Get list of all email files
    email_files = [f for f in os.listdir(emails_dir) if f.endswith('.eml')]
    
    for email_file in email_files:
        email_path = os.path.join(emails_dir, email_file)
        email_data = extract_questions_from_email(email_path)
        
        # Insert email record
        cursor.execute(
            "INSERT INTO emails (filename, subject) VALUES (?, ?)",
            (email_data['email_file'], email_data['subject'])
        )
        email_id = cursor.lastrowid
        
        # Insert questions
        for question in email_data['questions']:
            if question:  # Skip empty questions
                cursor.execute(
                    "INSERT INTO questions (email_id, question_text) VALUES (?, ?)",
                    (email_id, question)
                )
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Set paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    emails_dir = base_dir / "data" / "emails"
    db_path = base_dir / "backend" / "db" / "emails.db"
    
    # Process emails
    process_emails(emails_dir, db_path)
    
    print(f"Email questions extracted and stored in {db_path}") 