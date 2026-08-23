from models.ticket_comment import TicketComment

from dao.ticket_comment_dao import TicketCommentDAO
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO


class TicketCommentService:

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
    def _can_access_ticket(user, ticket):
        if user.role.name == "ADMIN":
            return True

        if user.role.name == "EMPLOYEE":
            return ticket.created_by == user.id

        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(
                user.id
            )

            return any(
                assignment.ticket_id == ticket.id
                for assignment in assignments
                if getattr(assignment, "unassigned_at", None) is None
            )

        return False

    @staticmethod
    def add_comment(
        user_id,
        ticket_id,
        comment_text
    ):
        user = TicketCommentService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if not TicketCommentService._can_access_ticket(
            user,
            ticket
        ):
            raise PermissionError(
                "You are not allowed to comment "
                "on this ticket."
            )

        if not comment_text or not comment_text.strip():
            raise ValueError(
                "Comment cannot be empty."
            )

        if ticket.status == "CLOSED":
            raise ValueError(
                "Cannot comment on a closed ticket."
            )

        new_comment = TicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            comment=comment_text.strip()
        )

        comment = TicketCommentDAO.create(
            new_comment
        )

        from services.ticket_history_service import TicketHistoryService

        TicketHistoryService.create_history(
            user_id=user_id,
            ticket_id=ticket_id,
            action="COMMENT_ADDED",
            description="A new comment was added."
        )

        return comment

    @staticmethod
    def get_comments(
        user_id,
        ticket_id
    ):
        user = TicketCommentService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if not TicketCommentService._can_access_ticket(
            user,
            ticket
        ):
            raise PermissionError(
                "You are not allowed to view "
                "comments for this ticket."
            )

        return TicketCommentDAO.get_by_ticket(
            ticket_id
        )

    @staticmethod
    def delete_comment(
        user_id,
        comment_id
    ):
        user = TicketCommentService._get_user(
            user_id
        )

        comment = TicketCommentDAO.get_by_id(
            comment_id
        )

        if not comment:
            raise ValueError(
                "Comment not found."
            )

        # Only ADMIN can delete comments
        if user.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can delete comments."
            )

        TicketCommentDAO.delete(comment)

        return True