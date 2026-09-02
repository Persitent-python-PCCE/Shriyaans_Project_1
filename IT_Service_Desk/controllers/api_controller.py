from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.security import check_password_hash
from services.user_service import UserService
from services.ticket_service import TicketService
from services.ticket_comment_service import TicketCommentService
from services.ticket_history_service import TicketHistoryService
from services.ticket_category_service import TicketCategoryService
from services.sla_rule_service import SLARuleService
from services.feedback_service import FeedbackService

api_bp = Blueprint("api", __name__, url_prefix="/api")

ticket_service = TicketService()
comment_service = TicketCommentService()
category_service = TicketCategoryService()
history_service = TicketHistoryService()
sla_service = SLARuleService()
feedback_service = FeedbackService()
user_service = UserService()


def _request_data():
    data = request.get_json(silent=True)

    if isinstance(data, dict):
        return data

    if request.form:
        return request.form.to_dict()

    return {}


def _user_to_dict(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "is_active": bool(user.is_active),
        "created_at": _iso(user.created_at),
    }


def _set_login_session(user):
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email
    session["role"] = user.role.name if user.role else None


def _api_login(role_name=None, use_jwt=False):
    data = _request_data()

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return _error("Email and password are required.", 400)

    try:
        user = user_service.get_user_by_email(email)

        if not user:
            return _error("Invalid email or password.", 401)

        if not user.is_active:
            return _error("Your account is inactive.", 403)

        if not user.role:
            return _error("User role is not configured.", 403)

        actual_role = user.role.name

        if role_name and actual_role != role_name:
            return _error(
                f"This login is only for {role_name.lower()} accounts.",
                403,
            )

        if not check_password_hash(user.password_hash, password):
            return _error("Invalid email or password.", 401)

        response_data = {
            "message": "Login successful.",
            "user": _user_to_dict(user),
        }

        if use_jwt:
            token = user_service.create_access_token(user)

            expires_minutes = int(
                current_app.config.get(
                    "JWT_EXPIRES_MINUTES",
                    15,
                )
            )

            response_data["token"] = token
            response_data["token_type"] = "Bearer"
            response_data["expires_in"] = expires_minutes * 60

        _set_login_session(user)

        return jsonify(response_data), 200

    except Exception:
        return _error("Unable to process login.", 500)


def _api_register(role_name=None):
    data = dict(_request_data())

    requested_role = str(
        data.get(
            "role_name",
            data.get("role", role_name or "EMPLOYEE"),
        )
    ).strip().upper()

    if role_name and requested_role != role_name:
        return _error(
            f"This endpoint is only for {role_name.lower()} registration.",
            400,
        )

    allowed_roles = {"EMPLOYEE", "AGENT", "ADMIN"}

    if requested_role not in allowed_roles:
        return _error("Invalid user role.", 400)

    if requested_role == "AGENT":
        user_id, user_role, auth_error = _current_user()

        if auth_error:
            return _error(
                "Only administrators can register agent accounts.",
                403,
            )

        if user_role != "ADMIN":
            return _error(
                "Only administrators can register agent accounts.",
                403,
            )

    if requested_role == "ADMIN":
        try:
            existing_admins = [
                user
                for user in user_service.get_all_users()
                if user.role and user.role.name == "ADMIN"
            ]
        except Exception:
            return _error(
                "Unable to check administrator accounts.",
                500,
            )

        if existing_admins:
            user_id, user_role, auth_error = _current_user()

            if auth_error:
                return _error(
                    "Admin registration is closed because an administrator already exists.",
                    403,
                )

            if user_role != "ADMIN":
                return _error(
                    "Admin registration is closed because an administrator already exists.",
                    403,
                )

    data["role_name"] = requested_role

    try:
        user = user_service.create_user(data)

        return jsonify({
            "message": "Registration successful.",
            "user": _user_to_dict(user),
        }), 201

    except ValueError as exc:
        return _error(str(exc), 400)

    except Exception:
        return _error(
            "Unable to register user.",
            500,
        )


