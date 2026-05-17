from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.auth import login_required, get_current_user
from utils.db import get_db
from models.task_model import create_task
from bson import ObjectId
from datetime import datetime

task_bp = Blueprint("tasks", __name__)

@task_bp.route("/tasks")
@login_required
def index():
    user = get_current_user()
    db = get_db()
    uid = ObjectId(session["user_id"])
    tasks_col    = list(db.tasks.find({"user_id": uid, "status": "todo"}).sort("created_at", -1))
    started_col  = list(db.tasks.find({"user_id": uid, "status": "started"}).sort("created_at", -1))
    inprog_col   = list(db.tasks.find({"user_id": uid, "status": "in_progress"}).sort("created_at", -1))
    done_col     = list(db.tasks.find({"user_id": uid, "status": "done"}).sort("created_at", -1))
    return render_template("kanban.html", user=user,
        todo=tasks_col, started=started_col,
        in_progress=inprog_col, done=done_col)

# Keep old /kanban route as alias
@task_bp.route("/kanban")
@login_required
def kanban_redirect():
    return redirect(url_for("tasks.index"))

@task_bp.route("/tasks/add", methods=["POST"])
@login_required
def add():
    db = get_db()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "")
    priority = request.form.get("priority", "medium")
    due_date_str = request.form.get("due_date", "")
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError:
            pass
    if not title:
        return jsonify({"error": "Title required"}), 400
    task = create_task(session["user_id"], title, description, priority, due_date)
    result = db.tasks.insert_one(task)
    return jsonify({"status": "ok", "id": str(result.inserted_id)})

@task_bp.route("/tasks/update/<task_id>", methods=["POST"])
@login_required
def update(task_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    data = request.get_json() or request.form.to_dict()
    allowed = ["status", "title", "description", "priority", "due_date"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    update_data["updated_at"] = datetime.utcnow()
    db.tasks.update_one({"_id": ObjectId(task_id), "user_id": uid}, {"$set": update_data})
    return jsonify({"status": "ok"})

@task_bp.route("/tasks/delete/<task_id>", methods=["POST"])
@login_required
def delete(task_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    db.tasks.delete_one({"_id": ObjectId(task_id), "user_id": uid})
    return jsonify({"status": "ok"})

@task_bp.route("/tasks/all")
@login_required
def get_all():
    db = get_db()
    uid = ObjectId(session["user_id"])
    tasks = list(db.tasks.find({"user_id": uid}).sort("created_at", -1))
    result = []
    for t in tasks:
        result.append({
            "id": str(t["_id"]),
            "title": t["title"],
            "description": t.get("description", ""),
            "priority": t.get("priority", "medium"),
            "status": t.get("status", "todo"),
            "due_date": t["due_date"].strftime("%Y-%m-%d") if t.get("due_date") else "",
            "created_at": t["created_at"].strftime("%Y-%m-%d") if t.get("created_at") else ""
        })
    return jsonify(result)
