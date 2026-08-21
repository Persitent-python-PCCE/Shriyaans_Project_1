from datetime import datetime

from models.ticket_assignment import TicketAssignment

from dao.ticket_assignment_dao import TicketAssignmentDAO
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO


class TicketAssignmentService:

    @staticmethod
    def _get_user(user_id):

        user = UserDAO.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        if not user.is_active:
            raise PermissionError(
                "User account is inactive."
            )

        return user

    @staticmethod
    def assign_ticket(
        admin_id,
        ticket_id,
        agent_id
    ):

        admin = TicketAssignmentService._get_user(
            admin_id
        )

        if not admin.role or admin.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can assign tickets."
            )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        agent = TicketAssignmentService._get_user(
            agent_id
        )

        if not agent.role or agent.role.name != "AGENT":
            raise ValueError(
                "Selected user is not a support agent."
            )

        if not agent.is_active:
            raise ValueError(
                "Selected agent is inactive."
            )

        existing_assignments = (
            TicketAssignmentDAO.get_by_ticket(
                ticket_id
            )
        )

        for assignment in existing_assignments:

            if assignment.unassigned_at is None:

                if assignment.agent_id == agent_id:
                    raise ValueError(
                        "Ticket is already assigned "
                        "to this agent."
                    )

                assignment.unassigned_at = (
                    datetime.utcnow()
                )

                TicketAssignmentDAO.update(
                    assignment
                )

        assignment = TicketAssignment(
            ticket_id=ticket_id,
            agent_id=agent_id,
            assigned_by=admin_id
        )

        assignment = TicketAssignmentDAO.create(
            assignment
        )

        old_status = ticket.status

        if ticket.status == "OPEN":

            ticket.status = "ASSIGNED"

            TicketDAO.update(ticket)

        from services.ticket_history_service import (
            TicketHistoryService
        )

        TicketHistoryService.create_history(
            user_id=admin_id,
            ticket_id=ticket_id,
            action="TICKET_ASSIGNED",
            old_value=old_status,
            new_value=ticket.status,
            description=(
                f"Ticket assigned to agent "
                f"{agent.name}."
            )
        )

        return assignment

    @staticmethod
    def unassign_ticket(
        admin_id,
        assignment_id
    ):

        admin = TicketAssignmentService._get_user(
            admin_id
        )

        if not admin.role or admin.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can unassign tickets."
            )

        assignment = TicketAssignmentDAO.get_by_id(
            assignment_id
        )

        if not assignment:
            raise ValueError(
                "Assignment not found."
            )

        if assignment.unassigned_at is not None:
            raise ValueError(
                "This assignment is already inactive."
            )

        assignment.unassigned_at = datetime.utcnow()

        TicketAssignmentDAO.update(
            assignment
        )

        ticket = TicketDAO.get_by_id(
            assignment.ticket_id
        )

        if ticket and ticket.status == "ASSIGNED":

            old_status = ticket.status

            ticket.status = "OPEN"

            TicketDAO.update(ticket)

            from services.ticket_history_service import (
                TicketHistoryService
            )

            TicketHistoryService.create_history(
                user_id=admin_id,
                ticket_id=ticket.id,
                action="TICKET_UNASSIGNED",
                old_value=old_status,
                new_value="OPEN",
                description="Ticket was unassigned."
            )

        return assignment

    @staticmethod
    def get_ticket_assignments(
        user_id,
        ticket_id
    ):

        user = TicketAssignmentService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if user.role.name == "ADMIN":

            return TicketAssignmentDAO.get_by_ticket(
                ticket_id
            )

        if user.role.name == "EMPLOYEE":

            if ticket.created_by != user_id:
                raise PermissionError(
                    "You cannot view this ticket."
                )

            return TicketAssignmentDAO.get_by_ticket(
                ticket_id
            )

        if user.role.name == "AGENT":

            assignments = (
                TicketAssignmentDAO.get_by_ticket(
                    ticket_id
                )
            )

            allowed = [
                assignment
                for assignment in assignments
                if (
                    assignment.agent_id == user_id
                    and assignment.unassigned_at is None
                )
            ]

            if not allowed:
                raise PermissionError(
                    "This ticket is not assigned to you."
                )

            return allowed

        raise PermissionError(
            "Invalid role."
        )

    @staticmethod
    def get_agent_assignments(agent_id):

        agent = TicketAssignmentService._get_user(
            agent_id
        )

        if not agent.role or agent.role.name != "AGENT":
            raise PermissionError(
                "Only agents can view agent assignments."
            )

        return TicketAssignmentDAO.get_by_agent(
            agent_id
        )