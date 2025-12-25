"""Telephony (Twilio) test runner + storage utilities."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

import requests

try:  # Optional dependency
    from twilio.rest import Client as TwilioClient  # type: ignore
except Exception:  # pragma: no cover - fallback when Twilio SDK missing
    TwilioClient = None

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "copilot.db"))
DEFAULT_VOICE_BASE_URL = os.environ.get("VOICE_BASE_URL") or os.environ.get("VOICE_SERVICE_URL") or "http://localhost:8004"
DEFAULT_TIMEOUT = float(os.environ.get("TELEPHONY_TEST_TIMEOUT", "6"))
REQUIRED_TWILIO_ENVS = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]


class TelephonyTestService:
    """Lightweight persistence wrapper for telephony test logs."""

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
        test_type: str,
        status: str,
        twilio_number: Optional[str] = None,
        call_sid: Optional[str] = None,
        latency_ms: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        serialized_details = json.dumps(details or {}, ensure_ascii=False)
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO telephony_test_logs
                        (test_type, status, twilio_number, call_sid, latency_ms, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        test_type,
                        status,
                        twilio_number,
                        call_sid,
                        latency_ms,
                        serialized_details,
                        created_at,
                    ),
                )
                row = conn.execute(
                    """
                    SELECT id, test_type, status, twilio_number, call_sid, latency_ms, details, created_at
                    FROM telephony_test_logs
                    WHERE id = ?
                    """,
                    (cursor.lastrowid,),
                ).fetchone()
        return self._row_to_dict(row)

    def get_latest_results(self, test_types: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
        params: List[Any] = []
        where_clause = ""
        if test_types:
            placeholders = ",".join("?" for _ in test_types)
            where_clause = f"WHERE test_type IN ({placeholders})"
            params.extend(test_types)

        query = f"""
            SELECT id, test_type, status, twilio_number, call_sid, latency_ms, details, created_at
            FROM telephony_test_logs
            {where_clause}
            ORDER BY datetime(created_at) DESC
        """

        latest: Dict[str, Dict[str, Any]] = {}
        with self._connect() as conn:
            for row in conn.execute(query, params):
                test_name = row["test_type"]
                if test_name in latest:
                    continue
                latest[test_name] = self._row_to_dict(row)
        return list(latest.values())

    def get_history(self, test_type: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
        params: List[Any] = []
        where_clause = ""
        if test_type:
            where_clause = "WHERE test_type = ?"
            params.append(test_type)
        params.append(limit)

        query = f"""
            SELECT id, test_type, status, twilio_number, call_sid, latency_ms, details, created_at
            FROM telephony_test_logs
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
                conn.execute("DELETE FROM telephony_test_logs")

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        details = {}
        if row["details"]:
            try:
                details = json.loads(row["details"])
            except json.JSONDecodeError:
                details = {"raw": row["details"]}
        return {
            "id": row["id"],
            "test_type": row["test_type"],
            "status": row["status"],
            "twilio_number": row["twilio_number"],
            "call_sid": row["call_sid"],
            "latency_ms": row["latency_ms"],
            "details": details,
            "created_at": row["created_at"],
        }


