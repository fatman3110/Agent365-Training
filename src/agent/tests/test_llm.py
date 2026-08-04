"""Unit tests for Ollama model readiness and residency settings."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from openai import NotFoundError

import llm


class LlmTests(unittest.TestCase):
    """Validate warmup retries and keep-alive propagation."""

    @patch("llm.time.sleep")
    @patch("llm.get_llm")
    def test_warmup_retries_until_model_exists(
        self, get_llm: MagicMock, sleep: MagicMock
    ) -> None:
        """Retry model loading while the sidecar is still pulling it."""
        client = get_llm.return_value.with_options.return_value
        response = MagicMock()
        client.chat.completions.create.side_effect = [
            NotFoundError("not found", response=response, body=None),
            MagicMock(),
        ]

        llm.warm_up_llm()

        self.assertEqual(client.chat.completions.create.call_count, 2)
        get_llm.return_value.with_options.assert_called_once_with(
            timeout=10.0,
            max_retries=0,
        )
        sleep.assert_called_once_with(1)
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["extra_body"],
            {"keep_alive": llm.KEEP_ALIVE},
        )

    @patch("llm.get_llm")
    def test_chat_keeps_model_loaded(self, get_llm: MagicMock) -> None:
        """Request an extended Ollama model residency on normal turns."""
        get_llm.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="ok"))
        ]

        self.assertEqual(llm.chat_complete("hello"), "ok")
        self.assertEqual(
            get_llm.return_value.chat.completions.create.call_args.kwargs["extra_body"],
            {"keep_alive": llm.KEEP_ALIVE},
        )
        self.assertEqual(
            get_llm.return_value.chat.completions.create.call_args.kwargs["max_tokens"],
            llm.MAX_TOKENS,
        )

    @patch("llm.time.monotonic")
    @patch("llm.get_llm")
    def test_warmup_stops_at_deadline(
        self, get_llm: MagicMock, monotonic: MagicMock
    ) -> None:
        """Fail startup after the configured real-time warmup deadline."""
        monotonic.side_effect = [0, llm.WARMUP_TIMEOUT_SECONDS + 1]

        with self.assertRaisesRegex(RuntimeError, "was not ready"):
            llm.warm_up_llm()

        get_llm.return_value.with_options.return_value.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()