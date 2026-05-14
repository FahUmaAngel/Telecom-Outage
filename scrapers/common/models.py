"""
Common data models for all scrapers.
"""
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OperatorEnum(str, Enum):
    """Telecom operator names."""
    TELIA = "telia"
    TRE = "tre"
    TELENOR = "telenor"
    TELE2 = "tele2"


class ServiceType(str, Enum):
    """Mobile generation service types. Only 5G+, 5G, 4G, 3G, 2G."""
    MOBILE_5G_PLUS = "5g+"
    MOBILE_5G = "5g"
    MOBILE_4G = "4g"
    MOBILE_3G = "3g"
    MOBILE_2G = "2g"
    MOBILE = "mobile"  # Legacy fallback only


class SeverityLevel(str, Enum):
    """Outage severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OutageStatus(str, Enum):
    """Outage status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    INVESTIGATING = "investigating"
    SCHEDULED = "scheduled"


class RawOutage(BaseModel):
    """Raw outage data from scraper before normalization."""
    operator: OperatorEnum
    source_url: Optional[str] = None
    raw_data: dict
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class NormalizedOutage(BaseModel):
    """Standardized outage format."""
    operator: OperatorEnum
    incident_id: Optional[str] = None
    title: dict  # Bilingual: {"sv": "...", "en": "..."}
    description: Optional[dict] = None  # Bilingual
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: OutageStatus
    severity: SeverityLevel = SeverityLevel.MEDIUM
    started_at: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_fix_time: Optional[datetime] = None
    affected_services: list[ServiceType] = Field(default_factory=list)
    source_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
