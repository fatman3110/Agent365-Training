import logging

from agent_interface import AgentInterface
from microsoft_agents.hosting.core import Authorization

import llm  # 既存の Foundry 呼び出し（chat_complete）

logger = logging.getLogger(__name__)


class MyAgent(AgentInterface):
    """Foundry モデルを頭脳に使う最小の AI Teammate 本体。"""

    async def initialize(self) -> None:
        logger.info("Agent initialized")

    async def process_user_message(
        self, message: str, auth: Authorization, auth_handler_name: str | None, context
    ) -> str:
        # 頭脳（Foundry モデル）に丸投げ。ツール/OBO を使う場合はここを拡張する。
        return llm.chat_complete(message)

    async def handle_agent_notification_activity(
        self, notification_type, payload, context, auth, auth_handler_name
    ) -> str | None:
        # メール等の通知に返信する場合はここで process_user_message を呼ぶ
        return None

    async def cleanup(self) -> None:
        logger.info("Agent cleaned up")
