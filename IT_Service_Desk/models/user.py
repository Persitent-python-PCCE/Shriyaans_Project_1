from datetime import datetime
from config.database import db
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

 
    role = db.relationship(
        "Role",
        back_populates="users"
    )

    
    tickets_created = db.relationship(
        "Ticket",
        back_populates="creator",
        foreign_keys="Ticket.created_by"
    )

     
    comments = db.relationship(
        "TicketComment",
        back_populates="user"
    )

     
    attachments = db.relationship(
        "TicketAttachment",
        back_populates="uploaded_by_user"
    )

     
    history_entries = db.relationship(
        "TicketHistory",
        back_populates="user"
    )

     
    feedback = db.relationship(
        "Feedback",
        back_populates="user"
    )

    def __repr__(self):
        return f"<User {self.email}>"