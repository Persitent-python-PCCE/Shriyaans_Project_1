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
        return SLARule.query.order_by(
            SLARule.priority.asc()
        ).all()

    @staticmethod
    def create(rule):

        try:
            db.session.add(rule)
            db.session.commit()

            return rule

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update(rule):

        try:
            db.session.commit()

            return rule

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(rule):

        try:
            db.session.delete(rule)
            db.session.commit()

            return True

        except Exception:
            db.session.rollback()
            raise