from datetime import datetime

from config.database import db


class TicketAttachment(db.Model):
    __tablename__ = "ticket_attachments"

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

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=False
    )

    file_type = db.Column(
        db.String(100)
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        back_populates="attachments"
    )

    uploaded_by_user = db.relationship(
        "User",
        back_populates="attachments"
    )

    def __repr__(self):
        return f"<TicketAttachment {self.original_filename}>"