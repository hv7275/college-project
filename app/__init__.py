from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime
from app.models import Reminder   # import your model
from flask_mail import Mail, Message   # optional if emailing

db = SQLAlchemy()
mail = Mail()
scheduler = APScheduler()

def check_reminders():
    """Background job to send due reminders."""
    now = datetime.utcnow()
    due = Reminder.query.filter(
        Reminder.remind_at <= now,
        Reminder.sent.is_(False)
    ).all()
    for r in due:
        # Example: send email
        msg = Message("Your Reminder", recipients=[r.user.email], body=r.message)
        mail.send(msg)
        r.sent = True
    db.session.commit()

def create_app():
    app = Flask(__name__)
    app.secret_key = "your_secret_key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Mail config (if using email)
    app.config.update(
        MAIL_SERVER='smtp.example.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='your_email@example.com',
        MAIL_PASSWORD='your_password'
    )

    db.init_app(app)
    mail.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    # Start the scheduler
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(
        id='check_reminders',
        func=check_reminders,
        trigger='interval',
        minutes=1
    )

    return app
