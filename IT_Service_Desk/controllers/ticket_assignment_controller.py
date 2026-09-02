from flask import Blueprint,render_template,request,redirect,url_for,session,flash,current_app
from services.ticket_assignment_service import TicketAssignmentService
from services.ticket_service import TicketService
from services.user_service import UserService
from services.ticket_category_service import TicketCategoryService


ticket_assignment_bp = Blueprint(
    "ticket_assignment",
    __name__,
    url_prefix="/agent"
)


assignment_service = TicketAssignmentService()
ticket_service = TicketService()
user_service = UserService()


@ticket_assignment_bp.route(
    "/assigned-tickets",
    methods=["GET"]
)
def view_assigned_tickets():

    user_id = session.get("user_id")

    if not user_id:

        flash(
            "Please log in first.",
            "warning"
        )

        return redirect(
            url_for("user_controller.agent_login")
        )

    if session.get("role") != "AGENT":

        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for("user_controller.agent_login")
        )

    status_filter = request.args.get(
        "status",
        ""
    ).strip().upper()

    if not status_filter:
        status_filter = None

    try:

        title = request.args.get('q', '').strip()
        priority_filter = request.args.get('priority', '').strip().upper() or None
        category_filter = request.args.get('category_id', '').strip() or None
        try:
            category_filter = int(category_filter) if category_filter else None
        except ValueError:
            category_filter = None
        if status_filter and status_filter not in TicketService.VALID_STATUSES:
            flash('Invalid status filter.', 'warning')
            status_filter = None
        tickets = ticket_service.search_tickets(
            user_id=user_id,
            title=title or None,
            status=status_filter,
            priority=priority_filter,
            category_id=category_filter
        )
        categories = TicketCategoryService.get_all_categories(user_id)

        return render_template(
            "assigned_tickets.html",
            tickets=tickets,
            categories=categories,
            current_query=title,
            current_status=status_filter,
            current_priority=priority_filter,
            current_category=category_filter,
            status_options=sorted(TicketService.VALID_STATUSES),
            priority_options=sorted(TicketService.VALID_PRIORITIES),
            status_flow=TicketService.STATUS_FLOW,
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
            url_for("user_controller.agent_login")
        )

    except Exception:

        current_app.logger.exception(
            "Error fetching assigned tickets "
            "for agent %s",
            user_id
        )

        flash(
            "Unable to retrieve assigned tickets.",
            "danger"
        )

        return render_template(
            "assigned_tickets.html",
            tickets=[],
            current_status=status_filter,
            status_options=sorted(TicketService.VALID_STATUSES),
            priority_options=sorted(TicketService.VALID_PRIORITIES),
            status_flow=TicketService.STATUS_FLOW,
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )


@ticket_assignment_bp.route(
    "/ticket/<int:ticket_id>/update-status",
    methods=["POST"]
)
def update_ticket_status(ticket_id):

    user_id = session.get("user_id")

    if not user_id:

        flash(
            "Please log in first.",
            "warning"
        )

        return redirect(
            url_for("user_controller.agent_login")
        )

    if session.get("role") != "AGENT":

        flash(
            "Unauthorized action.",
            "danger"
        )

        return redirect(
            url_for("user_controller.agent_login")
        )

    new_status = request.form.get(
        "status",
        ""
    ).strip().upper()

    if not new_status:

        flash(
            "Please select a status.",
            "warning"
        )

        return redirect(
            url_for(
                "ticket_assignment.view_assigned_tickets"
            )
        )

    try:

        ticket = ticket_service.update_status(
            user_id=user_id,
            ticket_id=ticket_id,
            new_status=new_status
        )

        flash(
            f"Ticket #{ticket.id} status updated "
            f"to {ticket.status}.",
            "success"
        )

    except PermissionError as exc:

        flash(
            str(exc),
            "danger"
        )

    except ValueError as exc:

        flash(
            str(exc),
            "warning"
        )

    except Exception:

        current_app.logger.exception(
            "Error updating ticket %s "
            "for agent %s",
            ticket_id,
            user_id
        )

        flash(
            "Unable to update ticket status.",
            "danger"
        )

    return redirect(
        request.referrer
        or url_for(
            "ticket_assignment.view_assigned_tickets"
        )
    )


@ticket_assignment_bp.route(
    "/ticket/<int:ticket_id>/assign",
    methods=["POST"]
)
def assign_ticket(ticket_id):

    admin_id = session.get("user_id")

    if not admin_id:

        flash(
            "Please log in first.",
            "warning"
        )

        return redirect(
            url_for("user_controller.admin_login")
        )

    if session.get("role") != "ADMIN":

        flash(
            "Only administrators can assign tickets.",
            "danger"
        )

        return redirect(
            url_for("user_controller.admin_login")
        )

    agent_id = request.form.get(
        "agent_id",
        ""
    ).strip()

    if not agent_id:

        flash(
            "Please select an agent.",
            "warning"
        )

        return redirect(
            request.referrer
            or url_for(
                "user_controller.admin_dashboard"
            )
        )

    try:

        agent_id = int(agent_id)

    except ValueError:

        flash(
            "Invalid agent selected.",
            "warning"
        )

        return redirect(
            request.referrer
            or url_for(
                "user_controller.admin_dashboard"
            )
        )

    try:

        agent = user_service.get_user_by_id(
            agent_id
        )

        if not agent:

            flash(
                "Selected agent was not found.",
                "warning"
            )

            return redirect(
                request.referrer
                or url_for(
                    "user_controller.admin_dashboard"
                )
            )

        if not agent.is_active:

            flash(
                "Selected agent is inactive.",
                "warning"
            )

            return redirect(
                request.referrer
                or url_for(
                    "user_controller.admin_dashboard"
                )
            )

        if not agent.role or agent.role.name != "AGENT":

            flash(
                "Selected user is not an agent.",
                "warning"
            )

            return redirect(
                request.referrer
                or url_for(
                    "user_controller.admin_dashboard"
                )
            )

        assignment_service.assign_ticket(
            admin_id=admin_id,
            ticket_id=ticket_id,
            agent_id=agent_id
        )

        flash(
            f"Ticket #{ticket_id} assigned "
            f"to {agent.name}.",
            "success"
        )

    except PermissionError as exc:

        flash(
            str(exc),
            "danger"
        )

    except ValueError as exc:

        flash(
            str(exc),
            "warning"
        )

    except Exception:

        current_app.logger.exception(
            "Error assigning ticket %s "
            "to agent %s",
            ticket_id,
            agent_id
        )

        flash(
            "Unable to assign ticket.",
            "danger"
        )

    return redirect(
        request.referrer
        or url_for(
            "user_controller.admin_dashboard"
        )
    )