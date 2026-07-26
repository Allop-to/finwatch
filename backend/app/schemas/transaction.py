from typing import Optional, List, Dict, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    amount: float
    type: str = Field(default="expense", pattern="^(income|expense|transfer)$")
    category_id: Optional[int] = None
    transaction_date: datetime
    description: Optional[str] = None
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    source: str = Field(default="manual", pattern="^(manual|import)$")
    tags: Optional[dict] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    type: str
    category_id: Optional[int]
    transaction_date: datetime
    description: Optional[str]
    merchant: Optional[str]
    payment_method: Optional[str]
    source: str
    import_id: Optional[int]
    tags: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