def _current_user():
    authorization = request.headers.get("Authorization", "").strip()

    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

        if token:
            payload = user_service.decode_access_token(token)

            if payload:
                try:
                    user_id = int(payload["sub"])
                    user_role = payload.get("role")

                    if user_role:
                        user_role = str(user_role).upper()

                    return user_id, user_role, None

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    pass

    user_id = session.get("user_id")

    if user_id:
        user_role = session.get("role")

        if user_role:
            user_role = str(user_role).upper()

        return user_id, user_role, None

    return None, None, (
        jsonify({
            "error": "Authentication required.",
        }),
        401,
    )


def _error(message, status=400):
    return jsonify({
        "error": message,
    }), status


def _iso(value):
    return value.isoformat() if value else None


def _ticket_to_dict(ticket):
    assignments = []

    for assignment in ticket.assignments:
        assignments.append({
            "id": assignment.id,
            "agent_id": assignment.agent_id,
            "agent_name": (
                assignment.agent.name
                if assignment.agent
                else None
            ),
            "assigned_at": _iso(
                assignment.assigned_at
            ),
        })

    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "category_id": ticket.category_id,
        "category": (
            ticket.category.name
            if ticket.category
            else None
        ),
        "created_by": ticket.created_by,
        "creator": (
            ticket.creator.name
            if ticket.creator
            else None
        ),
        "priority": ticket.priority,
        "severity": ticket.severity,
        "status": ticket.status,
        "due_date": _iso(ticket.due_date),
        "resolved_at": _iso(ticket.resolved_at),
        "closed_at": _iso(ticket.closed_at),
        "is_escalated": bool(ticket.is_escalated),
        "created_at": _iso(ticket.created_at),
        "updated_at": _iso(ticket.updated_at),
        "attachments": [
            {
                "id": attachment.id,
                "original_filename": attachment.original_filename,
                "file_size": attachment.file_size,
                "file_type": attachment.file_type,
                "uploaded_by": attachment.uploaded_by,
                "uploaded_at": _iso(
                    attachment.uploaded_at
                ),
            }
            for attachment in ticket.attachments
        ],
        "assignments": assignments,
        "feedback": (
            {
                "id": ticket.feedback.id,
                "rating": ticket.feedback.rating,
                "comment": ticket.feedback.comment,
                "created_at": _iso(
                    ticket.feedback.created_at
                ),
            }
            if ticket.feedback
            else None
        ),
    }


@api_bp.route("/login", methods=["POST"])
def api_login():
    return _api_login()


@api_bp.route("/employee/login", methods=["POST"])
def api_employee_login():
    return _api_login(
        "EMPLOYEE",
        use_jwt=True,
    )


@api_bp.route("/agent/login", methods=["POST"])
def api_agent_login():
    return _api_login(
        "AGENT",
        use_jwt=True,
    )


@api_bp.route("/admin/login", methods=["POST"])
def api_admin_login():
    return _api_login(
        "ADMIN",
        use_jwt=True,
    )


@api_bp.route("/register", methods=["POST"])
def api_register():
    return _api_register()


@api_bp.route("/employee/register", methods=["POST"])
def api_employee_register():
    return _api_register("EMPLOYEE")


@api_bp.route("/agent/register", methods=["POST"])
def api_agent_register():
    return _api_register("AGENT")


@api_bp.route("/admin/register", methods=["POST"])
def api_admin_register():
    return _api_register("ADMIN")


@api_bp.route("/tickets", methods=["GET", "POST"])
def tickets():
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    try:
        if request.method == "GET":
            status = request.args.get("status")
            priority = request.args.get("priority")
            category_id = request.args.get("category_id")

            tickets = ticket_service.search_tickets(
                user_id=user_id,
                title=request.args.get("title"),
                status=(
                    status.strip().upper()
                    if status
                    else None
                ),
                priority=(
                    priority.strip().upper()
                    if priority
                    else None
                ),
                category_id=(
                    int(category_id)
                    if category_id
                    else None
                ),
            )

            return jsonify({
                "count": len(tickets),
                "tickets": [
                    _ticket_to_dict(ticket)
                    for ticket in tickets
                ],
            }), 200

        data = _request_data()
        category_id = data.get("category_id")

        if category_id is None:
            return _error(
                "category_id is required.",
                400,
            )

        ticket = ticket_service.create_ticket(
            user_id=user_id,
            title=data.get("title"),
            description=data.get("description"),
            category_id=int(category_id),
            priority=data.get(
                "priority",
                "MEDIUM",
            ),
            severity=data.get(
                "severity",
                "MODERATE",
            ),
        )

        return jsonify(
            _ticket_to_dict(ticket)
        ), 201

    except (ValueError, TypeError) as exc:
        return _error(
            str(exc),
            400,
        )

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except Exception:
        return _error(
            "Unable to process ticket request.",
            500,
        )


