from dataclasses import dataclass

import httpx
from fastapi import HTTPException, Request

from .config import settings


@dataclass(frozen=True)
class Identity:
    user_id: str
    anonymous: bool


async def identity(request: Request) -> Identity:
    cookie = request.headers.get("cookie")
    if not cookie:
        raise HTTPException(401, "Your session has ended. Start a new demo to continue.")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{settings.auth_url}/api/auth/get-session",
                headers={"cookie": cookie},
                params={"disableCookieCache": "true"},
            )
        if response.status_code == 429:
            raise HTTPException(
                503, "Sign-in is busy. Wait a minute and try again. Your saved work is safe."
            )
        if response.status_code >= 500:
            raise HTTPException(503, "Sign-in is temporarily unavailable. Try again.")
        data = response.json() if response.status_code == 200 else None
        if not data or not isinstance(data.get("user", {}).get("id"), str):
            raise HTTPException(401, "Your session has ended. Start a new demo to continue.")
        return Identity(data["user"]["id"], data["user"].get("isAnonymous") is True)
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, "Sign-in is temporarily unavailable. Try again.") from None
