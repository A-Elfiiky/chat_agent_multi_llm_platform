import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "copilot.db"))
_ALLOWED_STATUSES = {"active", "draft", "archived"}


def _normalize_tags(tags: Optional[List[str]]) -> List[str]:
    if not tags:
        return []
    cleaned = []
    for tag in tags:
        if not tag:
            continue
        cleaned.append(str(tag).strip())
    return cleaned


class FAQRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS faqs (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    status TEXT DEFAULT 'active',
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))
        clauses = []
        params: List[Any] = []

        if search:
            tokens = [token.strip() for token in re.split(r"\s+", search.lower()) if token.strip()]
            if tokens:
                token_clauses = []
                for token in tokens[:6]:
                    like_term = f"%{token}%"
                    token_clauses.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                    params.extend([like_term, like_term])
                clauses.append(f"({' AND '.join(token_clauses)})")
        if category:
            clauses.append("category = ?")
            params.append(category)
        if status:
            clauses.append("status = ?")
            params.append(status)

        where_sql = " WHERE " + " AND ".join(clauses) if clauses else ""
        base_query = f"FROM faqs{where_sql}"

        with self._connect() as conn:
            cursor = conn.execute(f"SELECT COUNT(*) {base_query}", params)
            total = cursor.fetchone()[0]

            offset = (page - 1) * page_size
            data_cursor = conn.execute(
                f"SELECT * {base_query} ORDER BY COALESCE(updated_at, created_at) DESC LIMIT ? OFFSET ?",
                [*params, page_size, offset],
            )
            rows = [self._row_to_dict(row) for row in data_cursor.fetchall()]

        return rows, total

    def get(self, faq_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def create(
        self,
        *,
        question: str,
        answer: str,
        category: Optional[str],
        tags: Optional[List[str]] = None,
        status: str = "active",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{status}'")

        faq_id = str(uuid.uuid4())
        cleaned_tags = _normalize_tags(tags)
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO faqs (id, question, answer, category, tags, status, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    faq_id,
                    question.strip(),
                    answer.strip(),
                    category.strip() if category else None,
                    json.dumps(cleaned_tags),
                    status,
                    created_by,
                    now,
                    now,
                ),
            )

        return self.get(faq_id)

    def update(
        self,
        faq_id: str,
        *,
        question: str,
        answer: str,
        category: Optional[str],
        tags: Optional[List[str]] = None,
        status: str = "active",
    ) -> Optional[Dict[str, Any]]:
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{status}'")

        cleaned_tags = _normalize_tags(tags)
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE faqs
                   SET question = ?,
                       answer = ?,
                       category = ?,
                       tags = ?,
                       status = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    question.strip(),
                    answer.strip(),
                    category.strip() if category else None,
                    json.dumps(cleaned_tags),
                    status,
                    now,
                    faq_id,
                ),
            )
            if cursor.rowcount == 0:
                return None

        return self.get(faq_id)

    def delete(self, faq_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except json.JSONDecodeError:
                tags = []
        return {
            "id": row["id"],
            "question": row["question"],
            "answer": row["answer"],
            "category": row["category"],
            "tags": tags,
            "status": row["status"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }