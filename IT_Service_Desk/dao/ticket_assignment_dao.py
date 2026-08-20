from config.database import db
from models.ticket_assignment import TicketAssignment


class TicketAssignmentDAO:

    @staticmethod
    def create(assignment):
        try:
            db.session.add(assignment)
            db.session.commit()

            return assignment

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id(assignment_id):
        return db.session.get(
            TicketAssignment,
            assignment_id
        )

    @staticmethod
    def get_by_ticket(ticket_id):
        return TicketAssignment.query.filter_by(
            ticket_id=ticket_id
        ).order_by(
            TicketAssignment.assigned_at.desc()
        ).all()

    @staticmethod
    def get_by_agent(agent_id):
        return TicketAssignment.query.filter_by(
            agent_id=agent_id,
            unassigned_at=None
        ).order_by(
            TicketAssignment.assigned_at.desc()
        ).all()

    @staticmethod
    def update(assignment):
        try:
            db.session.commit()

            return assignment

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(assignment):
        try:
            db.session.delete(assignment)
            db.session.commit()

            return True

        except Exception:
            db.session.rollback()
            raise