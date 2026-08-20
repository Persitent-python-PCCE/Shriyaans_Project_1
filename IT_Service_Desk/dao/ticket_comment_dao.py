from config.database import db
from models.ticket_comment import TicketComment
class TicketCommentDAO:

    @staticmethod
    def create(comment):
        db.session.add(comment)
        db.session.commit()
        return comment

    @staticmethod
    def get_by_id(comment_id):
        return db.session.get(
            TicketComment,
            comment_id
        )

    @staticmethod
    def get_by_ticket(ticket_id):
        return TicketComment.query.filter_by(
            ticket_id=ticket_id
        ).order_by(
            TicketComment.created_at.asc()
        ).all()

    @staticmethod
    def delete(comment):
        db.session.delete(comment)
        db.session.commit()