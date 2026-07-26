from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, JSON, Boolean
from app.models.base import Base


class DetectionRule(Base):
    __tablename__ = "detection_rules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, default=1)
    name: Mapped[str] = mapped_column(nullable=False)
    condition: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_hard_rule: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
