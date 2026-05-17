from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    from utils.db import get_db
    from bson import ObjectId
    if "user_id" not in session:
        return None
    db = get_db()
    return db.users.find_one({"_id": ObjectId(session["user_id"])})
