from models.role import Role
from config.database import db
class RoleDAO:

    @staticmethod
    def get_by_id(role_id):
        return Role.query.get(role_id)

    @staticmethod
    def get_by_name(name):
        return Role.query.filter_by(name=name).first()

    @staticmethod
    def get_all():
        return Role.query.all()

    @staticmethod
    def create(role):
        db.session.add(role)
        db.session.commit()
        return role