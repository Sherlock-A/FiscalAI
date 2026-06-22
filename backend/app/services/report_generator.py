"""
PDF evidence report generator using ReportLab.

Each report covers a single gap detection and is intended for use by a commune
agent as a working document — not as an enforcement notice. The agent fills in
the recommendation section manually before any administrative action.

Legal disclaimer (last page footer):
  "Ce rapport est un outil d'aide à la décision. Toute action administrative
   est de la responsabilité exclusive de la commune."
"""

from __future__ import annotations

import io
import tempfile
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Colour palette (slate / green matching the dashboard)
BRAND_GREEN = colors.HexColor("#16a34a")
SLATE_800 = colors.HexColor("#1e293b")
SLATE_400 = colors.HexColor("#94a3b8")
RED_400 = colors.HexColor("#f87171")
WHITE = colors.white
BLACK = colors.black

GAP_TYPE_LABELS = {
    "missing_declaration": "Bâtiment non référencé dans le registre fiscal",
    "underdeclared": "Superficie déclarée potentiellement sous-estimée",
    "unlicensed_business": "Activité commerciale sans enregistrement fiscal",
}

STATUS_LABELS = {
    "new": "Nouveau",
    "under_review": "En cours de révision",
    "notice_sent": "Mise en demeure envoyée",
    "paid": "Régularisé",
    "contested": "Contesté",
    "dismissed": "Classé sans suite",
}


