"""
Pydantic Schemas for API responses.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class OutageStatus(str, Enum):
    detecting = "detecting"
    active = "active"
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"
    scheduled = "scheduled"

class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    unknown = "unknown"

class RegionResponse(BaseModel):
    id: int
    name: Dict[str, str]
    outage_count: Optional[int] = 0
    
    model_config = {"extra": "ignore"}

class OutageResponse(BaseModel):
    id: int
    incident_id: Optional[str] = None
    operator_id: Optional[int] = None
    operator_name: str
    region_id: Optional[int] = None
    region_name: Optional[Dict[str, str]] = None
    raw_data_id: Optional[int] = None
    
    title: Dict[str, str] # Bilingual
    description: Optional[Dict[str, str]] = None
    
    status: Optional[OutageStatus] = None
    severity: Optional[SeverityLevel] = None
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_fix_time: Optional[datetime] = None
    
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    affected_services: List[str] = []
    place: Optional[str] = None
    quality_issues: Optional[List[str]] = None
    updated_at: Optional[datetime] = None
    is_stale: bool = False
    stale_reason: Optional[str] = None
    resolution_type: Optional[str] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if v is None: return v
        val_str = str(v)
        if "OutageStatus" in val_str:
            val_str = val_str.split('.')[-1]
        return val_str.lower()

    @field_validator('severity', mode='before')
    @classmethod
    def normalize_severity(cls, v):
        if v is None: return v
        return str(v).lower()

    model_config = {"extra": "ignore"}

class ReportCreate(BaseModel):
    operator_name: Optional[str] = Field(default=None, max_length=50)
    title: str = Field(min_length=3, max_length=160)
    description: Optional[str] = Field(default=None, max_length=2000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

class ReportResponse(BaseModel):
    id: int
    operator_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    status: str
    created_at: datetime
    
    model_config = {"extra": "ignore"}

class MTTRResponse(BaseModel):
    operator_name: str
    average_mttr_hours: float
    outage_count: int
    active_count: int = 0
    stale_count: int = 0
    resolved_by_absence_count: int = 0
    estimated_mttr_hours: float = 0.0

class ReliabilityResponse(BaseModel):
    operator_name: str
    outage_count: int
    total_downtime_hours: float

class DailyTrend(BaseModel):
    date: str # YYYY-MM-DD
    count: int

class HistoricalTrendResponse(BaseModel):
    total_count: int
    trend: List[DailyTrend]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserBase(BaseModel):
    username: str
    role: str = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class HotspotResponse(BaseModel):
    operator_name: str
    region_name: Optional[Dict[str, str]] = None
    latitude: float
    longitude: float
    report_count: int
    type: str # USER_CLUSTER, EXTERNAL_SIGNAL
    source: Optional[str] = None
    detected_at: datetime

class OperatorResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class OutageUpdate(BaseModel):
    incident_id: Optional[str] = None
    operator_id: Optional[int] = None
    region_id: Optional[int] = None
    raw_data_id: Optional[int] = None
    title: Optional[Dict[str, str]] = None
    description: Optional[Dict[str, str]] = None
    status: Optional[OutageStatus] = None
    severity: Optional[SeverityLevel] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_fix_time: Optional[datetime] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    affected_services: Optional[List[str]] = None
    place: Optional[str] = None
    is_stale: Optional[bool] = None
    stale_reason: Optional[str] = None
    resolution_type: Optional[str] = None

    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if v is None: return v
        return str(v).lower()

    @field_validator('severity', mode='before')
    @classmethod
    def normalize_severity(cls, v):
        if v is None: return v
        val_str = str(v)
        if "SeverityLevel" in val_str:
            val_str = val_str.split('.')[-1]
        return val_str.lower()

class ResolvePlaceRequest(BaseModel):
    query: str

class ResolvePlaceResponse(BaseModel):
    latitude: float
    longitude: float
    display_name: str
    region_id: Optional[int] = None
