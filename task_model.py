from datetime import datetime
from bson import ObjectId

def create_task(user_id, title, description="", priority="medium", due_date=None, status="todo"):
    return {
        "user_id": ObjectId(user_id),
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
