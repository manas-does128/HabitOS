from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.auth import login_required, get_current_user
from utils.db import get_db
from models.user_model import check_password
from bson import ObjectId
import bcrypt
from datetime import datetime
from utils.helpers import calculate_streak

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
@login_required
def index():
    user = get_current_user()
    db = get_db()
    uid = ObjectId(session["user_id"])

    habits = list(db.habits.find({"user_id": uid, "active": True}))
    total_habits = len(habits)

    all_completions = []
    for h in habits:
        all_completions.extend(h.get("completions", []))
    current_streak = calculate_streak(all_completions)

    dsa_count = db.dsa_problems.count_documents({"user_id": uid})
    tasks_done = db.tasks.count_documents({"user_id": uid, "status": "done"})
    coding_profiles = list(db.coding_profiles.find({"user_id": uid}))

    return render_template("profile.html",
        user=user,
        total_habits=total_habits,
        current_streak=current_streak,
        dsa_count=dsa_count,
        tasks_done=tasks_done,
        coding_profiles=coding_profiles
    )

@profile_bp.route("/profile/update", methods=["POST"])
@login_required
def update():
    db = get_db()
    uid = ObjectId(session["user_id"])
    bio = request.form.get("bio", "").strip()
    db.users.update_one({"_id": uid}, {"$set": {"bio": bio}})
    flash("Profile updated!", "success")
    return redirect(url_for("profile.index"))

@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    db = get_db()
    uid = ObjectId(session["user_id"])
    user = get_current_user()
    current = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    if not check_password(user["password"], current):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile.index"))
    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "danger")
        return redirect(url_for("profile.index"))
    if new_pw != confirm:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("profile.index"))

    hashed = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt())
    db.users.update_one({"_id": uid}, {"$set": {"password": hashed}})
    flash("Password changed successfully!", "success")
    return redirect(url_for("profile.index"))
