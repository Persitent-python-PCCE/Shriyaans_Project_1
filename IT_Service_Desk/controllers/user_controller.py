from flask import Blueprint,request,render_template,redirect,url_for,session,current_app
from services.user_service import UserService
from services.ticket_service import TicketService
from werkzeug.security import check_password_hash


user_controller = Blueprint(
    "user_controller",
    __name__
)


user_service = UserService()
ticket_service = TicketService()

JWT_COOKIE_NAME = "access_token"


@user_controller.before_app_request
def _load_jwt_user_into_session():
    if request.path.startswith("/api"):
        return

    if request.path == "/logout":
        return

    token = request.cookies.get(JWT_COOKIE_NAME)

    if not token:
        if any(key in session for key in ("user_id", "role", "user_name", "user_email")):
            session.clear()
        return

    payload = user_service.decode_access_token(token)

    if not payload:
        session.clear()
        return

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        session.clear()
        return

    user = user_service.get_user_by_id(user_id)

    if not user or not user.is_active or not user.role:
        session.clear()
        return
    if payload.get("role") != user.role.name:
        session.clear()
        return

    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email
    session["role"] = user.role.name


def _login_user(user):
    session.clear()
    token = user_service.create_access_token(user)

    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email
    session["role"] = user.role.name

    if user.role.name == "EMPLOYEE":
        response = redirect(
            url_for("user_controller.employee_dashboard")
        )
    elif user.role.name == "AGENT":
        response = redirect(
            url_for("user_controller.agent_dashboard")
        )
    elif user.role.name == "ADMIN":
        response = redirect(
            url_for("user_controller.admin_dashboard")
        )
    else:
        session.clear()
        return redirect(
            url_for("user_controller.employee_login")
        )

    expires_minutes = current_app.config.get(
        "JWT_EXPIRES_MINUTES",
        1
    )

    response.set_cookie(
        JWT_COOKIE_NAME,
        token,
        max_age=int(expires_minutes * 60),
        httponly=True,
        secure=current_app.config.get("JWT_COOKIE_SECURE", False),
        samesite="Lax",
        path="/"
    )

    return response


def _process_login(role_name, template_name):

    if request.method == "GET":

        return render_template(
            template_name
        )

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:

        return render_template(
            template_name,
            error="Email and password are required."
        )

    try:

        user = user_service.get_user_by_email(
            email
        )

        if not user:

            return render_template(
                template_name,
                error="Invalid email or password."
            )

        if not user.is_active:

            return render_template(
                template_name,
                error="Your account is inactive."
            )

        if not user.role:

            return render_template(
                template_name,
                error="User role is not configured."
            )

        if user.role.name != role_name:

            return render_template(
                template_name,
                error=(
                    f"This login is only for "
                    f"{role_name.lower()} accounts."
                )
            )

        if not check_password_hash(
            user.password_hash,
            password
        ):

            return render_template(
                template_name,
                error="Invalid email or password."
            )

        return _login_user(user)

    except Exception:

        current_app.logger.exception(
            "Login failed for role %s.",
            role_name
        )

        return render_template(
            template_name,
            error="Unable to process login. Please try again."
        )


@user_controller.route(
    "/employee/login",
    methods=["GET", "POST"]
)
def employee_login():

    return _process_login(
        "EMPLOYEE",
        "employee_login.html"
    )


@user_controller.route(
    "/agent/login",
    methods=["GET", "POST"]
)
def agent_login():

    return _process_login(
        "AGENT",
        "agent_login.html"
    )


@user_controller.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    return _process_login(
        "ADMIN",
        "admin_login.html"
    )


@user_controller.route(
    "/admin/register",
    methods=["GET", "POST"]
)
def admin_register():

    users = user_service.get_all_users()

    if request.method == "GET":

        return render_template(
            "admin_register.html"
        )

    data = {
        "name": request.form.get(
            "name",
            ""
        ),

        "email": request.form.get(
            "email",
            ""
        ),

        "password": request.form.get(
            "password",
            ""
        ),
        "confirm_password":request.form.get(
            "confirm_password",""
        ),

        "role_name": "ADMIN"
    }

    try:

        user_service.create_user(
            data
        )

        return redirect(
            url_for(
                "user_controller.admin_login"
            )
        )

    except ValueError as exc:

        return render_template(
            "admin_register.html",
            error=str(exc)
        )

    except Exception:

        current_app.logger.exception(
            "Failed to create initial admin."
        )

        return render_template(
            "admin_register.html",
            error="Unable to create admin account."
        )


