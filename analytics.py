from datetime import datetime, timedelta
from utils.db import get_db
from bson import ObjectId

def get_weekly_stats(user_id):
    db = get_db()
    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)
    uid = ObjectId(user_id)

    habits = list(db.habits.find({"user_id": uid}))
    total_habits = len(habits)
    completed_this_week = 0
    for habit in habits:
        completions = habit.get("completions", [])
        for c in completions:
            if isinstance(c, datetime) and c >= week_ago:
                completed_this_week += 1

    dsa_count = db.dsa_problems.count_documents({"user_id": uid})
    tasks_done = db.tasks.count_documents({"user_id": uid, "status": "done"})

    return {
        "total_habits": total_habits,
        "completed_this_week": completed_this_week,
        "dsa_count": dsa_count,
        "tasks_done": tasks_done
    }

def get_habit_chart_data(user_id):
    db = get_db()
    uid = ObjectId(user_id)
    today = datetime.utcnow()
    labels = []
    data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        label = day.strftime("%a")
        labels.append(label)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        count = 0
        habits = db.habits.find({"user_id": uid})
        for habit in habits:
            for c in habit.get("completions", []):
                if isinstance(c, datetime) and start <= c < end:
                    count += 1
        data.append(count)
    return {"labels": labels, "data": data}

def get_dsa_chart_data(user_id):
    db = get_db()
    uid = ObjectId(user_id)
    easy = db.dsa_problems.count_documents({"user_id": uid, "difficulty": "Easy"})
    medium = db.dsa_problems.count_documents({"user_id": uid, "difficulty": "Medium"})
    hard = db.dsa_problems.count_documents({"user_id": uid, "difficulty": "Hard"})
    return {"easy": easy, "medium": medium, "hard": hard}
