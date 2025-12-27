"""
Pydantic Schemas for API responses.
"""
from pydantic import BaseModel
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
    minor = "minor"
    major = "major"
    critical = "critical"
    unknown = "unknown"

class RegionResponse(BaseModel):
    id: int
    name: Dict[str, str]
    outage_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class OutageResponse(BaseModel):
    id: int
    incident_id: Optional[str]
    operator_name: str
    region_id: Optional[int] = None
    region_name: Optional[Dict[str, str]] = None
    
    title: Dict[str, str] # Bilingual
    description: Optional[Dict[str, str]]
    
    status: OutageStatus
    severity: SeverityLevel
    
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    estimated_fix_time: Optional[datetime]
    
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    
    affected_services: List[str]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ReportCreate(BaseModel):
    operator_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float

class ReportResponse(BaseModel):
    id: int
    operator_name: Optional[str]
    title: str
    description: Optional[str]
    latitude: float
    longitude: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MTTRResponse(BaseModel):
    operator_name: str
    average_mttr_hours: float
    outage_count: int

class ReliabilityResponse(BaseModel):
    operator_name: str
    outage_count: int
    total_downtime_hours: float

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
    region_name: Optional[Dict[str, str]]
    report_count: int
    type: str # USER_CLUSTER, EXTERNAL_SIGNAL
    source: Optional[str] = None
    detected_at: datetime

class OperatorResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
