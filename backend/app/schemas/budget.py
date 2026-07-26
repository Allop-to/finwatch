from typing import Optional
from datetime import date
from pydantic import BaseModel


class BudgetCreate(BaseModel):
    category_id: Optional[int] = None
    amount_limit: float
    period: str = "monthly"
    start_date: date
    end_date: date
    alert_threshold: float = 0.80


class BudgetResponse(BaseModel):
    id: int
    category_id: Optional[int]
    amount_limit: float
    period: str
    start_date: date
    end_date: date
    alert_threshold: float
    spent_amount: float = 0.0
    progress_pct: float = 0.0

    model_config = {"from_attributes": True}
