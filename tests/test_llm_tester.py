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

from services.shared.llm_test_service import LLMTestRunner, LLMTestService

import importlib.util

ADMIN_ROUTES_PATH = os.path.join(PROJECT_ROOT, 'services', 'gateway-api', 'admin_routes.py')
if 'admin_routes' in sys.modules:
    admin_routes = sys.modules['admin_routes']
else:
    spec = importlib.util.spec_from_file_location('admin_routes', ADMIN_ROUTES_PATH)
    admin_routes = importlib.util.module_from_spec(spec)
    sys.modules['admin_routes'] = admin_routes
    spec.loader.exec_module(admin_routes)


class StubProvider:
    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        return "pong"


class StubRouter:
    def __init__(self):
        self.providers = {'stub': StubProvider()}


class LLMTesterAPITestCase(unittest.TestCase):
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

        # Preserve globals we override
        self._original_admin_token = admin_routes.ADMIN_TOKEN
        self._original_db_path = admin_routes.DB_PATH
        self._original_llm_service = admin_routes.llm_test_service
        self._original_llm_runner = admin_routes.llm_test_runner
        self._original_llm_config = admin_routes.llm_config

        admin_routes.ADMIN_TOKEN = "test-token"
        admin_routes.DB_PATH = self.temp_db_path

        os.environ['STUB_KEY'] = 'fake-key'
        stub_config = {
            'timeout_ms': 1000,
            'providers': {
                'stub': {
                    'api_key_env': 'STUB_KEY',
                    'model': 'test-stub',
                }
            }
        }

        service = LLMTestService(self.temp_db_path)
        router = StubRouter()
        runner = LLMTestRunner(service, router=router, llm_config=stub_config)

        admin_routes.llm_test_service = service
        admin_routes.llm_test_runner = runner
        admin_routes.llm_config = stub_config

    def tearDown(self):
        try:
            asyncio.set_event_loop(None)
            self.loop.close()
        except Exception:
            pass

        # Restore globals
        admin_routes.ADMIN_TOKEN = self._original_admin_token
        admin_routes.DB_PATH = self._original_db_path
        admin_routes.llm_test_service = self._original_llm_service
        admin_routes.llm_test_runner = self._original_llm_runner
        admin_routes.llm_config = self._original_llm_config

        os.environ.pop('STUB_KEY', None)

    def _cleanup_db(self):
        try:
            os.remove(self.temp_db_path)
        except OSError:
            pass

    def _bootstrap_tables(self):
        conn = sqlite3.connect(self.temp_db_path)
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS llm_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                status TEXT NOT NULL,
                api_key_present INTEGER NOT NULL,
                latency_ms INTEGER,
                response_sample TEXT,
                error_message TEXT,
                metadata TEXT,
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

    def test_run_llm_test_records_success(self):
        resp = self._request(
            "POST",
            "/admin/llm/tests/run",
            json={"providers": ["stub"]},
            headers=self.headers,
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn('results', payload)
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['provider'], 'stub')
        self.assertEqual(payload['results'][0]['status'], 'healthy')

        history = admin_routes.llm_test_service.get_history(provider='stub', limit=5)
        self.assertGreaterEqual(len(history), 1)

    def test_summary_and_history_endpoints(self):
        # ensure we have at least one record
        self._request(
            "POST",
            "/admin/llm/tests/run",
            json={"providers": ["stub"]},
            headers=self.headers,
        )

        summary_resp = self._request("GET", "/admin/llm/tests/summary", headers=self.headers)
        self.assertEqual(summary_resp.status_code, 200)
        summary = summary_resp.json()
        self.assertIn('providers', summary)
        self.assertTrue(any(item['provider'] == 'stub' for item in summary['providers']))

        history_resp = self._request(
            "GET",
            "/admin/llm/tests/history?provider=stub&limit=5",
            headers=self.headers,
        )
        self.assertEqual(history_resp.status_code, 200)
        history_payload = history_resp.json()
        self.assertEqual(history_payload['provider'], 'stub')
        self.assertGreaterEqual(len(history_payload['results']), 1)


if __name__ == "__main__":
    unittest.main()
