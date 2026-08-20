from config.database import db
from models.sla_rule import SLARule


class SLARuleDAO:

    @staticmethod
    def get_by_id(rule_id):
        return db.session.get(
            SLARule,
            rule_id
        )

    @staticmethod
    def get_by_priority(priority):
        return SLARule.query.filter_by(
            priority=priority
        ).first()

    @staticmethod
    def get_all():
        return SLARule.query.all()

    @staticmethod
    def create(rule):
        db.session.add(rule)
        db.session.commit()
        return rule

    @staticmethod
    def update(rule):
        db.session.commit()
        return rule