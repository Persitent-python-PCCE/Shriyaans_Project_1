from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from werkzeug.security import (
    generate_password_hash,
)

from app import app
import controllers.api_controller as api_controller


@pytest.fixture
def app_client():
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )

    with app.test_client() as client:
        yield client


def fake_user(
    uid=1,
    role="EMPLOYEE",
    active=True,
    email=None,
    name=None,
):
    return SimpleNamespace(
        id=uid,
        name=name or f"User {uid}",
        email=email or f"user{uid}@example.com",
        password_hash=generate_password_hash(
            "Password@123"
        ),
        is_active=active,
        role=SimpleNamespace(
            name=role
        ),
        created_at=datetime.utcnow(),
    )


def fake_ticket(
    tid=1,
    creator=1,
    status="OPEN",
    escalated=False,
):
    return SimpleNamespace(
        id=tid,
        title="Test ticket",
        description="Test description",
        category_id=1,
        category=SimpleNamespace(
            name="Hardware"
        ),
        created_by=creator,
        creator=SimpleNamespace(
            name="Employee"
        ),
        priority="HIGH",
        severity="MAJOR",
        status=status,
        due_date=None,
        resolved_at=None,
        closed_at=None,
        is_escalated=escalated,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        attachments=[],
        assignments=[],
        feedback=None,
    )


def login_session(
    client,
    user_id=1,
    role="EMPLOYEE",
):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Test"
        sess["user_email"] = "test@example.com"
        sess["role"] = role


def test_unauthenticated_ticket_access_rejected(
    app_client
):
    response = app_client.get(
        "/api/tickets"
    )

    assert response.status_code == 401
    assert (
        response.get_json()["error"]
        == "Authentication required."
    )


