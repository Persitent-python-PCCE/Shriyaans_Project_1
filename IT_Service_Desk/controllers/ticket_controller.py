import os
from flask import Blueprint,request,render_template,redirect,url_for,session,flash,send_file,abort,current_app
from services.ticket_service import TicketService
from services.ticket_category_service import TicketCategoryService
from services.ticket_comment_service import TicketCommentService
from services.ticket_attachment_service import TicketAttachmentService
from services.feedback_service import FeedbackService
from services.ticket_history_service import TicketHistoryService
from datetime import datetime


ticket_controller = Blueprint(
    "ticket_controller",
    __name__,
    url_prefix="/tickets"
)


ticket_service = TicketService()
category_service = TicketCategoryService()
comment_service = TicketCommentService()
attachment_service = TicketAttachmentService()


def _require_login():

    if "user_id" not in session:

        return redirect(
            url_for(
                "user_controller.employee_login"
            )
        )

    return None


def _require_role(role):

    if session.get("role") != role:

        return "Unauthorized", 403

    return None


@ticket_controller.route(
    "/my-tickets"
)
def my_tickets():

    login_check = _require_login()

    if login_check:

        return login_check

    role_check = _require_role(
        "EMPLOYEE"
    )

    if role_check:

        return role_check

    try:

        user_id = session.get(
            "user_id"
        )

        title = request.args.get('q', '').strip()
        status_filter = request.args.get('status', '').strip().upper() or None
        priority_filter = request.args.get('priority', '').strip().upper() or None
        category_filter = request.args.get('category_id', '').strip() or None
        try:
            category_filter = int(category_filter) if category_filter else None
        except ValueError:
            category_filter = None
        tickets = ticket_service.search_tickets(
            user_id=user_id,
            title=title or None,
            status=status_filter,
            priority=priority_filter,
            category_id=category_filter
        )
        categories = category_service.get_all_categories(user_id)

        return render_template(
            "my_tickets.html",
            tickets=tickets,
            categories=categories,
            current_query=title,
            current_status=status_filter,
            current_priority=priority_filter,
            current_category=category_filter,
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )

    except PermissionError as e:

        return str(e), 403

    except Exception:

        return render_template(
            "my_tickets.html",
            tickets=[],
            error="Unable to load your tickets.",
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )


@ticket_controller.route(
    "/create",
    methods=["GET", "POST"]
)
def create_ticket():

    login_check = _require_login()

    if login_check:

        return login_check

    role_check = _require_role(
        "EMPLOYEE"
    )

    if role_check:

        return role_check

    user_id = session.get(
        "user_id"
    )

    if request.method == "GET":

        try:

            categories = category_service.get_all_categories(
                user_id
            )

            return render_template(
                "create_ticket.html",
                categories=categories,
                name=session.get("user_name"),
                email=session.get("user_email"),
                role=session.get("role")
            )

        except Exception:

            return render_template(
                "create_ticket.html",
                categories=[],
                error="Unable to load ticket categories.",
                name=session.get("user_name"),
                email=session.get("user_email"),
                role=session.get("role")
            )

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    category_id = request.form.get(
        "category_id"
    )

    priority = request.form.get(
        "priority",
        "MEDIUM"
    ).strip().upper()

    severity = request.form.get(
        "severity",
        "MODERATE"
    ).strip().upper()

    if not title:

        return _render_create_ticket_with_error(
            "Ticket title is required."
        )

    if not description:

        return _render_create_ticket_with_error(
            "Ticket description is required."
        )

    if not category_id:

        return _render_create_ticket_with_error(
            "Please select a category."
        )

    try:

        category_id = int(
            category_id
        )

    except ValueError:

        return _render_create_ticket_with_error(
            "Invalid category."
        )

    try:

        ticket = ticket_service.create_ticket(
            user_id=user_id,
            title=title,
            description=description,
            category_id=category_id,
            priority=priority,
            severity=severity
        )

        return redirect(
            url_for(
                "ticket_controller.ticket_details",
                ticket_id=ticket.id
            )
        )

    except ValueError as e:

        return _render_create_ticket_with_error(
            str(e)
        )

    except PermissionError as e:

        return str(e), 403

    except Exception:

        return _render_create_ticket_with_error(
            "Unable to create the ticket. Please try again."
        )


