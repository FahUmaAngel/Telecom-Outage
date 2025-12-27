"""
Database Models (SQLAlchemy).
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from .connection import Base
from ..common.models import OperatorEnum, SeverityLevel, OutageStatus

class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    outages = relationship("Outage", back_populates="operator")

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(JSON) # Bilingual {"sv": "...", "en": "..."}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    outages = relationship("Outage", back_populates="region")
    user_reports = relationship("UserReport", back_populates="region")

class RawData(Base):
    __tablename__ = "raw_data"
    
    id = Column(Integer, primary_key=True, index=True)
    operator = Column(String, index=True)
    source_url = Column(String, nullable=True)
    data = Column(JSON) # Store full JSON blob
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    outages = relationship("Outage", back_populates="raw_data")

class Outage(Base):
    __tablename__ = "outages"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, index=True) # Operator specific ID
    operator_id = Column(Integer, ForeignKey("operators.id"))
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    raw_data_id = Column(Integer, ForeignKey("raw_data.id"))
    
    title = Column(JSON) # Bilingual {"sv": "...", "en": "..."}
    description = Column(JSON, nullable=True) # Bilingual
    
    status = Column(Enum(OutageStatus))
    severity = Column(Enum(SeverityLevel))
    
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    estimated_fix_time = Column(DateTime(timezone=True), nullable=True)
    
    location = Column(String, nullable=True)
    # SQLite fallback: using specific columns instead of PostGIS Geometry
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # geom = Column(Geometry("POINT", srid=4326), nullable=True)
    
    affected_services = Column(JSON) # List of strings/enums
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    operator = relationship("Operator", back_populates="outages")
    region = relationship("Region", back_populates="outages")
    raw_data = relationship("RawData", back_populates="outages")

class UserReport(Base):
    __tablename__ = "user_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    
    title = Column(String)
    description = Column(Text, nullable=True)
    
    latitude = Column(Float)
    longitude = Column(Float)
    
    status = Column(String, default="pending") # pending, verified, rejected
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    operator = relationship("Operator")
    region = relationship("Region", back_populates="user_reports")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # admin, researcher, user
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

