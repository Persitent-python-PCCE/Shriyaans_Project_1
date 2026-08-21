from dataclasses import asdict

from models.user import User

from dao.user_dao import UserDAO

from werkzeug.security import generate_password_hash

from utils.email_v import verify_email
from utils.password_v import validate_password


class UserService:

    @staticmethod
    def create_user(data):

        email = data["email"].strip().lower()
        password = data["password"]

        if not verify_email(email):
            raise ValueError(
                "Invalid email format."
            )

        if not validate_password(password):
            raise ValueError(
                "Password must be at least 8 characters "
                "and contain letters, digits and special characters."
            )

        existing_user = UserDAO.get_by_email(email)

        if existing_user:
            raise ValueError(
                "Email already registered."
            )

        hashed_password = generate_password_hash(
            password
        )

        user = User(
            name=data["name"].strip(),
            email=email,
            password_hash=hashed_password,
            role_id=int(data["role_id"]),
            is_active=True
        )

        return UserDAO.create(user)

    @staticmethod
    def get_user_by_email(email):

        if not email:
            return None

        return UserDAO.get_by_email(
            email.strip().lower()
        )

    @staticmethod
    def get_user_by_id(user_id):

        if not user_id:
            return None

        return UserDAO.get_by_id(
            user_id
        )

    @staticmethod
    def get_all_users():

        return UserDAO.get_all()

    @staticmethod
    def update_user(data):

        user_id = data.get("id")

        if not user_id:
            raise ValueError(
                "User ID is required."
            )

        user = UserDAO.get_by_id(
            user_id
        )

        if not user:
            raise ValueError(
                "User not found."
            )

        if "name" in data:

            name = data["name"].strip()

            if not name:
                raise ValueError(
                    "Name cannot be empty."
                )

            user.name = name

        if "email" in data:

            email = data["email"].strip().lower()

            if not verify_email(email):
                raise ValueError(
                    "Invalid email format."
                )

            existing_user = UserDAO.get_by_email(
                email
            )

            if existing_user and existing_user.id != user.id:
                raise ValueError(
                    "Email already registered."
                )

            user.email = email

        if "role_id" in data:

            if data["role_id"] is None:
                raise ValueError(
                    "Role ID is required."
                )

            user.role_id = int(
                data["role_id"]
            )

        if "is_active" in data:

            user.is_active = bool(
                data["is_active"]
            )

        return UserDAO.update(
            user
        )

    @staticmethod
    def delete_user(email):

        user = UserDAO.get_by_email(
            email.strip().lower()
        )

        if not user:
            raise ValueError(
                "User not found."
            )

        return UserDAO.delete(
            user
        )

    @staticmethod
    def get_system_statistics():

        users = UserDAO.get_all()

        total_users = len(users)

        total_employees = 0
        total_agents = 0
        total_admins = 0
        active_users = 0
        inactive_users = 0

        for user in users:

            if user.role:

                if user.role.name == "EMPLOYEE":
                    total_employees += 1

                elif user.role.name == "AGENT":
                    total_agents += 1

                elif user.role.name == "ADMIN":
                    total_admins += 1

            if user.is_active:
                active_users += 1
            else:
                inactive_users += 1

        return {
            "total_users": total_users,
            "total_employees": total_employees,
            "total_agents": total_agents,
            "total_admins": total_admins,
            "active_users": active_users,
            "inactive_users": inactive_users
        }