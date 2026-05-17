from datetime import datetime
import bcrypt

def create_user(username, email, password):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return {
        "username": username,
        "email": email,
        "password": hashed,
        "avatar": "",
        "bio": "",
        "created_at": datetime.utcnow(),
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }

def check_password(stored_hash, password):
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
