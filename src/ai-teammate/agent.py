# Copyright (c) Microsoft Corporation. Licensed under the MIT License.
# 最小の AI Teammate 本体：受信メッセージを Foundry モデル（llm.chat_complete）に渡す。
# A365 観測性：configure() で初期化し、InvokeAgentScope / InferenceScope で
# invoke_agent / chat のセマンティック span を生成して A365 にエクスポートする。
import logging
import os

from agent_interface import AgentInterface
from microsoft_agents.hosting.core import Authorization, TurnContext
from microsoft_agents_a365.observability.core import (
    InferenceCallDetails,
    InferenceOperationType,
    InferenceScope,
    InvokeAgentScope,
)

import llm  # 既存の Foundry 呼び出し（chat_complete）
from observability_config import configure_observability
from turn_context_utils import (
    build_baggage_builder,
    create_agent_details,
    create_caller_details,
    create_invoke_agent_details,
    create_request,
    extract_turn_context_details,
)

logger = logging.getLogger(__name__)


class MyAgent(AgentInterface):
    def __init__(self) -> None:
        # A365 観測性を初期化（span を A365 にエクスポート）。起動時に一度だけ実行される。
        configure_observability()

    async def initialize(self) -> None:
        logger.info("Agent initialized")

    async def process_user_message(
        self, message: str, auth: Authorization, auth_handler_name: str, context: TurnContext
    ) -> str:
        ctx = extract_turn_context_details(context)
        # baggage（tenant / agent / 会話 ID 等）を span 間に伝播させる
        with build_baggage_builder(context).build():
            agent_details = create_agent_details(ctx)
            caller_details = create_caller_details(ctx)
            request = create_request(ctx, message)
            invoke_details = create_invoke_agent_details(ctx)

            # invoke_agent セマンティック span（MAC Activity のルート）
            with InvokeAgentScope.start(
                request=request,
                scope_details=invoke_details,
                agent_details=agent_details,
                caller_details=caller_details,
            ) as invoke_scope:
                if hasattr(invoke_scope, "record_input_messages"):
                    invoke_scope.record_input_messages([message])

                # chat セマンティック span（LLM 呼び出し）
                inference_details = InferenceCallDetails(
                    operationName=InferenceOperationType.CHAT,
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "unknown"),
                    providerName="Azure OpenAI (Foundry)",
                )
                with InferenceScope.start(
                    request=request,
                    details=inference_details,
                    agent_details=agent_details,
                ) as inference_scope:
                    response = llm.chat_complete(message)
                    if hasattr(inference_scope, "record_output_messages"):
                        inference_scope.record_output_messages([response])

                if hasattr(invoke_scope, "record_output_messages"):
                    invoke_scope.record_output_messages([response])

            return response

    async def cleanup(self) -> None:
        logger.info("Agent cleaned up")
