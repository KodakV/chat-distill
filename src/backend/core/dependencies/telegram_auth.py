import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from config.backend_settings import get_backend_settings

_MAX_AUTH_AGE_SECONDS = 86400  # 24 hours


class WebAppUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    allows_write_to_pm: bool | None = None
    photo_url: str | None = None


def _verify_init_data(init_data_raw: str, bot_token: str) -> WebAppUser:
    """
    Validate WebApp initData according to the official algorithm:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    Raises HTTPException 401 on any validation failure.
    """
    pairs = dict(parse_qsl(init_data_raw, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing hash in initData",
        )

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(pairs.items())
    )
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    expected_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid initData signature",
        )

    try:
        auth_date = int(pairs["auth_date"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid auth_date in initData",
        )

    if time.time() - auth_date > _MAX_AUTH_AGE_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData has expired",
        )

    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user in initData",
        )

    try:
        user = WebAppUser(**json.loads(user_raw))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user payload in initData",
        )

    return user


async def get_webapp_user(
    authorization: str = Header(..., alias="Authorization"),
) -> WebAppUser:
    """
    FastAPI dependency that validates WebApp initData from the Authorization header.

    Expected header format:
        Authorization: tma <url-encoded initData string>
    """
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "tma" or not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use 'tma' scheme",
        )

    settings = get_backend_settings()
    return _verify_init_data(credentials, settings.bot_token)
