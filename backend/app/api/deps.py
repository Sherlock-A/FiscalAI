"""
FastAPI dependency injection — auth, RBAC, commune scoping.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token, CREDENTIALS_EXCEPTION
from app.db.database import get_db
from app.models.commune import Commune

bearer_scheme = HTTPBearer()


async def get_current_user_claims(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """Validate the JWT and return its claims."""
    return decode_token(credentials.credentials)


async def get_current_commune_id(
    claims: Annotated[dict, Depends(get_current_user_claims)],
) -> UUID:
    """
    Extract and validate the commune_id from the JWT claims.
    Every API call is automatically scoped to the caller's commune.
    """
    commune_id_str = claims.get("commune_id")
    if not commune_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not contain commune_id",
        )
    try:
        return UUID(commune_id_str)
    except ValueError:
        raise CREDENTIALS_EXCEPTION


def require_role(allowed_roles: list[str]):
    """Dependency factory for role-based access control."""
    async def _check(claims: Annotated[dict, Depends(get_current_user_claims)]):
        role = claims.get("role", "readonly")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not authorized for this action",
            )
    return _check
