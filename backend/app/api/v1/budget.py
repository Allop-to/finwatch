from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.budget import BudgetCreate, BudgetResponse
from app.services import budget_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetResponse, status_code=201)
def create(data: BudgetCreate, db: Session = Depends(get_db)):
    b = budget_service.create_budget(db, data)
    return budget_service.get_budget_with_progress(db, b)


@router.get("", response_model=List[BudgetResponse])
def list_all(db: Session = Depends(get_db)):
    budgets = budget_service.list_budgets(db)
    return [budget_service.get_budget_with_progress(db, b) for b in budgets]


@router.delete("/{budget_id}", status_code=204)
def delete(budget_id: int, db: Session = Depends(get_db)):
    ok = budget_service.delete_budget(db, budget_id)
    if not ok:
        raise HTTPException(404, "Budget not found")
