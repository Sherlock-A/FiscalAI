"""
PDF evidence report generation endpoint.

POST /api/v1/gaps/{gap_id}/report
  - Generates a PDF evidence report for a validated gap detection
  - Returns the PDF as a streaming download (application/pdf)
  - Requires analyst or admin role
  - The report is decision-support only — see legal disclaimer in the PDF
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.gap_detection import GapDetection
from app.models.commune import Commune
from app.api.deps import get_current_commune_id, require_role
from app.services.report_generator import generate_gap_report

import io

router = APIRouter(prefix="/gaps", tags=["Reports"])


class ReportRequest(BaseModel):
    agent_notes: str | None = None


@router.post("/{gap_id}/report")
async def generate_report(
    gap_id: UUID,
    body: ReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    commune_id: Annotated[UUID, Depends(get_current_commune_id)],
    _: Annotated[None, Depends(require_role(["admin", "analyst"]))],
):
    """
    Generate a PDF evidence report for a gap detection.

    The report is a decision-support document — it contains all data sources,
    a confidence indicator, an estimated gap, and a blank agent recommendation
    section. No enforcement action is embedded in the report.
    """
    gap = await db.get(GapDetection, gap_id)
    if not gap or gap.commune_id != commune_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection not found")

    commune = await db.get(Commune, commune_id)
    commune_name = commune.name if commune else "Commune"

    pdf_bytes = generate_gap_report(
        gap_id=str(gap.id),
        commune_name=commune_name,
        address_resolved=gap.address_resolved,
        gap_type=gap.gap_type,
        confidence_score=gap.confidence_score,
        estimated_gap_mad=gap.estimated_gap_mad,
        status=gap.status,
        evidence=gap.evidence,
        agent_notes=body.agent_notes,
        detected_at=gap.detected_at,
    )

    filename = f"FiscalAI_FA-{str(gap.id)[:8].upper()}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
