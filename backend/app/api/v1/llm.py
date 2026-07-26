"""LLM API endpoints: anomaly explanation + chat + usage stats."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.detection_result import DetectionResult
from app.models.transaction import Transaction
from app.services.llm_service import explainer, chat_manager

router = APIRouter(prefix="/llm", tags=["llm"])


class ExplainRequest(BaseModel):
    detection_id: int


class ExplainResponse(BaseModel):
    detection_id: int
    explanation: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[int] = None


class UsageResponse(BaseModel):
    auto_explain: dict
    chat: dict
    llm_enabled: bool


@router.post("/explain", response_model=ExplainResponse)
async def explain_anomaly(req: ExplainRequest, db: Session = Depends(get_db)):
    """Generate LLM explanation for a detection result."""
    dr = db.query(DetectionResult).filter(DetectionResult.id == req.detection_id).first()
    if not dr:
        raise HTTPException(404, "Detection result not found")

    txn = None
    if dr.transaction_id:
        txn = db.query(Transaction).filter(Transaction.id == dr.transaction_id).first()

    txn_context = {
        "amount": abs(txn.amount) if txn else 0,
        "merchant": txn.merchant if txn else "",
        "description": txn.description if txn else "",
        "transaction_date": str(txn.transaction_date) if txn else "",
        "time_context": _get_time_context(txn) if txn else "",
    }

    explanation = await explainer.explain(
        detection_result={
            "severity": dr.severity,
            "detector_type": dr.detector_type,
            "reason": dr.reason if isinstance(dr.reason, list) else [],
        },
        transaction_context=txn_context,
        statistics={},
    )

    # Save explanation back to DB
    dr.suggestion = explanation
    db.commit()

    return ExplainResponse(detection_id=req.detection_id, explanation=explanation)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Interactive financial analysis chat."""
    # Build data context from recent transactions
    recent_txns = (
        db.query(Transaction)
        .filter(Transaction.user_id == 1)
        .order_by(Transaction.transaction_date.desc())
        .limit(20)
        .all()
    )

    data_context = {
        "transactions": [
            {
                "id": t.id, "amount": abs(t.amount), "type": t.type,
                "merchant": t.merchant, "description": t.description,
                "transaction_date": str(t.transaction_date),
                "category_id": t.category_id,
                "source": t.source,
            }
            for t in recent_txns
        ],
        "statistics": _get_quick_stats(db),
    }

    reply = await chat_manager.chat(
        user_message=req.message,
        conversation_history=[],  # Phase 2: load from llm_conversations table
        data_context=data_context,
    )

    return ChatResponse(reply=reply, conversation_id=req.conversation_id)


@router.get("/usage", response_model=UsageResponse)
def get_usage():
    """Get LLM usage statistics and limits."""
    stats = chat_manager.get_usage_stats()
    return UsageResponse(**stats)


def _get_time_context(txn) -> str:
    """Get human-readable time context for a transaction."""
    if not txn or not txn.transaction_date:
        return ""
    hour = txn.transaction_date.hour
    if hour >= 23 or hour < 5:
        return "深夜"
    elif hour < 8:
        return "清晨"
    elif hour < 12:
        return "上午"
    elif hour < 14:
        return "中午"
    elif hour < 18:
        return "下午"
    return "晚上"


def _get_quick_stats(db: Session) -> dict:
    """Get quick statistics for chat context."""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    month_ago = datetime.now() - timedelta(days=30)
    total = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == 1,
            Transaction.type == "expense",
            Transaction.transaction_date >= month_ago,
        )
        .scalar()
    ) or 0
    count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == 1,
            Transaction.transaction_date >= month_ago,
        )
        .scalar()
    ) or 0

    return {
        "total_expense": round(float(total), 2),
        "transaction_count": count,
        "period": "近30天",
    }
