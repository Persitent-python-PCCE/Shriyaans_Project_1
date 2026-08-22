from flask import Blueprint,render_template,redirect,url_for,request,session,flash,current_app

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
            url_for(
                "user_controller.admin_login"
            )
        )

    if session.get("role") != "ADMIN":

        flash(
            "Administrator privileges are required.",
            "danger"
        )

        return redirect(
            url_for(
                "user_controller.admin_login"
            )
        )

    return None


@admin_user_bp.route(
    "/",
    methods=["GET"]
)
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

    except Exception:

        current_app.logger.exception(
            "Failed to load users."
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


@admin_user_bp.route(
    "/create",
    methods=["GET", "POST"]
)
def create_user():

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    if request.method == "GET":

        return render_template(
            "admin_create_user.html"
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    role_name = request.form.get(
        "role_name",
        ""
    ).strip().upper()

    if role_name not in {
        "EMPLOYEE",
        "AGENT"
    }:

        flash(
            "Only Employee or Agent accounts can be created here.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_user.create_user"
            )
        )

    try:

        user_service.create_user(
            {
                "name": name,
                "email": email,
                "password": password,
                "role_name": role_name
            }
        )

        flash(
            f"{role_name.title()} account created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_user.manage_users"
            )
        )

    except ValueError as exc:

        flash(
            str(exc),
            "danger"
        )

        return redirect(
            url_for(
                "admin_user.create_user"
            )
        )

    except Exception:

        current_app.logger.exception(
            "Failed to create %s account.",
            role_name
        )

        flash(
            "Unable to create the account.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_user.create_user"
            )
        )


@admin_user_bp.route(
    "/remove/<int:user_id>",
    methods=["POST"]
)
def remove_user(user_id):

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
                url_for(
                    "admin_user.manage_users"
                )
            )

        if not user.role:

            flash(
                "User role is not configured.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_user.manage_users"
                )
            )

        if user.role.name == "ADMIN":

            flash(
                "Admin accounts cannot be removed here.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_user.manage_users"
                )
            )

        user.is_active = False

        user_service.update_user(
            {
                "id": user.id,
                "is_active": False
            }
        )

        flash(
            f"{user.name} has been removed.",
            "success"
        )

    except Exception:

        current_app.logger.exception(
            "Failed to remove user %s.",
            user_id
        )

        flash(
            "Unable to remove the user.",
            "danger"
        )

    return redirect(
        url_for(
            "admin_user.manage_users"
        )
    )