from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, JSON, DateTime, func
from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, default=1)
    amount: Mapped[float] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)  # income / expense / transfer
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    merchant: Mapped[Optional[str]] = mapped_column(nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(nullable=False, default="manual")  # manual / import
    import_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_records.id"), nullable=True)
    idempotency_hash: Mapped[str] = mapped_column(unique=True, nullable=False)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    category = relationship("Category")
