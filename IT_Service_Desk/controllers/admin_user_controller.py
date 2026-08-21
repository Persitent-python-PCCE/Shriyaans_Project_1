from flask import Blueprint,render_template,redirect,url_for,session,flash,current_app
from services.user_service import UserService


admin_user_bp = Blueprint(
    "admin_user",
    __name__,
    url_prefix="/admin/users"
)

user_service = UserService()


def _require_admin():

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "warning"
        )

        return redirect(
            url_for("user_controller.login")
        )

    if session.get("role") != "ADMIN":

        flash(
            "Access denied. Administrator privileges are required.",
            "danger"
        )

        return redirect(
            url_for("user_controller.login")
        )

    return None


@admin_user_bp.route("/", methods=["GET"])
def manage_users():

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    try:

        users = user_service.get_all_users()

        employees = [
            user
            for user in users
            if user.role
            and user.role.name == "EMPLOYEE"
        ]

        agents = [
            user
            for user in users
            if user.role
            and user.role.name == "AGENT"
        ]

        admins = [
            user
            for user in users
            if user.role
            and user.role.name == "ADMIN"
        ]

        return render_template(
            "admin_users.html",
            users=users,
            employees=employees,
            agents=agents,
            admins=admins,
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )

    except PermissionError as exc:

        flash(
            str(exc),
            "danger"
        )

        return redirect(
            url_for("user_controller.login")
        )

    except Exception:

        current_app.logger.exception(
            "Failed to load admin users."
        )

        flash(
            "Unable to load users.",
            "danger"
        )

        return render_template(
            "admin_users.html",
            users=[],
            employees=[],
            agents=[],
            admins=[],
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )