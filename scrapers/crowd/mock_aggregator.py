"""
Mock implementation of a 3rd party aggregator.
Simulates high report counts to test the detection engine.
"""
from typing import List
from .base import BaseCrowdAggregator, CrowdSignal
from datetime import datetime
import random

class MockAggregator(BaseCrowdAggregator):
    def __init__(self):
        super().__init__(name="MockDetector")

    def fetch_signals(self) -> List[CrowdSignal]:
        # Simulate high traffic for 'telia' in 'Stockholms län'
        signals = [
            CrowdSignal(
                operator="telia",
                region_name="Stockholms län",
                count=random.randint(50, 200),
                source_name=self.name
            ),
            CrowdSignal(
                operator="tre",
                region_name="Västra Götalands län",
                count=random.randint(10, 30),
                source_name=self.name
            )
        ]
        return signals
