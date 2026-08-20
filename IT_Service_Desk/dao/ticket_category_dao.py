from config.database import db
from models.ticket_category import TicketCategory
class TicketCategoryDAO:

    @staticmethod
    def create(category):
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def get_by_id(category_id):
        return db.session.get(TicketCategory, category_id)

    @staticmethod
    def get_by_name(name):
        return TicketCategory.query.filter_by(name=name).first()

    @staticmethod
    def get_all():
        return TicketCategory.query.all()

    @staticmethod
    def update(category):
        db.session.commit()
        return category

    @staticmethod
    def delete(category):
        db.session.delete(category)
        db.session.commit()