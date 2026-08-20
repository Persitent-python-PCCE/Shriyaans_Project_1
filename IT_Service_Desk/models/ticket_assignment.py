from datetime import datetime

from config.database import db


class TicketAssignment(db.Model):
    __tablename__ = "ticket_assignments"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False
    )

    agent_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    assigned_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    assigned_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    unassigned_at = db.Column(
        db.DateTime,
        nullable=True
    )

    ticket = db.relationship(
        "Ticket",
        back_populates="assignments"
    )

    agent = db.relationship(
        "User",
        foreign_keys=[agent_id]
    )

    assigner = db.relationship(
        "User",
        foreign_keys=[assigned_by]
    )

    def __repr__(self):
        return f"<TicketAssignment Ticket={self.ticket_id} Agent={self.agent_id}>"