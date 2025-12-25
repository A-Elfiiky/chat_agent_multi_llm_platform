import asyncio
import os
import sys
import tempfile
import unittest

import httpx
from fastapi import FastAPI

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.shared.faq_repository import FAQRepository

import importlib.util

ADMIN_ROUTES_PATH = os.path.join(PROJECT_ROOT, 'services', 'gateway-api', 'admin_routes.py')
spec = importlib.util.spec_from_file_location('admin_routes', ADMIN_ROUTES_PATH)
admin_routes = importlib.util.module_from_spec(spec)
sys.modules['admin_routes'] = admin_routes
spec.loader.exec_module(admin_routes)


class FAQAdminAPITestCase(unittest.TestCase):
    def setUp(self):
        fd, self.temp_db_path = tempfile.mkstemp()
        os.close(fd)
        self.repo = FAQRepository(self.temp_db_path)
        admin_routes.faq_repo = self.repo
        admin_routes.DB_PATH = self.temp_db_path
        admin_routes.ADMIN_TOKEN = "test-token"

        self.app = FastAPI()
        self.app.include_router(admin_routes.router)
        self.headers = {"X-Admin-Token": "test-token"}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        try:
            asyncio.set_event_loop(None)
            self.loop.close()
        except Exception:
            pass
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except PermissionError:
                # On Windows, sqlite may keep a lock for a short period; best effort cleanup
                pass

    def _request(self, method: str, url: str, **kwargs):
        async def _inner():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, url, **kwargs)

        return self.loop.run_until_complete(_inner())

    def test_create_and_list_faq(self):
        payload = {
            "question": "How do I reset my password?",
            "answer": "Use the forgot password link.",
            "category": "Account",
            "tags": ["account", "password"],
            "status": "active",
        }
        response = self._request("POST", "/admin/faqs", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["question"], payload["question"])
        self.assertEqual(data["category"], "Account")

        list_resp = self._request("GET", "/admin/faqs?page=1&page_size=10", headers=self.headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertEqual(list_data["total"], 1)
        self.assertEqual(len(list_data["items"]), 1)

    def test_update_with_last_updated_guard(self):
        create_resp = self._request(
            "POST",
            "/admin/faqs",
            json={
                "question": "What are the support hours?",
                "answer": "9am-5pm",
                "category": "General",
                "tags": ["support"],
                "status": "draft",
            },
            headers=self.headers,
        )
        faq = create_resp.json()
        faq_id = faq["id"]
        last_updated = faq["last_updated"]

        update_payload = {
            "question": "What are the support hours?",
            "answer": "Support is available 24/7 via chat.",
            "category": "General",
            "tags": ["support"],
            "status": "active",
            "last_updated": last_updated,
        }
        update_resp = self._request("PUT", f"/admin/faqs/{faq_id}", json=update_payload, headers=self.headers)
        self.assertEqual(update_resp.status_code, 200)
        updated = update_resp.json()
        self.assertEqual(updated["answer"], "Support is available 24/7 via chat.")

        # Attempt with stale timestamp
        stale_payload = update_payload.copy()
        stale_payload["answer"] = "Stale answer"
        stale_resp = self._request("PUT", f"/admin/faqs/{faq_id}", json=stale_payload, headers=self.headers)
        self.assertEqual(stale_resp.status_code, 409)

    def test_delete_faq(self):
        create_resp = self._request(
            "POST",
            "/admin/faqs",
            json={
                "question": "How do I change my billing info?",
                "answer": "Use the billing portal.",
                "category": "Billing",
                "tags": ["billing"],
                "status": "active",
            },
            headers=self.headers,
        )
        faq_id = create_resp.json()["id"]

        delete_resp = self._request("DELETE", f"/admin/faqs/{faq_id}", headers=self.headers)
        self.assertEqual(delete_resp.status_code, 204)

        list_resp = self._request("GET", "/admin/faqs", headers=self.headers)
        self.assertEqual(list_resp.json()["total"], 0)


if __name__ == "__main__":
    unittest.main()
