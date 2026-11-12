"""Loan application model."""

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import LoanStatus

if TYPE_CHECKING:
    from app.models.loan_status_history import LoanStatusHistory
    from app.models.user import User


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    purpose: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus), nullable=False, default=LoanStatus.SUBMITTED, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="loan_applications")
    status_history: Mapped[list["LoanStatusHistory"]] = relationship(
        back_populates="loan_application", cascade="all, delete-orphan"
    )
