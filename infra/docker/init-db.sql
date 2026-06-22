-- FiscalAI Database Initialization
-- Runs once when the PostgreSQL container first starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- for fuzzy address matching
CREATE EXTENSION IF NOT EXISTS unaccent;  -- for Arabic/French normalization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Communes table (one row per client commune)
CREATE TABLE communes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code_commune    VARCHAR(10) UNIQUE NOT NULL,  -- official DGCT code
    name            VARCHAR(200) NOT NULL,
    name_ar         VARCHAR(200),
    province        VARCHAR(100),
    region          VARCHAR(100),
    population      INTEGER,
    geometry        GEOMETRY(MULTIPOLYGON, 4326),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Building footprints (from OSM + cadastre uploads)
CREATE TABLE buildings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commune_id      UUID REFERENCES communes(id) ON DELETE CASCADE,
    source          VARCHAR(50) NOT NULL,         -- 'osm', 'cadastre', 'satellite'
    external_id     VARCHAR(200),                 -- OSM node ID or cadastre ref
    address_raw     TEXT,
    address_normalized TEXT,
    footprint       GEOMETRY(POLYGON, 4326) NOT NULL,
    area_m2         NUMERIC(10,2),
    floor_count     SMALLINT,
    construction_year SMALLINT,
    osm_tags        JSONB,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX buildings_commune_idx ON buildings(commune_id);
CREATE INDEX buildings_footprint_idx ON buildings USING GIST(footprint);
CREATE INDEX buildings_address_trgm ON buildings USING GIN(address_normalized gin_trgm_ops);

-- Tax roll entries (imported from commune SIT)
CREATE TABLE tax_roll (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commune_id      UUID REFERENCES communes(id) ON DELETE CASCADE,
    redevable_id    VARCHAR(100),                 -- taxpayer ID from SIT
    address_raw     TEXT NOT NULL,
    address_normalized TEXT,
    declared_area_m2 NUMERIC(10,2),
    tsc_annual_mad  NUMERIC(12,2),                -- Taxe de Services Communaux
    tpb_annual_mad  NUMERIC(12,2),                -- Taxe sur Propriétés Bâties
    last_payment_year SMALLINT,
    declaration_status VARCHAR(50) DEFAULT 'declared',  -- declared | underdeclared | missing
    tax_year        SMALLINT NOT NULL,
    imported_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX tax_roll_commune_idx ON tax_roll(commune_id);
CREATE INDEX tax_roll_address_trgm ON tax_roll USING GIN(address_normalized gin_trgm_ops);

-- Utility connections (ONEE/RADEEMA hookups — proxy for occupancy)
CREATE TABLE utility_connections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commune_id      UUID REFERENCES communes(id) ON DELETE CASCADE,
    utility_type    VARCHAR(20) NOT NULL,  -- 'electricity', 'water', 'sewage'
    address_raw     TEXT NOT NULL,
    address_normalized TEXT,
    connection_date DATE,
    meter_id        VARCHAR(100),
    geo_point       GEOMETRY(POINT, 4326),
    imported_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX utility_connections_commune_idx ON utility_connections(commune_id);
CREATE INDEX utility_connections_geo_idx ON utility_connections USING GIST(geo_point);

-- Gap detections (output of the ML scoring engine)
CREATE TABLE gap_detections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commune_id      UUID REFERENCES communes(id) ON DELETE CASCADE,
    building_id     UUID REFERENCES buildings(id),
    utility_conn_id UUID REFERENCES utility_connections(id),
    address_resolved TEXT NOT NULL,
    gap_type        VARCHAR(50) NOT NULL,   -- 'missing_declaration', 'underdeclared', 'unlicensed_business'
    confidence_score NUMERIC(5,4),          -- 0.0000 – 1.0000
    estimated_gap_mad NUMERIC(12,2),        -- estimated annual tax gap
    evidence         JSONB,                 -- supporting facts used to score this gap
    status          VARCHAR(50) DEFAULT 'new',   -- new | under_review | notice_sent | paid | contested | dismissed
    assigned_to     UUID,                   -- agent UUID
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX gap_detections_commune_idx ON gap_detections(commune_id);
CREATE INDEX gap_detections_status_idx ON gap_detections(status);
CREATE INDEX gap_detections_score_idx ON gap_detections(confidence_score DESC);
CREATE INDEX gap_detections_gap_idx ON gap_detections(estimated_gap_mad DESC);

-- Enforcement notices generated from gap detections
CREATE TABLE enforcement_notices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detection_id    UUID REFERENCES gap_detections(id) ON DELETE CASCADE,
    commune_id      UUID REFERENCES communes(id),
    notice_number   VARCHAR(100) UNIQUE NOT NULL,
    pdf_path        TEXT,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    sent_at         TIMESTAMPTZ,
    response_due    DATE,
    outcome         VARCHAR(50)   -- pending | paid | contested | no_response
);

-- Immutable audit log (append-only — no DELETE or UPDATE)
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor_id        UUID NOT NULL,
    actor_email     VARCHAR(200),
    commune_id      UUID,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     UUID,
    payload         JSONB,
    ip_address      INET,
    user_agent      TEXT,
    occurred_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX audit_log_commune_idx ON audit_log(commune_id);
CREATE INDEX audit_log_occurred_idx ON audit_log(occurred_at DESC);

-- Users (per-commune, managed by Keycloak externally — this is a local mirror)
CREATE TABLE users (
    id              UUID PRIMARY KEY,       -- same as Keycloak sub
    commune_id      UUID REFERENCES communes(id),
    email           VARCHAR(200) UNIQUE NOT NULL,
    role            VARCHAR(50) NOT NULL,   -- admin | analyst | readonly
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Row-level security: users see only their commune's data
ALTER TABLE buildings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_roll ENABLE ROW LEVEL SECURITY;
ALTER TABLE utility_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE gap_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE enforcement_notices ENABLE ROW LEVEL SECURITY;

-- Sample commune for local development
INSERT INTO communes (code_commune, name, name_ar, province, region, population)
VALUES ('101040', 'Salé', 'سلا', 'Salé', 'Rabat-Salé-Kénitra', 900000);
