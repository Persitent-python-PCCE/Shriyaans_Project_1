from datetime import datetime

from config.database import db


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket_categories.id"),
        nullable=False
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    priority = db.Column(
        db.Enum(
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        ),
        default="MEDIUM",
        nullable=False
    )

    severity = db.Column(
        db.Enum(
            "MINOR",
            "MODERATE",
            "MAJOR",
            "CRITICAL"
        ),
        default="MODERATE",
        nullable=False
    )

    status = db.Column(
        db.Enum(
            "OPEN",
            "ASSIGNED",
            "IN_PROGRESS",
            "RESOLVED",
            "CLOSED"
        ),
        default="OPEN",
        nullable=False
    )

    due_date = db.Column(
        db.DateTime,
        nullable=True
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    closed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    is_escalated = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    category = db.relationship(
        "TicketCategory",
        back_populates="tickets"
    )

    creator = db.relationship(
        "User",
        back_populates="tickets_created",
        foreign_keys=[created_by]
    )

    assignments = db.relationship(
        "TicketAssignment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    comments = db.relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    attachments = db.relationship(
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    history = db.relationship(
        "TicketHistory",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

   
    feedback = db.relationship(
        "Feedback",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ticket {self.id}: {self.title}>"