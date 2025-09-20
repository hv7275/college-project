import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from datetime import datetime
from flask_mail import Mail, Message
from flask_migrate import Migrate

db = SQLAlchemy()
mail = Mail()
scheduler = APScheduler()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()


def check_reminders():
    """Background job to send due reminders."""
    from app.models import Reminder  # avoid circular import
    from flask import current_app
    
    with current_app.app_context():
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
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'instance', 'site.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail config
    app.config.update(
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD")
    )

    # Development features
    if os.environ.get("FLASK_ENV") == "development" or os.environ.get("FLASK_DEBUG") == "1":
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

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
        func=check_reminders,
        trigger="interval",
        minutes=1
    )
    scheduler.start()

    return app
