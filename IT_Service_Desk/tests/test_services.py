from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest

from werkzeug.datastructures import FileStorage

from services.ticket_service import TicketService
from services.ticket_assignment_service import (
    TicketAssignmentService,
)
from services.ticket_comment_service import (
    TicketCommentService,
)
from services.feedback_service import FeedbackService
from services.sla_rule_service import SLARuleService
from services.ticket_attachment_service import (
    TicketAttachmentService,
)


def user(
    uid=1,
    role="EMPLOYEE",
    active=True,
    name=None,
):
    return SimpleNamespace(
        id=uid,
        name=name or f"User {uid}",
        email=f"user{uid}@test.com",
        is_active=active,
        role=SimpleNamespace(
            name=role
        ),
    )


def ticket(
    tid=1,
    creator=1,
    status="OPEN",
    priority="HIGH",
):
    return SimpleNamespace(
        id=tid,
        created_by=creator,
        status=status,
        priority=priority,
        severity="MAJOR",
        is_escalated=False,
        due_date=None,
        created_at=datetime.utcnow(),
        resolved_at=None,
        closed_at=None,
    )


def no_history(monkeypatch):
    monkeypatch.setattr(
        "services.ticket_history_service."
        "TicketHistoryService.create_history",
        lambda **kwargs: None,
    )


def test_ticket_creation_valid(
    monkeypatch
):
    employee = user(
        1,
        "EMPLOYEE"
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: employee,
    )

    monkeypatch.setattr(
        "services.ticket_service."
        "TicketCategoryDAO.get_by_id",
        lambda cid: SimpleNamespace(
            id=cid
        ),
    )

    monkeypatch.setattr(
        SLARuleService,
        "ensure_default_rules",
        lambda: None,
    )

    monkeypatch.setattr(
        SLARuleService,
        "get_rule_by_priority",
        lambda priority: SimpleNamespace(
            resolution_time_minutes=1440
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.create",
        lambda obj: obj,
    )

    result = TicketService.create_ticket(
        1,
        "  Printer issue ",
        " Printer is offline ",
        10,
        "high",
        "major",
    )

    assert result.title == "Printer issue"
    assert result.description == "Printer is offline"
    assert result.status == "OPEN"
    assert result.priority == "HIGH"
    assert result.severity == "MAJOR"

    assert (
        result.due_date
        == result.created_at
        + timedelta(minutes=1440)
    )


def test_ticket_creation_non_employee_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT"
        ),
    )

    with pytest.raises(PermissionError):
        TicketService.create_ticket(
            1,
            "x",
            "y",
            1,
        )


def test_ticket_creation_inactive_user_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
            active=False,
        ),
    )

    with pytest.raises(PermissionError):
        TicketService.create_ticket(
            1,
            "x",
            "y",
            1,
        )


def test_ticket_creation_blank_title_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    with pytest.raises(
        ValueError,
        match="title",
    ):
        TicketService.create_ticket(
            1,
            "   ",
            "description",
            1,
        )


def test_ticket_creation_blank_description_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    with pytest.raises(
        ValueError,
        match="description",
    ):
        TicketService.create_ticket(
            1,
            "title",
            "   ",
            1,
        )


def test_ticket_creation_invalid_category_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service."
        "TicketCategoryDAO.get_by_id",
        lambda cid: None,
    )

    with pytest.raises(
        ValueError,
        match="category",
    ):
        TicketService.create_ticket(
            1,
            "title",
            "description",
            999,
        )


def test_ticket_creation_invalid_priority_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service."
        "TicketCategoryDAO.get_by_id",
        lambda cid: SimpleNamespace(
            id=cid
        ),
    )

    with pytest.raises(
        ValueError,
        match="priority",
    ):
        TicketService.create_ticket(
            1,
            "title",
            "description",
            1,
            "URGENT",
            "MAJOR",
        )


def test_ticket_creation_invalid_severity_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service."
        "TicketCategoryDAO.get_by_id",
        lambda cid: SimpleNamespace(
            id=cid
        ),
    )

    with pytest.raises(
        ValueError,
        match="severity",
    ):
        TicketService.create_ticket(
            1,
            "title",
            "description",
            1,
            "HIGH",
            "URGENT",
        )


def test_ticket_creation_without_sla_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service."
        "TicketCategoryDAO.get_by_id",
        lambda cid: SimpleNamespace(
            id=cid
        ),
    )

    monkeypatch.setattr(
        SLARuleService,
        "ensure_default_rules",
        lambda: None,
    )

    monkeypatch.setattr(
        SLARuleService,
        "get_rule_by_priority",
        lambda priority: None,
    )

    with pytest.raises(
        ValueError,
        match="No SLA rule",
    ):
        TicketService.create_ticket(
            1,
            "title",
            "description",
            1,
            "HIGH",
            "MAJOR",
        )