@api_bp.route(
    "/tickets/<int:ticket_id>",
    methods=["GET"],
)
def ticket_detail(ticket_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    try:
        ticket = ticket_service.get_ticket_by_id(
            user_id,
            ticket_id,
        )

        return jsonify(
            _ticket_to_dict(ticket)
        ), 200

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            404,
        )

    except Exception:
        return _error(
            "Unable to load ticket.",
            500,
        )


@api_bp.route(
    "/tickets/<int:ticket_id>/status",
    methods=["PATCH", "PUT"],
)
def ticket_status(ticket_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    data = _request_data()

    try:
        ticket = ticket_service.update_status(
            user_id=user_id,
            ticket_id=ticket_id,
            new_status=data.get(
                "status",
                "",
            ),
        )

        return jsonify(
            _ticket_to_dict(ticket)
        ), 200

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            400,
        )

    except Exception:
        return _error(
            "Unable to update ticket status.",
            500,
        )


@api_bp.route(
    "/tickets/<int:ticket_id>/escalate",
    methods=["POST"],
)
def escalate_ticket(ticket_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    data = _request_data()

    try:
        ticket = ticket_service.escalate_ticket(
            user_id=user_id,
            ticket_id=ticket_id,
            reason=data.get("reason"),
        )

        return jsonify(
            _ticket_to_dict(ticket)
        ), 200

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            400,
        )

    except Exception:
        return _error(
            "Unable to escalate ticket.",
            500,
        )


@api_bp.route(
    "/tickets/<int:ticket_id>/comments",
    methods=["GET", "POST"],
)
def ticket_comments(ticket_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    try:
        ticket_service.get_ticket_by_id(
            user_id,
            ticket_id,
        )

        if request.method == "GET":
            comments = comment_service.get_comments(
                user_id,
                ticket_id,
            )

            return jsonify({
                "comments": [
                    {
                        "id": comment.id,
                        "user_id": comment.user_id,
                        "user_name": (
                            comment.user.name
                            if comment.user
                            else None
                        ),
                        "comment": comment.comment,
                        "created_at": _iso(
                            comment.created_at
                        ),
                    }
                    for comment in comments
                ],
            }), 200

        data = _request_data()

        comment = comment_service.add_comment(
            user_id=user_id,
            ticket_id=ticket_id,
            comment_text=data.get(
                "comment",
                "",
            ),
        )

        return jsonify({
            "id": comment.id,
            "ticket_id": comment.ticket_id,
            "user_id": comment.user_id,
            "comment": comment.comment,
            "created_at": _iso(
                comment.created_at
            ),
        }), 201

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            400,
        )

    except Exception:
        return _error(
            "Unable to process comments.",
            500,
        )


@api_bp.route(
    "/tickets/<int:ticket_id>/history",
    methods=["GET"],
)
def ticket_history(ticket_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    try:
        history = history_service.get_ticket_history(
            user_id,
            ticket_id,
        )

        return jsonify({
            "history": [
                {
                    "id": entry.id,
                    "action": entry.action,
                    "old_value": entry.old_value,
                    "new_value": entry.new_value,
                    "description": entry.description,
                    "user_id": entry.user_id,
                    "user_name": (
                        entry.user.name
                        if entry.user
                        else None
                    ),
                    "created_at": _iso(
                        entry.created_at
                    ),
                }
                for entry in history
            ],
        }), 200

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            404,
        )

    except Exception:
        return _error(
            "Unable to load ticket history.",
            500,
        )