def test_employee_login_success_json(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="EMPLOYEE"
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/employee/login",
        json={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 200
    assert (
        response.get_json()["user"]["role"]
        == "EMPLOYEE"
    )

    with app_client.session_transaction() as sess:
        assert sess["user_id"] == user.id
        assert sess["role"] == "EMPLOYEE"


def test_agent_login_success_form_data(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="AGENT"
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/agent/login",
        data={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 200
    assert (
        response.get_json()["user"]["role"]
        == "AGENT"
    )


def test_admin_login_success(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="ADMIN"
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/admin/login",
        json={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 200


def test_generic_login_success(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="AGENT"
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/login",
        json={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 200


def test_login_wrong_password_rejected(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="EMPLOYEE"
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/employee/login",
        json={
            "email": user.email,
            "password": "Wrong@123",
        },
    )

    assert response.status_code == 401


def test_login_unknown_email_rejected(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: None,
    )

    response = app_client.post(
        "/api/employee/login",
        json={
            "email": "missing@example.com",
            "password": "Password@123",
        },
    )

    assert response.status_code == 401


def test_login_inactive_user_rejected(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="EMPLOYEE",
        active=False,
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/employee/login",
        json={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 403


def test_login_wrong_role_rejected(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="AGENT"
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/employee/login",
        json={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 403


def test_login_missing_email_rejected(
    app_client
):
    response = app_client.post(
        "/api/login",
        json={
            "password": "Password@123"
        },
    )

    assert response.status_code == 400


def test_login_missing_password_rejected(
    app_client
):
    response = app_client.post(
        "/api/login",
        json={
            "email": "user@example.com"
        },
    )

    assert response.status_code == 400


def test_login_user_without_role_rejected(
    app_client,
    monkeypatch,
):
    user = fake_user(
        role="EMPLOYEE"
    )

    user.role = None

    monkeypatch.setattr(
        api_controller.user_service,
        "get_user_by_email",
        lambda email: user,
    )

    response = app_client.post(
        "/api/login",
        json={
            "email": user.email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 403


def test_employee_register_success(
    app_client,
    monkeypatch,
):
    created = fake_user(
        role="EMPLOYEE",
        email="new@example.com",
    )

    captured = {}

    def create_user(data):
        captured.update(data)
        return created

    monkeypatch.setattr(
        api_controller.user_service,
        "create_user",
        create_user,
    )

    response = app_client.post(
        "/api/employee/register",
        json={
            "name": "New Employee",
            "email": "new@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 201
    assert (
        captured["role_name"]
        == "EMPLOYEE"
    )


def test_employee_register_validation_error(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.user_service,
        "create_user",
        Mock(
            side_effect=ValueError(
                "Email already registered."
            )
        ),
    )

    response = app_client.post(
        "/api/employee/register",
        json={
            "name": "New Employee",
            "email": "existing@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 400


def test_agent_register_requires_admin(
    app_client
):
    response = app_client.post(
        "/api/agent/register",
        json={
            "name": "Agent",
            "email": "agent@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 403


def test_agent_register_success_for_admin(
    app_client,
    monkeypatch,
):
    created = fake_user(
        role="AGENT",
        email="agent@example.com",
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "create_user",
        lambda data: created,
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    response = app_client.post(
        "/api/agent/register",
        json={
            "name": "Agent",
            "email": "agent@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 201


def test_admin_register_rejects_existing_admin(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.user_service,
        "get_all_users",
        lambda: [
            fake_user(
                role="ADMIN"
            )
        ],
    )

    response = app_client.post(
        "/api/admin/register",
        json={
            "name": "Second Admin",
            "email": "admin2@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 403


def test_admin_register_first_admin(
    app_client,
    monkeypatch,
):
    created = fake_user(
        role="ADMIN",
        email="firstadmin@example.com",
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "get_all_users",
        lambda: [],
    )

    monkeypatch.setattr(
        api_controller.user_service,
        "create_user",
        lambda data: created,
    )

    response = app_client.post(
        "/api/admin/register",
        json={
            "name": "First Admin",
            "email": "firstadmin@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 201


def test_generic_register_defaults_to_employee(
    app_client,
    monkeypatch,
):
    created = fake_user(
        role="EMPLOYEE",
        email="generic@example.com",
    )

    captured = {}

    def create_user(data):
        captured.update(data)
        return created

    monkeypatch.setattr(
        api_controller.user_service,
        "create_user",
        create_user,
    )

    response = app_client.post(
        "/api/register",
        json={
            "name": "Generic",
            "email": "generic@example.com",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
    )

    assert response.status_code == 201
    assert (
        captured["role_name"]
        == "EMPLOYEE"
    )


def test_create_ticket_success(
    app_client,
    monkeypatch,
):
    t = fake_ticket()

    monkeypatch.setattr(
        api_controller.ticket_service,
        "create_ticket",
        lambda **kwargs: t,
    )

    login_session(
        app_client,
        role="EMPLOYEE",
    )

    response = app_client.post(
        "/api/tickets",
        json={
            "title": "Laptop issue",
            "description": "Laptop does not boot",
            "category_id": 1,
            "priority": "HIGH",
            "severity": "MAJOR",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["id"] == 1


def test_create_ticket_requires_category(
    app_client
):
    login_session(
        app_client,
        role="EMPLOYEE",
    )

    response = app_client.post(
        "/api/tickets",
        json={
            "title": "x",
            "description": "y",
        },
    )

    assert response.status_code == 400


def test_create_ticket_permission_denied(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "create_ticket",
        Mock(
            side_effect=PermissionError(
                "Only employees can create tickets."
            )
        ),
    )

    login_session(
        app_client,
        role="AGENT",
    )

    response = app_client.post(
        "/api/tickets",
        json={
            "title": "x",
            "description": "y",
            "category_id": 1,
        },
    )

    assert response.status_code == 403


def test_get_tickets_with_filters(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "search_tickets",
        lambda **kwargs: [],
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets"
        "?title=laptop"
        "&status=open"
        "&priority=high"
        "&category_id=1"
    )

    assert response.status_code == 200
    assert (
        response.get_json()["count"]
        == 0
    )


def test_get_ticket_success(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        lambda user_id, ticket_id: fake_ticket(),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/1"
    )

    assert response.status_code == 200
    assert (
        response.get_json()["id"]
        == 1
    )


def test_get_ticket_forbidden(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        Mock(
            side_effect=PermissionError(
                "Not allowed"
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/99"
    )

    assert response.status_code == 403


def test_get_ticket_not_found(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        Mock(
            side_effect=ValueError(
                "Ticket not found."
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/999"
    )

    assert response.status_code == 404


def test_status_update_success(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "update_status",
        lambda **kwargs: fake_ticket(
            status="IN_PROGRESS"
        ),
    )

    login_session(
        app_client,
        role="AGENT",
    )

    response = app_client.patch(
        "/api/tickets/1/status",
        json={
            "status": "IN_PROGRESS"
        },
    )

    assert response.status_code == 200
    assert (
        response.get_json()["status"]
        == "IN_PROGRESS"
    )


def test_status_update_invalid_transition(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "update_status",
        Mock(
            side_effect=ValueError(
                "Invalid status transition"
            )
        ),
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    response = app_client.patch(
        "/api/tickets/1/status",
        json={
            "status": "CLOSED"
        },
    )

    assert response.status_code == 400


def test_employee_cannot_change_status(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "update_status",
        Mock(
            side_effect=PermissionError(
                "Employees cannot change ticket status."
            )
        ),
    )

    login_session(
        app_client,
        role="EMPLOYEE",
    )

    response = app_client.patch(
        "/api/tickets/1/status",
        json={
            "status": "IN_PROGRESS"
        },
    )

    assert response.status_code == 403


def test_escalate_success(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "escalate_ticket",
        lambda **kwargs: fake_ticket(
            escalated=True
        ),
    )

    login_session(
        app_client,
        role="AGENT",
    )

    response = app_client.post(
        "/api/tickets/1/escalate",
        json={
            "reason": "Urgent"
        },
    )

    assert response.status_code == 200
    assert (
        response.get_json()["is_escalated"]
        is True
    )


def test_escalate_employee_forbidden(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "escalate_ticket",
        Mock(
            side_effect=PermissionError(
                "Only assigned agents and administrators can escalate tickets."
            )
        ),
    )

    login_session(
        app_client,
        role="EMPLOYEE",
    )

    response = app_client.post(
        "/api/tickets/1/escalate",
        json={
            "reason": "Urgent"
        },
    )

    assert response.status_code == 403


def test_escalate_closed_ticket_rejected(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "escalate_ticket",
        Mock(
            side_effect=ValueError(
                "Closed tickets cannot be escalated."
            )
        ),
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    response = app_client.post(
        "/api/tickets/1/escalate",
        json={
            "reason": "Urgent"
        },
    )

    assert response.status_code == 400


def test_comments_get_and_post(
    app_client,
    monkeypatch,
):
    comment = SimpleNamespace(
        id=1,
        user_id=1,
        user=SimpleNamespace(
            name="Employee"
        ),
        comment="Hello",
        created_at=datetime.utcnow(),
        ticket_id=1,
    )

    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        lambda user_id, ticket_id: fake_ticket(),
    )

    monkeypatch.setattr(
        api_controller.comment_service,
        "get_comments",
        lambda user_id, ticket_id: [
            comment
        ],
    )

    monkeypatch.setattr(
        api_controller.comment_service,
        "add_comment",
        lambda **kwargs: comment,
    )

    login_session(
        app_client
    )

    get_response = app_client.get(
        "/api/tickets/1/comments"
    )

    post_response = app_client.post(
        "/api/tickets/1/comments",
        json={
            "comment": "Hello"
        },
    )

    assert get_response.status_code == 200
    assert post_response.status_code == 201


def test_comments_permission_denied(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        lambda user_id, ticket_id: fake_ticket(),
    )

    monkeypatch.setattr(
        api_controller.comment_service,
        "add_comment",
        Mock(
            side_effect=PermissionError(
                "Not allowed"
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.post(
        "/api/tickets/1/comments",
        json={
            "comment": "Hello"
        },
    )

    assert response.status_code == 403


def test_comment_validation_error(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        lambda user_id, ticket_id: fake_ticket(),
    )

    monkeypatch.setattr(
        api_controller.comment_service,
        "add_comment",
        Mock(
            side_effect=ValueError(
                "Comment cannot be empty."
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.post(
        "/api/tickets/1/comments",
        json={
            "comment": ""
        },
    )

    assert response.status_code == 400


def test_history_success(
    app_client,
    monkeypatch,
):
    entry = SimpleNamespace(
        id=1,
        action="STATUS_CHANGED",
        old_value="OPEN",
        new_value="ASSIGNED",
        description="Changed",
        user_id=1,
        user=SimpleNamespace(
            name="Admin"
        ),
        created_at=datetime.utcnow(),
    )

    monkeypatch.setattr(
        api_controller.history_service,
        "get_ticket_history",
        lambda user_id, ticket_id: [
            entry
        ],
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/1/history"
    )

    assert response.status_code == 200

    assert (
        response.get_json()["history"][0]["action"]
        == "STATUS_CHANGED"
    )


def test_history_forbidden(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.history_service,
        "get_ticket_history",
        Mock(
            side_effect=PermissionError(
                "Not allowed"
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/1/history"
    )

    assert response.status_code == 403


def test_feedback_get_and_post(
    app_client,
    monkeypatch,
):
    feedback = SimpleNamespace(
        id=1,
        ticket_id=1,
        user_id=1,
        rating=5,
        comment="Great",
        created_at=datetime.utcnow(),
    )

    monkeypatch.setattr(
        api_controller.feedback_service,
        "get_feedback",
        lambda user_id, ticket_id: feedback,
    )

    monkeypatch.setattr(
        api_controller.feedback_service,
        "submit_feedback",
        lambda **kwargs: feedback,
    )

    login_session(
        app_client,
        role="EMPLOYEE",
    )

    get_response = app_client.get(
        "/api/tickets/1/feedback"
    )

    post_response = app_client.post(
        "/api/tickets/1/feedback",
        json={
            "rating": 5,
            "comment": "Great",
        },
    )

    assert get_response.status_code == 200
    assert post_response.status_code == 201


def test_feedback_invalid_rating(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.feedback_service,
        "submit_feedback",
        Mock(
            side_effect=ValueError(
                "Rating must be between 1 and 5."
            )
        ),
    )

    login_session(
        app_client,
        role="EMPLOYEE",
    )

    response = app_client.post(
        "/api/tickets/1/feedback",
        json={
            "rating": 6,
            "comment": "Bad",
        },
    )

    assert response.status_code == 400


def test_feedback_permission_error(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.feedback_service,
        "get_feedback",
        Mock(
            side_effect=PermissionError(
                "Not allowed"
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/1/feedback"
    )

    assert response.status_code == 403


def test_categories_success(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.category_service,
        "get_all_categories",
        lambda user_id: [
            SimpleNamespace(
                id=1,
                name="Hardware",
            )
        ],
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/categories"
    )

    assert response.status_code == 200
    assert (
        response.get_json()["categories"][0]["name"]
        == "Hardware"
    )


def test_categories_permission_error(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.category_service,
        "get_all_categories",
        Mock(
            side_effect=PermissionError(
                "Not allowed"
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/categories"
    )

    assert response.status_code == 403


def test_sla_requires_admin(
    app_client
):
    login_session(
        app_client,
        role="EMPLOYEE",
    )

    response = app_client.get(
        "/api/sla-rules"
    )

    assert response.status_code == 403


def test_sla_admin_get_post(
    app_client,
    monkeypatch,
):
    rule = SimpleNamespace(
        id=1,
        priority="HIGH",
        response_time_minutes=240,
        resolution_time_minutes=1440,
        created_at=datetime.utcnow(),
    )

    monkeypatch.setattr(
        api_controller.sla_service,
        "ensure_default_rules",
        lambda: [rule],
    )

    monkeypatch.setattr(
        api_controller.sla_service,
        "get_all_rules",
        lambda admin_id: [rule],
    )

    monkeypatch.setattr(
        api_controller.sla_service,
        "create_rule",
        lambda **kwargs: rule,
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    get_response = app_client.get(
        "/api/sla-rules"
    )

    post_response = app_client.post(
        "/api/sla-rules",
        json={
            "priority": "HIGH",
            "response_time_minutes": 240,
            "resolution_time_minutes": 1440,
        },
    )

    assert get_response.status_code == 200
    assert post_response.status_code == 201


def test_sla_invalid_values(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.sla_service,
        "create_rule",
        Mock(
            side_effect=ValueError(
                "SLA times must be greater than zero."
            )
        ),
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    response = app_client.post(
        "/api/sla-rules",
        json={
            "priority": "HIGH",
            "response_time_minutes": 0,
            "resolution_time_minutes": 100,
        },
    )

    assert response.status_code == 400


def test_sla_patch_put_delete(
    app_client,
    monkeypatch,
):
    rule = SimpleNamespace(
        id=1,
        priority="HIGH",
        response_time_minutes=120,
        resolution_time_minutes=600,
    )

    monkeypatch.setattr(
        api_controller.sla_service,
        "update_rule",
        lambda **kwargs: rule,
    )

    monkeypatch.setattr(
        api_controller.sla_service,
        "delete_rule",
        lambda admin_id, rule_id: True,
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    patch_response = app_client.patch(
        "/api/sla-rules/1",
        json={
            "response_time_minutes": 120,
            "resolution_time_minutes": 600,
        },
    )

    put_response = app_client.put(
        "/api/sla-rules/1",
        json={
            "response_time_minutes": 120,
            "resolution_time_minutes": 600,
        },
    )

    delete_response = app_client.delete(
        "/api/sla-rules/1"
    )

    assert patch_response.status_code == 200
    assert put_response.status_code == 200
    assert delete_response.status_code == 200


def test_sla_management_forbidden_for_agent(
    app_client
):
    login_session(
        app_client,
        role="AGENT",
    )

    response = app_client.post(
        "/api/sla-rules",
        json={
            "priority": "HIGH",
            "response_time_minutes": 60,
            "resolution_time_minutes": 120,
        },
    )

    assert response.status_code == 403


def test_status_server_error_maps_to_500(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "update_status",
        Mock(
            side_effect=RuntimeError(
                "unexpected"
            )
        ),
    )

    login_session(
        app_client,
        role="ADMIN",
    )

    response = app_client.patch(
        "/api/tickets/1/status",
        json={
            "status": "IN_PROGRESS"
        },
    )

    assert response.status_code == 500


def test_ticket_get_server_error_maps_to_500(
    app_client,
    monkeypatch,
):
    monkeypatch.setattr(
        api_controller.ticket_service,
        "get_ticket_by_id",
        Mock(
            side_effect=RuntimeError(
                "unexpected"
            )
        ),
    )

    login_session(
        app_client
    )

    response = app_client.get(
        "/api/tickets/1"
    )

    assert response.status_code == 500