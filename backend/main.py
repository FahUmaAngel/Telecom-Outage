"""
FastAPI Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import outages, operators, reports, analytics, auth, regions, admin
from .middleware import LoggingMiddleware

app = FastAPI(
    title="Telecom Outage API",
    description="API for accessing Swedish telecom outage data (Telia, Tre, Lycamobile)",
    version="1.0.0"
)

# CORS Configuration
origins = ["*"]

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(outages.router)
app.include_router(operators.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(regions.router, prefix="/api/v1")
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Telecom Outage API is running"}
