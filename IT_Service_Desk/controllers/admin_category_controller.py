from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from services.ticket_category_service import TicketCategoryService

admin_category_bp = Blueprint('admin_category', __name__, url_prefix='/admin/categories')
category_service = TicketCategoryService()

def _require_admin():
    if 'user_id' not in session:
        return redirect(url_for('user_controller.admin_login'))
    if session.get('role') != 'ADMIN':
        flash('Administrator privileges are required.', 'danger')
        return redirect(url_for('user_controller.admin_login'))
    return None

@admin_category_bp.route('/', methods=['GET'])
def manage_categories():
    auth = _require_admin()
    if auth:
        return auth
    try:
        categories = category_service.get_all_categories(session['user_id'])
        return render_template('admin_categories.html', categories=categories, name=session.get('user_name'), email=session.get('user_email'), role=session.get('role'))
    except Exception:
        current_app.logger.exception('Failed to load ticket categories.')
        flash('Unable to load ticket categories.', 'danger')
        return render_template('admin_categories.html', categories=[], name=session.get('user_name'), email=session.get('user_email'), role=session.get('role')), 500

@admin_category_bp.route('/create', methods=['POST'])
def create_category():
    auth = _require_admin()
    if auth:
        return auth
    try:
        category_service.create_category(session['user_id'], request.form.get('name', ''), request.form.get('description', ''))
        flash('Category created successfully.', 'success')
    except (ValueError, PermissionError) as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Failed to create category.')
        flash('Unable to create category.', 'danger')
    return redirect(url_for('admin_category.manage_categories'))

@admin_category_bp.route('/<int:category_id>/update', methods=['POST'])
def update_category(category_id):
    auth = _require_admin()
    if auth:
        return auth
    try:
        category_service.update_category(session['user_id'], category_id, request.form.get('name', ''), request.form.get('description', ''))
        flash('Category updated successfully.', 'success')
    except (ValueError, PermissionError) as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Failed to update category %s.', category_id)
        flash('Unable to update category.', 'danger')
    return redirect(url_for('admin_category.manage_categories'))

@admin_category_bp.route('/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    auth = _require_admin()
    if auth:
        return auth
    try:
        category_service.delete_category(session['user_id'], category_id)
        flash('Category deleted successfully.', 'success')
    except (ValueError, PermissionError) as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Failed to delete category %s.', category_id)
        flash('Unable to delete category.', 'danger')
    return redirect(url_for('admin_category.manage_categories'))
