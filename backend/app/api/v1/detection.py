from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.detection_result import DetectionResult
from app.schemas.detection import DetectionResponse, DetectionTriggerResponse
from app.services.detection_service import run_detection

router = APIRouter(prefix="/detection", tags=["detection"])


@router.get("", response_model=List[DetectionResponse])
def list_results(
    severity: Optional[str] = None,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(DetectionResult).filter(DetectionResult.user_id == 1)
    if severity:
        q = q.filter(DetectionResult.severity == severity)
    if is_read is not None:
        q = q.filter(DetectionResult.is_read == is_read)
    return q.order_by(DetectionResult.created_at.desc()).limit(50).all()


@router.get("/{result_id}", response_model=DetectionResponse)
def get_one(result_id: int, db: Session = Depends(get_db)):
    r = db.query(DetectionResult).filter(DetectionResult.id == result_id).first()
    if not r:
        raise HTTPException(404, "Detection result not found")
    return r


@router.patch("/{result_id}/read")
def mark_read(result_id: int, db: Session = Depends(get_db)):
    r = db.query(DetectionResult).filter(DetectionResult.id == result_id).first()
    if not r:
        raise HTTPException(404, "Not found")
    r.is_read = True
    db.commit()
    return {"ok": True}


@router.post("/run", response_model=DetectionTriggerResponse)
async def trigger_detection(db: Session = Depends(get_db)):
    results = await run_detection(db)
    return DetectionTriggerResponse(
        message="Detection complete", results_count=len(results),
    )
