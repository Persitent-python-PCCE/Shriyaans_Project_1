from datetime import datetime

from config.database import db


class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

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

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    old_value = db.Column(
        db.String(255)
    )

    new_value = db.Column(
        db.String(255)
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        back_populates="history"
    )

    user = db.relationship(
        "User",
        back_populates="history_entries"
    )

    def __repr__(self):
        return f"<TicketHistory {self.action}>"