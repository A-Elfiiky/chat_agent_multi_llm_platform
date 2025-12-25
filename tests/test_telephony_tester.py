import asyncio
import os
import sqlite3
import sys
import tempfile
import unittest

import httpx
from fastapi import FastAPI

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.shared.telephony_test_service import TelephonyTestService

import importlib.util

ADMIN_ROUTES_PATH = os.path.join(PROJECT_ROOT, 'services', 'gateway-api', 'admin_routes.py')
if 'admin_routes' in sys.modules:
    admin_routes = sys.modules['admin_routes']
else:
    spec = importlib.util.spec_from_file_location('admin_routes', ADMIN_ROUTES_PATH)
    admin_routes = importlib.util.module_from_spec(spec)
    sys.modules['admin_routes'] = admin_routes
    spec.loader.exec_module(admin_routes)


class StubTelephonyRunner:
    def __init__(self, storage: TelephonyTestService):
        self.storage = storage
        self.default_mode = 'dry'

    def get_available_tests(self):
        return ['credentials', 'webhook_health']

    def voice_context(self):
        return {
            'voice_base_url': 'http://localhost:8004',
            'webhook_url': 'http://localhost:8004/voice/webhook',
            'health_url': 'http://localhost:8004/health',
            'twilio_number': '+15551234567',
        }

    def environment_snapshot(self):
        return {
            'missing_envs': [],
            'twilio_number': '+15551234567',
        }

    async def run_tests(self, tests=None, mode='dry'):
        names = tests or self.get_available_tests()
        results = []
        for name in names:
            results.append(
                self.storage.record_result(
                    test_type=name,
                    status='healthy',
                    twilio_number='+15551234567',
                    latency_ms=10,
                    details={'mode': mode, 'test': name},
                )
            )
        return results


class TelephonyTesterAPITestCase(unittest.TestCase):
    def setUp(self):
        fd, self.temp_db_path = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(self._cleanup_db)

        self._bootstrap_tables()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.app = FastAPI()
        self.app.include_router(admin_routes.router)
        self.headers = {"X-Admin-Token": "test-token"}

        self._original_admin_token = admin_routes.ADMIN_TOKEN
        self._original_db_path = admin_routes.DB_PATH
        self._original_telephony_service = getattr(admin_routes, 'telephony_test_service', None)
        self._original_telephony_runner = getattr(admin_routes, 'telephony_test_runner', None)

        admin_routes.ADMIN_TOKEN = "test-token"
        admin_routes.DB_PATH = self.temp_db_path

        service = TelephonyTestService(self.temp_db_path)
        runner = StubTelephonyRunner(service)

        admin_routes.telephony_test_service = service
        admin_routes.telephony_test_runner = runner

    def tearDown(self):
        try:
            asyncio.set_event_loop(None)
            self.loop.close()
        except Exception:
            pass

        admin_routes.ADMIN_TOKEN = self._original_admin_token
        admin_routes.DB_PATH = self._original_db_path
        if self._original_telephony_service is not None:
            admin_routes.telephony_test_service = self._original_telephony_service
        if self._original_telephony_runner is not None:
            admin_routes.telephony_test_runner = self._original_telephony_runner

    def _cleanup_db(self):
        try:
            os.remove(self.temp_db_path)
        except OSError:
            pass

    def _bootstrap_tables(self):
        conn = sqlite3.connect(self.temp_db_path)
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS telephony_test_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT NOT NULL,
                status TEXT NOT NULL,
                twilio_number TEXT,
                call_sid TEXT,
                latency_ms INTEGER,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )'''
        )
        conn.commit()
        conn.close()

    def _request(self, method: str, url: str, **kwargs):
        async def _inner():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, url, **kwargs)

        return self.loop.run_until_complete(_inner())

    def test_run_telephony_tests_records_log(self):
        resp = self._request(
            "POST",
            "/admin/telephony/tests/run",
            json={"tests": ["credentials"]},
            headers=self.headers,
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn('results', payload)
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['test_type'], 'credentials')

        history = admin_routes.telephony_test_service.get_history(limit=5)
        self.assertGreaterEqual(len(history), 1)

    def test_summary_and_history_endpoints(self):
        self._request(
            "POST",
            "/admin/telephony/tests/run",
            json={"tests": ["webhook_health"]},
            headers=self.headers,
        )

        summary_resp = self._request("GET", "/admin/telephony/tests/summary", headers=self.headers)
        self.assertEqual(summary_resp.status_code, 200)
        summary = summary_resp.json()
        self.assertIn('tests', summary)
        self.assertTrue(any(item['test_type'] == 'webhook_health' for item in summary['tests']))

        history_resp = self._request(
            "GET",
            "/admin/telephony/tests/history?test_type=webhook_health&limit=5",
            headers=self.headers,
        )
        self.assertEqual(history_resp.status_code, 200)
        history_payload = history_resp.json()
        self.assertEqual(history_payload['test_type'], 'webhook_health')
        self.assertGreaterEqual(len(history_payload['results']), 1)


if __name__ == "__main__":
    unittest.main()
