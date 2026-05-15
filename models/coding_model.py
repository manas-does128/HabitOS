from datetime import datetime
from bson import ObjectId

def create_coding_profile(user_id, platform, username):
    return {
        "user_id": ObjectId(user_id),
        "platform": platform,
        "username": username,
        "stats": {},
        "last_fetched": None,
        "created_at": datetime.utcnow()
    }
