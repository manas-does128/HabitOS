from datetime import datetime
from bson import ObjectId

def create_dsa_problem(user_id, title, difficulty, platform, topic_tags=None, notes="", url=""):
    return {
        "user_id": ObjectId(user_id),
        "title": title,
        "difficulty": difficulty,
        "platform": platform,
        "topic_tags": topic_tags or [],
        "notes": notes,
        "url": url,
        "solved_at": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
