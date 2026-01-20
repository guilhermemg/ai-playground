from pydantic import BaseModel
from typing import List, Literal

class Risk(BaseModel):
    description: str
    severity: Literal["low", "medium", "high"]

class RiskExtractionOutput(BaseModel):
    risks: List[Risk]
