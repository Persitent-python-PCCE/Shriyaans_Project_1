import re

from werkzeug.security import generate_password_hash

from dao.user_dao import UserDAO
from dao.role_dao import RoleDAO
from models.user import User


def verify_email(email):

    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(
        pattern,
        email
    ) is not None


def validate_password(password):

    if not password:
        return False

    if len(password) < 8:
        return False

    has_letter = any(
        character.isalpha()
        for character in password
    )

    has_digit = any(
        character.isdigit()
        for character in password
    )

    has_special = any(
        not character.isalnum()
        for character in password
    )

    return (
        has_letter
        and has_digit
        and has_special
    )


class UserService:

    def get_all_users(self):

        return UserDAO.get_all()

    def get_user_by_id(self, user_id):

        return UserDAO.get_by_id(
            user_id
        )

    def get_user_by_email(self, email):

        if not email:
            return None

        email = email.strip().lower()

        return UserDAO.get_by_email(
            email
        )

    def create_user(self, data):

        name = data.get(
            "name",
            ""
        ).strip()

        email = data.get(
            "email",
            ""
        ).strip().lower()

        password = data.get(
            "password",
            ""
        )

        role_name = data.get(
            "role_name",
            ""
        ).strip().upper()

        if not name:

            raise ValueError(
                "Name is required."
            )

        if not email:

            raise ValueError(
                "Email is required."
            )

        if not verify_email(email):

            raise ValueError(
                "Invalid email format."
            )

        if not password:

            raise ValueError(
                "Password is required."
            )

        if not validate_password(password):

            raise ValueError(
                "Password must be at least 8 characters "
                "and contain letters, digits and special characters."
            )

        if not role_name:

            raise ValueError(
                "User role is required."
            )

        allowed_roles = {
            "EMPLOYEE",
            "AGENT",
            "ADMIN"
        }

        if role_name not in allowed_roles:

            raise ValueError(
                "Invalid user role."
            )

        existing_user = UserDAO.get_by_email(
            email
        )

        if existing_user:

            raise ValueError(
                "Email already registered."
            )

        role = RoleDAO.get_by_name(
            role_name
        )

        if not role:

            raise ValueError(
                f"Role '{role_name}' does not exist."
            )

        password_hash = generate_password_hash(
            password
        )

        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role_id=role.id,
            is_active=True
        )

        return UserDAO.create(
            user
        )

    def update_user(self, data):

        user_id = data.get(
            "id"
        )

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

            name = data.get(
                "name",
                ""
            ).strip()

            if not name:

                raise ValueError(
                    "Name cannot be empty."
                )

            user.name = name

        if "email" in data:

            email = data.get(
                "email",
                ""
            ).strip().lower()

            if not email:

                raise ValueError(
                    "Email cannot be empty."
                )

            if not verify_email(email):

                raise ValueError(
                    "Invalid email format."
                )

            existing_user = UserDAO.get_by_email(
                email
            )

            if (
                existing_user
                and existing_user.id != user.id
            ):

                raise ValueError(
                    "Email already registered."
                )

            user.email = email

        if "password" in data:

            password = data.get(
                "password"
            )

            if password:

                if not validate_password(
                    password
                ):

                    raise ValueError(
                        "Password must be at least 8 characters "
                        "and contain letters, digits and special characters."
                    )

                user.password_hash = (
                    generate_password_hash(
                        password
                    )
                )

        if "role_name" in data:

            role_name = data.get(
                "role_name",
                ""
            ).strip().upper()

            allowed_roles = {
                "EMPLOYEE",
                "AGENT",
                "ADMIN"
            }

            if role_name not in allowed_roles:

                raise ValueError(
                    "Invalid user role."
                )

            role = RoleDAO.get_by_name(
                role_name
            )

            if not role:

                raise ValueError(
                    f"Role '{role_name}' does not exist."
                )

            user.role_id = role.id

        if "is_active" in data:

            user.is_active = bool(
                data.get(
                    "is_active"
                )
            )

        return UserDAO.update(
            user
        )

    def deactivate_user(self, user_id):

        user = UserDAO.get_by_id(
            user_id
        )

        if not user:

            raise ValueError(
                "User not found."
            )

        if user.role:

            if user.role.name == "ADMIN":

                raise ValueError(
                    "Admin accounts cannot be deactivated."
                )

        user.is_active = False

        return UserDAO.update(
            user
        )

    def activate_user(self, user_id):

        user = UserDAO.get_by_id(
            user_id
        )

        if not user:

            raise ValueError(
                "User not found."
            )

        user.is_active = True

        return UserDAO.update(
            user
        )

    def get_system_statistics(self):

        users = UserDAO.get_all()

        total_users = len(users)

        total_employees = 0
        total_agents = 0
        total_admins = 0

        active_users = 0
        inactive_users = 0

        for user in users:

            if user.is_active:

                active_users += 1

            else:

                inactive_users += 1

            if not user.role:
                continue

            role_name = user.role.name

            if role_name == "EMPLOYEE":

                total_employees += 1

            elif role_name == "AGENT":

                total_agents += 1

            elif role_name == "ADMIN":

                total_admins += 1

        return {
            "total_users": total_users,
            "total_employees": total_employees,
            "total_agents": total_agents,
            "total_admins": total_admins,
            "active_users": active_users,
            "inactive_users": inactive_users
        }