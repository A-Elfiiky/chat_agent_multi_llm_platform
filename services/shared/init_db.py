import sqlite3
import os

DB_PATH = "data/copilot.db"


def init_db():
    print(f"Initializing SQLite database at {DB_PATH}...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'agent', 'viewer')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
    )''')
    
    # 2. Sessions
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        channel TEXT CHECK(channel IN ('web', 'email', 'voice')),
        customer_id TEXT,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ended_at DATETIME
    )''')
    
    # 3. Message Logs
    c.execute('''CREATE TABLE IF NOT EXISTS message_logs (
        id TEXT PRIMARY KEY,
        session_id TEXT REFERENCES sessions(id),
        sender TEXT CHECK(sender IN ('user', 'bot', 'agent')),
        content TEXT NOT NULL,
        intent TEXT,
        sentiment_score REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 4. RAG Logs (Observability)
    c.execute('''CREATE TABLE IF NOT EXISTS rag_logs (
        id TEXT PRIMARY KEY,
        message_id TEXT REFERENCES message_logs(id),
        query_text TEXT,
        retrieved_doc_ids TEXT, -- JSON array
        llm_provider TEXT,
        llm_model TEXT,
        latency_ms INTEGER,
        confidence_score REAL,
        is_fallback BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 5. Tickets
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        id TEXT PRIMARY KEY,
        session_id TEXT REFERENCES sessions(id),
        status TEXT DEFAULT 'open',
        priority TEXT DEFAULT 'medium',
        assigned_to TEXT REFERENCES users(id),
        summary TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 6. Interaction Logs (used by analytics dashboards)
    c.execute('''CREATE TABLE IF NOT EXISTS interaction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        user_id TEXT,
        channel TEXT,
        user_message TEXT,
        assistant_response TEXT,
        provider TEXT,
        confidence REAL,
        response_time_ms REAL,
        sentiment TEXT,
        escalation_needed INTEGER DEFAULT 0,
        timestamp REAL DEFAULT (strftime('%s','now'))
    )''')

    c.execute('''CREATE INDEX IF NOT EXISTS idx_interaction_logs_timestamp
                 ON interaction_logs(timestamp)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_interaction_logs_session
                 ON interaction_logs(session_id)''')

    # 7. FAQ Management (source of truth for GUI)
    c.execute('''CREATE TABLE IF NOT EXISTS faqs (
        id TEXT PRIMARY KEY,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT,
        tags TEXT,
        status TEXT DEFAULT 'active',
        created_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_faqs_updated_at ON faqs(updated_at DESC)''')

    # 8. LLM API test history
    c.execute('''CREATE TABLE IF NOT EXISTS llm_test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider TEXT NOT NULL,
        status TEXT NOT NULL,
        api_key_present INTEGER NOT NULL,
        latency_ms INTEGER,
        response_sample TEXT,
        error_message TEXT,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_llm_tests_provider ON llm_test_results(provider, created_at DESC)''')

    # 9. Telephony test logs
    c.execute('''CREATE TABLE IF NOT EXISTS telephony_test_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_type TEXT NOT NULL,
        status TEXT NOT NULL,
        twilio_number TEXT,
        call_sid TEXT,
        latency_ms INTEGER,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_telephony_tests_type ON telephony_test_logs(test_type, created_at DESC)''')

    # 10. Lightweight cache view to power analytics (wraps response_cache table)
    c.execute('''CREATE VIEW IF NOT EXISTS cache AS
                 SELECT
                    id,
                    original_query AS query,
                    access_count AS hit_count,
                    created_at
                 FROM response_cache''')

    # --- Post-creation migrations / schema drift fixes ---
    def _add_column_if_missing(table: str, column: str, ddl: str):
        c.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in c.fetchall()}
        if column not in columns:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

    # Unanswered questions enhancements for routing workflow
    _add_column_if_missing('unanswered_questions', 'generated_answer', "generated_answer TEXT")
    _add_column_if_missing('unanswered_questions', 'asked_by', "asked_by TEXT")
    _add_column_if_missing('unanswered_questions', 'llm_provider', "llm_provider TEXT")
    _add_column_if_missing('unanswered_questions', 'status', "status TEXT DEFAULT 'unanswered'")
    _add_column_if_missing('unanswered_questions', 'converted_faq_id', "converted_faq_id TEXT")
    _add_column_if_missing('unanswered_questions', 'updated_at', "updated_at DATETIME")

    # Ensure updated_at populated to avoid NULLs
    c.execute("""
        UPDATE unanswered_questions
        SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
