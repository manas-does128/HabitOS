from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.auth import login_required, get_current_user
from utils.db import get_db
from models.habit_model import create_habit, is_completed_today
from bson import ObjectId
from datetime import datetime

habit_bp = Blueprint("habits", __name__)

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def _today_name():
    return datetime.utcnow().strftime("%A")   # e.g. "Monday"

@habit_bp.route("/habits")
@login_required
def index():
    user = get_current_user()
    db = get_db()
    uid = ObjectId(session["user_id"])
    habits = list(db.habits.find({"user_id": uid, "active": True}).sort("created_at", -1))
    for habit in habits:
        habit["completed_today"] = is_completed_today(habit)
        habit["completion_rate"] = get_completion_rate(habit)
        habit["streak"] = get_habit_streak(habit)
    return render_template("habits.html", user=user, habits=habits, DAYS=DAYS)

@habit_bp.route("/habits/add", methods=["POST"])
@login_required
def add():
    db = get_db()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "General")
    description = request.form.get("description", "")
    color = request.form.get("color", "#888888")
    days_of_week = request.form.getlist("days_of_week")  # multi-select list
    if not days_of_week:
        days_of_week = DAYS  # default: every day
    if not name:
        flash("Habit name is required.", "danger")
        return redirect(url_for("habits.index"))
    habit = create_habit(session["user_id"], name, category, description, color=color)
    habit["days_of_week"] = days_of_week
    db.habits.insert_one(habit)
    flash(f"Habit '{name}' created!", "success")
    return redirect(url_for("habits.index"))

@habit_bp.route("/habits/complete/<habit_id>", methods=["POST"])
@login_required
def complete(habit_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    habit = db.habits.find_one({"_id": ObjectId(habit_id), "user_id": uid})
    if not habit:
        return jsonify({"error": "Not found"}), 404
    today = datetime.utcnow().date()
    already_done = any(
        isinstance(c, datetime) and c.date() == today
        for c in habit.get("completions", [])
    )
    if already_done:
        db.habits.update_one(
            {"_id": ObjectId(habit_id)},
            {"$pull": {"completions": {"$gte": datetime.combine(today, datetime.min.time()),
                                        "$lt": datetime.combine(today, datetime.max.time())}}}
        )
        return jsonify({"status": "uncompleted"})
    else:
        db.habits.update_one(
            {"_id": ObjectId(habit_id)},
            {"$push": {"completions": datetime.utcnow()}}
        )
        return jsonify({"status": "completed"})

@habit_bp.route("/habits/edit/<habit_id>", methods=["POST"])
@login_required
def edit(habit_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "General")
    description = request.form.get("description", "")
    color = request.form.get("color", "#888888")
    days_of_week = request.form.getlist("days_of_week")
    if not days_of_week:
        days_of_week = DAYS
    db.habits.update_one(
        {"_id": ObjectId(habit_id), "user_id": uid},
        {"$set": {"name": name, "category": category, "description": description,
                  "color": color, "days_of_week": days_of_week}}
    )
    flash("Habit updated!", "success")
    return redirect(url_for("habits.index"))

@habit_bp.route("/habits/delete/<habit_id>", methods=["POST"])
@login_required
def delete(habit_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    db.habits.update_one(
        {"_id": ObjectId(habit_id), "user_id": uid},
        {"$set": {"active": False}}
    )
    flash("Habit deleted.", "info")
    return redirect(url_for("habits.index"))

@habit_bp.route("/habits/calendar/<habit_id>")
@login_required
def calendar(habit_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    habit = db.habits.find_one({"_id": ObjectId(habit_id), "user_id": uid})
    if not habit:
        return jsonify({"error": "Not found"}), 404
    completions = [c.strftime("%Y-%m-%d") for c in habit.get("completions", []) if isinstance(c, datetime)]
    return jsonify({"completions": completions, "name": habit["name"]})

def _is_scheduled_today(habit):
    """Return True if habit is scheduled for today's weekday (or has no days set = every day)."""
    days = habit.get("days_of_week", [])
    if not days:
        return True
    return _today_name() in days

def get_completion_rate(habit, days=30):
    from datetime import timedelta
    today = datetime.utcnow().date()
    start = today - timedelta(days=days)
    completed_days = set()
    for c in habit.get("completions", []):
        if isinstance(c, datetime):
            d = c.date()
            if d >= start:
                completed_days.add(d)
    return round(len(completed_days) / days * 100, 1)

def get_habit_streak(habit):
    from datetime import timedelta
    today = datetime.utcnow().date()
    dates = set()
    for c in habit.get("completions", []):
        if isinstance(c, datetime):
            dates.add(c.date())
    streak = 0
    current = today
    while current in dates:
        streak += 1
        current -= timedelta(days=1)
    return streak