def generate_gap_report(
    gap_id: str,
    commune_name: str,
    address_resolved: str,
    gap_type: str,
    confidence_score: float | Decimal | None,
    estimated_gap_mad: float | Decimal | None,
    status: str,
    evidence: dict[str, Any] | None,
    agent_notes: str | None = None,
    detected_at: datetime | None = None,
) -> bytes:
    """
    Generate a PDF evidence report for a single gap detection.

    Returns the PDF as raw bytes (application/pdf).
    The caller is responsible for streaming or saving to disk/S3.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"Rapport FiscalAI — {gap_id[:8]}",
        author="FiscalAI",
        subject="Rapport d'incohérence de données — Registre fiscal communal",
    )

    styles = _build_styles()
    story = []

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("FiscalAI", styles["brand"]))
    story.append(Paragraph("Système d'aide à la décision — Registre Fiscal Communal", styles["brand_sub"]))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GREEN, spaceAfter=4 * mm))

    # Report metadata table (right-aligned)
    meta_data = [
        ["Commune :", commune_name],
        ["Référence dossier :", f"FA-{gap_id[:8].upper()}"],
        ["Date de rapport :", date.today().strftime("%d/%m/%Y")],
        ["Date de détection :", detected_at.strftime("%d/%m/%Y") if detected_at else "—"],
        ["Statut :", STATUS_LABELS.get(status, status)],
    ]
    meta_table = Table(meta_data, colWidths=[5 * cm, 9 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE_400),
        ("TEXTCOLOR", (1, 0), (1, -1), BLACK),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6 * mm))

    # ── Section 1 — Property description ──────────────────────────────────────
    story.append(Paragraph("1. Identification de la propriété / entité", styles["section_header"]))
    story.append(Spacer(1, 2 * mm))

    prop_data = [
        ["Adresse", address_resolved or "—"],
        ["Type d'incohérence", GAP_TYPE_LABELS.get(gap_type, gap_type)],
        ["Surface estimée (OSM)", _fmt_area(evidence)],
    ]
    story.append(_data_table(prop_data, styles))
    story.append(Spacer(1, 6 * mm))

    # ── Section 2 — Discrepancy description ───────────────────────────────────
    story.append(Paragraph("2. Description de l'incohérence détectée", styles["section_header"]))
    story.append(Spacer(1, 2 * mm))

    description = _build_description(gap_type, evidence, estimated_gap_mad, confidence_score)
    story.append(Paragraph(description, styles["body"]))
    story.append(Spacer(1, 4 * mm))

    # Confidence + estimated gap highlight box
    conf_pct = int(float(confidence_score or 0) * 100)
    gap_str = f"{float(estimated_gap_mad or 0):,.0f} MAD/an".replace(",", " ")
    highlight_data = [
        ["Niveau de confiance de la détection", f"{conf_pct} %"],
        ["Écart fiscal estimé (annuel)", gap_str],
    ]
    h_table = Table(highlight_data, colWidths=[11 * cm, 5 * cm])
    h_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE_800),
        ("TEXTCOLOR", (1, 0), (1, -1), BRAND_GREEN),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 1, BRAND_GREEN),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, SLATE_400),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(h_table)
    story.append(Spacer(1, 6 * mm))

    # ── Section 3 — Evidence & data sources ───────────────────────────────────
    story.append(Paragraph("3. Sources de données et éléments probants", styles["section_header"]))
    story.append(Spacer(1, 2 * mm))

    sources = _build_sources_list(gap_type, evidence)
    for src in sources:
        story.append(Paragraph(f"• {src}", styles["bullet"]))
    story.append(Spacer(1, 6 * mm))

    # ── Section 4 — Agent recommendation (blank) ──────────────────────────────
    story.append(Paragraph("4. Recommandation de l'agent (à compléter manuellement)", styles["section_header"]))
    story.append(Spacer(1, 2 * mm))

    if agent_notes:
        story.append(Paragraph(agent_notes, styles["body"]))
    else:
        story.append(Paragraph(
            "[ Espace réservé à la recommandation de l'agent terrain — "
            "à compléter avant toute action administrative ]",
            styles["placeholder"],
        ))
    story.append(Spacer(1, 4 * mm))

    # Signature block
    sig_data = [
        ["Nom et prénom de l'agent :", ""],
        ["Matricule / Service :", ""],
        ["Date de validation :", ""],
        ["Signature :", ""],
    ]
    sig_table = Table(sig_data, colWidths=[7 * cm, 9 * cm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE_400),
        ("LINEBELOW", (1, 0), (1, -1), 0.5, SLATE_400),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8 * mm))

    # ── Legal disclaimer footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_400, spaceAfter=3 * mm))
    story.append(Paragraph(
        "<b>Avertissement légal :</b> Ce rapport est un outil d'aide à la décision produit par le "
        "système FiscalAI à partir de données publiques (OpenStreetMap, imagerie satellite Copernicus) "
        "et de données administratives transmises volontairement par la commune. Il ne constitue pas "
        "un acte administratif et ne peut pas être utilisé directement comme base légale d'imposition. "
        "<b>Toute décision administrative, mise en demeure ou procédure de régularisation fiscale "
        "est de la responsabilité exclusive de la commune et de ses agents habilités.</b> "
        "FiscalAI ne détient aucune donnée personnelle relative aux occupants ou propriétaires "
        "de la propriété concernée.",
        styles["disclaimer"],
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Généré par FiscalAI v0.1 · Traitement des données conforme à la Loi 09-08 (CNDP Maroc) · "
        f"Réf. dossier FA-{gap_id[:8].upper()}",
        styles["disclaimer_ref"],
    ))

    doc.build(story)
    return buffer.getvalue()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "brand", fontName="Helvetica-Bold", fontSize=18,
            textColor=BRAND_GREEN, spaceAfter=1 * mm,
        ),
        "brand_sub": ParagraphStyle(
            "brand_sub", fontName="Helvetica", fontSize=9,
            textColor=SLATE_400, spaceAfter=2 * mm,
        ),
        "section_header": ParagraphStyle(
            "section_header", fontName="Helvetica-Bold", fontSize=11,
            textColor=SLATE_800, borderPad=2, spaceBefore=2 * mm, spaceAfter=1 * mm,
            borderWidth=0, leftIndent=0, backColor=colors.HexColor("#f1f5f9"),
            leading=14,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9,
            textColor=BLACK, leading=14, spaceAfter=2 * mm,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=9,
            textColor=BLACK, leading=13, leftIndent=6 * mm, spaceAfter=1 * mm,
        ),
        "placeholder": ParagraphStyle(
            "placeholder", fontName="Helvetica-Oblique", fontSize=9,
            textColor=SLATE_400, leading=13,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", fontName="Helvetica", fontSize=7.5,
            textColor=SLATE_400, leading=11, spaceAfter=1 * mm,
        ),
        "disclaimer_ref": ParagraphStyle(
            "disclaimer_ref", fontName="Helvetica-Oblique", fontSize=7,
            textColor=SLATE_400, leading=10, alignment=TA_CENTER,
        ),
    }


def _data_table(rows: list[list[str]], styles: dict) -> Table:
    table = Table(rows, colWidths=[5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE_400),
        ("TEXTCOLOR", (1, 0), (1, -1), BLACK),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    return table


def _fmt_area(evidence: dict | None) -> str:
    if not evidence:
        return "—"
    area = evidence.get("building_area_m2") or evidence.get("actual_m2")
    if area:
        return f"{float(area):,.0f} m²"
    return "Non disponible"


def _build_description(
    gap_type: str,
    evidence: dict | None,
    estimated_gap_mad: float | Decimal | None,
    confidence_score: float | Decimal | None,
) -> str:
    e = evidence or {}
    conf_pct = int(float(confidence_score or 0) * 100)
    gap_val = float(estimated_gap_mad or 0)

    if gap_type == "missing_declaration":
        match_score = e.get("address_match_score", 0)
        has_utility = e.get("has_utility_hookup", False)
        utility_str = (
            "Une connexion électrique (ONEE) a été identifiée à cette adresse, "
            "ce qui constitue un indicateur fort d'occupation."
            if has_utility
            else "Aucune connexion électrique n'a pu être corrélée à cette adresse dans les données disponibles."
        )
        return (
            f"Le système a identifié un bâtiment référencé dans OpenStreetMap (base de données "
            f"géographique publique) pour lequel aucune entrée correspondante n'a été trouvée dans "
            f"le registre fiscal de la commune (score de correspondance d'adresse : {match_score:.0%}). "
            f"{utility_str} "
            f"L'écart fiscal annuel estimé, sur la base du taux TSC applicable, est de "
            f"{gap_val:,.0f} MAD. "
            f"Niveau de confiance de la détection : {conf_pct} %. "
            f"<b>Cette information doit être vérifiée par un agent terrain avant toute action.</b>"
        )
    elif gap_type == "underdeclared":
        declared = e.get("declared_m2", 0)
        actual = e.get("actual_m2", 0)
        return (
            f"Le relevé de superficie du bâtiment dans OpenStreetMap ({float(actual):,.0f} m²) "
            f"est significativement supérieur à la superficie déclarée dans le registre fiscal "
            f"({float(declared):,.0f} m²). "
            f"L'écart de superficie est de {float(actual) - float(declared):,.0f} m², "
            f"représentant un écart fiscal annuel estimé de {gap_val:,.0f} MAD. "
            f"<b>Cette information doit être vérifiée par un agent terrain avant toute action.</b>"
        )
    else:
        return (
            f"Une incohérence de type « {GAP_TYPE_LABELS.get(gap_type, gap_type)} » "
            f"a été détectée avec un niveau de confiance de {conf_pct} %. "
            f"Écart fiscal estimé : {gap_val:,.0f} MAD/an. "
            f"<b>Vérification terrain requise avant toute action administrative.</b>"
        )


def _build_sources_list(gap_type: str, evidence: dict | None) -> list[str]:
    e = evidence or {}
    sources = [
        "OpenStreetMap (openstreetmap.org) — données cartographiques publiques sous licence ODbL",
        "Registre fiscal communal — données transmises par la commune à FiscalAI sous convention de traitement",
    ]
    if e.get("has_utility_hookup"):
        sources.append(
            "Données de connexions électriques (ONEE) — fournies par la commune ou par l'opérateur "
            "dans le cadre d'un accord de partage de données"
        )
    if gap_type == "underdeclared":
        sources.append(
            "Empreinte bâtimentaire OSM — superficie calculée par projection UTM zone 29N (EPSG:32629)"
        )
    sources.append(
        "Imagerie satellite publique (ESA Copernicus Sentinel-2) — utilisée pour validation visuelle "
        "en cas de doute sur la géométrie OSM (non automatisée dans cette version)"
    )
    return sources
