"""Loan application routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_session,
    require_applicant,
    require_loan_officer,
)
from app.models.enums import LoanStatus
from app.models.user import User
from app.schemas.loan import (
    LoanApplicationCreate,
    LoanApplicationRead,
    LoanStatusUpdate,
)
from app.services.loan_service import (
    create_application,
    get_application,
    list_applications,
    update_application_status,
)

router = APIRouter(prefix="/applications", tags=["loan_applications"])


@router.post(
    "",
    response_model=LoanApplicationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_applicant)],
)
async def submit_application(
    application_in: LoanApplicationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit a new loan application (applicant only)."""
    application = await create_application(
        session, current_user.id, application_in.amount, application_in.purpose
    )
    return LoanApplicationRead.model_validate(application)


@router.get("", response_model=List[LoanApplicationRead])
async def list_applications_endpoint(
    status: Optional[LoanStatus] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List applications. Officers see all; applicants see only their own."""
    applications = await list_applications(session, current_user, status)
    return [LoanApplicationRead.model_validate(a) for a in applications]


@router.get("/{application_id}", response_model=LoanApplicationRead)
async def get_application_endpoint(
    application_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get an application by id (owner, or any loan officer/admin)."""
    application = await get_application(session, application_id, current_user)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan application not found"
        )
    return LoanApplicationRead.model_validate(application)


@router.patch(
    "/{application_id}/status",
    response_model=LoanApplicationRead,
)
async def update_application_status_endpoint(
    application_id: int,
    status_in: LoanStatusUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_loan_officer),
):
    """Approve or reject an application (loan officer only)."""
    try:
        application = await update_application_status(
            session, application_id, status_in.status, current_user.id, status_in.reason
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan application not found"
        )
    return LoanApplicationRead.model_validate(application)