def test_employee_can_access_owned_ticket(
    monkeypatch
):
    t = ticket(
        creator=1
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    assert (
        TicketService.get_ticket_by_id(
            1,
            1,
        )
        is t
    )


def test_employee_cannot_access_other_ticket(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=2
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.get_ticket_by_id(
            1,
            1,
        )


def test_agent_cannot_access_unassigned_ticket(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [],
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.get_ticket_by_id(
            2,
            1,
        )


def test_admin_can_access_any_ticket(
    monkeypatch
):
    t = ticket(
        creator=999
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    assert (
        TicketService.get_ticket_by_id(
            1,
            1,
        )
        is t
    )


def test_status_transition_success(
    monkeypatch
):
    agent = user(
        2,
        "AGENT",
    )

    t = ticket(
        status="ASSIGNED"
    )

    assignment = SimpleNamespace(
        ticket_id=1
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: agent,
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [assignment],
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.update",
        lambda obj: obj,
    )

    no_history(
        monkeypatch
    )

    result = TicketService.update_status(
        2,
        1,
        "IN_PROGRESS",
    )

    assert result.status == "IN_PROGRESS"


def test_status_same_value_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            status="OPEN"
        ),
    )

    with pytest.raises(
        ValueError,
        match="already",
    ):
        TicketService.update_status(
            1,
            1,
            "OPEN",
        )


def test_invalid_status_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    with pytest.raises(
        ValueError,
        match="Invalid ticket status",
    ):
        TicketService.update_status(
            1,
            1,
            "BROKEN",
        )


def test_invalid_transition_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            status="OPEN"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Invalid status transition",
    ):
        TicketService.update_status(
            1,
            1,
            "CLOSED",
        )


def test_employee_cannot_change_status(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            status="OPEN"
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.update_status(
            1,
            1,
            "ASSIGNED",
        )


def test_agent_cannot_update_unassigned_ticket(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            status="ASSIGNED"
        ),
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [],
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.update_status(
            2,
            1,
            "IN_PROGRESS",
        )


def test_agent_cannot_reopen_ticket(
    monkeypatch
):
    assignment = SimpleNamespace(
        ticket_id=1
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            status="ASSIGNED"
        ),
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [assignment],
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.update_status(
            2,
            1,
            "OPEN",
        )


def test_resolve_sets_timestamp(
    monkeypatch
):
    assignment = SimpleNamespace(
        ticket_id=1
    )

    t = ticket(
        status="IN_PROGRESS"
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [assignment],
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.update",
        lambda obj: obj,
    )

    no_history(
        monkeypatch
    )

    result = TicketService.update_status(
        2,
        1,
        "RESOLVED",
    )

    assert result.resolved_at is not None


def test_assignment_success(
    monkeypatch
):
    admin = user(
        1,
        "ADMIN",
    )

    agent = user(
        2,
        "AGENT",
        name="Agent One",
    )

    t = ticket(
        status="OPEN"
    )

    assignment = SimpleNamespace(
        ticket_id=1,
        agent_id=2,
        assigned_by=1,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: (
            admin
            if uid == 1
            else agent
        ),
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.get_by_ticket",
        lambda tid: [],
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.create",
        lambda obj: assignment,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.update",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        "services.ticket_history_service."
        "TicketHistoryService.create_history",
        lambda **kwargs: None,
    )

    result = TicketAssignmentService.assign_ticket(
        1,
        1,
        2,
    )

    assert result.agent_id == 2
    assert t.status == "ASSIGNED"


def test_assignment_non_admin_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketAssignmentService.assign_ticket(
            2,
            1,
            2,
        )


def test_assignment_invalid_agent_role_rejected(
    monkeypatch
):
    admin = user(
        1,
        "ADMIN",
    )

    employee = user(
        2,
        "EMPLOYEE",
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: (
            admin
            if uid == 1
            else employee
        ),
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    with pytest.raises(
        ValueError,
        match="support agent",
    ):
        TicketAssignmentService.assign_ticket(
            1,
            1,
            2,
        )


def test_assignment_inactive_agent_rejected(
    monkeypatch
):
    admin = user(
        1,
        "ADMIN",
    )

    inactive_agent = user(
        2,
        "AGENT",
        active=False,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: (
            admin
            if uid == 1
            else inactive_agent
        ),
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketAssignmentService.assign_ticket(
            1,
            1,
            2,
        )


def test_assignment_duplicate_rejected(
    monkeypatch
):
    admin = user(
        1,
        "ADMIN",
    )

    agent = user(
        2,
        "AGENT",
    )

    existing = SimpleNamespace(
        agent_id=2,
        unassigned_at=None,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: (
            admin
            if uid == 1
            else agent
        ),
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.get_by_ticket",
        lambda tid: [existing],
    )

    with pytest.raises(
        ValueError,
        match="already assigned",
    ):
        TicketAssignmentService.assign_ticket(
            1,
            1,
            2,
        )


def test_assignment_reassigns_old_agent(
    monkeypatch
):
    admin = user(
        1,
        "ADMIN",
    )

    agent1 = user(
        2,
        "AGENT",
    )

    agent2 = user(
        3,
        "AGENT",
    )

    t = ticket(
        status="ASSIGNED"
    )

    old_assignment = SimpleNamespace(
        agent_id=2,
        unassigned_at=None,
    )

    new_assignment = SimpleNamespace(
        ticket_id=1,
        agent_id=3,
        assigned_by=1,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: (
            admin
            if uid == 1
            else agent1
            if uid == 2
            else agent2
        ),
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.get_by_ticket",
        lambda tid: [old_assignment],
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.update",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.create",
        lambda obj: new_assignment,
    )

    monkeypatch.setattr(
        "services.ticket_history_service."
        "TicketHistoryService.create_history",
        lambda **kwargs: None,
    )

    result = TicketAssignmentService.assign_ticket(
        1,
        1,
        3,
    )

    assert (
        old_assignment.unassigned_at
        is not None
    )

    assert result.agent_id == 3


def test_unassign_success(
    monkeypatch
):
    admin = user(
        1,
        "ADMIN",
    )

    assignment = SimpleNamespace(
        id=10,
        ticket_id=1,
        unassigned_at=None,
    )

    t = ticket(
        status="ASSIGNED"
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: admin,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.get_by_id",
        lambda aid: assignment,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.update",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketDAO.update",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        "services.ticket_history_service."
        "TicketHistoryService.create_history",
        lambda **kwargs: None,
    )

    result = TicketAssignmentService.unassign_ticket(
        1,
        10,
    )

    assert result.unassigned_at is not None
    assert t.status == "OPEN"


def test_unassign_inactive_assignment_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    assignment = SimpleNamespace(
        unassigned_at=datetime.utcnow(),
        ticket_id=1,
    )

    monkeypatch.setattr(
        "services.ticket_assignment_service."
        "TicketAssignmentDAO.get_by_id",
        lambda aid: assignment,
    )

    with pytest.raises(
        ValueError,
        match="already inactive",
    ):
        TicketAssignmentService.unassign_ticket(
            1,
            1,
        )


def test_comment_success(
    monkeypatch
):
    employee = user(
        1,
        "EMPLOYEE",
    )

    t = ticket(
        creator=1
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "UserDAO.get_by_id",
        lambda uid: employee,
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "TicketCommentDAO.create",
        lambda obj: obj,
    )

    no_history(
        monkeypatch
    )

    result = TicketCommentService.add_comment(
        1,
        1,
        " Hello ",
    )

    assert result.comment == "Hello"


def test_comment_empty_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_comment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1
        ),
    )

    with pytest.raises(
        ValueError,
        match="empty",
    ):
        TicketCommentService.add_comment(
            1,
            1,
            "   ",
        )


def test_comment_closed_ticket_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_comment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1,
            status="CLOSED",
        ),
    )

    with pytest.raises(
        ValueError,
        match="closed",
    ):
        TicketCommentService.add_comment(
            1,
            1,
            "Hello",
        )


