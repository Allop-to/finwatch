from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate


def create_budget(db: Session, data: BudgetCreate, user_id: int = 1) -> Budget:
    b = Budget(user_id=user_id, **data.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def list_budgets(db: Session, user_id: int = 1) -> List[Budget]:
    return db.query(Budget).filter(Budget.user_id == user_id).all()


def get_budget_with_progress(db: Session, budget: Budget) -> dict:
    q = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == budget.user_id,
        Transaction.type == "expense",
        Transaction.transaction_date >= budget.start_date,
        Transaction.transaction_date <= budget.end_date,
    )
    if budget.category_id:
        q = q.filter(Transaction.category_id == budget.category_id)
    spent = q.scalar() or 0.0
    pct = round(spent / budget.amount_limit * 100, 1) if budget.amount_limit > 0 else 0
    return {**budget.__dict__, "spent_amount": spent, "progress_pct": pct}


def delete_budget(db: Session, budget_id: int, user_id: int = 1) -> bool:
    b = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not b:
        return False
    db.delete(b)
    db.commit()
    return True
