from datetime import datetime
from pydantic import BaseModel


class ImportResultResponse(BaseModel):
    import_id: int
    status: str
    row_count: int
    new_count: int
    skipped_count: int


class ImportRecordResponse(BaseModel):
    id: int
    filename: str
    source_type: str
    status: str
    row_count: int
    new_count: int
    skipped_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
