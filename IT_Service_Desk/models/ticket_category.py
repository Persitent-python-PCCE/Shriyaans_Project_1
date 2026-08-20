from datetime import datetime

from config.database import db


class TicketCategory(db.Model):
    __tablename__ = "ticket_categories"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    tickets = db.relationship(
        "Ticket",
        back_populates="category"
    )

    def __repr__(self):
        return f"<TicketCategory {self.name}>"