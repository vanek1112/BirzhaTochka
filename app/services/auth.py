from typing import Optional
from uuid import UUID
from fastapi import HTTPException, Header
from app.database import storage
from app.schemas import UserRole


async def get_current_user(authorization: Optional[str] = Header(None)) -> UUID:
    if not authorization or not authorization.startswith("TOKEN "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    api_key = authorization[6: ]
    user_id = storage.api_keys.get(api_key)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user_id


async def get_admin_user(authorization: Optional[str] = Header(None)) -> UUID:
    user_id = await get_current_user(authorization)
    user = storage.users.get(user_id)

    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user_id