from flask import Blueprint, jsonify, request, session

from services.ticket_service import TicketService
from services.ticket_comment_service import TicketCommentService
from services.ticket_history_service import TicketHistoryService
from services.ticket_category_service import TicketCategoryService
from services.sla_rule_service import SLARuleService


api_bp = Blueprint("api", __name__, url_prefix="/api")

ticket_service = TicketService()
comment_service = TicketCommentService()
category_service = TicketCategoryService()
history_service = TicketHistoryService()
sla_service = SLARuleService()


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"error": "Authentication required."}), 401)
    return user_id, None


def _error(message, status=400):
    return jsonify({"error": message}), status


def _iso(value):
    return value.isoformat() if value else None


def _ticket_to_dict(ticket):
    assignments = []
    for assignment in ticket.assignments:
        assignments.append({
            "id": assignment.id,
            "agent_id": assignment.agent_id,
            "agent_name": assignment.agent.name if assignment.agent else None,
            "assigned_at": _iso(assignment.assigned_at),
        })

    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "category_id": ticket.category_id,
        "category": ticket.category.name if ticket.category else None,
        "created_by": ticket.created_by,
        "creator": ticket.creator.name if ticket.creator else None,
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
                "uploaded_at": _iso(attachment.uploaded_at),
            }
            for attachment in ticket.attachments
        ],
        "assignments": assignments,
    }


@api_bp.route("/tickets", methods=["GET", "POST"])
def tickets():
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    try:
        if request.method == "GET":
            tickets = ticket_service.search_tickets(
                user_id=user_id,
                title=request.args.get("title"),
                status=(request.args.get("status").strip().upper() if request.args.get("status") else None),
                priority=(request.args.get("priority").strip().upper() if request.args.get("priority") else None),
                category_id=(int(request.args.get("category_id")) if request.args.get("category_id") else None),
            )
            return jsonify({
                "count": len(tickets),
                "tickets": [_ticket_to_dict(ticket) for ticket in tickets],
            })

        data = request.get_json(silent=True) or request.form
        category_id = data.get("category_id")
        if category_id is None:
            return _error("category_id is required.")

        ticket = ticket_service.create_ticket(
            user_id=user_id,
            title=data.get("title"),
            description=data.get("description"),
            category_id=int(category_id),
            priority=data.get("priority", "MEDIUM"),
            severity=data.get("severity", "MODERATE"),
        )
        return jsonify(_ticket_to_dict(ticket)), 201

    except (ValueError, TypeError) as exc:
        return _error(str(exc))
    except PermissionError as exc:
        return _error(str(exc), 403)
    except Exception:
        return _error("Unable to process ticket request.", 500)


@api_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
def ticket_detail(ticket_id):
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    try:
        ticket = ticket_service.get_ticket_by_id(user_id, ticket_id)
        return jsonify(_ticket_to_dict(ticket))
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception:
        return _error("Unable to load ticket.", 500)


@api_bp.route("/tickets/<int:ticket_id>/status", methods=["PATCH", "PUT"])
def ticket_status(ticket_id):
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or request.form
    try:
        ticket = ticket_service.update_status(
            user_id=user_id,
            ticket_id=ticket_id,
            new_status=data.get("status", ""),
        )
        return jsonify(_ticket_to_dict(ticket))
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception:
        return _error("Unable to update ticket status.", 500)


@api_bp.route("/tickets/<int:ticket_id>/escalate", methods=["POST"])
def escalate_ticket(ticket_id):
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or request.form
    try:
        ticket = ticket_service.escalate_ticket(
            user_id=user_id,
            ticket_id=ticket_id,
            reason=data.get("reason"),
        )
        return jsonify(_ticket_to_dict(ticket))
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception:
        return _error("Unable to escalate ticket.", 500)


