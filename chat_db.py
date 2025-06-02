import sqlite3
import uuid
from datetime import datetime
from typing import List, Tuple, Optional

DB_PATH = "chat_history.db"

def migrate_database(conn):
    """Add new columns to existing database if they don't exist"""
    cursor = conn.cursor()
    
    # Check if session_name column exists
    cursor.execute("PRAGMA table_info(chat_sessions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'session_name' not in columns:
        conn.execute("ALTER TABLE chat_sessions ADD COLUMN session_name TEXT")
        print("Added session_name column")
    
    if 'last_message_at' not in columns:
        conn.execute("ALTER TABLE chat_sessions ADD COLUMN last_message_at TIMESTAMP")
        print("Added last_message_at column")
    
    # Update existing sessions with default values
    conn.execute("""
        UPDATE chat_sessions 
        SET session_name = 'Session ' || substr(session_id, 1, 8),
            last_message_at = created_at
        WHERE session_name IS NULL OR last_message_at IS NULL
    """)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # Create tables with original schema first
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
            )
        """)
        
        # Migrate existing database to add new columns
        migrate_database(conn)

def start_session(session_name: str = None) -> str:
    session_id = str(uuid.uuid4())
    if not session_name:
        session_name = f"Research Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    with sqlite3.connect(DB_PATH) as conn:
        # Try to insert with new columns, fall back to old schema if needed
        try:
            conn.execute(
                "INSERT INTO chat_sessions (session_id, session_name, created_at, last_message_at) VALUES (?, ?, ?, ?)", 
                (session_id, session_name, datetime.utcnow(), datetime.utcnow())
            )
        except sqlite3.OperationalError:
            # New columns don't exist, use old schema
            conn.execute(
                "INSERT INTO chat_sessions (session_id, created_at) VALUES (?, ?)", 
                (session_id, datetime.utcnow())
            )
    return session_id

def save_message(session_id: str, role: str, content: str):
    with sqlite3.connect(DB_PATH) as conn:
        # Save the message
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.utcnow())
        )
        # Update last message time for the session (only if column exists)
        try:
            conn.execute(
                "UPDATE chat_sessions SET last_message_at = ? WHERE session_id = ?",
                (datetime.utcnow(), session_id)
            )
        except sqlite3.OperationalError:
            # Column doesn't exist yet, skip update
            pass

def get_chat_history(session_id: str) -> List[Tuple[str, str, str]]:
    """Returns list of (role, content, timestamp) tuples"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT role, content, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp", 
            (session_id,)
        )
        return cursor.fetchall()

def get_all_sessions() -> List[Tuple[str, str, str, str]]:
    """Returns list of (session_id, session_name, created_at, last_message_at) tuples"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """SELECT session_id, 
                      COALESCE(session_name, 'Session ' || substr(session_id, 1, 8)) as session_name,
                      created_at, 
                      COALESCE(last_message_at, created_at) as last_message_at 
               FROM chat_sessions 
               ORDER BY COALESCE(last_message_at, created_at) DESC"""
        )
        return cursor.fetchall()

def update_session_name(session_id: str, new_name: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE chat_sessions SET session_name = ? WHERE session_id = ?",
            (new_name, session_id)
        )

def delete_session(session_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))

def get_session_name(session_id: str) -> Optional[str]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT session_name FROM chat_sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        return result[0] if result else None