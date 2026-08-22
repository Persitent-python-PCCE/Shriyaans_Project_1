from config.database import db
from models.user import User

class UserDAO:
    @staticmethod
    def create(user):
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        return db.session.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_name(name):
        return User.query.filter_by(name=name).first()

    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def update(user):
        try:
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(user):
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_active(user, is_active):
        try:
            user.is_active = bool(is_active)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_role(role_id):
        return User.query.filter_by(role_id=role_id).all()