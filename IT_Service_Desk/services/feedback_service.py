from models.feedback import Feedback
from dao.feedback_dao import FeedbackDAO
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO

class FeedbackService:
    @staticmethod
    def _get_user(user_id):
        user = UserDAO.get_by_id(user_id)
        if not user:
            raise ValueError('User not found.')
        if not user.is_active:
            raise PermissionError('User account is inactive.')
        return user

    @staticmethod
    def get_feedback(user_id, ticket_id):
        user = FeedbackService._get_user(user_id)
        ticket = TicketDAO.get_by_id(ticket_id)
        if not ticket:
            raise ValueError('Ticket not found.')
        allowed = user.role and user.role.name in {'ADMIN', 'AGENT'}
        allowed = allowed or (user.role and user.role.name == 'EMPLOYEE' and ticket.created_by == user.id)
        if not allowed:
            raise PermissionError('You are not allowed to view feedback for this ticket.')
        return FeedbackDAO.get_by_ticket(ticket_id)

    @staticmethod
    def submit_feedback(user_id, ticket_id, rating, comment=''):
        user = FeedbackService._get_user(user_id)
        if not user.role or user.role.name != 'EMPLOYEE':
            raise PermissionError('Only employees can submit feedback.')
        ticket = TicketDAO.get_by_id(ticket_id)
        if not ticket:
            raise ValueError('Ticket not found.')
        if ticket.created_by != user.id:
            raise PermissionError('You are not allowed to submit feedback for this ticket.')
        if ticket.status not in {'RESOLVED', 'CLOSED'}:
            raise ValueError('Feedback is available only after the ticket is resolved.')
        if FeedbackDAO.get_by_ticket(ticket_id):
            raise ValueError('Feedback has already been submitted for this ticket.')
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            raise ValueError('Rating must be a whole number from 1 to 5.')
        if rating not in range(1, 6):
            raise ValueError('Rating must be between 1 and 5.')
        comment = (comment or '').strip()
        if len(comment) > 2000:
            raise ValueError('Feedback comment cannot exceed 2000 characters.')
        feedback = Feedback(ticket_id=ticket_id, user_id=user_id, rating=rating, comment=comment or None)
        created = FeedbackDAO.create(feedback)
        from services.ticket_history_service import TicketHistoryService
        TicketHistoryService.create_history(
            user_id=user_id,
            ticket_id=ticket_id,
            action='FEEDBACK_SUBMITTED',
            description=f'Employee submitted {rating}/5 satisfaction feedback.'
        )
        return created
