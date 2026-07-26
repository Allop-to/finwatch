"""Detection rules CRUD + data management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import csv, io
from datetime import datetime

from app.database import get_db
from app.models.detection_rule import DetectionRule
from app.models.transaction import Transaction
from app.models.detection_result import DetectionResult as DRModel
from app.models.budget import Budget
from app.models.category import Category

router = APIRouter(prefix="/rules", tags=["rules"])


# --- Schemas ---
class RuleCreate(BaseModel):
    name: str
    condition: dict
    is_hard_rule: bool = False
    is_enabled: bool = True


class RuleResponse(BaseModel):
    id: int
    name: str
    condition: dict
    is_hard_rule: bool
    is_enabled: bool

    model_config = {"from_attributes": True}


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    condition: Optional[dict] = None
    is_hard_rule: Optional[bool] = None
    is_enabled: Optional[bool] = None


# --- Detection Rules CRUD ---
@router.get("", response_model=List[RuleResponse])
def list_rules(db: Session = Depends(get_db)):
    return db.query(DetectionRule).filter(DetectionRule.user_id == 1).all()


@router.post("", response_model=RuleResponse, status_code=201)
def create_rule(data: RuleCreate, db: Session = Depends(get_db)):
    rule = DetectionRule(user_id=1, **data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: int, data: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(DetectionRule).filter(
        DetectionRule.id == rule_id, DetectionRule.user_id == 1,
    ).first()
    if not rule:
        raise HTTPException(404, "Rule not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(rule, key, val)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(DetectionRule).filter(
        DetectionRule.id == rule_id, DetectionRule.user_id == 1,
    ).first()
    if not rule:
        raise HTTPException(404, "Rule not found")
    db.delete(rule)
    db.commit()


# --- Seed default rules ---
@router.post("/seed-defaults")
def seed_default_rules(db: Session = Depends(get_db)):
    existing = db.query(DetectionRule).filter(DetectionRule.user_id == 1).count()
    if existing > 0:
        return {"message": "Rules already exist", "count": existing}

    defaults = [
        {
            "name": "单笔大额交易",
            "condition": {"field": "amount", "operator": ">", "value": 10000},
            "is_hard_rule": True,
            "is_enabled": True,
        },
        {
            "name": "深夜消费",
            "condition": {"field": "hour", "operator": "in", "value": [23, 0, 1, 2, 3, 4, 5]},
            "is_hard_rule": False,
            "is_enabled": True,
        },
        {
            "name": "日消费频次异常",
            "condition": {"field": "daily_count", "operator": ">", "value": 20},
            "is_hard_rule": False,
            "is_enabled": False,
        },
    ]
    for d in defaults:
        rule = DetectionRule(user_id=1, **d)
        db.add(rule)
    db.commit()
    return {"message": f"Seeded {len(defaults)} default rules", "count": len(defaults)}


# --- Data Management ---
class DataStats(BaseModel):
    transactions: int
    detections: int
    budgets: int
    categories: int
    db_size_kb: float


@router.get("/data/stats", response_model=DataStats)
def data_stats(db: Session = Depends(get_db)):
    import os
    db_path = "finwatch.db"
    size_kb = round(os.path.getsize(db_path) / 1024, 1) if os.path.exists(db_path) else 0
    return DataStats(
        transactions=db.query(Transaction).filter(Transaction.user_id == 1).count(),
        detections=db.query(DRModel).filter(DRModel.user_id == 1).count(),
        budgets=db.query(Budget).filter(Budget.user_id == 1).count(),
        categories=db.query(Category).filter(Category.user_id == 1).count(),
        db_size_kb=size_kb,
    )


@router.get("/data/export")
def export_csv(db: Session = Depends(get_db)):
    txns = db.query(Transaction).filter(Transaction.user_id == 1).order_by(
        Transaction.transaction_date.desc(),
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "类型", "金额", "分类ID", "商户", "备注", "支付方式", "来源"])
    for t in txns:
        writer.writerow([
            str(t.transaction_date)[:19], t.type, t.amount,
            t.category_id or "", t.merchant or "", t.description or "",
            t.payment_method or "", t.source,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=finwatch_export.csv"},
    )


@router.post("/data/clear-detections")
def clear_detections(db: Session = Depends(get_db)):
    count = db.query(DRModel).filter(DRModel.user_id == 1).delete()
    db.commit()
    return {"message": f"Cleared {count} detection results"}


@router.post("/data/clear-all")
def clear_all(db: Session = Depends(get_db)):
    db.query(DRModel).filter(DRModel.user_id == 1).delete()
    db.query(Transaction).filter(Transaction.user_id == 1).delete()
    db.query(Budget).filter(Budget.user_id == 1).delete()
    db.query(Category).filter(Category.user_id == 1).delete()
    db.commit()
    return {"message": "All user data cleared"}
