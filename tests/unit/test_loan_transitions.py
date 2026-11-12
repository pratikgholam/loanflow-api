"""Unit tests for loan status transition rules (no DB required)."""

from app.models.enums import LoanStatus
from app.services.loan_service import _ALLOWED_TRANSITIONS


def test_submitted_can_only_go_to_under_review():
    assert _ALLOWED_TRANSITIONS[LoanStatus.SUBMITTED] == {LoanStatus.UNDER_REVIEW}


def test_under_review_can_be_approved_or_rejected():
    assert _ALLOWED_TRANSITIONS[LoanStatus.UNDER_REVIEW] == {
        LoanStatus.APPROVED,
        LoanStatus.REJECTED,
    }


def test_terminal_statuses_have_no_outgoing_transitions():
    assert _ALLOWED_TRANSITIONS.get(LoanStatus.APPROVED, set()) == set()
    assert _ALLOWED_TRANSITIONS.get(LoanStatus.REJECTED, set()) == set()
