from typing import Optional, List, Dict, Tuple
from datetime import datetime
from pydantic import BaseModel


class DetectionResponse(BaseModel):
    id: int
    user_id: int
    transaction_id: Optional[int]
    detector_type: str
    severity: str
    anomaly_score: float
    reason: List[dict]
    suggestion: Optional[str]
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DetectionTriggerResponse(BaseModel):
    message: str
    results_count: int
