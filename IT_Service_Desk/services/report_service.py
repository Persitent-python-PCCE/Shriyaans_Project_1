from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dao.feedback_dao import FeedbackDAO
from dao.ticket_assignment_dao import TicketAssignmentDAO
from dao.ticket_category_dao import TicketCategoryDAO
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO

class ReportService:

    PERIOD_OPTIONS = [
        ("all", "All Time"),
        ("7", "Last 7 Days"),
        ("30", "Last 30 Days"),
        ("90", "Last 90 Days"),
        ("365", "Last 12 Months")
    ]

    STATUS_LABELS = {
        "OPEN": "Open",
        "ASSIGNED": "Assigned",
        "IN_PROGRESS": "In Progress",
        "RESOLVED": "Resolved",
        "CLOSED": "Closed"
    }

    PRIORITY_LABELS = {
        "LOW": "Low",
        "MEDIUM": "Medium",
        "HIGH": "High",
        "CRITICAL": "Critical"
    }

    @staticmethod
    def build_report(period="all"):
        tickets = TicketDAO.get_all()
        users = UserDAO.get_all()
        categories = TicketCategoryDAO.get_all()
        feedback_list = FeedbackDAO.get_all()
        now = datetime.utcnow()

        period_days = {
            "7": 7,
            "30": 30,
            "90": 90,
            "365": 365
        }

        selected_days = period_days.get(period)

        if selected_days:
            cutoff = now - timedelta(days=selected_days)

            tickets = [
                ticket for ticket in tickets
                if ticket.created_at and ticket.created_at >= cutoff
            ]

            feedback_list = [
                feedback for feedback in feedback_list
                if feedback.created_at and feedback.created_at >= cutoff
            ]
        else:
            period = "all"

        total_tickets = len(tickets)

        status_counts = Counter(ticket.status for ticket in tickets)
        priority_counts = Counter(ticket.priority for ticket in tickets)
        category_counts = Counter(ticket.category_id for ticket in tickets)

        status_report = []

        for status in ("OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"):
            count = status_counts.get(status, 0)

            percentage = round(
                (count / total_tickets) * 100,
                1
            ) if total_tickets else 0

            status_report.append({
                "key": status,
                "label": ReportService.STATUS_LABELS[status],
                "count": count,
                "percentage": percentage
            })

        priority_report = []

        for priority in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            count = priority_counts.get(priority, 0)

            percentage = round(
                (count / total_tickets) * 100,
                1
            ) if total_tickets else 0

            priority_report.append({
                "key": priority,
                "label": ReportService.PRIORITY_LABELS[priority],
                "count": count,
                "percentage": percentage
            })

        category_names = {
            category.id: category.name
            for category in categories
        }

        category_report = []

        for category_id, count in category_counts.most_common():
            category_report.append({
                "name": category_names.get(category_id, "Uncategorized"),
                "count": count,
                "percentage": round(
                    (count / total_tickets) * 100,
                    1
                ) if total_tickets else 0
            })

        escalated_tickets = [
            ticket for ticket in tickets
            if ticket.is_escalated
        ]

        overdue_tickets = [
            ticket for ticket in tickets
            if (
                ticket.due_date
                and ticket.due_date < now
                and ticket.status != "CLOSED"
            )
        ]

        active_agents = [
            user for user in users
            if (
                user.is_active
                and user.role
                and user.role.name == "AGENT"
            )
        ]

        agent_workload = []

        for agent in active_agents:
            assignments = TicketAssignmentDAO.get_by_agent(agent.id)

            ticket_ids = {
                assignment.ticket_id
                for assignment in assignments
            }

            agent_tickets = [
                ticket for ticket in tickets
                if ticket.id in ticket_ids
            ]

            closed = sum(
                1
                for ticket in agent_tickets
                if ticket.status == "CLOSED"
            )

            open_work = sum(
                1
                for ticket in agent_tickets
                if ticket.status != "CLOSED"
            )

            agent_workload.append({
                "name": agent.name,
                "email": agent.email,
                "active": open_work,
                "closed": closed,
                "total": len(agent_tickets)
            })

        agent_workload.sort(
            key=lambda item: item["active"],
            reverse=True
        )

        selected_ticket_ids = {
            ticket.id
            for ticket in tickets
        }

        filtered_feedback = [
            feedback for feedback in feedback_list
            if feedback.ticket_id in selected_ticket_ids
        ]

        feedback_count = len(filtered_feedback)

        average_rating = round(
            sum(
                feedback.rating
                for feedback in filtered_feedback
            ) / feedback_count,
            2
        ) if feedback_count else 0

        rating_distribution = []

        for rating in range(5, 0, -1):
            count = sum(
                1
                for feedback in filtered_feedback
                if feedback.rating == rating
            )

            rating_distribution.append({
                "rating": rating,
                "count": count
            })

        feedback_details = []

        for feedback in filtered_feedback:
            ticket = next(
                (
                    ticket
                    for ticket in tickets
                    if ticket.id == feedback.ticket_id
                ),
                None
            )

            assignments = TicketAssignmentDAO.get_by_ticket(
                feedback.ticket_id
            )

            latest_assignment = assignments[0] if assignments else None

            feedback_details.append({
                "ticket_id": feedback.ticket_id,
                "ticket_title": (
                    ticket.title
                    if ticket
                    else "Unknown Ticket"
                ),
                "employee_name": (
                    feedback.user.name
                    if feedback.user
                    else "Unknown Employee"
                ),
                "employee_email": (
                    feedback.user.email
                    if feedback.user
                    else ""
                ),
                "rating": feedback.rating,
                "comment": (
                    feedback.comment
                    or "No comment provided."
                ),
                "agent_name": (
                    latest_assignment.agent.name
                    if (
                        latest_assignment
                        and latest_assignment.agent
                    )
                    else "Unassigned"
                ),
                "created_at": feedback.created_at
            })

        feedback_details.sort(
            key=lambda item: item["created_at"] or datetime.min,
            reverse=True
        )

        recent_closed = sorted(
            [
                ticket
                for ticket in tickets
                if ticket.status == "CLOSED"
            ],
            key=lambda ticket: (
                ticket.closed_at
                or ticket.updated_at
                or ticket.created_at
            ),
            reverse=True
        )[:10]

        monthly_counter = defaultdict(int)

        for ticket in tickets:
            if ticket.created_at:
                key = ticket.created_at.strftime("%Y-%m")
                monthly_counter[key] += 1

        monthly_report = []

        for month_key in sorted(
            monthly_counter.keys(),
            reverse=True
        )[:6]:
            month_date = datetime.strptime(
                month_key,
                "%Y-%m"
            )

            monthly_report.append({
                "label": month_date.strftime("%b %Y"),
                "count": monthly_counter[month_key]
            })

        monthly_report.reverse()

        return {
            "period": period,
            "total_tickets": total_tickets,
            "open_tickets": status_counts.get("OPEN", 0),
            "assigned_tickets": status_counts.get("ASSIGNED", 0),
            "in_progress_tickets": status_counts.get("IN_PROGRESS", 0),
            "resolved_tickets": status_counts.get("RESOLVED", 0),
            "closed_tickets": status_counts.get("CLOSED", 0),
            "escalated_tickets": len(escalated_tickets),
            "overdue_tickets": len(overdue_tickets),
            "status_report": status_report,
            "priority_report": priority_report,
            "category_report": category_report,
            "agent_workload": agent_workload,
            "feedback_count": feedback_count,
            "average_rating": average_rating,
            "rating_distribution": rating_distribution,
            "feedback_details": feedback_details,
            "recent_closed": recent_closed,
            "monthly_report": monthly_report
        }