from models.ticket_history import TicketHistory

from dao.ticket_history_dao import TicketHistoryDAO
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO


class TicketHistoryService:

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
    def create_history(
        user_id,
        ticket_id,
        action,
        old_value=None,
        new_value=None,
        description=None
    ):
        user = TicketHistoryService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if not action or not action.strip():
            raise ValueError(
                "History action is required."
            )

        history = TicketHistory(
            ticket_id=ticket_id,
            user_id=user.id,
            action=action.strip(),
            old_value=old_value,
            new_value=new_value,
            description=description
        )

        return TicketHistoryDAO.create(
            history
        )

    @staticmethod
    def get_ticket_history(
        user_id,
        ticket_id
    ):
        user = TicketHistoryService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if user.role.name == "ADMIN":
            return TicketHistoryDAO.get_by_ticket(
                ticket_id
            )

        if user.role.name == "EMPLOYEE":

            if ticket.created_by != user.id:
                raise PermissionError(
                    "You are not allowed to view "
                    "this ticket history."
                )

            return TicketHistoryDAO.get_by_ticket(
                ticket_id
            )

        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(
                user.id
            )

            assigned = any(
                assignment.ticket_id == ticket_id
                for assignment in assignments
            )

            if not assigned:
                raise PermissionError(
                    "You are not allowed to view "
                    "this ticket history."
                )

            return TicketHistoryDAO.get_by_ticket(
                ticket_id
            )

        raise PermissionError("Invalid role.")