@api_bp.route("/tickets/<int:ticket_id>/comments", methods=["GET", "POST"])
def ticket_comments(ticket_id):
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    try:
        ticket_service.get_ticket_by_id(user_id, ticket_id)
        if request.method == "GET":
            comments = comment_service.get_comments(user_id, ticket_id)
            return jsonify({
                "comments": [
                    {
                        "id": comment.id,
                        "user_id": comment.user_id,
                        "user_name": comment.user.name if comment.user else None,
                        "comment": comment.comment,
                        "created_at": _iso(comment.created_at),
                    }
                    for comment in comments
                ]
            })

        data = request.get_json(silent=True) or request.form
        comment = comment_service.add_comment(
            user_id=user_id,
            ticket_id=ticket_id,
            comment_text=data.get("comment", ""),
        )
        return jsonify({
            "id": comment.id,
            "ticket_id": comment.ticket_id,
            "user_id": comment.user_id,
            "comment": comment.comment,
            "created_at": _iso(comment.created_at),
        }), 201
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception:
        return _error("Unable to process comments.", 500)


@api_bp.route("/tickets/<int:ticket_id>/history", methods=["GET"])
def ticket_history(ticket_id):
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    try:
        history = history_service.get_ticket_history(user_id, ticket_id)
        return jsonify({
            "history": [
                {
                    "id": entry.id,
                    "action": entry.action,
                    "old_value": entry.old_value,
                    "new_value": entry.new_value,
                    "description": entry.description,
                    "user_id": entry.user_id,
                    "user_name": entry.user.name if entry.user else None,
                    "created_at": _iso(entry.created_at),
                }
                for entry in history
            ]
        })
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception:
        return _error("Unable to load ticket history.", 500)


@api_bp.route("/categories", methods=["GET"])
def categories():
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    try:
        categories = category_service.get_all_categories(user_id)
        return jsonify({
            "categories": [
                {"id": category.id, "name": category.name}
                for category in categories
            ]
        })
    except PermissionError as exc:
        return _error(str(exc), 403)
    except Exception:
        return _error("Unable to load categories.", 500)


@api_bp.route("/sla-rules", methods=["GET", "POST"])
def sla_rules():
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    if session.get("role") != "ADMIN":
        return _error("Only administrators can access SLA rules.", 403)

    try:
        if request.method == "GET":
            sla_service.ensure_default_rules()
            rules = sla_service.get_all_rules(admin_id=user_id)
            return jsonify({
                "sla_rules": [
                    {
                        "id": rule.id,
                        "priority": rule.priority,
                        "response_time_minutes": rule.response_time_minutes,
                        "resolution_time_minutes": rule.resolution_time_minutes,
                        "created_at": _iso(rule.created_at),
                    }
                    for rule in rules
                ]
            })

        data = request.get_json(silent=True) or request.form
        rule = sla_service.create_rule(
            admin_id=user_id,
            priority=data.get("priority"),
            response_time_minutes=data.get("response_time_minutes"),
            resolution_time_minutes=data.get("resolution_time_minutes"),
        )
        return jsonify({
            "id": rule.id,
            "priority": rule.priority,
            "response_time_minutes": rule.response_time_minutes,
            "resolution_time_minutes": rule.resolution_time_minutes,
            "created_at": _iso(rule.created_at),
        }), 201
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception:
        return _error("Unable to process SLA rules.", 500)


@api_bp.route("/sla-rules/<int:rule_id>", methods=["PATCH", "PUT", "DELETE"])
def sla_rule_detail(rule_id):
    user_id, auth_error = _current_user()
    if auth_error:
        return auth_error

    if session.get("role") != "ADMIN":
        return _error("Only administrators can manage SLA rules.", 403)

    try:
        if request.method == "DELETE":
            sla_service.delete_rule(user_id, rule_id)
            return jsonify({"message": "SLA rule deleted."})

        data = request.get_json(silent=True) or request.form
        rule = sla_service.update_rule(
            admin_id=user_id,
            rule_id=rule_id,
            response_time_minutes=data.get("response_time_minutes"),
            resolution_time_minutes=data.get("resolution_time_minutes"),
        )
        return jsonify({
            "id": rule.id,
            "priority": rule.priority,
            "response_time_minutes": rule.response_time_minutes,
            "resolution_time_minutes": rule.resolution_time_minutes,
        })
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception:
        return _error("Unable to process SLA rule.", 500)
