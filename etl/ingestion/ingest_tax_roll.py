"""
Tax roll CSV ingestion script.

Usage:
  python ingest_tax_roll.py \
    --commune-code 101040 \
    --file /data/sale_tax_roll_2025.csv \
    --db-url postgresql://fiscalai:secret@localhost:5432/fiscalai

Expected CSV columns (flexible — column mapping in COLUMN_MAP below):
  - address or adresse or ADDRESS
  - declared_area or surface or surface_declaree
  - tsc_amount or tsc or montant_tsc
  - tpb_amount or tpb or montant_tpb  (optional)
  - last_payment_year or annee_paiement (optional)
  - taxpayer_id or redevable_id (optional)

The script normalizes addresses and loads into the tax_roll table.
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Add backend to path when run standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
from app.services.address_normalizer import batch_normalize

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Flexible column name mapping: canonical name → list of accepted CSV headers
COLUMN_MAP = {
    "address_raw":        ["adresse", "address", "addr", "ADDRESS", "ADRESSE"],
    "declared_area_m2":   ["surface", "surface_declaree", "declared_area", "area_m2", "SURFACE"],
    "tsc_annual_mad":     ["tsc", "montant_tsc", "tsc_amount", "TSC"],
    "tpb_annual_mad":     ["tpb", "montant_tpb", "tpb_amount", "TPB"],
    "last_payment_year":  ["annee_paiement", "last_payment_year", "last_year"],
    "redevable_id":       ["redevable_id", "taxpayer_id", "id_redevable", "ID"],
}


def detect_column(df: pd.DataFrame, canonical: str) -> str | None:
    for candidate in COLUMN_MAP[canonical]:
        if candidate in df.columns:
            return candidate
    return None


def ingest_csv(file_path: str, commune_code: str, db_url: str, year: int = 2025, dry_run: bool = False):
    logger.info(f"Reading {file_path}")
    df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
    logger.info(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

    # Map columns
    col_mapping = {}
    for canonical in COLUMN_MAP:
        found = detect_column(df, canonical)
        if found:
            col_mapping[found] = canonical
        elif canonical == "address_raw":
            logger.error(f"Required column 'address' not found. Available: {list(df.columns)}")
            sys.exit(1)

    df = df.rename(columns=col_mapping)
    df["tax_year"] = year

    # Normalize addresses
    logger.info("Normalizing addresses...")
    df["address_normalized"] = batch_normalize(df["address_raw"].tolist())

    # Clean numeric columns
    for col in ["declared_area_m2", "tsc_annual_mad", "tpb_annual_mad"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove rows with no address
    df = df.dropna(subset=["address_raw"])
    logger.info(f"After cleaning: {len(df)} valid rows")

    if dry_run:
        logger.info("DRY RUN — first 5 normalized rows:")
        print(df[["address_raw", "address_normalized"]].head(5).to_string())
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Get commune_id
    cur.execute("SELECT id FROM communes WHERE code_commune = %s", (commune_code,))
    row = cur.fetchone()
    if not row:
        logger.error(f"Commune with code {commune_code} not found in database")
        sys.exit(1)
    commune_id = row[0]

    # Clear existing year data for this commune
    cur.execute("DELETE FROM tax_roll WHERE commune_id = %s AND tax_year = %s", (commune_id, year))
    logger.info(f"Cleared existing {year} tax roll for commune {commune_code}")

    # Batch insert
    records = []
    for _, row_data in df.iterrows():
        records.append((
            commune_id,
            row_data.get("redevable_id"),
            row_data["address_raw"],
            row_data.get("address_normalized"),
            row_data.get("declared_area_m2") or None,
            row_data.get("tsc_annual_mad") or None,
            row_data.get("tpb_annual_mad") or None,
            int(row_data["last_payment_year"]) if pd.notna(row_data.get("last_payment_year", float("nan"))) else None,
            year,
        ))

    execute_values(
        cur,
        """
        INSERT INTO tax_roll
          (commune_id, redevable_id, address_raw, address_normalized,
           declared_area_m2, tsc_annual_mad, tpb_annual_mad, last_payment_year, tax_year)
        VALUES %s
        """,
        records,
        page_size=500,
    )
    conn.commit()
    logger.info(f"Inserted {len(records)} rows into tax_roll for commune {commune_code}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest commune tax roll CSV into FiscalAI")
    parser.add_argument("--commune-code", required=True, help="DGCT commune code (e.g. 101040)")
    parser.add_argument("--file", required=True, help="Path to tax roll CSV file")
    parser.add_argument("--db-url", required=True, help="PostgreSQL connection URL")
    parser.add_argument("--year", type=int, default=2025, help="Tax year")
    parser.add_argument("--dry-run", action="store_true", help="Show normalization output without inserting")
    args = parser.parse_args()

    ingest_csv(args.file, args.commune_code, args.db_url, args.year, args.dry_run)
