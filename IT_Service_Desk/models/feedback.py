from datetime import datetime

from config.database import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        back_populates="feedback"
    )

    user = db.relationship(
        "User",
        back_populates="feedback"
    )

    def __repr__(self):
        return f"<Feedback Ticket={self.ticket_id} Rating={self.rating}>"