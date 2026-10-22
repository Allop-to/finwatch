from typing import Optional, List, Dict, Tuple
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate


def _compute_hash(user_id: int, amount: float, txn_date: datetime,
                  merchant: Optional[str], description: Optional[str]) -> str:
    # Normalize before hashing so re-imports that differ only in whitespace,
    # case or amount formatting still dedupe.
    merchant_norm = (merchant or "").strip().casefold()
    description_norm = (description or "").strip().casefold()
    amount_norm = "{:.2f}".format(float(amount))
    raw = f"{user_id}|{amount_norm}|{txn_date.isoformat()}|{merchant_norm}|{description_norm}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_transaction(db: Session, data: TransactionCreate, user_id: int = 1,
                       import_id: Optional[int] = None) -> Transaction:
    txn_hash = _compute_hash(user_id, data.amount, data.transaction_date,
                             data.merchant, data.description)
    existing = db.query(Transaction).filter(
        Transaction.idempotency_hash == txn_hash
    ).first()
    if existing:
        return existing

    txn = Transaction(
        user_id=user_id,
        amount=data.amount,
        type=data.type,
        category_id=data.category_id,
        transaction_date=data.transaction_date,
        description=data.description,
        merchant=data.merchant,
        payment_method=data.payment_method,
        source=data.source,
        import_id=import_id,
        idempotency_hash=txn_hash,
        tags=data.tags,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_transactions(
    db: Session, user_id: int = 1, page: int = 1, page_size: int = 20,
    category_id: Optional[int] = None, type: Optional[str] = None,
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> Tuple[List[Transaction], int]:
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if type:
        query = query.filter(Transaction.type == type)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if search:
        query = query.filter(
            Transaction.description.contains(search) |
            Transaction.merchant.contains(search)
        )
    total = query.count()
    items = query.order_by(desc(Transaction.transaction_date)) \
        .offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_transaction(db: Session, txn_id: int, user_id: int = 1) -> Optional[Transaction]:
    return db.query(Transaction).filter(
        Transaction.id == txn_id, Transaction.user_id == user_id
    ).first()


def update_transaction(db: Session, txn_id: int, data: TransactionCreate,
                       user_id: int = 1) -> Optional[Transaction]:
    txn = get_transaction(db, txn_id, user_id)
    if not txn:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(txn, key, val)
    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, txn_id: int, user_id: int = 1) -> bool:
    txn = get_transaction(db, txn_id, user_id)
    if not txn:
        return False
    db.delete(txn)
    db.commit()
    return True
