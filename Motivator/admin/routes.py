from flask import Blueprint, render_template
from .auth import require_admin_key
from .services import get_all_users, get_message_logs
from flask import request
from datetime import datetime, date

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/users")
@require_admin_key
def users():
    users = get_all_users()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/logs")
@require_admin_key
def logs():
    from Motivator.db import engine
    print("ADMIN DB URL:", engine.url)

    status = request.args.get("status")
    phone = request.args.get("phone")
    limit = int(request.args.get("limit", 100))
    since_date = request.args.get("since_date")

    logs = get_message_logs(
        status=status,
        phone=phone,
        since_date=since_date,
        limit=limit
    )
    return render_template("admin/logs.html", logs=logs)