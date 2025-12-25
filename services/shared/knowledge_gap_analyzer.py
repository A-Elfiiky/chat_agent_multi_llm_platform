"""
Knowledge Base Auto-Learning System
Identifies gaps in knowledge base and suggests improvements
"""
import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from collections import Counter
import os
import json

class KnowledgeGapAnalyzer:
    """
    Analyzes conversation patterns to identify knowledge base gaps:
    - Low confidence responses
    - Unanswered questions
    - Frequently asked questions not in KB
    - Similar questions with different answers
    """
    
    def __init__(self, db_path: str = "data/copilot.db", confidence_threshold: float = 0.6):
        self.db_path = db_path
        self.confidence_threshold = confidence_threshold
        self._init_db()
    
    def _init_db(self):
        """Initialize knowledge gap tracking tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Unanswered questions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unanswered_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    question_hash TEXT UNIQUE,
                    first_asked TEXT,
                    last_asked TEXT,
                    ask_count INTEGER DEFAULT 1,
                    avg_confidence REAL,
                    status TEXT DEFAULT 'pending',
                    notes TEXT
                )
            """)
            
            # Suggested FAQ entries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faq_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    suggested_answer TEXT,
                    confidence REAL,
                    supporting_queries TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'pending',
                    reviewed_by TEXT,
                    reviewed_at TEXT
                )
            """)
            
            # Knowledge base feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kb_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    answer TEXT,
                    confidence REAL,
                    feedback_type TEXT,
                    feedback_details TEXT,
                    timestamp TEXT
                )
            """)
            
            conn.commit()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def analyze_response(
        self,
        question: str,
        answer: str,
        confidence: float,
        citations: List[Dict] = None
    ):
        """Analyze a response and identify potential gaps"""
        
        # Track low confidence responses
        if confidence < self.confidence_threshold:
            self._track_low_confidence(question, answer, confidence)
        
        # Track questions with no citations (potential gap)
        if not citations or len(citations) == 0:
            self._track_uncited_question(question, answer, confidence)
        
        # Track patterns in failed responses
        if "I don't have enough information" in answer or "I don't know" in answer.lower():
            self._track_unanswered(question)
    
    def _track_low_confidence(self, question: str, answer: str, confidence: float):
        """Track low confidence responses for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO kb_feedback
                (question, answer, confidence, feedback_type, feedback_details, timestamp)
                VALUES (?, ?, ?, 'low_confidence', '', ?)
            """, (question, answer, confidence, datetime.now(timezone.utc).isoformat()))
            
            conn.commit()
    
    def _track_uncited_question(self, question: str, answer: str, confidence: float):
        """Track questions answered without KB citations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO kb_feedback
                (question, answer, confidence, feedback_type, feedback_details, timestamp)
                VALUES (?, ?, ?, 'no_citations', '', ?)
            """, (question, answer, confidence, datetime.now(timezone.utc).isoformat()))
            
            conn.commit()
    
    def _track_unanswered(self, question: str, confidence: float = 0.0, notes: Optional[str] = None):
        """Track questions that couldn't be answered"""
        if not question:
            return

        question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ask_count, avg_confidence
                  FROM unanswered_questions
                 WHERE question_hash = ?
                """,
                (question_hash,),
            )
            row = cursor.fetchone()

            if row:
                existing_count = row["ask_count"] or 0
                existing_avg = row["avg_confidence"] or 0.0
                new_count = existing_count + 1
                new_avg = ((existing_avg * existing_count) + confidence) / max(new_count, 1)
                cursor.execute(
                    """
                    UPDATE unanswered_questions
                       SET ask_count = ?,
                           last_asked = ?,
                           avg_confidence = ?,
                           notes = COALESCE(?, notes)
                     WHERE question_hash = ?
                    """,
                    (new_count, now, round(new_avg, 4), notes, question_hash),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO unanswered_questions
                        (question, question_hash, first_asked, last_asked, ask_count, avg_confidence, notes)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                    """,
                    (question, question_hash, now, now, confidence, notes),
                )

            conn.commit()

    def record_unanswered_question(self, question: str, *, confidence: float = 0.0, notes: Optional[str] = None):
        """Public helper for services to log unanswered questions proactively."""
        self._track_unanswered(question, confidence, notes)
    
    def get_knowledge_gaps(self, *, min_frequency: int = 3, days: int = 30) -> List[Dict]:
        """
        Get questions that indicate knowledge base gaps
        
        Returns questions asked multiple times with low confidence
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            cursor.execute(
                """
                SELECT 
                    question,
                    ask_count,
                    first_asked,
                    last_asked,
                    status,
                    avg_confidence
                FROM unanswered_questions
                WHERE last_asked > ? AND ask_count >= ?
                ORDER BY ask_count DESC
                """,
                (cutoff, min_frequency),
            )
            
            gaps = []
            for row in cursor.fetchall():
                gaps.append({
                    'question': row[0],
                    'ask_count': row[1],
                    'first_asked': row[2],
                    'last_asked': row[3],
                    'status': row[4],
                    'avg_confidence': row[5]
                })
            
            return gaps
    
    def get_low_confidence_patterns(self, days: int = 7) -> List[Dict]:
        """Get common patterns in low confidence responses"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT question, confidence, timestamp
                FROM kb_feedback
                WHERE feedback_type = 'low_confidence'
                    AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (cutoff,))
            
            low_confidence_items = []
            for row in cursor.fetchall():
                low_confidence_items.append({
                    'question': row[0],
                    'confidence': row[1],
                    'timestamp': row[2]
                })
            
            return low_confidence_items
    
    def suggest_faq_entry(
        self,
        question: str,
        answer: str,
        confidence: float,
        supporting_queries: List[str] = None
    ):
        """Suggest a new FAQ entry based on patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO faq_suggestions
                (question, suggested_answer, confidence, supporting_queries, created_at, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (
                question,
                answer,
                confidence,
                json.dumps(supporting_queries or []),
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            
            return cursor.lastrowid
    
    def get_faq_suggestions(self, status: str = 'pending') -> List[Dict]:
        """Get pending FAQ suggestions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    question,
                    suggested_answer,
                    confidence,
                    supporting_queries,
                    created_at,
                    status
                FROM faq_suggestions
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))
            
            suggestions = []
            for row in cursor.fetchall():
                suggestions.append({
                    'id': row[0],
                    'question': row[1],
                    'suggested_answer': row[2],
                    'confidence': row[3],
                    'supporting_queries': json.loads(row[4]) if row[4] else [],
                    'created_at': row[5],
                    'status': row[6]
                })
            
            return suggestions
    
    def approve_suggestion(self, suggestion_id: int, reviewed_by: str = "admin"):
        """Approve an FAQ suggestion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE faq_suggestions
                SET status = 'approved',
                    reviewed_by = ?,
                    reviewed_at = ?
                WHERE id = ?
            """, (reviewed_by, datetime.now(timezone.utc).isoformat(), suggestion_id))
            
            conn.commit()
    
    def reject_suggestion(self, suggestion_id: int, reviewed_by: str = "admin"):
        """Reject an FAQ suggestion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE faq_suggestions
                SET status = 'rejected',
                    reviewed_by = ?,
                    reviewed_at = ?
                WHERE id = ?
            """, (reviewed_by, datetime.now(timezone.utc).isoformat(), suggestion_id))
            
            conn.commit()
    
    def get_improvement_report(self, days: int = 30) -> Dict:
        """Generate comprehensive knowledge base improvement report"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            # Total questions analyzed
            cursor.execute("""
                SELECT COUNT(*) FROM kb_feedback
                WHERE timestamp > ?
            """, (cutoff,))
            total_analyzed = cursor.fetchone()[0]
            
            # Low confidence count
            cursor.execute("""
                SELECT COUNT(*) FROM kb_feedback
                WHERE feedback_type = 'low_confidence' AND timestamp > ?
            """, (cutoff,))
            low_confidence_count = cursor.fetchone()[0]
            
            # Unanswered questions
            cursor.execute("""
                SELECT COUNT(*) FROM unanswered_questions
                WHERE last_asked > ? AND status = 'pending'
            """, (cutoff,))
            unanswered_count = cursor.fetchone()[0]
            
            # Top gaps (most asked unanswered)
            cursor.execute("""
                SELECT question, ask_count
                FROM unanswered_questions
                WHERE last_asked > ?
                ORDER BY ask_count DESC
                LIMIT 10
            """, (cutoff,))
            top_gaps = [{"question": row[0], "ask_count": row[1]} for row in cursor.fetchall()]
            
            # Pending suggestions
            cursor.execute("""
                SELECT COUNT(*) FROM faq_suggestions
                WHERE status = 'pending'
            """)
            pending_suggestions = cursor.fetchone()[0]
            
            # Average confidence for low-confidence items
            cursor.execute("""
                SELECT AVG(confidence) FROM kb_feedback
                WHERE feedback_type = 'low_confidence' AND timestamp > ?
            """, (cutoff,))
            avg_low_confidence = cursor.fetchone()[0] or 0
            
            return {
                'period_days': days,
                'total_questions_analyzed': total_analyzed,
                'low_confidence_responses': low_confidence_count,
                'unanswered_questions': unanswered_count,
                'pending_faq_suggestions': pending_suggestions,
                'avg_confidence_of_poor_responses': round(avg_low_confidence, 3),
                'top_knowledge_gaps': top_gaps,
                'coverage_rate': round((1 - (unanswered_count / max(total_analyzed, 1))) * 100, 2)
            }
    
    def mark_gap_resolved(self, question_hash: str):
        """Mark a knowledge gap as resolved"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE unanswered_questions
                SET status = 'resolved'
                WHERE question_hash = ?
            """, (question_hash,))
            
            conn.commit()


class QuestionClusterer:
    """
    Clusters similar questions to identify FAQ topics
    Uses simple text similarity for clustering
    """
    
    def __init__(self):
        self.questions: List[str] = []
    
    def add_question(self, question: str):
        """Add a question to the clustering pool"""
        self.questions.append(question.lower().strip())
    
    def find_similar_questions(self, question: str, threshold: float = 0.7) -> List[str]:
        """Find questions similar to the given question"""
        from difflib import SequenceMatcher
        
        question_lower = question.lower().strip()
        similar = []
        
        for q in self.questions:
            if q == question_lower:
                continue
            
            similarity = SequenceMatcher(None, question_lower, q).ratio()
            if similarity >= threshold:
                similar.append(q)
        
        return similar
    
    def get_question_clusters(self, min_cluster_size: int = 3) -> List[List[str]]:
        """Group similar questions into clusters"""
        from difflib import SequenceMatcher
        
        clusters = []
        processed = set()
        
        for i, q1 in enumerate(self.questions):
            if q1 in processed:
                continue
            
            cluster = [q1]
            processed.add(q1)
            
            for j, q2 in enumerate(self.questions[i+1:], start=i+1):
                if q2 in processed:
                    continue
                
                # Check similarity with all cluster members
                max_similarity = max(
                    SequenceMatcher(None, q2, member).ratio()
                    for member in cluster
                )
                
                if max_similarity >= 0.7:
                    cluster.append(q2)
                    processed.add(q2)
            
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)
        
        return clusters
