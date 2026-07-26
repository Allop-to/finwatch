import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Category

SEEDS_DIR = Path(__file__).parent


def seed_categories(db: Session) -> None:
    existing = db.query(Category).filter(Category.is_system == True).count()
    if existing > 0:
        return

    data = json.loads((SEEDS_DIR / "categories.json").read_text(encoding="utf-8"))
    sort_order = 0

    def create_cat(name, icon, parent_id=None):
        nonlocal sort_order
        cat = Category(
            name=name, icon=icon, parent_id=parent_id,
            user_id=None, is_system=True, sort_order=sort_order,
        )
        sort_order += 1
        db.add(cat)
        db.flush()
        return cat

    for item in data:
        parent = create_cat(item["name"], item.get("icon"))
        for child in item.get("children", []):
            create_cat(child["name"], child.get("icon"), parent_id=parent.id)

    db.commit()
