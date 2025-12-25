"""SQLite-backed storage for integration, webhook, and API key state."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "copilot.db"))

DEFAULT_INTEGRATIONS: List[Dict[str, Any]] = [
    {
        "name": "salesforce",
        "display_name": "Salesforce CRM",
        "description": "Sync customer data and interactions",
        "category": "crm",
        "icon": "💼",
    },
    {
        "name": "slack",
        "display_name": "Slack",
        "description": "Receive notifications and alerts",
        "category": "messaging",
        "icon": "💬",
    },
    {
        "name": "teams",
        "display_name": "Microsoft Teams",
        "description": "Team collaboration and alerts",
        "category": "messaging",
        "icon": "👥",
    },
    {
        "name": "analytics",
        "display_name": "Google Analytics",
        "description": "Track user interactions",
        "category": "analytics",
        "icon": "📊",
    },
    {
        "name": "stripe",
        "display_name": "Stripe",
        "description": "Payment processing integration",
        "category": "payments",
        "icon": "💳",
    },
    {
        "name": "zendesk",
        "display_name": "Zendesk",
        "description": "Ticket management system",
        "category": "support",
        "icon": "🗂️",
    },
    {
        "name": "sendgrid",
        "display_name": "SendGrid",
        "description": "Email delivery service",
        "category": "email",
        "icon": "📧",
    },
    {
        "name": "twilio",
        "display_name": "Twilio",
        "description": "SMS and voice communication",
        "category": "telephony",
        "icon": "📞",
    },
]


def _mask_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    clean_value = value.strip()
    if len(clean_value) <= 6:
        return clean_value[0] + "•" * max(len(clean_value) - 2, 0) + clean_value[-1]
    return f"{clean_value[:4]}…{clean_value[-4:]}"


class IntegrationService:
    """Persists integration/webhook/API key state in SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._lock = threading.Lock()
        self._ensure_tables()
        self._seed_integrations()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS integrations (
                    name TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    icon TEXT,
                    status TEXT DEFAULT 'disconnected',
                    api_key TEXT,
                    webhook_url TEXT,
                    metadata TEXT,
                    last_connected_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS integration_api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    key_name TEXT NOT NULL,
                    key_value TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    last_used_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS custom_webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    events TEXT,
                    status TEXT DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def _seed_integrations(self) -> None:
        with self._connect() as conn:
            for integration in DEFAULT_INTEGRATIONS:
                conn.execute(
                    """
                    INSERT INTO integrations (name, display_name, description, category, icon)
                    VALUES (:name, :display_name, :description, :category, :icon)
                    ON CONFLICT(name) DO UPDATE SET
                        display_name = excluded.display_name,
                        description = excluded.description,
                        category = excluded.category,
                        icon = excluded.icon
                    """,
                    integration,
                )

    # Serialization helpers -------------------------------------------------
    def _serialize_integration(self, row: sqlite3.Row) -> Dict[str, Any]:
        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                metadata = row["metadata"]
        return {
            "name": row["name"],
            "display_name": row["display_name"],
            "description": row["description"],
            "category": row["category"],
            "icon": row["icon"],
            "status": row["status"],
            "api_key_present": bool(row["api_key"]),
            "webhook_url": row["webhook_url"],
            "metadata": metadata,
            "last_connected_at": row["last_connected_at"],
        }

    def _serialize_api_key(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "service": row["service"],
            "key_name": row["key_name"],
            "status": row["status"],
            "masked_key": _mask_secret(row["key_value"]),
            "last_used_at": row["last_used_at"],
            "created_at": row["created_at"],
        }

    def _serialize_webhook(self, row: sqlite3.Row) -> Dict[str, Any]:
        events: List[str] = []
        if row["events"]:
            try:
                events = json.loads(row["events"])
            except json.JSONDecodeError:
                events = [row["events"]]
        return {
            "id": row["id"],
            "name": row["name"],
            "url": row["url"],
            "events": events,
            "status": row["status"],
            "created_at": row["created_at"],
        }

    # Public API ------------------------------------------------------------
    def get_state(self) -> Dict[str, Any]:
        return {
            "integrations": self.list_integrations(),
            "api_keys": self.list_api_keys(),
            "webhooks": self.list_webhooks(),
        }

    def list_integrations(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM integrations ORDER BY display_name COLLATE NOCASE"
            ).fetchall()
            return [self._serialize_integration(row) for row in rows]

    def connect_integration(
        self,
        name: str,
        api_key: Optional[str] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = metadata or {}
        metadata_value = json.dumps(payload) if payload else None
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM integrations WHERE name = ?",
                    (name,),
                ).fetchone()
                if not row:
                    raise ValueError(f"Unknown integration '{name}'")

                conn.execute(
                    """
                    UPDATE integrations
                    SET status = 'connected',
                        api_key = COALESCE(?, api_key),
                        webhook_url = COALESCE(?, webhook_url),
                        metadata = COALESCE(?, metadata),
                        last_connected_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                    """,
                    (api_key, webhook_url, metadata_value, name),
                )
                updated = conn.execute(
                    "SELECT * FROM integrations WHERE name = ?",
                    (name,),
                ).fetchone()
                return self._serialize_integration(updated)

    def disconnect_integration(self, name: str) -> Dict[str, Any]:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM integrations WHERE name = ?",
                    (name,),
                ).fetchone()
                if not row:
                    raise ValueError(f"Unknown integration '{name}'")
                conn.execute(
                    """
                    UPDATE integrations
                    SET status = 'disconnected',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                    """,
                    (name,),
                )
                updated = conn.execute(
                    "SELECT * FROM integrations WHERE name = ?",
                    (name,),
                ).fetchone()
                return self._serialize_integration(updated)

    def add_api_key(self, service: str, key_name: str, key_value: str) -> Dict[str, Any]:
        if not key_value:
            raise ValueError("API key value is required")
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO integration_api_keys (service, key_name, key_value)
                    VALUES (?, ?, ?)
                    """,
                    (service, key_name, key_value.strip()),
                )
                key_id = cursor.lastrowid
                row = conn.execute(
                    "SELECT * FROM integration_api_keys WHERE id = ?",
                    (key_id,),
                ).fetchone()
                return self._serialize_api_key(row)

    def rotate_api_key(self, key_id: int, new_value: str) -> Dict[str, Any]:
        if not new_value:
            raise ValueError("New key value is required")
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM integration_api_keys WHERE id = ?",
                    (key_id,),
                ).fetchone()
                if not row:
                    raise ValueError("API key not found")
                conn.execute(
                    """
                    UPDATE integration_api_keys
                    SET key_value = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_value.strip(), key_id),
                )
                updated = conn.execute(
                    "SELECT * FROM integration_api_keys WHERE id = ?",
                    (key_id,),
                ).fetchone()
                return self._serialize_api_key(updated)

    def revoke_api_key(self, key_id: int) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE integration_api_keys
                    SET status = 'revoked', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (key_id,)
                )

    def list_api_keys(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM integration_api_keys ORDER BY created_at DESC"
            ).fetchall()
            return [self._serialize_api_key(row) for row in rows]

    def add_webhook(self, name: str, url: str, events: Optional[List[str]] = None) -> Dict[str, Any]:
        events_value = json.dumps(events or [])
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO custom_webhooks (name, url, events)
                    VALUES (?, ?, ?)
                    """,
                    (name.strip(), url.strip(), events_value),
                )
                webhook_id = cursor.lastrowid
                row = conn.execute(
                    "SELECT * FROM custom_webhooks WHERE id = ?",
                    (webhook_id,),
                ).fetchone()
                return self._serialize_webhook(row)

    def delete_webhook(self, webhook_id: int) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM custom_webhooks WHERE id = ?", (webhook_id,))

    def list_webhooks(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM custom_webhooks ORDER BY created_at DESC"
            ).fetchall()
            return [self._serialize_webhook(row) for row in rows]


_integration_service: Optional[IntegrationService] = None


def get_integration_service() -> IntegrationService:
    global _integration_service
    if _integration_service is None:
        _integration_service = IntegrationService()
    return _integration_service
