"""HTTP contract tests for the combined Teams and A2A host."""

from __future__ import annotations

import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from start_server import create_app


class A2AServerTests(unittest.TestCase):
    """Validate public cards, API-key enforcement, and route registration."""

    def setUp(self) -> None:
        os.environ["A2A_API_KEY"] = "test-key"
        os.environ["WEBSITE_HOSTNAME"] = "testserver"
        os.environ["AGENT365OBSERVABILITY__TENANTID"] = ""
        self.warmup_patcher = patch("start_server.warm_up_llm")
        self.token_patcher = patch(
            "start_server._start_observability_token_service",
            new=AsyncMock(return_value=None),
        )
        self.warmup_patcher.start()
        self.token_patcher.start()

    def tearDown(self) -> None:
        self.token_patcher.stop()
        self.warmup_patcher.stop()

    def test_cards_authentication_and_message_response(self) -> None:
        """Serve cards publicly and require an API key for A2A execution."""
        with patch(
            "a2a_server.run_agent_turn",
            side_effect=lambda text, _session_id, channel: f"echo:{channel}:{text}",
        ):
            with TestClient(create_app(object())) as client:
                card = client.get("/.well-known/agent.json")
                card_alias = client.get("/.well-known/agent-card.json")
                endpoint_card = client.get("/a2a")
                nested_card = client.get("/a2a/.well-known/agent.json")
                unauthorized = client.post("/a2a", json={})
                authorized = client.post(
                    "/a2a",
                    headers={
                        "X-A2A-API-Key": "test-key",
                        "A2A-Version": "1.0",
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": "test-1",
                        "method": "SendMessage",
                        "params": {
                            "message": {
                                "messageId": "message-1",
                                "role": "ROLE_USER",
                                "parts": [{"text": "hello"}],
                            }
                        },
                    },
                )
                rest_authorized = client.post(
                    "/a2a/message:send",
                    headers={
                        "X-A2A-API-Key": "test-key",
                        "A2A-Version": "1.0",
                    },
                    json={
                        "message": {
                            "messageId": "message-2",
                            "role": "ROLE_USER",
                            "parts": [{"text": "hello"}],
                        }
                    },
                )
                private_task = client.get("/a2a/tasks/not-found")
                oversized = client.post(
                    "/a2a",
                    headers={"X-A2A-API-Key": "test-key"},
                    content=b"x" * 1_048_577,
                )

        self.assertEqual(card.status_code, 200)
        self.assertEqual(card_alias.status_code, 200)
        self.assertEqual(endpoint_card.status_code, 200)
        self.assertEqual(nested_card.status_code, 200)
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(rest_authorized.status_code, 200)
        self.assertEqual(private_task.status_code, 401)
        self.assertEqual(oversized.status_code, 413)
        self.assertEqual(
            authorized.json()["result"]["message"]["parts"][0]["text"],
            "echo:a2a:hello",
        )

    def test_teams_and_a2a_routes_are_registered(self) -> None:
        """Keep the Teams endpoint while adding both A2A bindings."""
        routes = {route.path for route in create_app(object()).routes}

        self.assertIn("/api/messages", routes)
        self.assertIn("/a2a", routes)
        self.assertIn("/a2a/message:send", routes)


if __name__ == "__main__":
    unittest.main()