def _render_create_ticket_with_error(
    message
):

    try:

        categories = category_service.get_all_categories(
            session.get("user_id")
        )

    except Exception:

        categories = []

    return render_template(
        "create_ticket.html",
        categories=categories,
        error=message,
        name=session.get("user_name"),
        email=session.get("user_email"),
        role=session.get("role")
    )


@ticket_controller.route(
    "/<int:ticket_id>"
)
def ticket_details(ticket_id):

    login_check = _require_login()

    if login_check:

        return login_check

    try:

        user_id = session.get(
            "user_id"
        )

        ticket = ticket_service.get_ticket_by_id(
            user_id=user_id,
            ticket_id=ticket_id
        )

        comments = comment_service.get_comments(
            user_id=user_id,
            ticket_id=ticket_id
        )

        attachments = attachment_service.get_ticket_attachments(
            user_id=user_id,
            ticket_id=ticket_id
        )
        history = TicketHistoryService.get_ticket_history(user_id=user_id, ticket_id=ticket_id)
        feedback = FeedbackService.get_feedback(user_id=user_id, ticket_id=ticket_id)

        return render_template(
            "ticket_details.html",
            ticket=ticket,
            comments=comments,
            attachments=attachments,
            history=history,
            feedback=feedback,
            now=datetime.utcnow(),
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )

    except PermissionError as e:

        return str(e), 403

    except ValueError as e:

        return str(e), 404

    except Exception:

        return render_template(
            "ticket_details.html",
            ticket=None,
            comments=[],
            error="Unable to load ticket details.",
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        ), 500


@ticket_controller.route('/<int:ticket_id>/attachments/<int:attachment_id>/download')
def download_attachment(ticket_id, attachment_id):
    login_check = _require_login()
    if login_check:
        return login_check
    try:
        attachment = attachment_service.get_attachment(session['user_id'], attachment_id)
        if attachment.ticket_id != ticket_id:
            return 'Attachment does not belong to this ticket.', 404
        if not attachment.file_path or not os.path.isfile(attachment.file_path):
            return 'Attachment file not found.', 404
        return send_file(attachment.file_path, as_attachment=True, download_name=attachment.original_filename, max_age=0)
    except PermissionError as exc:
        return str(exc), 403
    except ValueError as exc:
        return str(exc), 404
    except Exception:
        current_app.logger.exception('Failed to download attachment %s.', attachment_id)
        return 'Unable to download attachment.', 500


@ticket_controller.route(
    "/<int:ticket_id>/edit",
    methods=["GET", "POST"]
)
def edit_ticket(ticket_id):

    login_check = _require_login()

    if login_check:

        return login_check

    role_check = _require_role(
        "EMPLOYEE"
    )

    if role_check:

        return role_check

    user_id = session.get(
        "user_id"
    )

    try:

        ticket = ticket_service.get_ticket_by_id(
            user_id=user_id,
            ticket_id=ticket_id
        )

        if request.method == "GET":

            categories = category_service.get_all_categories(
                user_id
            )

            return render_template(
                "edit_ticket.html",
                ticket=ticket,
                categories=categories,
                name=session.get("user_name"),
                email=session.get("user_email"),
                role=session.get("role")
            )

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            "MEDIUM"
        ).strip().upper()

        severity = request.form.get(
            "severity",
            "MODERATE"
        ).strip().upper()

        if not category_id:

            raise ValueError(
                "Please select a category."
            )

        category_id = int(
            category_id
        )

        updated_ticket = ticket_service.update_employee_ticket(
            user_id=user_id,
            ticket_id=ticket_id,
            title=title,
            description=description,
            category_id=category_id,
            priority=priority,
            severity=severity
        )

        return redirect(
            url_for(
                "ticket_controller.ticket_details",
                ticket_id=updated_ticket.id
            )
        )

    except PermissionError as e:

        return str(e), 403

    except ValueError as e:

        try:

            categories = category_service.get_all_categories(
                user_id
            )

        except Exception:

            categories = []

        try:

            ticket = ticket_service.get_ticket_by_id(
                user_id=user_id,
                ticket_id=ticket_id
            )

        except Exception:

            ticket = None

        return render_template(
            "edit_ticket.html",
            ticket=ticket,
            categories=categories,
            error=str(e),
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        ), 400

    except Exception:

        return "Unable to update ticket.", 500


