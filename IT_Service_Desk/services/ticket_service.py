from datetime import datetime
import os
from models.ticket import Ticket
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO
from dao.ticket_category_dao import TicketCategoryDAO


class TicketService:

    VALID_PRIORITIES = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    VALID_SEVERITIES = {
        "MINOR",
        "MODERATE",
        "MAJOR",
        "CRITICAL"
    }

    VALID_STATUSES = {
        "OPEN",
        "ASSIGNED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    }

    STATUS_FLOW = {
        "OPEN": {
            "ASSIGNED"
        },
        "ASSIGNED": {
            "IN_PROGRESS",
            "OPEN"
        },
        "IN_PROGRESS": {
            "RESOLVED"
        },
        "RESOLVED": {
            "CLOSED",
            "IN_PROGRESS"
        },
        "CLOSED": set()
    }

    @staticmethod
    def _get_user(user_id):

        user = UserDAO.get_by_id(
            user_id
        )

        if not user:
            raise ValueError(
                "User not found."
            )

        if not user.is_active:
            raise PermissionError(
                "User account is inactive."
            )

        return user

    @staticmethod
    def _get_ticket(ticket_id):

        ticket = TicketDAO.get_by_id(
            ticket_id
        )

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        return ticket

    @staticmethod
    def create_ticket(
        user_id,
        title,
        description,
        category_id,
        priority="MEDIUM",
        severity="MODERATE"
    ):

        user = TicketService._get_user(
            user_id
        )

        if not user.role or user.role.name != "EMPLOYEE":

            raise PermissionError(
                "Only employees can create tickets."
            )

        if not title or not title.strip():

            raise ValueError(
                "Ticket title is required."
            )

        if not description or not description.strip():

            raise ValueError(
                "Ticket description is required."
            )

        category = TicketCategoryDAO.get_by_id(
            category_id
        )

        if not category:

            raise ValueError(
                "Invalid ticket category."
            )

        priority = priority.strip().upper()
        severity = severity.strip().upper()

        if priority not in TicketService.VALID_PRIORITIES:

            raise ValueError(
                "Invalid priority."
            )

        if severity not in TicketService.VALID_SEVERITIES:

            raise ValueError(
                "Invalid severity."
            )

        ticket = Ticket(
            title=title.strip(),
            description=description.strip(),
            category_id=category_id,
            created_by=user_id,
            priority=priority,
            severity=severity,
            status="OPEN"
        )

        return TicketDAO.create(
            ticket
        )

    @staticmethod
    def get_employee_tickets(user_id):

        user = TicketService._get_user(
            user_id
        )

        if not user.role or user.role.name != "EMPLOYEE":

            raise PermissionError(
                "Only employees can access their tickets."
            )

        return TicketDAO.get_by_creator(
            user_id
        )

    @staticmethod
    def get_agent_tickets(user_id):

        user = TicketService._get_user(
            user_id
        )

        if not user.role or user.role.name != "AGENT":

            raise PermissionError(
                "Only agents can access assigned tickets."
            )

        from dao.ticket_assignment_dao import TicketAssignmentDAO

        assignments = TicketAssignmentDAO.get_by_agent(
            user_id
        )

        tickets = []

        for assignment in assignments:

            if assignment.ticket is not None:

                tickets.append(
                    assignment.ticket
                )

        return tickets

    @staticmethod
    def get_agent_statistics(agent_id):

        tickets = TicketService.get_agent_tickets(
            agent_id
        )

        assigned_tickets = len(
            tickets
        )

        in_progress_tickets = sum(
            1
            for ticket in tickets
            if ticket.status == "IN_PROGRESS"
        )

        resolved_tickets = sum(
            1
            for ticket in tickets
            if ticket.status == "RESOLVED"
        )

        closed_tickets = sum(
            1
            for ticket in tickets
            if ticket.status == "CLOSED"
        )

        return {
            "assigned_tickets": assigned_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets
        }

    @staticmethod
    def get_all_tickets(user_id):

        user = TicketService._get_user(
            user_id
        )

        if not user.role or user.role.name != "ADMIN":

            raise PermissionError(
                "Only administrators can access all tickets."
            )

        return TicketDAO.get_all()

    @staticmethod
    def get_ticket_by_id(
        user_id,
        ticket_id
    ):

        user = TicketService._get_user(
            user_id
        )

        ticket = TicketService._get_ticket(
            ticket_id
        )

        if user.role.name == "ADMIN":

            return ticket

        if user.role.name == "EMPLOYEE":

            if ticket.created_by != user_id:

                raise PermissionError(
                    "You are not allowed to access this ticket."
                )

            return ticket

        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(
                user_id
            )

            assigned_ticket_ids = {
                assignment.ticket_id
                for assignment in assignments
            }

            if ticket.id not in assigned_ticket_ids:

                raise PermissionError(
                    "This ticket is not assigned to you."
                )

            return ticket

        raise PermissionError(
            "Invalid role."
        )

    @staticmethod
    def update_status(
        user_id,
        ticket_id,
        new_status
    ):

        user = TicketService._get_user(
            user_id
        )

        ticket = TicketService._get_ticket(
            ticket_id
        )

        new_status = new_status.strip().upper()

        if new_status not in TicketService.VALID_STATUSES:

            raise ValueError(
                "Invalid ticket status."
            )

        current_status = ticket.status

        if current_status == new_status:

            raise ValueError(
                "Ticket already has this status."
            )

        allowed_statuses = TicketService.STATUS_FLOW.get(
            current_status,
            set()
        )

        if new_status not in allowed_statuses:

            raise ValueError(
                f"Invalid status transition: "
                f"{current_status} -> {new_status}"
            )

        if not user.role:

            raise PermissionError(
                "Invalid role."
            )

        if user.role.name == "EMPLOYEE":

            raise PermissionError(
                "Employees cannot change ticket status."
            )

        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(
                user_id
            )

            assigned_ticket_ids = {
                assignment.ticket_id
                for assignment in assignments
            }

            if ticket.id not in assigned_ticket_ids:

                raise PermissionError(
                    "You can only update tickets assigned to you."
                )

            allowed_for_agent = {
                "IN_PROGRESS",
                "RESOLVED",
                "CLOSED"
            }

            if new_status not in allowed_for_agent:

                raise PermissionError(
                    "Agents can only change tickets to "
                    "IN_PROGRESS, RESOLVED, or CLOSED."
                )

        elif user.role.name == "ADMIN":

            pass

        else:

            raise PermissionError(
                "Invalid role."
            )

        old_status = ticket.status

        ticket.status = new_status

        if new_status == "RESOLVED":

            ticket.resolved_at = datetime.utcnow()

        elif new_status == "CLOSED":

            ticket.closed_at = datetime.utcnow()

        TicketDAO.update(
            ticket
        )

        from services.ticket_history_service import TicketHistoryService

        TicketHistoryService.create_history(
            user_id=user_id,
            ticket_id=ticket.id,
            action="STATUS_CHANGED",
            old_value=old_status,
            new_value=new_status,
            description=(
                f"Ticket status changed from "
                f"{old_status} to {new_status}."
            )
        )

        return ticket

    @staticmethod
    def update_employee_ticket(
        user_id,
        ticket_id,
        title,
        description,
        category_id,
        priority,
        severity
    ):

        user = TicketService._get_user(
            user_id
        )

        if not user.role or user.role.name != "EMPLOYEE":

            raise PermissionError(
                "Only employees can update tickets."
            )

        ticket = TicketService._get_ticket(
            ticket_id
        )

        if ticket.created_by != user_id:

            raise PermissionError(
                "You are not allowed to update this ticket."
            )

        if not title or not title.strip():

            raise ValueError(
                "Ticket title is required."
            )

        if not description or not description.strip():

            raise ValueError(
                "Ticket description is required."
            )

        try:

            category_id = int(
                category_id
            )

        except (TypeError, ValueError):

            raise ValueError(
                "Invalid ticket category."
            )

        category = TicketCategoryDAO.get_by_id(
            category_id
        )

        if not category:

            raise ValueError(
                "Invalid ticket category."
            )

        priority = priority.strip().upper()
        severity = severity.strip().upper()

        if priority not in TicketService.VALID_PRIORITIES:

            raise ValueError(
                "Invalid priority."
            )

        if severity not in TicketService.VALID_SEVERITIES:

            raise ValueError(
                "Invalid severity."
            )

        ticket.title = title.strip()
        ticket.description = description.strip()
        ticket.category_id = category_id
        ticket.priority = priority
        ticket.severity = severity

        TicketDAO.update(
            ticket
        )

        return ticket

    @staticmethod
    def delete_employee_ticket(
        user_id,
        ticket_id
    ):

        user = TicketService._get_user(
            user_id
        )

        if not user.role or user.role.name != "EMPLOYEE":

            raise PermissionError(
                "Only employees can delete tickets."
            )

        ticket = TicketService._get_ticket(
            ticket_id
        )

        if ticket.created_by != user_id:

            raise PermissionError(
                "You are not allowed to delete this ticket."
            )

        attachment_paths = [
            attachment.file_path
            for attachment in ticket.attachments
            if attachment.file_path
        ]

        deleted_ticket_id = ticket.id

        TicketDAO.delete(
            ticket
        )

        for file_path in attachment_paths:

            if os.path.exists(file_path):

                try:

                    os.remove(
                        file_path
                    )

                except OSError:

                    pass

        return deleted_ticket_id

    @staticmethod
    def search_tickets(
        user_id,
        title=None,
        status=None,
        priority=None,
        category_id=None
    ):

        user = TicketService._get_user(
            user_id
        )

        tickets = TicketDAO.search(
            title=title,
            status=status,
            priority=priority,
            category_id=category_id
        )

        if user.role.name == "ADMIN":

            return tickets

        if user.role.name == "EMPLOYEE":

            return [
                ticket
                for ticket in tickets
                if ticket.created_by == user_id
            ]

        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(
                user_id
            )

            assigned_ids = {
                assignment.ticket_id
                for assignment in assignments
            }

            return [
                ticket
                for ticket in tickets
                if ticket.id in assigned_ids
            ]

        raise PermissionError(
            "Invalid role."
        )

    @staticmethod
    def get_system_statistics():

        tickets = TicketDAO.get_all()

        total_tickets = len(
            tickets
        )

        open_tickets = 0
        assigned_tickets = 0
        in_progress_tickets = 0
        resolved_tickets = 0
        closed_tickets = 0
        escalated_tickets = 0

        for ticket in tickets:

            if ticket.status == "OPEN":

                open_tickets += 1

            elif ticket.status == "ASSIGNED":

                assigned_tickets += 1

            elif ticket.status == "IN_PROGRESS":

                in_progress_tickets += 1

            elif ticket.status == "RESOLVED":

                resolved_tickets += 1

            elif ticket.status == "CLOSED":

                closed_tickets += 1

            if ticket.is_escalated:

                escalated_tickets += 1

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "assigned_tickets": assigned_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets,
            "escalated_tickets": escalated_tickets
        }