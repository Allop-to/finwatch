from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
def list_all(db: Session = Depends(get_db)):
    all_cats = db.query(Category).filter(
        (Category.is_system == True) | (Category.user_id == 1)
    ).order_by(Category.sort_order).all()

    parents = [c for c in all_cats if c.parent_id is None]
    child_map: Dict[int, List[Category]] = {}
    for c in all_cats:
        if c.parent_id:
            child_map.setdefault(c.parent_id, []).append(c)

    result = []
    for p in parents:
        d = CategoryResponse.model_validate(p)
        d.children = [CategoryResponse.model_validate(ch) for ch in child_map.get(p.id, [])]
        result.append(d)
    return result


@router.post("", response_model=CategoryResponse, status_code=201)
def create(data: CategoryCreate, db: Session = Depends(get_db)):
    cat = Category(
        name=data.name, icon=data.icon, parent_id=data.parent_id,
        user_id=1, is_system=False,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.delete("/{cat_id}", status_code=204)
def delete(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(
        Category.id == cat_id, Category.is_system == False
    ).first()
    if not cat:
        raise HTTPException(404, "Category not found or is system category")
    db.delete(cat)
    db.commit()
