"""Loan application service: submit, list/filter, view, and status transitions."""

from typing import Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LoanStatus, UserRole
from app.models.loan_application import LoanApplication
from app.models.loan_status_history import LoanStatusHistory

# Allowed status transitions per AGENTS.md domain rules.
# submitted -> under_review -> {approved, rejected}; both terminal.
_ALLOWED_TRANSITIONS: dict[LoanStatus, Set[LoanStatus]] = {
    LoanStatus.SUBMITTED: {LoanStatus.UNDER_REVIEW},
    LoanStatus.UNDER_REVIEW: {LoanStatus.APPROVED, LoanStatus.REJECTED},
}


async def create_application(
    session: AsyncSession, user_id: int, amount: float, purpose: str
) -> LoanApplication:
    """Create a new loan application in submitted status."""
    application = LoanApplication(
        user_id=user_id, amount=amount, purpose=purpose, status=LoanStatus.SUBMITTED
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def list_applications(
    session: AsyncSession,
    current_user,
    status: Optional[LoanStatus] = None,
) -> list[LoanApplication]:
    """List applications. Officers see all; applicants see only their own."""
    stmt = select(LoanApplication)
    if current_user.role == UserRole.APPLICANT:
        stmt = stmt.where(LoanApplication.user_id == current_user.id)
    if status is not None:
        stmt = stmt.where(LoanApplication.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_application(
    session: AsyncSession, application_id: int, current_user
) -> Optional[LoanApplication]:
    """Get an application by id. Applicants see only their own."""
    result = await session.execute(
        select(LoanApplication).where(LoanApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    if application is None:
        return None
    if (
        current_user.role == UserRole.APPLICANT
        and application.user_id != current_user.id
    ):
        return None
    return application


async def update_application_status(
    session: AsyncSession,
    application_id: int,
    new_status: LoanStatus,
    changed_by_id: int,
    reason: Optional[str] = None,
) -> Optional[LoanApplication]:
    """Transition an application's status; history row written in same transaction.

    Returns None if missing. Raises ValueError on invalid transitions.
    """
    result = await session.execute(
        select(LoanApplication)
        .where(LoanApplication.id == application_id)
        .with_for_update()
    )
    application = result.scalar_one_or_none()
    if application is None:
        return None
    if application.status == new_status:
        raise ValueError(f"Status already {new_status.value}")
    allowed = _ALLOWED_TRANSITIONS.get(application.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition from {application.status.value} to {new_status.value}"
        )
    old_status = application.status
    application.status = new_status
    session.add(
        LoanStatusHistory(
            loan_application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by_id=changed_by_id,
            reason=reason,
        )
    )
    await session.commit()
    await session.refresh(application)
    return application
