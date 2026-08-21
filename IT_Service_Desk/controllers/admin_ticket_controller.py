from flask import Blueprint,render_template,request,redirect,url_for,session,flash,current_app
from services.ticket_service import TicketService
from services.ticket_assignment_service import (
    TicketAssignmentService
)
from services.user_service import UserService


admin_ticket_bp = Blueprint(
    "admin_ticket",
    __name__,
    url_prefix="/admin/tickets"
)

ticket_service = TicketService()
assignment_service = TicketAssignmentService()
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


@admin_ticket_bp.route("/", methods=["GET"])
def manage_tickets():

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    try:

        admin_id = session.get("user_id")

        tickets = ticket_service.get_all_tickets(
            user_id=admin_id
        )

        all_users = user_service.get_all_users()

        agents = [
            user
            for user in all_users
            if user.role
            and user.role.name == "AGENT"
            and user.is_active
        ]

        return render_template(
            "admin_tickets.html",
            tickets=tickets,
            agents=agents,
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
            "Failed to load admin ticket management."
        )

        flash(
            "Unable to load tickets.",
            "danger"
        )

        return render_template(
            "admin_tickets.html",
            tickets=[],
            agents=[],
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )


@admin_ticket_bp.route(
    "/<int:ticket_id>",
    methods=["GET"]
)
def ticket_details(ticket_id):

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    try:

        admin_id = session.get("user_id")

        ticket = ticket_service.get_ticket_by_id(
            user_id=admin_id,
            ticket_id=ticket_id
        )

        if not ticket:

            flash(
                "Ticket not found.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_ticket.manage_tickets"
                )
            )

        all_users = user_service.get_all_users()

        agents = [
            user
            for user in all_users
            if user.role
            and user.role.name == "AGENT"
            and user.is_active
        ]

        assignments = assignment_service.get_ticket_assignments(
            user_id=admin_id,
            ticket_id=ticket_id
        )

        assigned_agent = None

        if assignments:

            for assignment in assignments:

                if assignment.agent:

                    assigned_agent = assignment.agent

                    break

        employee = ticket.creator

        return render_template(
            "admin_ticket_details.html",
            ticket=ticket,
            employee=employee,
            agents=agents,
            assignments=assignments,
            assigned_agent=assigned_agent,
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
            "Failed to load ticket details for ticket %s.",
            ticket_id
        )

        flash(
            "Unable to load ticket details.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_ticket.manage_tickets"
            )
        )


@admin_ticket_bp.route(
    "/<int:ticket_id>/assign",
    methods=["POST"]
)
def assign_ticket(ticket_id):

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    admin_id = session.get("user_id")

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
                "admin_ticket.manage_tickets"
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
                "admin_ticket.manage_tickets"
            )
        )

    try:

        agent = user_service.get_user_by_id(
            agent_id
        )

        if not agent:

            flash(
                "Agent not found.",
                "warning"
            )

            return redirect(
                request.referrer
                or url_for(
                    "admin_ticket.manage_tickets"
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
                    "admin_ticket.manage_tickets"
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
                    "admin_ticket.manage_tickets"
                )
            )

        assignment_service.assign_ticket(
            admin_id=admin_id,
            ticket_id=ticket_id,
            agent_id=agent_id
        )

        flash(
            f"Ticket #{ticket_id} assigned to "
            f"{agent.name}.",
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
            "Failed to assign ticket %s to agent %s.",
            ticket_id,
            agent_id
        )

        flash(
            "Unable to assign the ticket.",
            "danger"
        )

    return redirect(
        request.referrer
        or url_for(
            "admin_ticket.manage_tickets"
        )
    )


@admin_ticket_bp.route(
    "/<int:ticket_id>/unassign/<int:assignment_id>",
    methods=["POST"]
)
def unassign_ticket(
    ticket_id,
    assignment_id
):

    auth_check = _require_admin()

    if auth_check:
        return auth_check

    admin_id = session.get("user_id")

    try:

        assignment_service.unassign_ticket(
            admin_id=admin_id,
            assignment_id=assignment_id
        )

        flash(
            f"Ticket #{ticket_id} has been unassigned.",
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
            "Failed to unassign ticket %s.",
            ticket_id
        )

        flash(
            "Unable to unassign the ticket.",
            "danger"
        )

    return redirect(
        request.referrer
        or url_for(
            "admin_ticket.manage_tickets"
        )
    )