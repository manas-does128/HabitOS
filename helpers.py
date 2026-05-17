from datetime import datetime, timedelta
from bson import ObjectId
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_week_dates():
    today = datetime.utcnow().date()
    start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]

def get_month_dates():
    today = datetime.utcnow()
    start = today.replace(day=1)
    days = (today - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]

def calculate_streak(completions):
    if not completions:
        return 0
    today = datetime.utcnow().date()
    streak = 0
    current = today
    dates = sorted([c.date() if isinstance(c, datetime) else c for c in completions], reverse=True)
    date_set = set(dates)
    while current in date_set:
        streak += 1
        current -= timedelta(days=1)
    return streak

def format_date(dt):
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d") if dt else ""
