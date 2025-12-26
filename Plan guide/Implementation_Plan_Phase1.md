# Implementation Plan: Data Ingestion Layer (Phase 1)

## Goal Description

Build the foundational data ingestion layer for the Telecom Outage Platform. This phase focuses on creating web scrapers to collect outage information from three Swedish telecom operators (Telia, Tre, Lycamobile), normalizing the data into a consistent format, and storing it in a PostgreSQL database with PostGIS for geospatial queries.

## User Review Required

> [!IMPORTANT]
> **Technology Stack Decisions**
> - **Language**: Python 3.11+ (for scraping and data processing)
> - **Scraping Libraries**: 
>   - `requests` + `BeautifulSoup4` for static HTML parsing
>   - `playwright` or `selenium` as fallback for JavaScript-heavy pages
> - **Database**: PostgreSQL 15+ with PostGIS extension
> - **ORM**: SQLAlchemy for database models
> - **Scheduler**: APScheduler for periodic scraping (1-5 minute intervals)

> [!WARNING]
> **Data Source Limitations**
> The scrapers will depend on the public-facing structure of operator websites. If these sites change their HTML structure or implement anti-scraping measures, the scrapers will need updates.

---

## Proposed Changes

### Component: Project Structure

#### [NEW] [scrapers/](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/)
Root directory for all scraping-related code.

#### [NEW] [scrapers/requirements.txt](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/requirements.txt)
Python dependencies for the scraper layer:
- `requests`
- `beautifulsoup4`
- `lxml`
- `python-dateutil`
- `pydantic` (for data validation)
- `playwright` (optional, for JS-heavy sites)
- `apscheduler`
- `python-dotenv`

---

### Component: Telia Scraper

#### [NEW] [scrapers/telia/fetch.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/telia/fetch.py)
Fetches raw HTML/JSON from Telia's outage information page.
- Function: `fetch_telia_outages()` → Returns raw response
- Handles HTTP errors and retries
- Includes user-agent headers to mimic browser requests

#### [NEW] [scrapers/telia/parser.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/telia/parser.py)
Parses the fetched data to extract outage information.
- Function: `parse_telia_html(html_content)` → Returns list of raw outage dicts
- Extracts: incident ID, location, status, description, timestamps
- Uses BeautifulSoup4 for HTML parsing

#### [NEW] [scrapers/telia/mapper.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/telia/mapper.py)
Maps Telia-specific data to our standardized schema.
- Function: `map_to_standard(raw_outages)` → Returns list of normalized outages
- Converts Telia's format to our common schema

---

### Component: Tre Scraper

#### [NEW] [scrapers/tre/fetch.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/tre/fetch.py)
Fetches coverage/outage data from Tre's website.

#### [NEW] [scrapers/tre/parser.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/tre/parser.py)
Parses Tre's data structure (likely JSON from their coverage map API).

#### [NEW] [scrapers/tre/mapper.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/tre/mapper.py)
Maps Tre data to standard schema.

---

### Component: Lycamobile Scraper

#### [NEW] [scrapers/lycamobile/fetch.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/lycamobile/fetch.py)
Fetches 5G coverage data from Lycamobile.

#### [NEW] [scrapers/lycamobile/parser.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/lycamobile/parser.py)
Parses Lycamobile's coverage information.

#### [NEW] [scrapers/lycamobile/mapper.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/lycamobile/mapper.py)
Maps Lycamobile data to standard schema.

---

### Component: Common Utilities

#### [NEW] [scrapers/common/normalizer.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/common/normalizer.py)
Standardizes data across all operators.
- Defines `OutageSchema` using Pydantic
- Validates and normalizes timestamps (to UTC)
- Standardizes location formats
- Assigns severity levels based on keywords

#### [NEW] [scrapers/common/deduplicator.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/common/deduplicator.py)
Detects duplicate outages across multiple scraping runs.
- Compares by: operator + location + timestamp window
- Prevents storing the same outage multiple times

#### [NEW] [scrapers/common/models.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/common/models.py)
Pydantic models for data validation:
- `RawOutage`: Raw data from scrapers
- `NormalizedOutage`: Standardized format
- `Operator`: Enum for operator names

---

### Component: Database Layer

#### [NEW] [scrapers/db/connection.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/db/connection.py)
Database connection management using SQLAlchemy.

#### [NEW] [scrapers/db/models.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/db/models.py)
SQLAlchemy ORM models:
- `Operator` table
- `Outage` table (with PostGIS geometry column for location)
- `OutageUpdate` table (timeline of status changes)
- `RawData` table (immutable storage of original scraper responses)

#### [NEW] [scrapers/db/init_db.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/db/init_db.py)
Database initialization script:
- Creates tables
- Enables PostGIS extension
- Seeds operator data (Telia, Tre, Lycamobile)

---

### Component: Orchestration

#### [NEW] [scrapers/run.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/run.py)
Main orchestration script:
- Runs all scrapers sequentially
- Normalizes data
- Deduplicates
- Stores in database
- Can be run manually or via scheduler

#### [NEW] [scrapers/scheduler.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/scheduler.py)
Automated scheduling using APScheduler:
- Runs scrapers every 3 minutes
- Logs execution status
- Handles failures gracefully

---

### Component: Configuration

#### [NEW] [scrapers/.env.example](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/.env.example)
Environment variable template:
```
DATABASE_URL=postgresql://user:password@localhost:5432/telecom_outage
SCRAPER_INTERVAL_MINUTES=3
LOG_LEVEL=INFO
```

#### [NEW] [scrapers/config.py](file:///d:/94%20FAH%20works/Telecom-Outage/scrapers/config.py)
Configuration management using `pydantic-settings`.

---

## Verification Plan

### Automated Tests

1. **Unit Tests for Parsers**
   ```bash
   cd scrapers
   python -m pytest tests/test_parsers.py -v
   ```
   - Test Telia parser with sample HTML
   - Test Tre parser with sample JSON
   - Test Lycamobile parser

2. **Integration Test for Full Pipeline**
   ```bash
   python -m pytest tests/test_integration.py -v
   ```
   - Run scraper → normalize → deduplicate → store
   - Verify data in test database

### Manual Verification

1. **Database Setup**
   ```bash
   # Install PostgreSQL with PostGIS
   # Create database
   createdb telecom_outage
   
   # Run initialization
   cd scrapers
   python db/init_db.py
   ```

2. **Run Single Scraper Test**
   ```bash
   cd scrapers
   python -c "from telia.fetch import fetch_telia_outages; print(fetch_telia_outages())"
   ```
   - Verify that data is fetched successfully
   - Check console output for any errors

3. **Run Full Orchestration**
   ```bash
   cd scrapers
   python run.py
   ```
   - Check database for new outage records
   - Verify timestamps are in UTC
   - Confirm no duplicate entries

4. **User Verification**
   - Ask user to check if PostgreSQL is installed
   - Ask user to provide database credentials
   - User should verify scraped data makes sense (locations, descriptions)