def test_comment_wrong_owner_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_comment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=2
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketCommentService.add_comment(
            1,
            1,
            "Hello",
        )


def test_comment_delete_requires_admin(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_comment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_comment_service."
        "TicketCommentDAO.get_by_id",
        lambda cid: SimpleNamespace(
            id=cid
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketCommentService.delete_comment(
            1,
            1,
        )


def test_sla_create_success(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.sla_rule_service."
        "SLARuleDAO.get_by_priority",
        lambda priority: None,
    )

    monkeypatch.setattr(
        "services.sla_rule_service."
        "SLARuleDAO.create",
        lambda rule: rule,
    )

    result = SLARuleService.create_rule(
        1,
        "high",
        60,
        120,
    )

    assert result.priority == "HIGH"
    assert result.response_time_minutes == 60
    assert result.resolution_time_minutes == 120


def test_sla_non_admin_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        SLARuleService.create_rule(
            1,
            "HIGH",
            60,
            120,
        )


def test_sla_invalid_priority_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    with pytest.raises(
        ValueError,
        match="priority",
    ):
        SLARuleService.create_rule(
            1,
            "URGENT",
            60,
            120,
        )


def test_sla_non_integer_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    with pytest.raises(
        ValueError,
        match="whole numbers",
    ):
        SLARuleService.create_rule(
            1,
            "HIGH",
            "abc",
            120,
        )


def test_sla_zero_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        SLARuleService.create_rule(
            1,
            "HIGH",
            0,
            120,
        )


def test_sla_negative_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        SLARuleService.create_rule(
            1,
            "HIGH",
            -1,
            120,
        )


def test_sla_response_greater_than_resolution_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    with pytest.raises(
        ValueError,
        match="greater than resolution",
    ):
        SLARuleService.create_rule(
            1,
            "HIGH",
            200,
            100,
        )


def test_sla_duplicate_priority_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.sla_rule_service."
        "SLARuleDAO.get_by_priority",
        lambda priority: SimpleNamespace(
            id=5
        ),
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        SLARuleService.create_rule(
            1,
            "HIGH",
            60,
            120,
        )


def test_sla_update_missing_rule_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.sla_rule_service."
        "SLARuleDAO.get_by_id",
        lambda rid: None,
    )

    with pytest.raises(
        ValueError,
        match="not found",
    ):
        SLARuleService.update_rule(
            1,
            999,
            60,
            120,
        )


def test_sla_delete_missing_rule_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.sla_rule_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.sla_rule_service."
        "SLARuleDAO.get_by_id",
        lambda rid: None,
    )

    with pytest.raises(
        ValueError,
        match="not found",
    ):
        SLARuleService.delete_rule(
            1,
            999,
        )


