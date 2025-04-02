"""
Data models for the Quantum CLI SDK.
"""

from typing import Dict, Optional

# Define the result structure here
class SimulationResult:
    """Data class to hold simulation results consistently across backends."""
    def __init__(self, counts: dict, platform: str, shots: int, metadata: Optional[Dict] = None):
        self.counts = counts
        self.platform = platform
        self.shots = shots
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        """Convert the result object to a dictionary for serialization."""
        return {
            "platform": self.platform,
            "shots": self.shots,
            "counts": self.counts, # This might hold counts or probabilities
            "metadata": self.metadata
        }

# Could add other shared models here later, e.g., ValidationResult, SecurityScanResult 