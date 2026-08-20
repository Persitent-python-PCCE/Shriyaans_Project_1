from config.database import db
from models.role import Role
class RoleDAO:
    @staticmethod
    def get_by_id(role_id):
        return db.session.get(
            Role,
            role_id
        )
    @staticmethod
    def get_by_name(name):
        return Role.query.filter_by(
            name=name
        ).first()

    @staticmethod
    def get_all():
        return Role.query.order_by(
            Role.id.asc()
        ).all()

    @staticmethod
    def create(role):

        try:
            db.session.add(role)
            db.session.commit()

            return role

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update(role):

        try:
            db.session.commit()

            return role

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(role):

        try:
            db.session.delete(role)
            db.session.commit()

            return True

        except Exception:
            db.session.rollback()
            raise