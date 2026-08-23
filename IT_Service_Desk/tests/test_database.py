import pytest
from flask import Flask

from config.database import db

from models.role import Role
from models.user import User
from models.ticket_category import TicketCategory
from models.ticket import Ticket
from models.ticket_assignment import TicketAssignment
from models.ticket_comment import TicketComment
from models.sla_rule import SLARule
from models.feedback import Feedback

from dao.role_dao import RoleDAO
from dao.user_dao import UserDAO
from dao.ticket_category_dao import TicketCategoryDAO
from dao.ticket_dao import TicketDAO
from dao.ticket_assignment_dao import TicketAssignmentDAO
from dao.ticket_comment_dao import TicketCommentDAO
from dao.sla_rule_dao import SLARuleDAO
from dao.feedback_dao import FeedbackDAO


@pytest.fixture
def sqlite_app():
    test_app = Flask("database_tests")

    test_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(test_app)

    with test_app.app_context():
        db.create_all()

        try:
            yield test_app
        finally:
            db.session.remove()
            db.drop_all()


def test_role_and_user_database_operations(sqlite_app):
    with sqlite_app.app_context():
        role = Role(name="EMPLOYEE")
        RoleDAO.create(role)

        fetched_role = RoleDAO.get_by_id(role.id)

        assert fetched_role is not None
        assert fetched_role.name == "EMPLOYEE"

        fetched_by_name = RoleDAO.get_by_name("EMPLOYEE")

        assert fetched_by_name is not None
        assert fetched_by_name.id == role.id

        user = User(
            name="DB User",
            email="dbuser@example.com",
            password_hash="hash",
            role_id=role.id,
            is_active=True,
        )

        UserDAO.create(user)

        fetched_user = UserDAO.get_by_email(
            "dbuser@example.com"
        )

        assert fetched_user is not None
        assert fetched_user.name == "DB User"
        assert fetched_user.role.name == "EMPLOYEE"

        fetched_user.name = "Updated User"

        UserDAO.update(fetched_user)

        updated_user = UserDAO.get_by_id(
            fetched_user.id
        )

        assert updated_user.name == "Updated User"

        UserDAO.set_active(
            updated_user,
            False
        )

        assert (
            UserDAO.get_by_id(
                updated_user.id
            ).is_active
            is False
        )

        UserDAO.set_active(
            updated_user,
            True
        )

        assert (
            UserDAO.get_by_id(
                updated_user.id
            ).is_active
            is True
        )

        users_by_role = UserDAO.get_by_role(
            role.id
        )

        assert len(users_by_role) == 1
        assert users_by_role[0].id == updated_user.id


def test_ticket_category_database_operations(sqlite_app):
    with sqlite_app.app_context():
        category = TicketCategory(
            name="Hardware",
            description="Hardware incidents",
        )

        TicketCategoryDAO.create(category)

        fetched = TicketCategoryDAO.get_by_id(
            category.id
        )

        assert fetched is not None
        assert fetched.name == "Hardware"
        assert fetched.description == "Hardware incidents"


