from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db
from models.user_model import create_user, check_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        # Detect email vs username
        if "@" in identifier:
            user = db.users.find_one({"email": identifier.lower()})
        else:
            user = db.users.find_one({"username": identifier})
            if not user:
                user = db.users.find_one({"username": {"$regex": f"^{identifier}$", "$options": "i"}})
        if user and check_password(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}! 🚀", "success")
            return redirect(url_for("dashboard.index"))
        flash("Invalid credentials. Check your email/username and password.", "danger")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        db = get_db()
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")
        if db.users.find_one({"email": email}):
            flash("Email already registered.", "danger")
            return render_template("register.html")
        if db.users.find_one({"username": username}):
            flash("Username already taken.", "danger")
            return render_template("register.html")
        user_doc = create_user(username, email, password)
        result = db.users.insert_one(user_doc)
        session["user_id"] = str(result.inserted_id)
        session["username"] = username
        flash(f"Account created! Welcome to HabitOS, {username}! 🎯", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("auth.login"))
