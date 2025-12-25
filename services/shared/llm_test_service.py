"""Utilities for running and persisting LLM API health tests."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

CHAT_ORCHESTRATOR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chat-orchestrator"))
if CHAT_ORCHESTRATOR_PATH not in sys.path:
    sys.path.append(CHAT_ORCHESTRATOR_PATH)

from llm_provider import LLMRouter
from services.shared.config_utils import load_config

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "copilot.db"))
DEFAULT_TEST_PROMPT = "Health check ping. Respond with the word 'pong'."
DEFAULT_SYSTEM_PROMPT = (
    "You are a fast LLM diagnostics agent. Respond succinctly with \"pong\" if you can read the prompt."
)


class LLMTestService:
    """Stores and retrieves LLM test executions."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = Lock()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record_result(
        self,
        *,
        provider: str,
        status: str,
        api_key_present: bool,
        latency_ms: Optional[int] = None,
        response_sample: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
        truncated_response = (response_sample or "")[:500] or None
        truncated_error = (error_message or "")[:500] or None

        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO llm_test_results
                        (provider, status, api_key_present, latency_ms, response_sample, error_message, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        provider,
                        status,
                        1 if api_key_present else 0,
                        latency_ms,
                        truncated_response,
                        truncated_error,
                        metadata_json,
                        created_at,
                    ),
                )
                result_id = cursor.lastrowid
                row = conn.execute(
                    """
                    SELECT id, provider, status, api_key_present, latency_ms, response_sample,
                           error_message, metadata, created_at
                    FROM llm_test_results
                    WHERE id = ?
                    """,
                    (result_id,),
                ).fetchone()
        return self._row_to_dict(row)

    def get_latest_results(self, providers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        params: List[Any] = []
        where_clause = ""
        if providers:
            placeholders = ",".join("?" for _ in providers)
            where_clause = f"WHERE provider IN ({placeholders})"
            params.extend(providers)

        query = f"""
            SELECT id, provider, status, api_key_present, latency_ms, response_sample,
                   error_message, metadata, created_at
            FROM llm_test_results
            {where_clause}
            ORDER BY datetime(created_at) DESC
        """

        latest: Dict[str, Dict[str, Any]] = {}
        with self._connect() as conn:
            for row in conn.execute(query, params):
                provider_name = row["provider"]
                if provider_name in latest:
                    continue
                latest[provider_name] = self._row_to_dict(row)
        return list(latest.values())

    def get_history(self, provider: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
        params: List[Any] = []
        where_clause = ""
        if provider:
            where_clause = "WHERE provider = ?"
            params.append(provider)
        params.append(limit)

        query = f"""
            SELECT id, provider, status, api_key_present, latency_ms, response_sample,
                   error_message, metadata, created_at
            FROM llm_test_results
            {where_clause}
            ORDER BY datetime(created_at) DESC
            LIMIT ?
        """

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def clear(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM llm_test_results")

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                metadata = {"raw": row["metadata"]}
        return {
            "id": row["id"],
            "provider": row["provider"],
            "status": row["status"],
            "api_key_present": bool(row["api_key_present"]),
            "latency_ms": row["latency_ms"],
            "response_sample": row["response_sample"],
            "error_message": row["error_message"],
            "metadata": metadata,
            "created_at": row["created_at"],
        }


class LLMTestRunner:
    """Executes live LLM pings and records the results."""

    def __init__(
        self,
        storage: LLMTestService,
        *,
        router: Optional[LLMRouter] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ):
        self.storage = storage
        self.router = router or LLMRouter()
        self.llm_config = llm_config or load_config().get("llm", {})
        timeout_ms = self.llm_config.get("timeout_ms", 5000)
        self._default_timeout = max(5.0, (timeout_ms / 1000.0) * 1.5)

    def get_active_providers(self) -> List[str]:
        return sorted(self.router.providers.keys())

    def get_configured_providers(self) -> List[str]:
        providers_cfg = self.llm_config.get("providers", {}) or {}
        return sorted(providers_cfg.keys())

    async def run_tests(
        self,
        providers: Optional[List[str]] = None,
        prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        targets = providers or self.get_configured_providers() or self.get_active_providers()
        if not targets:
            return []

        seen = []
        for name in targets:
            if name not in seen:
                seen.append(name)

        raw_prompt = (prompt or "").strip()
        test_prompt = raw_prompt or DEFAULT_TEST_PROMPT
        tasks = [self._execute_provider_test(name, test_prompt) for name in seen]
        return await asyncio.gather(*tasks)

    async def _execute_provider_test(self, provider_name: str, prompt: str) -> Dict[str, Any]:
        system_instruction = DEFAULT_SYSTEM_PROMPT
        provider = self.router.providers.get(provider_name)
        provider_cfg = (self.llm_config.get("providers", {}) or {}).get(provider_name, {})
        required_envs = self._collect_required_envs(provider_cfg)
        missing_envs = [env for env in required_envs if not os.environ.get(env)]
        api_key_present = not missing_envs

        metadata: Dict[str, Any] = {
            "prompt": prompt,
            "system_instruction": system_instruction,
            "required_envs": required_envs,
            "missing_envs": missing_envs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not provider:
            metadata["reason"] = "provider_not_initialized"
            return self.storage.record_result(
                provider=provider_name,
                status="unavailable",
                api_key_present=api_key_present,
                latency_ms=None,
                response_sample=None,
                error_message="Provider is not configured in this deployment.",
                metadata=metadata,
            )

        if missing_envs:
            metadata["reason"] = "missing_credentials"
            return self.storage.record_result(
                provider=provider_name,
                status="missing_credentials",
                api_key_present=False,
                latency_ms=None,
                response_sample=None,
                error_message=f"Set environment variables: {', '.join(missing_envs)}",
                metadata=metadata,
            )

        start = time.perf_counter()
        try:
            response_text = await asyncio.wait_for(
                provider.generate_response(prompt, system_instruction),
                timeout=self._default_timeout,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            metadata["latency_ms"] = latency_ms
            return self.storage.record_result(
                provider=provider_name,
                status="healthy",
                api_key_present=True,
                latency_ms=latency_ms,
                response_sample=response_text,
                error_message=None,
                metadata=metadata,
            )
        except asyncio.TimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            metadata["latency_ms"] = latency_ms
            return self.storage.record_result(
                provider=provider_name,
                status="timeout",
                api_key_present=True,
                latency_ms=latency_ms,
                response_sample=None,
                error_message=f"No response within {self._default_timeout:.1f}s",
                metadata=metadata,
            )
        except Exception as exc:  # pragma: no cover - error branches vary per provider
            latency_ms = int((time.perf_counter() - start) * 1000)
            metadata["latency_ms"] = latency_ms
            return self.storage.record_result(
                provider=provider_name,
                status="error",
                api_key_present=True,
                latency_ms=latency_ms,
                response_sample=None,
                error_message=str(exc),
                metadata=metadata,
            )

    @staticmethod
    def _collect_required_envs(provider_cfg: Optional[Dict[str, Any]]) -> List[str]:
        provider_cfg = provider_cfg or {}
        env_fields = ["api_key_env", "token_env"]
        envs = []
        for field in env_fields:
            value = provider_cfg.get(field)
            if value:
                envs.append(value)
        return envs


_llm_test_service: Optional[LLMTestService] = None
_llm_test_runner: Optional[LLMTestRunner] = None


def get_llm_test_service(db_path: Optional[str] = None) -> LLMTestService:
    global _llm_test_service
    if _llm_test_service is None:
        _llm_test_service = LLMTestService(db_path=db_path)
    elif db_path:
        desired_path = os.path.abspath(db_path)
        current_path = os.path.abspath(_llm_test_service.db_path)
        if desired_path != current_path:
            _llm_test_service = LLMTestService(db_path=db_path)
    return _llm_test_service


def get_llm_test_runner() -> LLMTestRunner:
    global _llm_test_runner
    if _llm_test_runner is None:
        _llm_test_runner = LLMTestRunner(get_llm_test_service())
    return _llm_test_runner
