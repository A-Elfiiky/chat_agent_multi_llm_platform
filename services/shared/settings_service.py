"""Centralized service for persisting runtime platform settings."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any, Dict, Optional

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "copilot.db"))


class SettingsService:
	"""SQLite-backed key/value store for runtime settings."""

	def __init__(self, db_path: Optional[str] = None):
		self.db_path = db_path or DB_PATH
		self._lock = threading.Lock()
		self._ensure_table()

	def _connect(self) -> sqlite3.Connection:
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		return conn

	def _ensure_table(self) -> None:
		os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
		with self._connect() as conn:
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS system_settings (
					key TEXT PRIMARY KEY,
					value TEXT NOT NULL,
					updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
				)
				"""
			)

	def get(self, key: str, default: Any = None) -> Any:
		with self._connect() as conn:
			row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
			if not row:
				return default
			raw_value = row["value"]
			try:
				return json.loads(raw_value)
			except (json.JSONDecodeError, TypeError):
				return raw_value

	def set(self, key: str, value: Any) -> None:
		stored_value = value if isinstance(value, str) else json.dumps(value)
		with self._lock:
			with self._connect() as conn:
				conn.execute(
					"""
					INSERT INTO system_settings (key, value, updated_at)
					VALUES (?, ?, CURRENT_TIMESTAMP)
					ON CONFLICT(key)
					DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
					""",
					(key, stored_value),
				)

	def get_many(self, keys: Dict[str, Any]) -> Dict[str, Any]:
		"""Return multiple settings, falling back to provided defaults."""

		results: Dict[str, Any] = {}
		for key, default in keys.items():
			results[key] = self.get(key, default)
		return results


_settings_service: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
	global _settings_service
	if _settings_service is None:
		_settings_service = SettingsService()
	return _settings_service
