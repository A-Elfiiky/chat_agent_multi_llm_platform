import sqlite3
import json
import os
import datetime
import uuid

class InteractionLogger:
    def __init__(self, db_path="data/copilot.db"):
        self.db_path = db_path
        # DB init is handled by init_db.py now, but we ensure dir exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def log_interaction(self, query, answer, provider, latency_ms, confidence, citations):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        log_id = str(uuid.uuid4())
        
        # For this prototype, we are logging directly to rag_logs without a parent message/session
        # In a full impl, we'd create session -> message -> rag_log
        
        c.execute("""
            INSERT INTO rag_logs (id, query_text, llm_provider, latency_ms, confidence_score, retrieved_doc_ids) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, query, provider, latency_ms, confidence, json.dumps([c.dict() for c in citations])))
        
        conn.commit()
        conn.close()
        print(f"Logged interaction {log_id} to DB")

# Singleton
logger = InteractionLogger()
