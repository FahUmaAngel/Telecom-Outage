# Telecom Outage Project - Task Checklist

This task list is generated based on the architectural documents in the `Plan guide` folder.

## 📡 Data Sources

### Telecom Operators
- **Telia**: [Driftinformation - Mobila Nätet](https://www.telia.se/foretag/support/driftinformation?category=mobila-natet)
- **Tre**: [Täckningskarta](https://www.tre.se/varfor-tre/tackning/tackningskarta)
- **Lycamobile**: [5G Coverage](https://www.lycamobile.se/sv/5g-coverage/)

## 🏗️ Backend Development (FastAPI / Node.js)
- [ ] **Infrastructure & Core**
  - [ ] Initialize FastAPI project structure
  - [ ] Configure environment variables and `config.py`
  - [ ] Implement Logging and Error Handling
  - [ ] Set up RBAC (Role-Based Access Control) & Permissions
- [ ] **Database Layer**
  - [ ] Set up PostgreSQL with PostGIS extension
  - [ ] Implement Database Models (Outage, Operator, Report, User)
  - [ ] Configure Alembic for Migrations
  - [ ] Create Database Seed scripts
- [ ] **API Development**
  - [ ] `GET /api/outages/current` - Live outages
  - [ ] `GET /api/outages/{id}` - Detailed outage info
  - [ ] `GET /api/outages/history` - Historical data
  - [ ] `GET /api/analytics/mttr` - Mean Time To Recovery stats
  - [ ] `GET /api/analytics/reliability` - Operator reliability comparison
  - [ ] `POST /api/reports` - Crowdsourced report submission
  - [ ] Auth Endpoints (Login, API Key management for researchers)
- [ ] **Core Engine Services**
  - [ ] Implement Deduplication logic
  - [ ] Implement Severity Scoring engine
  - [ ] Implement Incident Status Change detection
  - [ ] Geocoding service for user reports
- [ ] **Background Tasks**
  - [ ] Set up Scheduler (Cron/Celery)
  - [ ] Implement Database cleanup tasks

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
- [ ] **Scraper Implementation**
  - [ ] **Telia**: Fetcher, HTML/API Parser, and Data Mapper
  - [ ] **Tre**: Fetcher, HTML/JSON Parser, and Data Mapper
  - [ ] **Crowd**: Listener for user reports and 3rd party aggregators
- [ ] **Processing Pipeline**
  - [ ] Implement Data Normalizer (Standardize formats)
  - [ ] Implement Identity Mapping (Link raw data to known operators/locations)
  - [ ] Set up Immutable Raw Data storage
- [ ] **Orchestration**
  - [ ] Create the main Scraper Runner script
  - [ ] Configure execution frequency (1–5 minutes)

## 🚀 DevOps & Deployment
- [ ] Containerize Application (Dockerfiles for all services)
- [ ] Configure CI/CD Pipelines
- [ ] Set up AWS/Cloud Infrastructure:
  - [ ] CloudFront for Frontend CDN
  - [ ] API Gateway for Backend routing
  - [ ] ECS/Lambda for compute clusters
  - [ ] RDS for Managed Postgres + PostGIS
