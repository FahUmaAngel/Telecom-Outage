# Telecom Outage Project - Task Checklist

This task list is generated based on the architectural documents in the `Plan guide` folder.

## 📡 Data Sources

### Telecom Operators
- **Telia**: [Driftinformation - Mobila Nätet](https://www.telia.se/foretag/support/driftinformation?category=mobila-natet)
- **Tre**: [Täckningskarta](https://www.tre.se/varfor-tre/tackning/tackningskarta)
- **Lycamobile**: [5G Coverage](https://www.lycamobile.se/sv/5g-coverage/)

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
- [x] **Core Engine Services**
  - [x] Implement Deduplication logic
  - [x] Implement Severity Scoring engine
  - [x] Implement Incident Status Change detection
  - [x] Geocoding service for user reports (Haversine logic implemented)
- [x] **Background Tasks**
  - [x] Set up Scheduler (Cron/Celery) (APScheduler implemented)
  - [x] Implement Database cleanup tasks

## 🌐 Frontend Development (React / Next.js)
- [ ] **Setup & UI Kit**
  - [ ] Initialize Next.js with App Router and TypeScript
  - [ ] Configure Tailwind CSS / Vanilla CSS strategy
  - [ ] Create Reusable UI Components (Button, Modal, Filter, Badge)
- [ ] **Interactive Map**
  - [ ] Integrate Mapbox / Leaflet
  - [ ] Implement Outage Marker Layer with clusters
  - [ ] Create Map Legend and Info Overlays
- [ ] **Pages & Features**
  - [ ] **Home**: Live Outage Map with real-time updates
  - [ ] **Outage List**: Searchable and filterable list of incidents
  - [ ] **Incident Details**: Deep dive into specific outages with timeline
  - [ ] **Analytics Dashboards**:
    - [ ] MTTR Charts
    - [ ] Reliability Comparison (Bar charts)
    - [ ] Trends & Heatmaps
  - [ ] **Reporting Flow**: Multistep form for user reports
  - [ ] **Transparency**: Static pages for Methodology, Sources, etc.
  - [ ] **Admin Dashboard**: Incident validation and system health
- [ ] **State & API Integration**
  - [ ] Implement custom hooks for data fetching (`useOutages`, etc.)
  - [ ] Set up Real-time updates (Polling or WebSockets)
  - [ ] Implement Auth flow (Login, protected routes)

## 🕵️ Data Ingestion (Scrapers & Workers)
- [x] **Scraper Implementation**
  - [x] **Telia**: Fetcher, HTML/API Parser, and Data Mapper
  - [x] **Tre**: Fetcher, HTML/JSON Parser, and Data Mapper
  - [ ] **Crowd**: Listener for user reports and 3rd party aggregators
- [x] **Processing Pipeline**
  - [x] Implement Data Normalizer (Standardize formats)
  - [x] Implement Identity Mapping (Link raw data to known operators/locations)
  - [x] Set up Immutable Raw Data storage
- [x] **Orchestration**
  - [x] Create the main Scraper Runner script
  - [x] Configure execution frequency (1–5 minutes)

## 🚀 DevOps & Deployment
- [ ] Containerize Application (Dockerfiles for all services)
- [ ] Configure CI/CD Pipelines
- [ ] Set up AWS/Cloud Infrastructure:
  - [ ] CloudFront for Frontend CDN
  - [ ] API Gateway for Backend routing
  - [ ] ECS/Lambda for compute clusters
  - [ ] RDS for Managed Postgres + PostGIS
