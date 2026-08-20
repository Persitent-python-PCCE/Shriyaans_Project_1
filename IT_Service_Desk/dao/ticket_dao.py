from config.database import db
from models.ticket import Ticket
class TicketDAO:

    @staticmethod
    def create(ticket):
        db.session.add(ticket)
        db.session.commit()
        return ticket

    @staticmethod
    def get_by_id(ticket_id):
        return db.session.get(Ticket, ticket_id)

    @staticmethod
    def get_all():
        return Ticket.query.order_by(
            Ticket.created_at.desc()
        ).all()

    @staticmethod
    def update(ticket):
        db.session.commit()
        return ticket

    @staticmethod
    def delete(ticket):
        db.session.delete(ticket)
        db.session.commit()

    @staticmethod
    def get_by_creator(user_id):
        return Ticket.query.filter_by(
            created_by=user_id
        ).order_by(
            Ticket.created_at.desc()
        ).all()

    @staticmethod
    def get_by_status(status):
        return Ticket.query.filter_by(
            status=status
        ).all()

    @staticmethod
    def get_by_priority(priority):
        return Ticket.query.filter_by(
            priority=priority
        ).all()

    @staticmethod
    def get_by_category(category_id):
        return Ticket.query.filter_by(
            category_id=category_id
        ).all()

    @staticmethod
    def get_escalated():
        return Ticket.query.filter_by(
            is_escalated=True
        ).all()
    
    @staticmethod
    def search(
        title=None,
        status=None,
        priority=None,
        category_id=None
    ):
        query = Ticket.query

        if title:
            query = query.filter(
                Ticket.title.ilike(f"%{title}%")
            )

        if status:
            query = query.filter(
                Ticket.status == status
            )

        if priority:
            query = query.filter(
                Ticket.priority == priority
            )

        if category_id:
            query = query.filter(
                Ticket.category_id == category_id
            )

        return query.order_by(
            Ticket.created_at.desc()
        ).all()