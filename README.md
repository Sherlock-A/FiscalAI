# FiscalAI — Municipal Revenue Intelligence Platform

> Turn every Moroccan commune's uncollected tax debt into a real-time, AI-prioritized action queue.

## What It Does

FiscalAI cross-references a commune's property tax roll against utility hookups, building footprints, and business licenses to surface properties that are legally taxable but have never been declared. The output: a ranked list of enforcement targets, pre-filled legal notices, and a dashboard that proves ROI within 90 days.

## Project Structure

```
fiscalai/
├── backend/          FastAPI Python service (API + ML pipeline)
├── frontend/         Next.js 14 dashboard (map + tables + PDF)
├── etl/              Airflow DAGs + data ingestion scripts
├── ml/               Jupyter notebooks + trained model artifacts
├── infra/            Terraform (AWS eu-west-3) + Docker Compose
└── data/             Sample/test data (never commit real commune data)
```

## Quick Start (Local Dev)

```bash
# Start all services
docker compose up -d

# Backend API
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Stack

- **Frontend:** Next.js 14 + TypeScript + Tailwind + shadcn/ui + MapLibre GL
- **Backend:** FastAPI (Python 3.12) + PostgreSQL/PostGIS + Redis + Celery
- **ML:** XGBoost + GeoPandas + scikit-learn
- **Infra:** AWS ECS Fargate + RDS + ElastiCache — Terraform managed
- **CI/CD:** GitHub Actions → ECR → ECS

## Pilot Target

Medium Moroccan communes (30,000–200,000 residents) with active construction zones (Salé, Témara, Kénitra, Mohammedia).

**Pricing:** 3,000–18,000 MAD/month + 2% success fee on recovered revenue.