@user_controller.route(
    "/employee/dashboard"
)
def employee_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for(
                "user_controller.employee_login"
            )
        )

    if session.get("role") != "EMPLOYEE":

        return "Unauthorized", 403

    return render_template(
        "employee_dashboard.html",
        name=session.get("user_name"),
        email=session.get("user_email"),
        role=session.get("role")
    )


@user_controller.route(
    "/agent/dashboard"
)
def agent_dashboard():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return redirect(
            url_for(
                "user_controller.agent_login"
            )
        )

    if session.get("role") != "AGENT":

        return "Unauthorized", 403

    try:

        statistics = (
            ticket_service.get_agent_statistics(
                agent_id=user_id
            )
        )

        return render_template(
            "agent_dashboard.html",

            name=session.get(
                "user_name"
            ),

            email=session.get(
                "user_email"
            ),

            role=session.get(
                "role"
            ),

            assigned_tickets=statistics[
                "assigned_tickets"
            ],

            in_progress_tickets=statistics[
                "in_progress_tickets"
            ],

            resolved_tickets=statistics[
                "resolved_tickets"
            ],

            closed_tickets=statistics[
                "closed_tickets"
            ]
        )

    except Exception:

        current_app.logger.exception(
            "Failed to load agent dashboard."
        )

        return render_template(
            "agent_dashboard.html",

            name=session.get(
                "user_name"
            ),

            email=session.get(
                "user_email"
            ),

            role=session.get(
                "role"
            ),

            assigned_tickets=0,
            in_progress_tickets=0,
            resolved_tickets=0,
            closed_tickets=0,

            error="Unable to load dashboard statistics."
        )
    
@user_controller.route(
    "/admin/dashboard"
)
def admin_dashboard():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return redirect(
            url_for(
                "user_controller.admin_login"
            )
        )

    if session.get("role") != "ADMIN":

        return "Unauthorized", 403

    try:

        current_user = user_service.get_user_by_id(
            user_id
        )

        if not current_user:

            session.clear()

            return redirect(
                url_for(
                    "user_controller.admin_login"
                )
            )

        user_statistics = (
            user_service.get_system_statistics()
        )

        ticket_statistics = (
            ticket_service.get_system_statistics()
        )

        return render_template(
            "admin_dashboard.html",

            name=current_user.name,

            email=current_user.email,

            role=(
                current_user.role.name
                if current_user.role
                else "ADMIN"
            ),

            status=(
                "Active"
                if current_user.is_active
                else "Inactive"
            ),

            user_statistics=user_statistics,

            ticket_statistics=ticket_statistics
        )

    except Exception:

        current_app.logger.exception(
            "Failed to load admin dashboard."
        )

        return render_template(
            "admin_dashboard.html",

            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role"),
            status="Active",

            user_statistics={
                "total_users": 0,
                "total_employees": 0,
                "total_agents": 0,
                "total_admins": 0,
                "active_users": 0,
                "inactive_users": 0
            },

            ticket_statistics={
                "total_tickets": 0,
                "open_tickets": 0,
                "assigned_tickets": 0,
                "in_progress_tickets": 0,
                "resolved_tickets": 0,
                "closed_tickets": 0,
                "escalated_tickets": 0
            },

            error="Unable to load system statistics."
        )


@user_controller.route("/logout")
def logout():

    role = request.args.get("role") or session.get("role")
    session.clear()

    if role == "ADMIN":
        response = redirect(
            url_for("user_controller.admin_login")
        )
    elif role == "AGENT":
        response = redirect(
            url_for("user_controller.agent_login")
        )
    
    else:
        response = redirect(
            url_for("user_controller.employee_login")
        )

    response.delete_cookie(
        JWT_COOKIE_NAME,
        path="/"
    )

    return response


@user_controller.route("/")
def login():

    return redirect(
        url_for(
            "user_controller.employee_login"
        )
    )