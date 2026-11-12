"""Domain enums."""

from enum import Enum


class UserRole(str, Enum):
    APPLICANT = "applicant"
    LOAN_OFFICER = "loan_officer"
    ADMIN = "admin"


class LoanStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