class TelephonyTestRunner:
    """Executes telephony diagnostic tests (dry-run by default)."""

    def __init__(
        self,
        storage: TelephonyTestService,
        *,
        voice_base_url: Optional[str] = None,
        http_timeout: float = DEFAULT_TIMEOUT,
        default_mode: str = "dry",
    ):
        self.storage = storage
        self.voice_base_url = self._normalize_base_url(voice_base_url)
        self.http_timeout = max(1.0, http_timeout)
        self.default_mode = default_mode if default_mode in {"dry", "live"} else "dry"
        self.twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
        self._health_url = os.environ.get("VOICE_HEALTH_URL") or f"{self.voice_base_url}/health"
        self._webhook_url = os.environ.get("VOICE_WEBHOOK_URL") or f"{self.voice_base_url}/voice/webhook"
        self._tests = {
            "credentials": self._test_credentials,
            "webhook_health": self._test_voice_health,
            "webhook_flow": self._test_voice_flow,
            "outbound_simulation": self._test_outbound_simulation,
        }

    @staticmethod
    def _normalize_base_url(base: Optional[str]) -> str:
        normalized = (base or DEFAULT_VOICE_BASE_URL).strip()
        if normalized.endswith('/'):
            normalized = normalized[:-1]
        return normalized or "http://localhost:8004"

    def get_available_tests(self) -> List[str]:
        return list(self._tests.keys())

    def voice_context(self) -> Dict[str, Any]:
        return {
            "voice_base_url": self.voice_base_url,
            "health_url": self._health_url,
            "webhook_url": self._webhook_url,
            "twilio_number": self.twilio_number,
        }

    def environment_snapshot(self) -> Dict[str, Any]:
        missing_envs = [env for env in REQUIRED_TWILIO_ENVS if not os.environ.get(env)]
        return {
            "missing_envs": missing_envs,
            "configured_envs": [env for env in REQUIRED_TWILIO_ENVS if env not in missing_envs],
            "twilio_number": self.twilio_number,
        }

    async def run_tests(
        self,
        *,
        tests: Optional[Sequence[str]] = None,
        mode: str = "dry",
    ) -> List[Dict[str, Any]]:
        normalized_mode = mode if mode in {"dry", "live"} else self.default_mode
        targets = list(dict.fromkeys(tests or self.get_available_tests()))
        tasks = [self._execute_test(name, normalized_mode) for name in targets]
        return await asyncio.gather(*tasks)

    async def _execute_test(self, test_name: str, mode: str) -> Dict[str, Any]:
        handler = self._tests.get(test_name)
        if not handler:
            return self.storage.record_result(
                test_type=test_name,
                status="skipped",
                twilio_number=self.twilio_number,
                latency_ms=None,
                details={"reason": "unknown_test", "requested_mode": mode},
            )
        try:
            return await handler(mode=mode)
        except Exception as exc:  # pragma: no cover - defensive logging path
            return self.storage.record_result(
                test_type=test_name,
                status="error",
                twilio_number=self.twilio_number,
                latency_ms=None,
                details={"error": str(exc), "requested_mode": mode},
            )

    async def _test_credentials(self, *, mode: str) -> Dict[str, Any]:
        missing = [env for env in REQUIRED_TWILIO_ENVS if not os.environ.get(env)]
        metadata: Dict[str, Any] = {
            "mode": mode,
            "missing_envs": missing,
        }
        status = "missing_credentials" if missing else "ready"
        latency_ms: Optional[int] = None
        detail_msg = "Credentials missing."

        if not missing:
            detail_msg = "Credentials detected (dry run)."
            if mode == "live" and TwilioClient:
                def _verify() -> int:
                    client = TwilioClient(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
                    start = time.perf_counter()
                    client.api.accounts(os.environ["TWILIO_ACCOUNT_SID"]).fetch()
                    return int((time.perf_counter() - start) * 1000)

                try:
                    latency_ms = await asyncio.to_thread(_verify)
                    status = "verified"
                    detail_msg = "Twilio account fetched successfully."
                except Exception as exc:  # pragma: no cover - depends on network/Twilio
                    status = "error"
                    detail_msg = f"Twilio verification failed: {exc}"[:240]
            elif mode == "live" and not TwilioClient:
                detail_msg = "Twilio SDK not installed; falling back to dry run."
        metadata["detail"] = detail_msg
        return self.storage.record_result(
            test_type="credentials",
            status=status,
            twilio_number=self.twilio_number,
            latency_ms=latency_ms,
            details=metadata,
        )

    async def _test_voice_health(self, *, mode: str) -> Dict[str, Any]:
        if not self._health_url:
            return self.storage.record_result(
                test_type="webhook_health",
                status="skipped",
                twilio_number=self.twilio_number,
                details={"reason": "health_url_missing"},
            )

        def _ping() -> Dict[str, Any]:
            start = time.perf_counter()
            response = requests.get(self._health_url, timeout=self.http_timeout)
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "status_code": response.status_code,
                "latency_ms": latency,
                "body": response.text[:500],
            }

        try:
            payload = await asyncio.to_thread(_ping)
            status = "healthy" if payload["status_code"] < 400 else "error"
            return self.storage.record_result(
                test_type="webhook_health",
                status=status,
                twilio_number=self.twilio_number,
                latency_ms=payload["latency_ms"],
                details={
                    "status_code": payload["status_code"],
                    "mode": mode,
                    "endpoint": self._health_url,
                },
            )
        except requests.RequestException as exc:
            return self.storage.record_result(
                test_type="webhook_health",
                status="error",
                twilio_number=self.twilio_number,
                details={
                    "mode": mode,
                    "endpoint": self._health_url,
                    "error": str(exc),
                },
            )

    async def _test_voice_flow(self, *, mode: str) -> Dict[str, Any]:
        if not self._webhook_url:
            return self.storage.record_result(
                test_type="webhook_flow",
                status="skipped",
                twilio_number=self.twilio_number,
                details={"reason": "webhook_url_missing"},
            )

        payload = {
            "CallSid": f"SIM-{uuid4().hex[:10]}",
            "Digits": "1",
            "From": self.twilio_number or "+10000000000",
            "To": self.twilio_number or "+10000000000",
        }

        def _invoke() -> Dict[str, Any]:
            start = time.perf_counter()
            response = requests.post(
                self._webhook_url,
                data=payload,
                timeout=self.http_timeout,
            )
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "status_code": response.status_code,
                "latency_ms": latency,
                "is_twi_ml": "<Response" in response.text,
                "call_sid": payload["CallSid"],
            }

        try:
            result = await asyncio.to_thread(_invoke)
            status = "healthy" if result["status_code"] < 400 and result["is_twi_ml"] else "error"
            return self.storage.record_result(
                test_type="webhook_flow",
                status=status,
                call_sid=result["call_sid"],
                twilio_number=self.twilio_number,
                latency_ms=result["latency_ms"],
                details={
                    "status_code": result["status_code"],
                    "mode": mode,
                    "twi_ml_detected": result["is_twi_ml"],
                },
            )
        except requests.RequestException as exc:
            return self.storage.record_result(
                test_type="webhook_flow",
                status="error",
                twilio_number=self.twilio_number,
                details={
                    "mode": mode,
                    "endpoint": self._webhook_url,
                    "error": str(exc),
                },
            )

    async def _test_outbound_simulation(self, *, mode: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        call_sid = f"SIM-{uuid4().hex[:12]}"
        missing = [env for env in REQUIRED_TWILIO_ENVS if not os.environ.get(env)]
        status = "missing_credentials" if missing else "simulated"
        return self.storage.record_result(
            test_type="outbound_simulation",
            status=status,
            call_sid=call_sid,
            twilio_number=self.twilio_number,
            details={
                "mode": mode,
                "scheduled_at": now,
                "missing_envs": missing,
            },
        )


_telephony_test_service: Optional[TelephonyTestService] = None
_telephony_test_runner: Optional[TelephonyTestRunner] = None


def get_telephony_test_service(db_path: Optional[str] = None) -> TelephonyTestService:
    global _telephony_test_service
    if _telephony_test_service is None:
        _telephony_test_service = TelephonyTestService(db_path=db_path)
    elif db_path:
        desired = os.path.abspath(db_path)
        current = os.path.abspath(_telephony_test_service.db_path)
        if desired != current:
            _telephony_test_service = TelephonyTestService(db_path=db_path)
    return _telephony_test_service


def get_telephony_test_runner(service: Optional[TelephonyTestService] = None) -> TelephonyTestRunner:
    global _telephony_test_runner
    if _telephony_test_runner is None or (service and _telephony_test_runner.storage is not service):
        _telephony_test_runner = TelephonyTestRunner(service or get_telephony_test_service())
    return _telephony_test_runner
