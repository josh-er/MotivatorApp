import os
from functools import wraps
from flask import request, abort

ADMIN_KEY = os.getenv("ADMIN_KEY")

def require_admin_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-Admin-Key")
        if not key or key != ADMIN_KEY:
            abort(401)
        return fn(*args, **kwargs)
    return wrapper
