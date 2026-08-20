from datetime import datetime

from config.database import db


class SLARule(db.Model):
    __tablename__ = "sla_rules"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    priority = db.Column(
        db.Enum(
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        ),
        nullable=False,
        unique=True
    )

    response_time_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    resolution_time_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<SLARule {self.priority}>"