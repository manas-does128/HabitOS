from flask import Blueprint, render_template, session
from utils.auth import login_required, get_current_user
from utils.analytics import get_habit_chart_data, get_dsa_chart_data
from utils.db import get_db
from bson import ObjectId
from datetime import datetime, timedelta
from models.habit_model import is_completed_today
from utils.helpers import calculate_streak as calc_streak

dashboard_bp = Blueprint("dashboard", __name__)

def _today_name():
    return datetime.utcnow().strftime("%A")

def _is_scheduled_today(habit):
    days = habit.get("days_of_week", [])
    if not days:
        return True
    return _today_name() in days

@dashboard_bp.route("/dashboard")
@login_required
def index():
    user = get_current_user()
    db = get_db()
    uid = ObjectId(session["user_id"])

    all_habits = list(db.habits.find({"user_id": uid, "active": True}))
    for habit in all_habits:
        habit["completed_today"] = is_completed_today(habit)
        habit["completion_rate"] = _completion_rate(habit)

    # Filter to only today's scheduled habits for the dashboard widget
    todays_habits = [h for h in all_habits if _is_scheduled_today(h)]
    habits_done_today = sum(1 for h in todays_habits if h["completed_today"])

    all_completions = []
    for h in all_habits:
        all_completions.extend(h.get("completions", []))
    current_streak = calc_streak(all_completions)

    tasks       = list(db.tasks.find({"user_id": uid}).sort("created_at", -1).limit(5))
    tasks_todo  = db.tasks.count_documents({"user_id": uid, "status": {"$in": ["todo","started","in_progress"]}})
    tasks_done  = db.tasks.count_documents({"user_id": uid, "status": "done"})

    habit_chart = get_habit_chart_data(session["user_id"])

    return render_template("dashboard.html",
        user=user,
        habits=todays_habits,           # only today's scheduled habits
        total_habits=len(todays_habits),
        habits_done_today=habits_done_today,
        current_streak=current_streak,
        tasks=tasks,
        tasks_todo=tasks_todo,
        tasks_done=tasks_done,
        habit_chart=habit_chart,
    )

def _completion_rate(habit, days=30):
    today = datetime.utcnow().date()
    start = today - timedelta(days=days)
    done = set()
    for c in habit.get("completions", []):
        if isinstance(c, datetime) and c.date() >= start:
            done.add(c.date())
    return round(len(done) / days * 100, 1)