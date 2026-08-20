from config.database import db
from models.feedback import Feedback


class FeedbackDAO:

    @staticmethod
    def create(feedback):

        try:
            db.session.add(feedback)
            db.session.commit()

            return feedback

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id(feedback_id):
        return db.session.get(
            Feedback,
            feedback_id
        )

    @staticmethod
    def get_by_ticket(ticket_id):
        return Feedback.query.filter_by(
            ticket_id=ticket_id
        ).first()

    @staticmethod
    def get_all():
        return Feedback.query.order_by(
            Feedback.created_at.desc()
        ).all()

    @staticmethod
    def update(feedback):

        try:
            db.session.commit()

            return feedback

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(feedback):

        try:
            db.session.delete(feedback)
            db.session.commit()

            return True

        except Exception:
            db.session.rollback()
            raise