def test_ticket_assignment_comment_sla_feedback_database_operations(
    sqlite_app
):
    with sqlite_app.app_context():
        employee_role = Role(
            name="EMPLOYEE"
        )

        agent_role = Role(
            name="AGENT"
        )

        RoleDAO.create(employee_role)
        RoleDAO.create(agent_role)

        employee = User(
            name="Employee",
            email="employee@example.com",
            password_hash="hash",
            role_id=employee_role.id,
            is_active=True,
        )

        agent = User(
            name="Agent",
            email="agent@example.com",
            password_hash="hash",
            role_id=agent_role.id,
            is_active=True,
        )

        UserDAO.create(employee)
        UserDAO.create(agent)

        category = TicketCategory(
            name="Software",
            description="Software issues",
        )

        TicketCategoryDAO.create(category)

        ticket = Ticket(
            title="Database test ticket",
            description="Database CRUD test",
            category_id=category.id,
            created_by=employee.id,
            priority="HIGH",
            severity="MAJOR",
            status="OPEN",
        )

        TicketDAO.create(ticket)

        fetched_ticket = TicketDAO.get_by_id(
            ticket.id
        )

        assert fetched_ticket is not None
        assert fetched_ticket.title == (
            "Database test ticket"
        )

        assert (
            TicketDAO.get_by_creator(
                employee.id
            )[0].id
            == ticket.id
        )

        assert (
            TicketDAO.get_by_status(
                "OPEN"
            )[0].id
            == ticket.id
        )

        assert (
            TicketDAO.get_by_priority(
                "HIGH"
            )[0].id
            == ticket.id
        )

        assert (
            TicketDAO.get_by_category(
                category.id
            )[0].id
            == ticket.id
        )

        search_results = TicketDAO.search(
            title="database"
        )

        assert len(search_results) == 1
        assert search_results[0].id == ticket.id

        ticket.status = "ASSIGNED"

        TicketDAO.update(ticket)

        assert (
            TicketDAO.get_by_id(
                ticket.id
            ).status
            == "ASSIGNED"
        )

        assignment = TicketAssignment(
            ticket_id=ticket.id,
            agent_id=agent.id,
            assigned_by=employee.id,
        )

        TicketAssignmentDAO.create(
            assignment
        )

        fetched_assignment = (
            TicketAssignmentDAO.get_by_id(
                assignment.id
            )
        )

        assert fetched_assignment is not None
        assert fetched_assignment.agent_id == agent.id

        assert (
            TicketAssignmentDAO.get_by_ticket(
                ticket.id
            )[0].id
            == assignment.id
        )

        assert (
            TicketAssignmentDAO.get_by_agent(
                agent.id
            )[0].id
            == assignment.id
        )

        comment = TicketComment(
            ticket_id=ticket.id,
            user_id=employee.id,
            comment="Database comment",
        )

        TicketCommentDAO.create(
            comment
        )

        fetched_comment = (
            TicketCommentDAO.get_by_id(
                comment.id
            )
        )

        assert fetched_comment is not None
        assert fetched_comment.comment == (
            "Database comment"
        )

        assert (
            TicketCommentDAO.get_by_ticket(
                ticket.id
            )[0].id
            == comment.id
        )

        sla = SLARule(
            priority="CRITICAL",
            response_time_minutes=60,
            resolution_time_minutes=240,
        )

        SLARuleDAO.create(
            sla
        )

        fetched_sla = (
            SLARuleDAO.get_by_id(
                sla.id
            )
        )

        assert fetched_sla is not None
        assert fetched_sla.priority == "CRITICAL"

        assert (
            SLARuleDAO.get_by_priority(
                "CRITICAL"
            ).id
            == sla.id
        )

        ticket.status = "RESOLVED"

        TicketDAO.update(ticket)

        feedback = Feedback(
            ticket_id=ticket.id,
            user_id=employee.id,
            rating=5,
            comment="Good service",
        )

        FeedbackDAO.create(
            feedback
        )

        fetched_feedback = (
            FeedbackDAO.get_by_ticket(
                ticket.id
            )
        )

        assert fetched_feedback is not None
        assert fetched_feedback.rating == 5
        assert fetched_feedback.comment == (
            "Good service"
        )


def test_database_duplicate_email_is_rejected(
    sqlite_app
):
    with sqlite_app.app_context():
        role = Role(
            name="EMPLOYEE"
        )

        RoleDAO.create(role)

        first_user = User(
            name="First User",
            email="duplicate@example.com",
            password_hash="hash",
            role_id=role.id,
        )

        UserDAO.create(first_user)

        duplicate_user = User(
            name="Second User",
            email="duplicate@example.com",
            password_hash="hash",
            role_id=role.id,
        )

        with pytest.raises(Exception):
            UserDAO.create(
                duplicate_user
            )

        existing = UserDAO.get_by_email(
            "duplicate@example.com"
        )

        assert existing is not None
        assert existing.name == "First User"