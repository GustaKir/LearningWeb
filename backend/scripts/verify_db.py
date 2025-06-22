import sqlite3
from pathlib import Path

def verify_database():
    # Set paths
    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / "db" / "emails.db"
    
    # Connect to DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check if we have exactly 1 question per email
    cursor.execute("""
        SELECT e.id, e.filename, COUNT(q.id) as question_count
        FROM emails e
        LEFT JOIN questions q ON e.id = q.email_id
        GROUP BY e.id
        ORDER BY e.id;
    """)
    
    print("Email counts (ensuring 1 question per email):")
    print("=" * 70)
    print("ID | Filename | Question Count")
    print("-" * 70)
    
    for row in cursor.fetchall():
        email_id, filename, count = row
        print(f"{email_id:2} | {filename} | {count}")
    
    # 2. Count total emails and questions
    cursor.execute("SELECT COUNT(*) FROM emails;")
    email_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM questions;")
    question_count = cursor.fetchone()[0]
    
    print("\nSummary:")
    print(f"Total emails: {email_count}")
    print(f"Total questions: {question_count}")
    
    # Now verify that questions are long enough and meaningful
    cursor.execute("""
        SELECT q.id, LENGTH(q.question_text), SUBSTR(q.question_text, 1, 50) || '...'
        FROM questions q
        ORDER BY LENGTH(q.question_text);
    """)
    
    print("\nQuestion lengths (shortest to longest):")
    print("=" * 70)
    print("ID | Length | Question Preview")
    print("-" * 70)
    
    for row in cursor.fetchall():
        q_id, length, preview = row
        print(f"{q_id:2} | {length:6} | {preview}")
    
    conn.close()

if __name__ == "__main__":
    verify_database() 