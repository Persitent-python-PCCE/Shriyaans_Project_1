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

from services.ticket_assignment_service import (
    TicketAssignmentService
)

from services.ticket_service import (
    TicketService
)

from services.user_service import (
    UserService
)


ticket_assignment_bp = Blueprint(
    "ticket_assignment",
    __name__,
    url_prefix="/agent"
)


assignment_service = TicketAssignmentService()
ticket_service = TicketService()
user_service = UserService()


# ============================================================
# AGENT - ASSIGNED TICKETS
# ============================================================

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
            url_for("user_controller.login")
        )

    if session.get("role") != "AGENT":

        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for("user_controller.login")
        )

    status_filter = request.args.get(
        "status"
    )

    try:

        tickets = ticket_service.get_agent_tickets(
            user_id=user_id
        )

        if status_filter:

            status_filter = status_filter.upper()

            valid_statuses = {
                "ASSIGNED",
                "IN_PROGRESS",
                "RESOLVED",
                "CLOSED"
            }

            if status_filter not in valid_statuses:

                flash(
                    "Invalid status filter.",
                    "warning"
                )

                status_filter = None

            else:

                tickets = [
                    ticket
                    for ticket in tickets
                    if ticket.status == status_filter
                ]

        return render_template(
            "assigned_tickets.html",
            tickets=tickets,
            current_status=status_filter,
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
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )


# ============================================================
# AGENT - UPDATE STATUS
# ============================================================

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
            url_for("user_controller.login")
        )

    if session.get("role") != "AGENT":

        flash(
            "Unauthorized action.",
            "danger"
        )

        return redirect(
            url_for("user_controller.login")
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


# ============================================================
# ADMIN - ASSIGN TICKET
# ============================================================

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
            url_for("user_controller.login")
        )

    if session.get("role") != "ADMIN":

        flash(
            "Only administrators can assign tickets.",
            "danger"
        )

        return redirect(
            url_for("user_controller.login")
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