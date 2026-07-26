from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, JSON, DateTime, func
from app.models.base import Base


class DetectionResult(Base):
    __tablename__ = "detection_results"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, default=1)
    transaction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    detector_type: Mapped[str] = mapped_column(nullable=False)
    severity: Mapped[str] = mapped_column(nullable=False)  # high / medium / low
    anomaly_score: Mapped[float] = mapped_column(nullable=False)
    reason: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON array
    suggestion: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
