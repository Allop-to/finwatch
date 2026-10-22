from sqlalchemy.orm import Session
from app.models.import_record import ImportRecord
from app.models.transaction import Transaction
from app.engine.parsers import get_parser
from app.services.transaction_service import create_transaction
from app.schemas.transaction import TransactionCreate


def process_import(db: Session, filename: str, source_type: str, content: str, user_id: int = 1) -> dict:
    imp = ImportRecord(
        user_id=user_id, filename=filename, source_type=source_type, status="processing",
    )
    db.add(imp)
    db.commit()
    db.refresh(imp)

    try:
        parser = get_parser(source_type)
        parsed = parser.parse(content)
        count_before = db.query(Transaction).filter(Transaction.user_id == user_id).count()

        for pt in parsed:
            txn_data = TransactionCreate(
                amount=pt.amount, type=pt.type, transaction_date=pt.transaction_date,
                merchant=pt.merchant, description=pt.description,
                payment_method=pt.payment_method, source="import",
            )
            create_transaction(db, txn_data, user_id, import_id=imp.id)

        count_after = db.query(Transaction).filter(Transaction.user_id == user_id).count()
        new_count = count_after - count_before
        skipped_count = len(parsed) - new_count

        imp.status = "done"
        imp.row_count = len(parsed)
        imp.new_count = new_count
        imp.skipped_count = skipped_count
        db.commit()

        return {
            "import_id": imp.id, "status": "done", "row_count": len(parsed),
            "new_count": new_count, "skipped_count": skipped_count,
        }
    except Exception as e:
        imp.status = "failed"
        db.commit()
        raise e
