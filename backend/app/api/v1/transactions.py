from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionListResponse
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create(data: TransactionCreate, db: Session = Depends(get_db)):
    return transaction_service.create_transaction(db, data)


@router.get("", response_model=TransactionListResponse)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items, total = transaction_service.get_transactions(
        db, page=page, page_size=page_size, category_id=category_id,
        type=type, start_date=start_date, end_date=end_date, search=search,
    )
    return TransactionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{txn_id}", response_model=TransactionResponse)
def get_one(txn_id: int, db: Session = Depends(get_db)):
    txn = transaction_service.get_transaction(db, txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return txn


@router.put("/{txn_id}", response_model=TransactionResponse)
def update(txn_id: int, data: TransactionCreate, db: Session = Depends(get_db)):
    txn = transaction_service.update_transaction(db, txn_id, data)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return txn


@router.delete("/{txn_id}", status_code=204)
def delete(txn_id: int, db: Session = Depends(get_db)):
    ok = transaction_service.delete_transaction(db, txn_id)
    if not ok:
        raise HTTPException(404, "Transaction not found")