def test_feedback_success(
    monkeypatch
):
    employee = user(
        1,
        "EMPLOYEE",
    )

    t = ticket(
        creator=1,
        status="RESOLVED",
    )

    feedback = SimpleNamespace(
        rating=5,
        comment="Great",
    )

    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: employee,
    )

    monkeypatch.setattr(
        "services.feedback_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "services.feedback_service.FeedbackDAO.get_by_ticket",
        lambda tid: None,
    )

    monkeypatch.setattr(
        "services.feedback_service.FeedbackDAO.create",
        lambda obj: feedback,
    )

    no_history(
        monkeypatch
    )

    result = FeedbackService.submit_feedback(
        1,
        1,
        5,
        "Great",
    )

    assert result.rating == 5


def test_feedback_requires_resolved_ticket(
    monkeypatch
):
    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1,
            status="IN_PROGRESS",
        ),
    )

    with pytest.raises(
        ValueError,
        match="resolved",
    ):
        FeedbackService.submit_feedback(
            1,
            1,
            5,
            "",
        )


def test_feedback_only_employee_can_submit(
    monkeypatch
):
    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        FeedbackService.submit_feedback(
            2,
            1,
            5,
            "",
        )


def test_feedback_wrong_owner_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=2,
            status="RESOLVED",
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        FeedbackService.submit_feedback(
            1,
            1,
            5,
            "",
        )


def test_feedback_invalid_rating_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1,
            status="RESOLVED",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.FeedbackDAO.get_by_ticket",
        lambda tid: None,
    )

    with pytest.raises(
        ValueError
    ):
        FeedbackService.submit_feedback(
            1,
            1,
            6,
            "",
        )


def test_feedback_duplicate_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1,
            status="RESOLVED",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.FeedbackDAO.get_by_ticket",
        lambda tid: SimpleNamespace(
            id=1
        ),
    )

    with pytest.raises(
        ValueError,
        match="already been submitted",
    ):
        FeedbackService.submit_feedback(
            1,
            1,
            5,
            "",
        )


def test_feedback_comment_too_long_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.feedback_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1,
            status="RESOLVED",
        ),
    )

    monkeypatch.setattr(
        "services.feedback_service.FeedbackDAO.get_by_ticket",
        lambda tid: None,
    )

    with pytest.raises(
        ValueError,
        match="2000",
    ):
        FeedbackService.submit_feedback(
            1,
            1,
            5,
            "x" * 2001,
        )


def make_file(
    filename,
    content=b"hello",
):
    return FileStorage(
        stream=BytesIO(content),
        filename=filename,
        content_type="application/octet-stream",
    )


