from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str]
    parent_id: Optional[int]
    is_system: bool
    sort_order: int
    children: List["CategoryResponse"] = []

    model_config = {"from_attributes": True}
