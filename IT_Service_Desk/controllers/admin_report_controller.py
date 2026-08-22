from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from services.report_service import ReportService

admin_report_bp = Blueprint("admin_report", __name__, url_prefix="/admin/reports")

report_service = ReportService()

def _require_admin():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("user_controller.admin_login"))

    if session.get("role") != "ADMIN":
        flash("Administrator privileges are required.", "danger")
        return redirect(url_for("user_controller.admin_login"))

    return None

@admin_report_bp.route("/", methods=["GET"])
def reports():
    auth_check = _require_admin()

    if auth_check:
        return auth_check

    period = request.args.get("period", "all").strip()

    if period not in {"all", "7", "30", "90", "365"}:
        period = "all"

    try:
        report = report_service.build_report(period=period)

        return render_template(
            "reports.html",
            report=report,
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )

    except Exception:
        current_app.logger.exception("Failed to generate admin reports.")

        flash("Unable to generate reports.", "danger")

        return render_template(
            "reports.html",
            report={
                "period": period,
                "total_tickets": 0,
                "open_tickets": 0,
                "assigned_tickets": 0,
                "in_progress_tickets": 0,
                "resolved_tickets": 0,
                "closed_tickets": 0,
                "escalated_tickets": 0,
                "overdue_tickets": 0,
                "status_report": [],
                "priority_report": [],
                "category_report": [],
                "agent_workload": [],
                "feedback_count": 0,
                "average_rating": 0,
                "rating_distribution": [],
                "feedback_details": [],
                "recent_closed": [],
                "monthly_report": []
            },
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role")
        )