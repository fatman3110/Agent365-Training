# Copyright (c) Microsoft Corporation. Licensed under the MIT License.
# 最小の AI Teammate 本体：受信メッセージを Foundry モデル（llm.chat_complete）に渡す。
import logging

from agent_interface import AgentInterface
from microsoft_agents.hosting.core import Authorization, TurnContext

import llm  # 既存の Foundry 呼び出し（chat_complete）

logger = logging.getLogger(__name__)


class MyAgent(AgentInterface):
    async def initialize(self) -> None:
        logger.info("Agent initialized")

    async def process_user_message(
        self, message: str, auth: Authorization, auth_handler_name: str, context: TurnContext
    ) -> str:
        return llm.chat_complete(message)

    async def cleanup(self) -> None:
        logger.info("Agent cleaned up")
