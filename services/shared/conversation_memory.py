"""
Conversation Memory System
Tracks conversation context for follow-up questions and multi-turn dialogues
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class ConversationMemory:
    def __init__(self, db_path: str = "data/copilot.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize conversation memory tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id TEXT PRIMARY KEY,
                    client_id TEXT,
                    created_at TEXT,
                    last_activity TEXT,
                    metadata TEXT
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    confidence REAL,
                    timestamp TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id)
                )
            """)
            
            # Context entities table (for tracking mentioned entities)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    entity_type TEXT,
                    entity_value TEXT,
                    first_mentioned TEXT,
                    last_mentioned TEXT,
                    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id)
                )
            """)
            
            conn.commit()
    
    def create_session(self, client_id: str, session_id: str = None) -> str:
        """Create a new conversation session"""
        if not session_id:
            session_id = f"{client_id}_{datetime.utcnow().timestamp()}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversation_sessions 
                (session_id, client_id, created_at, last_activity, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, client_id, now, now, json.dumps({})))
            
            conn.commit()
        
        return session_id
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        confidence: float = None,
        metadata: dict = None
    ):
        """Add a message to the conversation history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            # Add message
            cursor.execute("""
                INSERT INTO conversation_messages 
                (session_id, role, content, confidence, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id, 
                role, 
                content, 
                confidence,
                now,
                json.dumps(metadata or {})
            ))
            
            # Update session last activity
            cursor.execute("""
                UPDATE conversation_sessions 
                SET last_activity = ?
                WHERE session_id = ?
            """, (now, session_id))
            
            conn.commit()
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history for context"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, content, confidence, timestamp, metadata
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "role": row[0],
                    "content": row[1],
                    "confidence": row[2],
                    "timestamp": row[3],
                    "metadata": json.loads(row[4]) if row[4] else {}
                })
            
            return list(reversed(messages))  # Return in chronological order
    
    def get_conversation_context(self, session_id: str) -> str:
        """Build context string from recent conversation history"""
        history = self.get_conversation_history(session_id, limit=5)
        
        if not history:
            return ""
        
        context_parts = ["Previous conversation:"]
        for msg in history:
            prefix = "Customer" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{prefix}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def track_entity(
        self, 
        session_id: str, 
        entity_type: str, 
        entity_value: str
    ):
        """Track mentioned entities (products, order IDs, etc.)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            # Check if entity already exists
            cursor.execute("""
                SELECT id FROM conversation_entities
                WHERE session_id = ? AND entity_type = ? AND entity_value = ?
            """, (session_id, entity_type, entity_value))
            
            if cursor.fetchone():
                # Update last mentioned
                cursor.execute("""
                    UPDATE conversation_entities
                    SET last_mentioned = ?
                    WHERE session_id = ? AND entity_type = ? AND entity_value = ?
                """, (now, session_id, entity_type, entity_value))
            else:
                # Insert new entity
                cursor.execute("""
                    INSERT INTO conversation_entities
                    (session_id, entity_type, entity_value, first_mentioned, last_mentioned)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, entity_type, entity_value, now, now))
            
            conn.commit()
    
    def get_session_entities(self, session_id: str) -> Dict[str, List[str]]:
        """Get all entities mentioned in this session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT entity_type, entity_value
                FROM conversation_entities
                WHERE session_id = ?
                ORDER BY last_mentioned DESC
            """, (session_id,))
            
            entities = {}
            for row in cursor.fetchall():
                entity_type, entity_value = row
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].append(entity_value)
            
            return entities
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up sessions older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Get old session IDs
            cursor.execute("""
                SELECT session_id FROM conversation_sessions
                WHERE last_activity < ?
            """, (cutoff,))
            
            old_sessions = [row[0] for row in cursor.fetchall()]
            
            # Delete related data
            for session_id in old_sessions:
                cursor.execute(
                    "DELETE FROM conversation_messages WHERE session_id = ?",
                    (session_id,)
                )
                cursor.execute(
                    "DELETE FROM conversation_entities WHERE session_id = ?",
                    (session_id,)
                )
                cursor.execute(
                    "DELETE FROM conversation_sessions WHERE session_id = ?",
                    (session_id,)
                )
            
            conn.commit()
            
            return len(old_sessions)
    
    def get_active_sessions(self, hours: int = 24) -> List[Dict]:
        """Get sessions active within specified hours"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            cursor.execute("""
                SELECT session_id, client_id, created_at, last_activity
                FROM conversation_sessions
                WHERE last_activity > ?
                ORDER BY last_activity DESC
            """, (cutoff,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "client_id": row[1],
                    "created_at": row[2],
                    "last_activity": row[3]
                })
            
            return sessions
