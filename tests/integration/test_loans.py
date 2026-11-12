"""Integration tests for loan application endpoints against the test DB."""

from app.models.enums import LoanStatus


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_applicant_submits_and_sees_only_own(client, users, tokens):
    """Applicant submits (201) and can view only their own application."""
    resp = await client.post(
        "/applications",
        json={"amount": 1000.0, "purpose": "car"},
        headers=auth_headers(tokens["applicant"]),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == LoanStatus.SUBMITTED
    app_id = data["id"]

    # applicant sees their own
    resp = await client.get(
        f"/applications/{app_id}", headers=auth_headers(tokens["applicant"])
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == app_id


async def test_applicant_cannot_view_another_application(client, users, tokens):
    """Applicant viewing someone else's loan gets 404 (not visible)."""
    resp = await client.post(
        "/applications",
        json={"amount": 500.0, "purpose": "bike"},
        headers=auth_headers(tokens["applicant"]),
    )
    other_id = resp.json()["id"]

    resp = await client.get(
        f"/applications/{other_id}", headers=auth_headers(tokens["applicant2"])
    )
    assert resp.status_code == 404


async def test_loan_officer_lists_all_and_filters(client, users, tokens):
    """Loan officer lists all applications and can filter by status."""
    for _ in range(2):
        await client.post(
            "/applications",
            json={"amount": 100.0, "purpose": "x"},
            headers=auth_headers(tokens["applicant"]),
        )

    resp = await client.get(
        "/applications", headers=auth_headers(tokens["loan_officer"])
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get(
        "/applications?status=submitted", headers=auth_headers(tokens["loan_officer"])
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get(
        "/applications?status=approved", headers=auth_headers(tokens["loan_officer"])
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_loan_officer_approves_and_rejects(client, users, tokens):
    """Officer moves submitted -> under_review -> approved; approved is terminal."""
    resp = await client.post(
        "/applications",
        json={"amount": 2000.0, "purpose": "home"},
        headers=auth_headers(tokens["applicant"]),
    )
    app_id = resp.json()["id"]

    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.UNDER_REVIEW},
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 200, resp.text

    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.APPROVED, "reason": "looks good"},
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == LoanStatus.APPROVED

    # approved is terminal: further transition is invalid (422)
    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.REJECTED},
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 422


async def test_applicant_cannot_approve(client, users, tokens):
    """Applicant on approve/reject endpoint gets 403."""
    resp = await client.post(
        "/applications",
        json={"amount": 100.0, "purpose": "x"},
        headers=auth_headers(tokens["applicant"]),
    )
    app_id = resp.json()["id"]

    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.APPROVED},
        headers=auth_headers(tokens["applicant"]),
    )
    assert resp.status_code == 403


async def test_unauthenticated_is_401(client):
    """Requests without a bearer token get 401."""
    resp = await client.post("/applications", json={"amount": 100.0, "purpose": "x"})
    assert resp.status_code == 401

    resp = await client.get("/applications")
    assert resp.status_code == 401


async def test_history_row_written_in_same_transaction(client, session, users, tokens):
    """Approving writes history rows in the same transaction as each status change."""
    resp = await client.post(
        "/applications",
        json={"amount": 3000.0, "purpose": "boat"},
        headers=auth_headers(tokens["applicant"]),
    )
    assert resp.status_code == 201
    app_id = resp.json()["id"]

    # submitted -> under_review (row 1)
    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.UNDER_REVIEW, "reason": "reviewing"},
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 200, resp.text

    # under_review -> approved (row 2); approved is terminal
    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.APPROVED, "reason": "final"},
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 200, resp.text

    # further transition on a terminal status is rejected (422)
    resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": LoanStatus.REJECTED},
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 422

    # exactly two history rows were written (one per transition).
    from sqlalchemy import select

    from app.models.loan_status_history import LoanStatusHistory

    rows = await session.execute(
        select(LoanStatusHistory).where(LoanStatusHistory.loan_application_id == app_id)
    )
    history = rows.scalars().all()
    assert len(history) == 2
    assert history[0].old_status == LoanStatus.SUBMITTED
    assert history[0].new_status == LoanStatus.UNDER_REVIEW
    assert history[1].old_status == LoanStatus.UNDER_REVIEW
    assert history[1].new_status == LoanStatus.APPROVED


async def test_invalid_status_query_is_422(client, users, tokens):
    """Bad ?status= filter value returns 422."""
    resp = await client.get(
        "/applications?status=not_a_status",
        headers=auth_headers(tokens["loan_officer"]),
    )
    assert resp.status_code == 422
