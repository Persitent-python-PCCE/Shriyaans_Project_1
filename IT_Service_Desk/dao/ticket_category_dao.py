from config.database import db
from models.ticket_category import TicketCategory


class TicketCategoryDAO:

    @staticmethod
    def create(category):
        try:
            db.session.add(category)
            db.session.commit()

            return category

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id(category_id):
        return db.session.get(
            TicketCategory,
            category_id
        )

    @staticmethod
    def get_by_name(name):
        return TicketCategory.query.filter_by(
            name=name
        ).first()

    @staticmethod
    def get_all():
        return TicketCategory.query.order_by(
            TicketCategory.name.asc()
        ).all()

    @staticmethod
    def update(category):
        try:
            db.session.commit()

            return category

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(category):
        try:
            db.session.delete(category)
            db.session.commit()

            return True

        except Exception:
            db.session.rollback()
            raise