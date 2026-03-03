from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config.backend_settings import get_backend_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> None:
    settings = get_backend_settings()
    if api_key != settings.backend_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
