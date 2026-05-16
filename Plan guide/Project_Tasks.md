# Telecom Outage Project - Task Checklist

This task list is generated based on the architectural documents in the `Plan guide` folder.

## 📡 Data Sources

### Telecom Operators
- **Telia**: [Driftinformation - Mobila Nätet](https://www.telia.se/foretag/support/driftinformation?category=mobila-natet)
- **Tre**: [Täckningskarta](https://www.tre.se/varfor-tre/tackning/tackningskarta)
- **Telenor**: Scraper implemented (1,090 outages)
- **Lycamobile**: [5G Coverage](https://www.lycamobile.se/sv/5g-coverage/) — scraper not yet implemented

## 🏗️ Backend Development (FastAPI / Node.js)
- [x] **Infrastructure & Core**
  - [x] Initialize FastAPI project structure
  - [x] Configure environment variables and `config.py`
  - [x] Implement Logging and Error Handling
  - [x] Set up RBAC (Role-Based Access Control) & Permissions
- [x] **Database Layer**
  - [x] Set up PostgreSQL with PostGIS extension (Pivoted to SQLite for now)
  - [x] Implement Database Models (Outage, Operator, Report, User)
  - [x] Configure Alembic for Migrations
  - [x] Create Database Seed scripts
- [x] **API Development**
  - [x] `GET /api/outages/current` - Live outages
  - [x] `GET /api/outages/{id}` - Detailed outage info
  - [x] `GET /api/outages/history` - Historical data
  - [x] `GET /api/analytics/mttr` - Mean Time To Recovery stats
  - [x] `GET /api/analytics/reliability` - Operator reliability comparison
  - [x] `POST /api/reports` - Crowdsourced report submission
  - [x] Auth Endpoints (CORS & Base setup done)
  - [x] `GET /api/research/mttr-percentiles` - MTTR percentiles per operator
  - [x] `GET /api/research/mttr-distribution` - MTTR histogram distribution
  - [x] `GET /api/research/statistical-test` - Kruskal-Wallis / ANOVA
  - [x] `GET /api/research/sla-compliance` - SLA compliance vs ITU-T/ETSI/PTS
  - [x] `GET /api/research/value-score` - Consumer Value Score (CVS)
- [x] **Core Engine Services**
  - [x] Implement Deduplication logic
  - [x] Implement Severity Scoring engine
  - [x] Implement Incident Status Change detection
  - [x] Geocoding service for user reports (Haversine logic implemented)
- [x] **Background Tasks**
  - [x] Set up Scheduler (Cron/Celery) (APScheduler implemented)
  - [x] Implement Database cleanup tasks

## 🌐 Frontend Development (React / Next.js)
- [x] **Setup & UI Kit**
  - [x] Initialize Next.js with App Router
  - [x] Configure CSS strategy (styled-jsx + CSS variables)
  - [x] Dark / Light theme toggle
  - [x] EN / SV language toggle
  - [x] Responsive layout — Header, Sidebar (mobile hamburger + slide-in)
- [x] **Interactive Map**
  - [x] Integrate Leaflet
  - [x] Implement Outage Marker Layer
  - [x] Create Map Legend and Info Overlays
  - [ ] Marker clustering (not yet implemented)
- [x] **Pages & Features**
  - [x] **Home** (`/`): Live dashboard with KPI cards, charts, operator comparison
  - [x] **Live Map** (`/map`): Real-time outage map with Leaflet
  - [x] **Regions** (`/regions`): Outages grouped by region
  - [x] **Analytics** (`/analytics`): MTTR charts, reliability comparison
  - [x] **Performance** (`/prestanda`): Operator performance metrics
  - [x] **Reports** (`/reports`): Searchable and filterable outage list
  - [x] **Report Outage** (`/report`): Multistep form for crowdsourced reports
  - [x] **Admin** (`/admin`): Incident validation and system health
  - [x] **Statistics** (`/statistics`): MTTR percentiles, histograms, hypothesis testing — CSV export
  - [x] **SLA Compliance** (`/sla-compliance`): Compliance vs ITU-T E.800 / ETSI / PTS — CSV export
  - [x] **Value Score** (`/value-score`): Consumer Value Score (CVS) radar + ranking — CSV export
  - [x] **Methodology** (`/methodology`): Research questions, pipeline, architecture diagram, references
- [x] **State & API Integration**
  - [x] API client (`lib/api.js`) with custom fetch hooks
  - [x] Toast notifications
  - [x] CSV export utility (`lib/exportCsv.js`)
  - [ ] Real-time updates (Polling / WebSockets) — not yet implemented
  - [ ] Auth flow (Login, protected routes) — not yet implemented

## 🕵️ Data Ingestion (Scrapers & Workers)
- [x] **Scraper Implementation**
  - [x] **Telia**: Fetcher, HTML/API Parser, and Data Mapper (962 outages)
  - [x] **Tre**: Fetcher, HTML/JSON Parser, and Data Mapper (229 outages)
  - [x] **Telenor**: Fetcher, Parser, and Data Mapper (1,090 outages)
  - [x] **Crowd**: Listener for user reports and 3rd party aggregators
  - [ ] **Lycamobile**: Not yet implemented
  - [ ] **Tele2**: Raw data collected but not imported as outages
- [x] **Processing Pipeline**
  - [x] Implement Data Normalizer (Standardize formats)
  - [x] Implement Identity Mapping (Link raw data to known operators/locations)
  - [x] Set up Immutable Raw Data storage (25,796 raw rows)
- [x] **Orchestration**
  - [x] Create the main Scraper Runner script (`run_scheduler.bat`)
  - [x] Configure execution frequency (1–5 minutes)

## 🚀 DevOps & Deployment
- [ ] Containerize Application (Dockerfiles for all services)
- [ ] Configure CI/CD Pipelines
- [ ] Set up AWS/Cloud Infrastructure:
  - [ ] CloudFront for Frontend CDN
  - [ ] API Gateway for Backend routing
  - [ ] ECS/Lambda for compute clusters
  - [ ] RDS for Managed Postgres + PostGIS
