from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.import_record import ImportRecord
from app.schemas.import_ import ImportResultResponse, ImportRecordResponse
from app.services.import_service import process_import

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/upload", response_model=ImportResultResponse)
async def upload(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: Session = Depends(get_db),
):
    if source_type not in ("alipay", "wechat"):
        raise HTTPException(400, f"Unsupported source type: {source_type}")
    content = (await file.read()).decode("utf-8")
    return process_import(db, file.filename, source_type, content)


@router.get("", response_model=List[ImportRecordResponse])
def list_imports(db: Session = Depends(get_db)):
    return db.query(ImportRecord).order_by(ImportRecord.created_at.desc()).limit(20).all()
