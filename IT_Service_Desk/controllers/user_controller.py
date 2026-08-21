from flask import Blueprint,request,render_template,redirect,url_for,session,current_app
from services.user_service import UserService
from services.ticket_service import TicketService
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError

user_controller = Blueprint(
    "user_controller",
    __name__
)

user_service = UserService()
ticket_service = TicketService()


@user_controller.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        return render_template(
            "login_page.html"
        )

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:

        return render_template(
            "login_page.html",
            error="Email and password are required."
        )

    try:

        user = user_service.get_user_by_email(
            email
        )

        if not user:

            return render_template(
                "login_page.html",
                error="Invalid email or password."
            )

        if not user.is_active:

            return render_template(
                "login_page.html",
                error="Your account is inactive."
            )

        if not check_password_hash(
            user.password_hash,
            password
        ):

            return render_template(
                "login_page.html",
                error="Invalid email or password."
            )

        if not user.role:

            return render_template(
                "login_page.html",
                error="User role is not configured."
            )

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        session["role"] = user.role.name

        if user.role.name == "EMPLOYEE":

            return redirect(
                url_for(
                    "user_controller.employee_dashboard"
                )
            )

        elif user.role.name == "AGENT":

            return redirect(
                url_for(
                    "user_controller.agent_dashboard"
                )
            )

        elif user.role.name == "ADMIN":

            return redirect(
                url_for(
                    "user_controller.admin_dashboard"
                )
            )

        return render_template(
            "login_page.html",
            error="Invalid user role."
        )

    except Exception:

        current_app.logger.exception(
            "Unexpected error during login."
        )

        return render_template(
            "login_page.html",
            error="Unable to process login. Please try again."
        )


@user_controller.route(
    "/users/add",
    methods=["GET", "POST"]
)
def register():

    if request.method == "GET":

        return render_template(
            "login_page.html",
            register=True
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
        "role_id": request.form.get(
            "role_id"
        )
    }

    try:

        user_service.create_user(
            data
        )

        return redirect(
            url_for(
                "user_controller.login"
            )
        )

    except ValueError as exc:

        return render_template(
            "login_page.html",
            error=str(exc),
            register=True
        )

    except IntegrityError:

        return render_template(
            "login_page.html",
            error=(
                "Database constraint error. "
                "Please check your details."
            ),
            register=True
        )

    except Exception:

        current_app.logger.exception(
            "Unexpected error while creating user."
        )

        return render_template(
            "login_page.html",
            error=(
                "Something went wrong while "
                "creating the account."
            ),
            register=True
        )


@user_controller.route(
    "/employee/dashboard"
)
def employee_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for(
                "user_controller.login"
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
                "user_controller.login"
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

            escalated_tickets=statistics[
                "escalated_tickets"
            ]
        )

    except Exception:

        current_app.logger.exception(
            "Failed to load agent dashboard "
            "for user %s.",
            user_id
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
            escalated_tickets=0,

            error=(
                "Unable to load dashboard "
                "statistics."
            )
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
                "user_controller.login"
            )
        )

    if session.get("role") != "ADMIN":

        return "Unauthorized", 403

    try:

        user_statistics = (
            user_service.get_system_statistics()
        )

        ticket_statistics = (
            ticket_service.get_system_statistics()
        )

        current_app.logger.info(
            "Admin statistics loaded: "
            "users=%s tickets=%s",
            user_statistics,
            ticket_statistics
        )

        return render_template(
            "admin_dashboard.html",

            name=session.get(
                "user_name"
            ),

            email=session.get(
                "user_email"
            ),

            role=session.get(
                "role"
            ),

            user_statistics=user_statistics,

            ticket_statistics=ticket_statistics
        )

    except Exception:

        current_app.logger.exception(
            "Failed to load admin dashboard "
            "statistics for user %s.",
            user_id
        )

        return render_template(
            "admin_dashboard.html",

            name=session.get(
                "user_name"
            ),

            email=session.get(
                "user_email"
            ),

            role=session.get(
                "role"
            ),

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


@user_controller.route(
    "/logout"
)
def logout():

    session.clear()

    return redirect(
        url_for(
            "user_controller.login"
        )
    )