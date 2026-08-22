from flask import Blueprint, flash, redirect, request, session, url_for, current_app
from services.feedback_service import FeedbackService

feedback_bp = Blueprint('feedback', __name__, url_prefix='/tickets')

@feedback_bp.route('/<int:ticket_id>/feedback', methods=['POST'])
def submit_feedback(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('user_controller.employee_login'))
    try:
        FeedbackService.submit_feedback(
            user_id=session['user_id'],
            ticket_id=ticket_id,
            rating=request.form.get('rating'),
            comment=request.form.get('comment', '')
        )
        flash('Thank you. Your feedback was submitted successfully.', 'success')
    except (ValueError, PermissionError) as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Failed to submit feedback for ticket %s.', ticket_id)
        flash('Unable to submit feedback.', 'danger')
    return redirect(url_for('ticket_controller.ticket_details', ticket_id=ticket_id))
