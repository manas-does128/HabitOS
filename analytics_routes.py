from flask import Blueprint, render_template, session, jsonify, request
from utils.auth import login_required, get_current_user
from utils.analytics import get_habit_chart_data, get_dsa_chart_data, get_weekly_stats
from utils.db import get_db
from bson import ObjectId
from datetime import datetime, timedelta

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def index():
    user = get_current_user()
    db = get_db()
    uid = ObjectId(session["user_id"])
    stats = get_weekly_stats(session["user_id"])
    habit_chart = get_habit_chart_data(session["user_id"])
    dsa_chart = get_dsa_chart_data(session["user_id"])

    today = datetime.utcnow()
    monthly_labels, monthly_data = [], []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        monthly_labels.append(day.strftime("%b %d"))
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        count = 0
        for habit in db.habits.find({"user_id": uid}):
            for c in habit.get("completions", []):
                if isinstance(c, datetime) and start <= c < end:
                    count += 1
        monthly_data.append(count)

    problems = list(db.dsa_problems.find({"user_id": uid}))
    topic_counts = {}
    for p in problems:
        for tag in p.get("topic_tags", []):
            topic_counts[tag] = topic_counts.get(tag, 0) + 1

    return render_template("analytics.html",
        user=user, stats=stats,
        habit_chart=habit_chart, dsa_chart=dsa_chart,
        monthly_labels=monthly_labels, monthly_data=monthly_data,
        topic_counts=topic_counts,
        all_problems=problems
    )

@analytics_bp.route("/analytics/data")
@login_required
def data():
    return jsonify({
        "habit_chart": get_habit_chart_data(session["user_id"]),
        "dsa_chart": get_dsa_chart_data(session["user_id"]),
        "stats": get_weekly_stats(session["user_id"])
    })

@analytics_bp.route("/analytics/day")
@login_required
def day_analytics():
    date_str = request.args.get("date", "")
    if not date_str:
        return jsonify({"error": "date required"}), 400
    try:
        day = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "invalid date"}), 400

    db = get_db()
    uid = ObjectId(session["user_id"])
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    # Habits completed on this day
    habits_completed = 0
    for habit in db.habits.find({"user_id": uid}):
        for c in habit.get("completions", []):
            if isinstance(c, datetime) and start <= c < end:
                habits_completed += 1

    # Tasks completed on this day
    tasks_done = db.tasks.count_documents({
        "user_id": uid, "status": "done",
        "updated_at": {"$gte": start, "$lt": end}
    })

    # DSA problems on this day
    dsa_solved = db.dsa_problems.count_documents({
        "user_id": uid,
        "solved_at": {"$gte": start, "$lt": end}
    })

    return jsonify({
        "date": date_str,
        "habits_completed": habits_completed,
        "tasks_done": tasks_done,
        "dsa_solved": dsa_solved
    })
