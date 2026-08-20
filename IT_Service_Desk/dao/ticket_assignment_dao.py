from config.database import db
from models.ticket_assignment import TicketAssignment
class TicketAssignmentDAO:

    @staticmethod
    def create(assignment):
        db.session.add(assignment)
        db.session.commit()
        return assignment

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
        ).all()

    @staticmethod
    def get_by_agent(agent_id):
        return TicketAssignment.query.filter_by(
            agent_id=agent_id,
            unassigned_at=None
        ).all()

    @staticmethod
    def update(assignment):
        db.session.commit()
        return assignment