def test_attachment_missing_file_rejected():
    with pytest.raises(
        ValueError,
        match="No file",
    ):
        TicketAttachmentService._validate_file(
            None
        )


def test_attachment_invalid_extension_rejected():
    with pytest.raises(
        ValueError,
        match="not allowed",
    ):
        TicketAttachmentService._validate_file(
            make_file(
                "malware.exe"
            )
        )


def test_attachment_empty_filename_rejected():
    empty_name = FileStorage(
        stream=BytesIO(b"x"),
        filename="",
    )

    with pytest.raises(
        ValueError,
        match="Filename",
    ):
        TicketAttachmentService._validate_file(
            empty_name
        )


def test_attachment_size_limit_rejected():
    large_file = FileStorage(
        stream=BytesIO(
            b"x"
            * (
                TicketAttachmentService.MAX_FILE_SIZE
                + 1
            )
        ),
        filename="large.txt",
    )

    with pytest.raises(
        ValueError,
        match="10 MB",
    ):
        TicketAttachmentService._validate_file(
            large_file
        )


def test_attachment_closed_ticket_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1,
            status="CLOSED",
        ),
    )

    with pytest.raises(
        ValueError,
        match="closed ticket",
    ):
        TicketAttachmentService.upload_attachment(
            1,
            1,
            make_file("test.txt"),
        )


def test_attachment_wrong_owner_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=2
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketAttachmentService.upload_attachment(
            1,
            1,
            make_file("test.txt"),
        )


def test_attachment_upload_success(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=1
        ),
    )

    monkeypatch.setattr(
        TicketAttachmentService,
        "UPLOAD_FOLDER",
        str(tmp_path),
    )

    saved = SimpleNamespace(
        id=1,
        ticket_id=1,
        uploaded_by=1,
        original_filename="test.txt",
        stored_filename="stored.txt",
        file_path=str(
            tmp_path
            / "1"
            / "stored.txt"
        ),
        file_size=5,
        file_type="txt",
    )

    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "TicketAttachmentDAO.create",
        lambda obj: saved,
    )

    no_history(
        monkeypatch
    )

    result = (
        TicketAttachmentService.upload_attachment(
            1,
            1,
            make_file(
                "test.txt",
                b"hello",
            ),
        )
    )

    assert (
        result.original_filename
        == "test.txt"
    )


def test_attachment_get_wrong_owner_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    attachment = SimpleNamespace(
        ticket_id=1
    )

    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "TicketAttachmentDAO.get_by_id",
        lambda aid: attachment,
    )

    monkeypatch.setattr(
        "services.ticket_attachment_service."
        "TicketDAO.get_by_id",
        lambda tid: ticket(
            creator=2
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketAttachmentService.get_attachment(
            1,
            1,
        )


def test_escalation_success(
    monkeypatch
):
    agent = user(
        2,
        "AGENT",
    )

    t = ticket(
        status="IN_PROGRESS"
    )

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: agent,
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [
            SimpleNamespace(
                ticket_id=1
            )
        ],
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.update",
        lambda obj: obj,
    )

    no_history(
        monkeypatch
    )

    result = TicketService.escalate_ticket(
        2,
        1,
        "Urgent",
    )

    assert result.is_escalated is True


def test_escalation_employee_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "EMPLOYEE",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.escalate_ticket(
            1,
            1,
            "Urgent",
        )


def test_escalation_unassigned_agent_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "AGENT",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(),
    )

    monkeypatch.setattr(
        "dao.ticket_assignment_dao."
        "TicketAssignmentDAO.get_by_agent",
        lambda uid: [],
    )

    with pytest.raises(
        PermissionError
    ):
        TicketService.escalate_ticket(
            2,
            1,
            "Urgent",
        )


def test_escalation_closed_ticket_rejected(
    monkeypatch
):
    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: ticket(
            status="CLOSED"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Closed tickets",
    ):
        TicketService.escalate_ticket(
            1,
            1,
            "Urgent",
        )


def test_escalation_duplicate_rejected(
    monkeypatch
):
    t = ticket(
        status="IN_PROGRESS"
    )

    t.is_escalated = True

    monkeypatch.setattr(
        "services.ticket_service.UserDAO.get_by_id",
        lambda uid: user(
            uid,
            "ADMIN",
        ),
    )

    monkeypatch.setattr(
        "services.ticket_service.TicketDAO.get_by_id",
        lambda tid: t,
    )

    with pytest.raises(
        ValueError,
        match="already escalated",
    ):
        TicketService.escalate_ticket(
            1,
            1,
            "Urgent",
        )