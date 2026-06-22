"""
Authentication routes.

For production: replace with Keycloak / OIDC integration.
The /auth/demo-token endpoint is only available in non-production environments
and auto-issues a JWT for the Salé demo commune so the dashboard works without
a full auth server during development and demos.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.database import get_db
from app.models.commune import Commune

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.get("/demo-token")
async def demo_token(db: AsyncSession = Depends(get_db)):
    """
    Return a short-lived JWT scoped to the Salé demo commune.
    Only available in development — returns 404 in production.
    """
    if settings.environment == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    result = await db.execute(
        select(Commune).where(Commune.code_commune == "101040")
    )
    commune = result.scalar_one_or_none()
    if not commune:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo commune not found — run generate_demo_data.py first, then seed the DB.",
        )

    token = create_access_token(
        subject=str(commune.id),
        extra_claims={"commune_id": str(commune.id), "role": "analyst"},
        expires_minutes=1440,  # 24h for demo sessions
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "commune_id": str(commune.id),
        "commune_name": commune.name,
    }
