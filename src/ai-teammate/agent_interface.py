from abc import ABC, abstractmethod

from microsoft_agents.hosting.core import Authorization


class AgentInterface(ABC):
    """AI Teammate 本体の抽象基底（host_agent_server がこのI/Fを呼ぶ）。"""

    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def process_user_message(
        self, message: str, auth: Authorization, auth_handler_name: str | None, context
    ) -> str: ...

    async def handle_agent_notification_activity(
        self, notification_type, payload, context, auth, auth_handler_name
    ) -> str | None:
        return None

    async def cleanup(self) -> None: ...
