import httpx

from bot.schemas.messages import MessageRequest
from bot.utils.logging import logger
from config.bot_settings import get_bot_settings


class BackendClient:
    _client: httpx.AsyncClient | None = None

    def __init__(self) -> None:
        if not BackendClient._client:
            settings = get_bot_settings()
            BackendClient._client = httpx.AsyncClient(
                base_url=settings.backend_base_url,
                timeout=httpx.Timeout(60.0),
                headers={"X-API-Key": settings.backend_api_key},
            )

        self._client = BackendClient._client

    async def save_message(self, payload: MessageRequest) -> None:
        logger.debug("SAVE MESSAGE PAYLOAD:\n%s", payload.model_dump())

        response = await self._client.post(
            "/v1/messages/messages",
            json=payload.model_dump(mode="json"),
        )

        if response.status_code in (400, 409):
            return

        response.raise_for_status()
