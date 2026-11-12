"""Loan status history model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import LoanStatus

if TYPE_CHECKING:
    from app.models.loan_application import LoanApplication
    from app.models.user import User


class LoanStatusHistory(Base):
    __tablename__ = "loan_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    loan_application_id: Mapped[int] = mapped_column(
        ForeignKey("loan_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status: Mapped[Optional[LoanStatus]] = mapped_column(
        Enum(LoanStatus), nullable=True
    )
    new_status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), nullable=False)
    changed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    loan_application: Mapped["LoanApplication"] = relationship(
        back_populates="status_history"
    )
    changed_by: Mapped[Optional["User"]] = relationship(foreign_keys=[changed_by_id])
