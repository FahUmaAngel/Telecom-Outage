"""
Base class for 3rd party crowd aggregators.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class CrowdSignal(BaseModel):
    operator: str
    region_name: Optional[str] = None
    latitude: float
    longitude: float
    count: int
    source_name: str
    detected_at: datetime = datetime.utcnow()

class BaseCrowdAggregator(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fetch_signals(self) -> List[CrowdSignal]:
        """
        Fetch signals from the 3rd party source.
        """
        pass
