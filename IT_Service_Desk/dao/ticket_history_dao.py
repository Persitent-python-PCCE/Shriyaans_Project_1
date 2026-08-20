from config.database import db
from models.ticket_history import TicketHistory


class TicketHistoryDAO:

    @staticmethod
    def create(history):
        db.session.add(history)
        db.session.commit()
        return history

    @staticmethod
    def get_by_ticket(ticket_id):
        return TicketHistory.query.filter_by(
            ticket_id=ticket_id
        ).order_by(
            TicketHistory.created_at.asc()
        ).all()

    @staticmethod
    def get_by_id(history_id):
        return db.session.get(
            TicketHistory,
            history_id
        )