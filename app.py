import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from utils.db import init_db

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "habitos-dev-secret-2024")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/habitos")

    # Initialize DB
    init_db(app)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.habit_routes import habit_bp
    from routes.task_routes import task_bp
    from routes.analytics_routes import analytics_bp
    from routes.profile_routes import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(habit_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(analytics_bp)
    from routes.dsa_routes import dsa_bp
    app.register_blueprint(dsa_bp)
    app.register_blueprint(profile_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
