from config.database import db
from models.feedback import Feedback
class FeedbackDAO:
    @staticmethod
    def create(feedback):
        db.session.add(feedback)
        db.session.commit()
        return feedback

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
        return Feedback.query.all()

    @staticmethod
    def update(feedback):
        db.session.commit()
        return feedback