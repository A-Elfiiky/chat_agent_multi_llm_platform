"""Provider metrics store for tracking LLM fallback attempts."""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any, Dict, List, Optional
from threading import Lock

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "copilot.db"))


class ProviderMetrics:
	"""Collects telemetry about each LLM provider attempt."""

	def __init__(self, db_path: Optional[str] = None):
		self.db_path = db_path or DB_PATH
		self._lock = Lock()
		os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
		self._ensure_table()

	def _connect(self) -> sqlite3.Connection:
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		return conn

	def _ensure_table(self) -> None:
		with self._connect() as conn:
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS llm_provider_events (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					request_id TEXT,
					session_id TEXT,
					provider TEXT NOT NULL,
					success INTEGER NOT NULL,
					latency_ms REAL,
					error_message TEXT,
					fallback_depth INTEGER DEFAULT 0,
					created_at REAL NOT NULL
				)
				"""
			)
			conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_provider_events_provider ON llm_provider_events(provider)")
			conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_provider_events_created_at ON llm_provider_events(created_at)")

	def record_event(
		self,
		provider: str,
		success: bool,
		latency_ms: Optional[float] = None,
		error_message: Optional[str] = None,
		fallback_depth: int = 0,
		request_id: Optional[str] = None,
		session_id: Optional[str] = None,
	) -> None:
		"""Record a single provider attempt."""
		payload = (
			request_id,
			session_id,
			provider,
			1 if success else 0,
			float(latency_ms) if latency_ms is not None else None,
			error_message[:500] if error_message else None,
			fallback_depth,
			time.time(),
		)
		with self._lock:
			with self._connect() as conn:
				conn.execute(
					"""
					INSERT INTO llm_provider_events
					(request_id, session_id, provider, success, latency_ms, error_message, fallback_depth, created_at)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?)
					""",
					payload,
				)

	def get_summary(self, days: int = 7) -> Dict[str, Any]:
		cutoff = time.time() - (days * 86400)
		with self._connect() as conn:
			rows = conn.execute(
				"""
				SELECT provider,
				       COUNT(*) as attempts,
				       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
				       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures,
				       AVG(latency_ms) as avg_latency,
				       MAX(CASE WHEN success = 0 THEN created_at ELSE NULL END) as last_failure,
				       SUM(CASE WHEN fallback_depth > 0 AND success = 1 THEN 1 ELSE 0 END) as fallback_saves
				FROM llm_provider_events
				WHERE created_at >= ?
				GROUP BY provider
				ORDER BY attempts DESC
				""",
				(cutoff,),
			).fetchall()

		details = []
		for row in rows:
			attempts = row["attempts"] or 0
			successes = row["successes"] or 0
			failures = row["failures"] or 0
			success_rate = successes / attempts if attempts else 0.0
			details.append({
				"provider": row["provider"],
				"attempts": int(attempts),
				"successes": int(successes),
				"failures": int(failures),
				"success_rate": round(success_rate, 3),
				"avg_latency_ms": round(row["avg_latency"], 2) if row["avg_latency"] else None,
				"last_failure": row["last_failure"],
				"fallback_saves": int(row["fallback_saves"]) if row["fallback_saves"] else 0,
			})

		return {
			"window_days": days,
			"providers": details,
			"totals": {
				"attempts": sum(item["attempts"] for item in details),
				"successes": sum(item["successes"] for item in details),
				"failures": sum(item["failures"] for item in details),
			}
		}

	def get_fallback_distribution(self, days: int = 7) -> List[Dict[str, Any]]:
		cutoff = time.time() - (days * 86400)
		with self._connect() as conn:
			rows = conn.execute(
				"""
				SELECT fallback_depth, COUNT(*) as count
				FROM llm_provider_events
				WHERE created_at >= ?
				GROUP BY fallback_depth
				ORDER BY fallback_depth
				""",
				(cutoff,)
			).fetchall()
		return [
			{"fallback_depth": row["fallback_depth"], "count": row["count"]}
			for row in rows
		]

	def get_recent_failures(self, limit: int = 20) -> List[Dict[str, Any]]:
		with self._connect() as conn:
			rows = conn.execute(
				"""
				SELECT provider, error_message, fallback_depth, created_at
				FROM llm_provider_events
				WHERE success = 0
				ORDER BY created_at DESC
				LIMIT ?
				""",
				(limit,),
			).fetchall()
		return [
			{
				"provider": row["provider"],
				"error_message": row["error_message"],
				"fallback_depth": row["fallback_depth"],
				"created_at": row["created_at"],
			}
			for row in rows
		]


_provider_metrics: Optional[ProviderMetrics] = None


def get_provider_metrics() -> ProviderMetrics:
	global _provider_metrics
	if _provider_metrics is None:
		_provider_metrics = ProviderMetrics()
	return _provider_metrics
