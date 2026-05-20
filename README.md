# Swedish Telecom Outage Monitor

A research platform for monitoring and analyzing network outage data from Swedish telecom operators — Telia, Telenor, and Tre — with the goal of evaluating service reliability and consumer value.

**Live Dashboard:** [fahumaangel.github.io/Telecom-Outage](https://fahumaangel.github.io/Telecom-Outage)

---

## Research Background

Swedish consumers pay among the highest mobile subscription fees in Europe, yet there is limited publicly available data on how often networks fail, how long outages last, and whether operators meet international standards. This project addresses that gap by automatically collecting real-time outage data and applying structured analysis to answer three core research questions:

**RQ1 — MTTR Distribution:** What is the Mean Time To Repair (MTTR) distribution per operator?
Analyzed using percentile analysis (P50, P75, P90, P95, P99) and Kruskal-Wallis H-test to determine whether differences across operators are statistically significant.

**RQ2 — Consumer Value:** Are consumers receiving value for their money?
Measured using a composite **Consumer Value Score (CVS)** weighted across five dimensions: MTTR (30%), outage frequency (20%), total downtime (20%), service coverage (15%), and SLA compliance (15%).

**RQ3 — SLA Compliance:** Are operators meeting international SLA standards?
Benchmarked against ITU-T E.800, ETSI EG 202 057-1, and Swedish regulator PTSFS 2014:1 — categorized by incident severity (critical: 4h, major: 24h, minor: 48h).

---

## Methodology

Data is collected automatically every 5 minutes from the official outage status portals of each operator. Each incident is recorded with start time, estimated resolution time, affected region, and service type (2G/4G/5G).

MTTR is calculated as `resolved_at − start_time` in hours, with unrealistic values (> 8,760h / 1 year) excluded. Bootstrap confidence intervals use 1,000 iterations. CVS components are normalized to [0, 1] using min-max scaling — lower MTTR, frequency, and downtime produce higher scores. Statistical testing uses Kruskal-Wallis H (non-parametric) with effect size η² at α = 0.05.

This work targets IEEE publication standards.

---

## Platform Features

- Real-time outage tracking with 5-minute refresh cycle
- Interactive map showing outage locations across Swedish counties
- MTTR statistics and percentile distributions per operator
- Consumer Value Score ranking
- SLA compliance comparison against ITU-T and ETSI benchmarks
- Outage trend analysis over time
- User-submitted outage reports
- Bilingual interface (Swedish / English)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (static export) → GitHub Pages |
| Backend API | FastAPI + APScheduler → Render |
| Database | PostgreSQL on Supabase |
| Scrapers | Python `requests` (HTTP, no browser) |

---

## Project Structure

```
Telecom-Outage/
├── backend/              # FastAPI application
│   ├── main.py           # Entry point, background scheduler
│   ├── routers/          # API endpoints
│   └── middleware.py     # Logging & security headers
├── scrapers/             # Automated data collection
│   ├── run.py            # Main scraper runner (Telia, Telenor, Tre)
│   ├── telia/            # Telia HTTP scraper
│   ├── telenor/          # Telenor HTTP scraper
│   ├── tre/              # Tre HTTP scraper
│   └── db/               # Database models & CRUD
├── frontend/             # Next.js dashboard
│   └── src/app/
│       ├── page.js           # Dashboard — active outages
│       ├── reports/          # All incidents list
│       ├── analytics/        # Trend and reliability charts
│       ├── statistics/       # MTTR distributions
│       ├── value-score/      # Consumer Value Score
│       ├── sla-compliance/   # SLA benchmark comparison
│       ├── map/              # Geographic outage map
│       └── methodology/      # Research methodology & references
└── migrate_sqlite_to_postgres.py  # Data migration tool
```

---

## Local Development

### Backend

```bash
pip install -r backend/requirements.txt
# Create .env with DATABASE_URL=...
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## References

- ITU-T Recommendation E.800 (2008) — QoS definitions and SLA thresholds
- ETSI EG 202 057-1 V2.1.1 (2013) — Time-to-restore benchmarks (P95 ≤ 48h)
- PTSFS 2014:1 — Swedish PTS regulation on incident reporting
- ITU-T M.3400 (2000) — MTTR definition in telecom management
- Soldani et al. (2006) — QoS/QoE weighting framework
- Kruskal & Wallis (1952) — Non-parametric variance analysis