@api_bp.route(
    "/tickets/<int:ticket_id>/feedback",
    methods=["GET", "POST"],
)
def ticket_feedback(ticket_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    try:
        if request.method == "GET":
            feedback = feedback_service.get_feedback(
                user_id,
                ticket_id,
            )

            return jsonify({
                "feedback": (
                    {
                        "id": feedback.id,
                        "ticket_id": feedback.ticket_id,
                        "user_id": feedback.user_id,
                        "rating": feedback.rating,
                        "comment": feedback.comment,
                        "created_at": _iso(
                            feedback.created_at
                        ),
                    }
                    if feedback
                    else None
                ),
            }), 200

        data = _request_data()

        feedback = feedback_service.submit_feedback(
            user_id=user_id,
            ticket_id=ticket_id,
            rating=data.get("rating"),
            comment=data.get(
                "comment",
                "",
            ),
        )

        return jsonify({
            "id": feedback.id,
            "ticket_id": feedback.ticket_id,
            "user_id": feedback.user_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": _iso(
                feedback.created_at
            ),
        }), 201

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            400,
        )

    except Exception:
        return _error(
            "Unable to process feedback.",
            500,
        )


@api_bp.route(
    "/categories",
    methods=["GET"],
)
def categories():
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    try:
        categories = category_service.get_all_categories(
            user_id
        )

        return jsonify({
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                }
                for category in categories
            ],
        }), 200

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except Exception:
        return _error(
            "Unable to load categories.",
            500,
        )


@api_bp.route(
    "/sla-rules",
    methods=["GET", "POST"],
)
def sla_rules():
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    if user_role != "ADMIN":
        return _error(
            "Only administrators can access SLA rules.",
            403,
        )

    try:
        if request.method == "GET":
            sla_service.ensure_default_rules()

            rules = sla_service.get_all_rules(
                admin_id=user_id
            )

            return jsonify({
                "sla_rules": [
                    {
                        "id": rule.id,
                        "priority": rule.priority,
                        "response_time_minutes": (
                            rule.response_time_minutes
                        ),
                        "resolution_time_minutes": (
                            rule.resolution_time_minutes
                        ),
                        "created_at": _iso(
                            rule.created_at
                        ),
                    }
                    for rule in rules
                ],
            }), 200

        data = _request_data()

        rule = sla_service.create_rule(
            admin_id=user_id,
            priority=data.get("priority"),
            response_time_minutes=data.get(
                "response_time_minutes"
            ),
            resolution_time_minutes=data.get(
                "resolution_time_minutes"
            ),
        )

        return jsonify({
            "id": rule.id,
            "priority": rule.priority,
            "response_time_minutes": (
                rule.response_time_minutes
            ),
            "resolution_time_minutes": (
                rule.resolution_time_minutes
            ),
            "created_at": _iso(
                rule.created_at
            ),
        }), 201

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            400,
        )

    except Exception:
        return _error(
            "Unable to process SLA rules.",
            500,
        )


@api_bp.route(
    "/sla-rules/<int:rule_id>",
    methods=["PATCH", "PUT", "DELETE"],
)
def sla_rule_detail(rule_id):
    user_id, user_role, auth_error = _current_user()

    if auth_error:
        return auth_error

    if user_role != "ADMIN":
        return _error(
            "Only administrators can manage SLA rules.",
            403,
        )

    try:
        if request.method == "DELETE":
            sla_service.delete_rule(
                user_id,
                rule_id,
            )

            return jsonify({
                "message": "SLA rule deleted.",
            }), 200

        data = _request_data()

        rule = sla_service.update_rule(
            admin_id=user_id,
            rule_id=rule_id,
            response_time_minutes=data.get(
                "response_time_minutes"
            ),
            resolution_time_minutes=data.get(
                "resolution_time_minutes"
            ),
        )

        return jsonify({
            "id": rule.id,
            "priority": rule.priority,
            "response_time_minutes": (
                rule.response_time_minutes
            ),
            "resolution_time_minutes": (
                rule.resolution_time_minutes
            ),
        }), 200

    except PermissionError as exc:
        return _error(
            str(exc),
            403,
        )

    except ValueError as exc:
        return _error(
            str(exc),
            400,
        )

    except Exception:
        return _error(
            "Unable to process SLA rule.",
            500,
        )