@ticket_controller.route(
    "/<int:ticket_id>/delete",
    methods=["POST"]
)
def delete_ticket(ticket_id):

    login_check = _require_login()

    if login_check:

        return login_check

    role_check = _require_role(
        "EMPLOYEE"
    )

    if role_check:

        return role_check

    user_id = session.get(
        "user_id"
    )

    try:

        ticket_service.delete_employee_ticket(
            user_id=user_id,
            ticket_id=ticket_id
        )

        return redirect(
            url_for(
                "ticket_controller.my_tickets"
            )
        )

    except PermissionError as e:

        return str(e), 403

    except ValueError as e:

        return str(e), 404

    except Exception:

        return "Unable to delete ticket.", 500


@ticket_controller.route(
    "/<int:ticket_id>/attachments",
    methods=["POST"]
)
def upload_attachment(ticket_id):

    login_check = _require_login()
    if login_check:
        return login_check

    user_id = session.get("user_id")
    uploaded_file = request.files.get("file")

    try:
        attachment_service.upload_attachment(
            user_id=user_id,
            ticket_id=ticket_id,
            file=uploaded_file
        )
        flash("Attachment uploaded successfully.", "success")

    except PermissionError as exc:
        flash(str(exc), "danger")
    except ValueError as exc:
        flash(str(exc), "warning")
    except IOError as exc:
        flash(str(exc), "danger")
    except Exception:
        flash("Unable to upload attachment.", "danger")

    return redirect(
        url_for(
            "ticket_controller.ticket_details",
            ticket_id=ticket_id
        )
    )


@ticket_controller.route(
    "/<int:ticket_id>/escalate",
    methods=["POST"]
)
def escalate_ticket(ticket_id):

    login_check = _require_login()
    if login_check:
        return login_check

    user_id = session.get("user_id")
    reason = request.form.get("reason", "").strip()

    try:
        ticket_service.escalate_ticket(
            user_id=user_id,
            ticket_id=ticket_id,
            reason=reason
        )
        flash("Ticket escalated successfully.", "success")
    except PermissionError as exc:
        flash(str(exc), "danger")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception:
        flash("Unable to escalate ticket.", "danger")

    return redirect(
        url_for(
            "ticket_controller.ticket_details",
            ticket_id=ticket_id
        )
    )


@ticket_controller.route(
    "/<int:ticket_id>/comments",
    methods=["POST"]
)
def add_comment(ticket_id):

    login_check = _require_login()

    if login_check:

        return login_check

    user_id = session.get(
        "user_id"
    )

    comment_text = request.form.get(
        "comment",
        ""
    ).strip()

    if not comment_text:

        return redirect(
            url_for(
                "ticket_controller.ticket_details",
                ticket_id=ticket_id,
                error="Comment cannot be empty."
            )
        )

    try:

        comment_service.add_comment(
            user_id=user_id,
            ticket_id=ticket_id,
            comment_text=comment_text
        )

        return redirect(
            url_for(
                "ticket_controller.ticket_details",
                ticket_id=ticket_id
            )
        )

    except PermissionError as e:

        return str(e), 403

    except ValueError as e:

        return redirect(
            url_for(
                "ticket_controller.ticket_details",
                ticket_id=ticket_id,
                error=str(e)
            )
        )

    except Exception:

        return redirect(
            url_for(
                "ticket_controller.ticket_details",
                ticket_id=ticket_id,
                error="Unable to add comment."
            )
        )