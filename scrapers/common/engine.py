"""
Core Engine Services: Severity Scoring and Analytics tools.
"""
from typing import List
from .models import OutageStatus, SeverityLevel, ServiceType

def calculate_severity_score(severity: SeverityLevel, affected_services: List[ServiceType]) -> float:
    """
    Calculate a normalized severity score (0.0 to 10.0).
    Factors:
    - Base severity (Critical=1.0, High=0.8, Medium=0.5, Low=0.2)
    - Service impact (Mobile/Internet weight 1.5, Landline 1.0)
    """
    severity_weights = {
        SeverityLevel.CRITICAL: 1.0,
        SeverityLevel.HIGH: 0.8,
        SeverityLevel.MEDIUM: 0.5,
        SeverityLevel.LOW: 0.2
    }
    
    base_weight = severity_weights.get(severity, 0.5)
    
    # Simple multiplier based on service types
    service_multiplier = 1.0
    critical_services = [ServiceType.MOBILE, ServiceType.INTERNET, ServiceType.VOIP]
    
    for service in affected_services:
        if service in critical_services:
            service_multiplier += 0.5
        else:
            service_multiplier += 0.2
            
    # Max out at 10.0
    score = (base_weight * service_multiplier) * 5.0
    return min(10.0, score)
