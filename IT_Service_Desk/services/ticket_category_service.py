from models.ticket_category import TicketCategory

from dao.ticket_category_dao import TicketCategoryDAO
from dao.user_dao import UserDAO


class TicketCategoryService:

    @staticmethod
    def _get_user(user_id):
        user = UserDAO.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        if not user.is_active:
            raise PermissionError(
                "User account is inactive."
            )

        return user

     
    @staticmethod
    def get_all_categories(user_id):
        user = TicketCategoryService._get_user(user_id)

        if user.role.name not in {
            "EMPLOYEE",
            "AGENT",
            "ADMIN"
        }:
            raise PermissionError(
                "Invalid role."
            )

        return TicketCategoryDAO.get_all()

    @staticmethod
    def get_category_by_id(user_id, category_id):
        TicketCategoryService._get_user(user_id)

        category = TicketCategoryDAO.get_by_id(
            category_id
        )

        if not category:
            raise ValueError(
                "Category not found."
            )

        return category

  
    @staticmethod
    def create_category(
        admin_id,
        name,
        description=None
    ):
        admin = TicketCategoryService._get_user(
            admin_id
        )

        if admin.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can create categories."
            )

        if not name or not name.strip():
            raise ValueError(
                "Category name is required."
            )

        name = name.strip()

        existing = TicketCategoryDAO.get_by_name(name)

        if existing:
            raise ValueError(
                "Category already exists."
            )

        category = TicketCategory(
            name=name,
            description=(
                description.strip()
                if description
                else None
            )
        )

        return TicketCategoryDAO.create(
            category
        )

    @staticmethod
    def update_category(
        admin_id,
        category_id,
        name,
        description=None
    ):
        admin = TicketCategoryService._get_user(
            admin_id
        )

        if admin.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can update categories."
            )

        category = TicketCategoryDAO.get_by_id(
            category_id
        )

        if not category:
            raise ValueError(
                "Category not found."
            )

        name = name.strip()

        existing = TicketCategoryDAO.get_by_name(name)

        if existing and existing.id != category_id:
            raise ValueError(
                "Another category already uses this name."
            )

        category.name = name

        category.description = (
            description.strip()
            if description
            else None
        )

        return TicketCategoryDAO.update(
            category
        )

    @staticmethod
    def delete_category(
        admin_id,
        category_id
    ):
        admin = TicketCategoryService._get_user(
            admin_id
        )

        if admin.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can delete categories."
            )

        category = TicketCategoryDAO.get_by_id(
            category_id
        )

        if not category:
            raise ValueError(
                "Category not found."
            )

        # Prevent deletion when tickets use it
        if category.tickets:
            raise ValueError(
                "Cannot delete category because "
                "tickets are using it."
            )

        TicketCategoryDAO.delete(category)

        return True