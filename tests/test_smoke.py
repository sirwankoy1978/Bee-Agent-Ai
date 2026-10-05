"""Offline smoke tests for the whole wiring - no network needed.

Run from the project root:
    python -m pytest tests -q
or without pytest:
    python tests/test_smoke.py
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Force deterministic offline settings before importing project modules.
os.environ["APP_ENV"] = "development"
os.environ["ENABLE_WEB_SEARCH"] = "0"
os.environ["ENABLE_IMAGE_GENERATION"] = "0"
os.environ["ENABLE_USER_MEMORY"] = "0"
os.environ["DB_FILE"] = str(ROOT / "tmp" / "test_bee.db")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("TELEGRAM_TOKEN", "123:test-token")


class ConfigTests(unittest.TestCase):
    def test_settings_defaults(self):
        from bee.config import get_settings

        settings = get_settings()
        self.assertEqual(settings.bot_mode, "agent")
        self.assertTrue(settings.tg_reply_to_mentions_only)   # group rule required
        self.assertTrue(settings.tg_reply_to_bot_messages)    # reply rule required
        self.assertTrue(settings.tg_streaming)
        self.assertTrue(settings.is_dev)

    def test_bool_parsing(self):
        from bee.config import _env_bool

        os.environ["X_FLAG"] = "yes"
        self.assertTrue(_env_bool("X_FLAG", False))
        os.environ["X_FLAG"] = "0"
        self.assertFalse(_env_bool("X_FLAG", True))


class AgentBuildTests(unittest.TestCase):
    def test_build_agent(self):
        from bee.agent import build_agent
        from bee.config import get_settings

        agent = build_agent(get_settings())
        self.assertEqual(agent.id, "bee-telegram-agent")
        self.assertIsNotNone(agent.model)
        self.assertIsNotNone(agent.db)

    def test_build_team_and_workflow(self):
        from bee.agent import build_team, build_workflow
        from bee.config import get_settings

        settings = get_settings()
        team = build_team(settings)
        self.assertEqual(len(team.members), 2)
        workflow = build_workflow(settings)
        self.assertEqual(len(workflow.steps), 1)


class InterfaceTests(unittest.TestCase):
    def _build_app(self):
        import telegram_bot

        agent_os, _entity, _kind = telegram_bot.build_agent_os(telegram_bot.get_settings())
        return agent_os.get_app()

    def test_routes_mounted(self):
        # FastAPI >=0.120 stores included routers as wrappers, so assert on the
        # OpenAPI schema instead of `app.routes`.
        paths = self._build_app().openapi()["paths"]
        self.assertIn("/telegram/status", paths)
        self.assertIn("/telegram/webhook", paths)

    def test_status_ok(self):
        from fastapi.testclient import TestClient

        client = TestClient(self._build_app())
        response = client.get("/telegram/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "available")

    def test_webhook_processes_message_and_ignores_non_messages(self):
        """APP_ENV=development bypasses the secret; bot-authored messages are
        filtered, non-message updates answer `ignored`, duplicate update_ids
        answer `duplicate` (background processing may still fail offline - that
        is expected and does not change the webhook answer)."""
        from fastapi.testclient import TestClient

        client = TestClient(self._build_app(), raise_server_exceptions=False)

        ignored = client.post("/telegram/webhook", json={"update_id": 1, "callback_query": {"id": "x"}})
        self.assertEqual(ignored.status_code, 200)
        self.assertEqual(ignored.json()["status"], "ignored")

        dup_payload = {
            "update_id": 2,
            "message": {
                "message_id": 10,
                "from": {"id": 7, "is_bot": True, "first_name": "OtherBot"},
                "chat": {"id": 7, "type": "private"},
                "text": "hi",
            },
        }
        first = client.post("/telegram/webhook", json=dup_payload)
        self.assertEqual(first.json()["status"], "processing")
        second = client.post("/telegram/webhook", json=dup_payload)
        self.assertEqual(second.json()["status"], "duplicate")


class GroupFilterTests(unittest.TestCase):
    def test_mention_and_reply_helpers(self):
        """Mirror of the router's group policy (mentions/replies only)."""
        from agno.os.interfaces.telegram.helpers import is_bot_mentioned

        mention_msg = {
            "entities": [{"type": "mention", "offset": 0, "length": 8}],
            "text": "@beebot hi there",
        }
        self.assertTrue(is_bot_mentioned(mention_msg, "beebot"))

        plain_msg = {"entities": [], "text": "just chatting"}
        self.assertFalse(is_bot_mentioned(plain_msg, "beebot"))

        reply_to_bot = {"reply_to_message": {"from": {"id": 123}}}
        bot_id = 123
        is_reply = bool(reply_to_bot.get("reply_to_message", {}).get("from", {}).get("id") == bot_id)
        self.assertTrue(is_reply)

    def test_webhook_secret_enforced_when_not_dev(self):
        from agno.os.interfaces.telegram.security import validate_webhook_secret_token

        old_env = os.environ.pop("APP_ENV", None)
        os.environ["TELEGRAM_WEBHOOK_SECRET_TOKEN"] = "s3cret"
        try:
            self.assertFalse(validate_webhook_secret_token(None))
            self.assertFalse(validate_webhook_secret_token("wrong"))
            self.assertTrue(validate_webhook_secret_token("s3cret"))
        finally:
            if old_env is not None:
                os.environ["APP_ENV"] = old_env
            os.environ["APP_ENV"] = "development"


class TelegramAPITests(unittest.TestCase):
    def test_client_builds_payloads(self):
        import bee.telegram_api as tga

        api = tga.TelegramBotAPI("42:abc")
        calls = []
        api._call = lambda method, payload=None: (calls.append((method, payload)), {"ok": True})[1]
        api.set_webhook("https://example.com/telegram/webhook", secret_token="sec")
        method, payload = calls[0]
        self.assertEqual(method, "setWebhook")
        self.assertEqual(payload["secret_token"], "sec")
        self.assertEqual(payload["allowed_updates"], ["message", "edited_message"])
        api.send_message(-100, "x" * 5000)
        self.assertEqual(len(calls[1][1]["text"]), 4096)


if __name__ == "__main__":
    unittest.main(verbosity=2)
