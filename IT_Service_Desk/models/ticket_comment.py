from datetime import datetime

from config.database import db


class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

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

    comment = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        back_populates="comments"
    )

    user = db.relationship(
        "User",
        back_populates="comments"
    )

    def __repr__(self):
        return f"<TicketComment {self.id}>"