from flask import Blueprint, render_template
from .auth import require_admin_key
from .services import get_all_users

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/users")
@require_admin_key
def users():
    users = get_all_users()
    return render_template("admin/users.html", users=users)
