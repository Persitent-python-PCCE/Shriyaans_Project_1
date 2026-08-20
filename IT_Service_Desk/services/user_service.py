from models.user import User
from dao.user_dao import UserDAO
from werkzeug.security import check_password_hash, generate_password_hash
from utils.password_v import validate_password
from utils.email_v import verify_email
class UserService:
    def __init__(self):
        self.user_dao = UserDAO()

    def get_all_users(self):
        users = self.user_dao.get_all()
        return users

    def get_user_by_name(self, name):
        user = self.user_dao.get_by_name(name)
        return user

    def get_user_by_email(self, email):
        user_email = self.user_dao.get_by_email(email=email)
        return user_email

    def get_user_by_id(self, user_id):
        user_id = self.user_dao.get_by_id(user_id=user_id)
        return user_id

    def get_user_by_role(self, role_id):
        user_role = self.user_dao.get_by_role(role_id=role_id)
        return user_role
    
    def update_user(self, data):
        user = self.user_dao.get_by_id(data["id"])
        if not user:
            return None
        if "name" in data:
            user.name = data["name"]
        if "email" in data:
            user.email = data["email"]
        if "role_id" in data:
            user.role_id = data["role_id"]
        if "is_active" in data:
            user.is_active = data["is_active"]
        usr = self.user_dao.update(user)
        return usr

    def delete_user(self, email):
        user = self.user_dao.get_by_email(email=email)
        if not user:
            return False
        self.user_dao.delete(user)
        return True

    def create_user(self, data):
        exist = self.user_dao.get_by_email(data["email"])

        v_password=validate_password(data["password"])

        if not v_password:
            raise ValueError("Password must be at least 8 characters long "
            "and contain a digit and special character.")
        
        v_email=verify_email(data["email"])
        if not v_email:
            raise ValueError("Invalid Email format.")
        if exist:
            raise ValueError("User already exists.")
        password_hash = generate_password_hash(
            data["password"]
        )
        user = User(
            name=data["name"],
            email=data["email"],
            password_hash=password_hash,
            role_id=data["role_id"]
        )
        usr = self.user_dao.create(user)
        return usr

    @staticmethod
    def get_system_statistics():

        users = UserDAO.get_all()

        total_users = len(users)

        total_employees = sum(
            1
            for user in users
            if user.role and user.role.name == "EMPLOYEE"
        )

        total_agents = sum(
            1
            for user in users
            if user.role and user.role.name == "AGENT"
        )

        total_admins = sum(
            1
            for user in users
            if user.role and user.role.name == "ADMIN"
        )

        active_users = sum(
            1
            for user in users
            if user.is_active
        )

        inactive_users = sum(
            1
            for user in users
            if not user.is_active
        )

        return {
            "total_users": total_users,
            "total_employees": total_employees,
            "total_agents": total_agents,
            "total_admins": total_admins,
            "active_users": active_users,
            "inactive_users": inactive_users
        }