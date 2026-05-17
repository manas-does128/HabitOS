from datetime import datetime
from bson import ObjectId

def create_habit(user_id, name, category, description="", frequency="daily", color="#7c3aed"):
    return {
        "user_id": ObjectId(user_id),
        "name": name,
        "category": category,
        "description": description,
        "frequency": frequency,
        "color": color,
        "completions": [],
        "streak": 0,
        "created_at": datetime.utcnow(),
        "active": True
    }

def is_completed_today(habit):
    today = datetime.utcnow().date()
    for c in habit.get("completions", []):
        if isinstance(c, datetime) and c.date() == today:
            return True
    return False

def get_completion_rate(habit, days=30):
    from datetime import timedelta
    today = datetime.utcnow().date()
    start = today - timedelta(days=days)
    completions = habit.get("completions", [])
    completed_days = set()
    for c in completions:
        if isinstance(c, datetime):
            d = c.date()
            if d >= start:
                completed_days.add(d)
    return round(len(completed_days) / days * 100, 1)
