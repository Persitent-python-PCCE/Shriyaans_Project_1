from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)

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

        return render_template(
            "admin_users.html",
            users=users,
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )

    except Exception:

        current_app.logger.exception(
            "Failed to load admin user management."
        )

        flash(
            "Unable to load users.",
            "danger"
        )

        return render_template(
            "admin_users.html",
            users=[],
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )


@admin_user_bp.route(
    "/<int:user_id>/edit",
    methods=["GET", "POST"]
)
def edit_user(user_id):

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    try:

        user = user_service.get_user_by_id(
            user_id
        )

        if not user:
            flash(
                "User not found.",
                "warning"
            )

            return redirect(
                url_for("admin_user.manage_users")
            )

        if request.method == "GET":

            all_users = user_service.get_all_users()

            agents = [
                current_user
                for current_user in all_users
                if current_user.role
                and current_user.role.name == "AGENT"
            ]

            return render_template(
                "edit_user.html",
                user=user,
                users=all_users,
                agents=agents
            )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        role_id = request.form.get(
            "role_id"
        )

        if not name:
            flash(
                "Name is required.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_user.edit_user",
                    user_id=user_id
                )
            )

        if not email:
            flash(
                "Email is required.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_user.edit_user",
                    user_id=user_id
                )
            )

        if not role_id:
            flash(
                "Role is required.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_user.edit_user",
                    user_id=user_id
                )
            )

        try:
            role_id = int(role_id)

        except ValueError:

            flash(
                "Invalid role selected.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_user.edit_user",
                    user_id=user_id
                )
            )

        updated_user = user_service.update_user(
            {
                "id": user_id,
                "name": name,
                "email": email,
                "role_id": role_id
            }
        )

        if not updated_user:
            flash(
                "Unable to update user.",
                "danger"
            )

            return redirect(
                url_for("admin_user.manage_users")
            )

        flash(
            "User updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin_user.manage_users")
        )

    except ValueError as exc:

        flash(
            str(exc),
            "warning"
        )

        return redirect(
            url_for(
                "admin_user.edit_user",
                user_id=user_id
            )
        )

    except Exception:

        current_app.logger.exception(
            "Failed to update user %s.",
            user_id
        )

        flash(
            "Unable to update user.",
            "danger"
        )

        return redirect(
            url_for("admin_user.manage_users")
        )


@admin_user_bp.route(
    "/<int:user_id>/toggle-status",
    methods=["POST"]
)
def toggle_user_status(user_id):

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    try:

        user = user_service.get_user_by_id(
            user_id
        )

        if not user:
            flash(
                "User not found.",
                "warning"
            )

            return redirect(
                url_for("admin_user.manage_users")
            )

        admin_id = session.get("user_id")

        if user.id == admin_id:

            flash(
                "You cannot deactivate your own account.",
                "warning"
            )

            return redirect(
                url_for("admin_user.manage_users")
            )

        new_status = not user.is_active

        updated_user = user_service.update_user(
            {
                "id": user.id,
                "is_active": new_status
            }
        )

        if not updated_user:
            flash(
                "Unable to update user status.",
                "danger"
            )

            return redirect(
                url_for("admin_user.manage_users")
            )

        if new_status:

            flash(
                f"{user.name}'s account has been activated.",
                "success"
            )

        else:

            flash(
                f"{user.name}'s account has been deactivated.",
                "success"
            )

    except Exception:

        current_app.logger.exception(
            "Failed to change status for user %s.",
            user_id
        )

        flash(
            "Unable to update user status.",
            "danger"
        )

    return redirect(
        url_for("admin_user.manage_users")
    )