from flask import Blueprint, render_template
from .auth import require_admin_key
from .services import get_all_users, get_message_logs

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/users")
@require_admin_key
def users():
    users = get_all_users()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/logs")
@require_admin_key
def logs():
    logs = get_message_logs()
    return render_template("admin/logs.html", logs=logs)