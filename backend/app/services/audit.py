from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    actor_id: UUID,
    commune_id: UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    payload: dict | None = None,
) -> None:
    entry = AuditLog(
        actor_id=actor_id,
        commune_id=commune_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload,
    )
    db.add(entry)
    await db.flush()
