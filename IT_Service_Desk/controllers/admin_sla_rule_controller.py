from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app

from services.sla_rule_service import SLARuleService


admin_sla_rule_bp = Blueprint(
    "admin_sla_rule",
    __name__,
    url_prefix="/admin/sla-rules",
)

sla_service = SLARuleService()


def _require_admin():
    if "user_id" not in session:
        return redirect(url_for("user_controller.admin_login"))

    if session.get("role") != "ADMIN":
        flash("Administrator privileges are required.", "danger")
        return redirect(url_for("user_controller.admin_login"))

    return None


@admin_sla_rule_bp.route("/", methods=["GET"])
def manage_rules():
    auth_check = _require_admin()
    if auth_check:
        return auth_check

    admin_id = session.get("user_id")

    try:
        sla_service.ensure_default_rules()
        rules = sla_service.get_all_rules(admin_id=admin_id)
        return render_template(
            "admin_sla_rules.html",
            rules=rules,
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role"),
        )
    except Exception:
        current_app.logger.exception("Failed to load SLA rules.")
        flash("Unable to load SLA rules.", "danger")
        return render_template(
            "admin_sla_rules.html",
            rules=[],
            name=session.get("user_name"),
            email=session.get("user_email"),
            role=session.get("role"),
        ), 500


@admin_sla_rule_bp.route("/create", methods=["POST"])
def create_rule():
    auth_check = _require_admin()
    if auth_check:
        return auth_check

    try:
        sla_service.create_rule(
            admin_id=session.get("user_id"),
            priority=request.form.get("priority"),
            response_time_minutes=request.form.get("response_time_minutes"),
            resolution_time_minutes=request.form.get("resolution_time_minutes"),
        )
        flash("SLA rule created successfully.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Failed to create SLA rule.")
        flash("Unable to create SLA rule.", "danger")

    return redirect(url_for("admin_sla_rule.manage_rules"))


@admin_sla_rule_bp.route("/<int:rule_id>/update", methods=["POST"])
def update_rule(rule_id):
    auth_check = _require_admin()
    if auth_check:
        return auth_check

    try:
        sla_service.update_rule(
            admin_id=session.get("user_id"),
            rule_id=rule_id,
            response_time_minutes=request.form.get("response_time_minutes"),
            resolution_time_minutes=request.form.get("resolution_time_minutes"),
        )
        flash("SLA rule updated successfully.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Failed to update SLA rule %s.", rule_id)
        flash("Unable to update SLA rule.", "danger")

    return redirect(url_for("admin_sla_rule.manage_rules"))


@admin_sla_rule_bp.route("/<int:rule_id>/delete", methods=["POST"])
def delete_rule(rule_id):
    auth_check = _require_admin()
    if auth_check:
        return auth_check

    try:
        sla_service.delete_rule(
            admin_id=session.get("user_id"),
            rule_id=rule_id,
        )
        flash("SLA rule deleted successfully.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Failed to delete SLA rule %s.", rule_id)
        flash("Unable to delete SLA rule.", "danger")

    return redirect(url_for("admin_sla_rule.manage_rules"))