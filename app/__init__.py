import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from datetime import datetime
from flask_mail import Mail, Message
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
mail = Mail()
scheduler = APScheduler()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()


def check_reminders(app):
    """Background job to send due reminders."""
    from app.models import Reminder  # avoid circular import
    
    with app.app_context():
        now = datetime.utcnow()
        due = Reminder.query.filter(
            Reminder.remind_at <= now,
            Reminder.sent.is_(False)
        ).all()
        for r in due:
            try:
                msg = Message("Your Reminder", recipients=[r.user.email], body=r.message)
                mail.send(msg)
                r.sent = True
            except Exception as e:
                print(f"Error sending reminder {r.id}: {e}")
        db.session.commit()


def create_app():
    app = Flask(__name__)
    
    # Basic Flask configuration
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["WTF_CSRF_ENABLED"] = os.environ.get("WTF_CSRF_ENABLED", "True").lower() == "true"
    app.config["WTF_CSRF_TIME_LIMIT"] = int(os.environ.get("WTF_CSRF_TIME_LIMIT", "3600"))

    # Database configuration
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url and database_url != "":
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # Fallback to absolute path
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'site.db'))
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail configuration
    app.config.update(
        MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.environ.get("MAIL_PORT", "587")),
        MAIL_USE_TLS=os.environ.get("MAIL_USE_TLS", "True").lower() == "true",
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME", "noreply@example.com"))
    )

    # Development features
    if os.environ.get("FLASK_ENV") == "development" or os.environ.get("FLASK_DEBUG") == "1":
        app.config["TEMPLATES_AUTO_RELOAD"] = os.environ.get("TEMPLATES_AUTO_RELOAD", "True").lower() == "true"
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = int(os.environ.get("SEND_FILE_MAX_AGE_DEFAULT", "0"))

        @app.context_processor
        def inject_cache_buster():
            import time
            return {"cache_buster": int(time.time())}

        @app.after_request
        def after_request(response):
            if request.endpoint == "static":
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    # Scheduler config
    scheduler.init_app(app)
    scheduler.add_job(
        id="check_reminders",
        func=lambda: check_reminders(app),
        trigger="interval",
        minutes=1
    )
    scheduler.start()

    return app
