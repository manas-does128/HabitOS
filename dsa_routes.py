from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.auth import login_required, get_current_user
from utils.db import get_db
from models.dsa_model import create_dsa_problem
from bson import ObjectId
from datetime import datetime

dsa_bp = Blueprint("dsa", __name__)

@dsa_bp.route("/dsa")
@login_required
def index():
    user = get_current_user()
    db = get_db()
    uid = ObjectId(session["user_id"])
    problems = list(db.dsa_problems.find({"user_id": uid}).sort("solved_at", -1))
    sheets = list(db.dsa_sheets.find({"user_id": uid}))

    easy   = sum(1 for p in problems if p.get("difficulty") == "Easy")
    medium = sum(1 for p in problems if p.get("difficulty") == "Medium")
    hard   = sum(1 for p in problems if p.get("difficulty") == "Hard")

    topic_counts = {}
    for p in problems:
        for tag in p.get("topic_tags", []):
            topic_counts[tag] = topic_counts.get(tag, 0) + 1

    platform_counts = {}
    for p in problems:
        plat = p.get("platform", "Other")
        platform_counts[plat] = platform_counts.get(plat, 0) + 1

    return render_template("dsa.html",
        user=user, problems=problems, sheets=sheets,
        easy=easy, medium=medium, hard=hard,
        total=len(problems),
        topic_counts=topic_counts,
        platform_counts=platform_counts
    )

@dsa_bp.route("/dsa/add", methods=["POST"])
@login_required
def add():
    db = get_db()
    title      = request.form.get("title","").strip()
    difficulty = request.form.get("difficulty","Easy")
    platform   = request.form.get("platform","LeetCode")
    tags_raw   = request.form.get("tags","")
    notes      = request.form.get("notes","")
    url        = request.form.get("url","")
    topic_tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    if not title:
        flash("Problem title is required.", "danger")
        return redirect(url_for("dsa.index"))
    problem = create_dsa_problem(session["user_id"], title, difficulty, platform, topic_tags, notes, url)
    db.dsa_problems.insert_one(problem)
    flash(f"Problem '{title}' added! 💪", "success")
    return redirect(url_for("dsa.index"))

@dsa_bp.route("/dsa/delete/<problem_id>", methods=["POST"])
@login_required
def delete(problem_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    db.dsa_problems.delete_one({"_id": ObjectId(problem_id), "user_id": uid})
    return jsonify({"status": "ok"})

@dsa_bp.route("/dsa/stats")
@login_required
def stats():
    db = get_db()
    uid = ObjectId(session["user_id"])
    problems = list(db.dsa_problems.find({"user_id": uid}))
    topic_counts = {}
    for p in problems:
        for tag in p.get("topic_tags", []):
            topic_counts[tag] = topic_counts.get(tag, 0) + 1
    return jsonify({
        "easy":   sum(1 for p in problems if p.get("difficulty") == "Easy"),
        "medium": sum(1 for p in problems if p.get("difficulty") == "Medium"),
        "hard":   sum(1 for p in problems if p.get("difficulty") == "Hard"),
        "total":  len(problems),
        "topics": topic_counts
    })

# DSA Sheet routes
@dsa_bp.route("/dsa/sheets/add", methods=["POST"])
@login_required
def add_sheet():
    db = get_db()
    uid = ObjectId(session["user_id"])
    name     = request.form.get("sheet_name","").strip()
    url      = request.form.get("sheet_url","").strip()
    topics_raw = request.form.get("sheet_topics","").strip()
    total_raw  = request.form.get("sheet_total","0")
    if not name or not url:
        flash("Sheet name and URL are required.", "danger")
        return redirect(url_for("dsa.index"))
    topics = [t.strip() for t in topics_raw.split(",") if t.strip()]
    try:
        total = int(total_raw)
    except ValueError:
        total = 0
    sheet = {
        "user_id": uid,
        "name": name,
        "url": url,
        "topics": topics,
        "total_problems": total,
        "solved_problems": 0,
        "created_at": datetime.utcnow()
    }
    db.dsa_sheets.insert_one(sheet)
    flash(f"Sheet '{name}' added!", "success")
    return redirect(url_for("dsa.index"))

@dsa_bp.route("/dsa/sheets/delete/<sheet_id>", methods=["POST"])
@login_required
def delete_sheet(sheet_id):
    db = get_db()
    uid = ObjectId(session["user_id"])
    db.dsa_sheets.delete_one({"_id": ObjectId(sheet_id), "user_id": uid})
    return jsonify({"status": "ok"})
