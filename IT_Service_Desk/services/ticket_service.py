from datetime import datetime

from models.ticket import Ticket
from models.user import User

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
        "OPEN": {"ASSIGNED"},
        "ASSIGNED": {"IN_PROGRESS", "OPEN"},
        "IN_PROGRESS": {"RESOLVED"},
        "RESOLVED": {"CLOSED", "IN_PROGRESS"},
        "CLOSED": set()
    }

    @staticmethod
    def _get_user(user_id):
        user = UserDAO.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        if not user.is_active:
            raise PermissionError("User account is inactive.")

        return user

    @staticmethod
    def _get_ticket(ticket_id):
        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError("Ticket not found.")

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
        user = TicketService._get_user(user_id)

        if user.role.name != "EMPLOYEE":
            raise PermissionError(
                "Only employees can create tickets."
            )

        if not title or not title.strip():
            raise ValueError("Ticket title is required.")

        if not description or not description.strip():
            raise ValueError("Ticket description is required.")

        category = TicketCategoryDAO.get_by_id(category_id)

        if not category:
            raise ValueError("Invalid ticket category.")

        priority = priority.upper()
        severity = severity.upper()

        if priority not in TicketService.VALID_PRIORITIES:
            raise ValueError("Invalid priority.")

        if severity not in TicketService.VALID_SEVERITIES:
            raise ValueError("Invalid severity.")

        ticket = Ticket(
            title=title.strip(),
            description=description.strip(),
            category_id=category_id,
            created_by=user_id,
            priority=priority,
            severity=severity,
            status="OPEN"
        )

        return TicketDAO.create(ticket)

    @staticmethod
    def get_employee_tickets(user_id):
        user = TicketService._get_user(user_id)

        if user.role.name != "EMPLOYEE":
            raise PermissionError(
                "Only employees can access their tickets."
            )

        return TicketDAO.get_by_creator(user_id)

    
    @staticmethod
    def get_agent_tickets(user_id):
        user = TicketService._get_user(user_id)

        if user.role.name != "AGENT":
            raise PermissionError(
                "Only agents can access assigned tickets."
            )

        from dao.ticket_assignment_dao import TicketAssignmentDAO

        assignments = TicketAssignmentDAO.get_by_agent(user_id)

        return [
            assignment.ticket
            for assignment in assignments
            if assignment.ticket is not None
        ]

 

    @staticmethod
    def get_all_tickets(user_id):
        user = TicketService._get_user(user_id)

        if user.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can access all tickets."
            )

        return TicketDAO.get_all()

    
    @staticmethod
    def get_ticket_by_id(user_id, ticket_id):
        user = TicketService._get_user(user_id)
        ticket = TicketService._get_ticket(ticket_id)

        role = user.role.name

        if role == "ADMIN":
            return ticket

        if role == "EMPLOYEE":
            if ticket.created_by != user_id:
                raise PermissionError(
                    "You are not allowed to access this ticket."
                )

            return ticket

        if role == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(user_id)

            assigned_ticket_ids = {
                assignment.ticket_id
                for assignment in assignments
            }

            if ticket.id not in assigned_ticket_ids:
                raise PermissionError(
                    "This ticket is not assigned to you."
                )

            return ticket

        raise PermissionError("Invalid role.")

    
    @staticmethod
    def update_status(user_id, ticket_id, new_status):
        user = TicketService._get_user(user_id)
        ticket = TicketService._get_ticket(ticket_id)

        new_status = new_status.upper()

        if new_status not in TicketService.VALID_STATUSES:
            raise ValueError("Invalid ticket status.")

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

         
        if user.role.name == "EMPLOYEE":
            raise PermissionError(
                "Employees cannot change ticket status."
            )

       
        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(user_id)

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
                "RESOLVED"
            }

            if new_status not in allowed_for_agent:
                raise PermissionError(
                    "Agents can only move tickets to "
                    "IN_PROGRESS or RESOLVED."
                )

        
        elif user.role.name == "ADMIN":
            pass

        else:
            raise PermissionError("Invalid role.")

        old_status = ticket.status

        ticket.status = new_status

        if new_status == "RESOLVED":
            ticket.resolved_at = datetime.utcnow()

        elif new_status == "CLOSED":
            ticket.closed_at = datetime.utcnow()

        TicketDAO.update(ticket)

      
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
    def search_tickets(
        user_id,
        title=None,
        status=None,
        priority=None,
        category_id=None
    ):
        user = TicketService._get_user(user_id)

        role = user.role.name

        if role == "ADMIN":

            return TicketDAO.search(
                title=title,
                status=status,
                priority=priority,
                category_id=category_id
            )

        if role == "EMPLOYEE":

            tickets = TicketDAO.search(
                title=title,
                status=status,
                priority=priority,
                category_id=category_id
            )

            return [
                ticket
                for ticket in tickets
                if ticket.created_by == user_id
            ]

        if role == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(user_id)

            assigned_ids = {
                assignment.ticket_id
                for assignment in assignments
            }

            tickets = TicketDAO.search(
                title=title,
                status=status,
                priority=priority,
                category_id=category_id
            )

            return [
                ticket
                for ticket in tickets
                if ticket.id in assigned_ids
            ]

        raise PermissionError("Invalid role.")

    @staticmethod
    def get_system_statistics():
        tickets = TicketDAO.get_all()

        total_tickets = len(tickets)

        open_tickets = sum(
            1
            for ticket in tickets
            if ticket.status == "OPEN"
        )

        assigned_tickets = sum(
            1
            for ticket in tickets
            if ticket.status == "ASSIGNED"
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

        escalated_tickets = sum(
            1
            for ticket in tickets
            if ticket.is_escalated
        )

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "assigned_tickets": assigned_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets,
            "escalated_tickets": escalated_tickets
        }