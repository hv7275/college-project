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
    from app.models import Reminder, Task  # avoid circular import
    
    with app.app_context():
        now = datetime.utcnow()
        due = Reminder.query.filter(
            Reminder.remind_at <= now,
            Reminder.sent.is_(False)
        ).all()
        for r in due:
            try:
                if "Task Reminder:" in r.message:
                    task_title = r.message.replace("Task Reminder: ", "")
                    task = Task.query.filter_by(
                        user_id=r.user_id,
                        title=task_title
                    ).first()
                    if task:
                        email_body = f"""
Hello {r.user.first_name},

This is a reminder for your scheduled task:

Task: {task.title}
Priority: {task.priority}
Status: {task.status}
Scheduled Date: {task.scheduled_date.strftime('%B %d, %Y') if task.scheduled_date else 'Not set'}
Scheduled Time: {task.scheduled_time.strftime('%I:%M %p') if task.scheduled_time else 'Not set'}
Estimated Duration: {f'{task.estimated_duration} minutes' if task.estimated_duration else 'Not estimated'}

Please don't forget to work on this task!

Best regards,
Your Task Management System
                        """.strip()
                        msg = Message(
                            f"Task Reminder: {task.title}",
                            recipients=[r.user.email],
                            body=email_body
                        )
                    else:
                        msg = Message("Your Reminder", recipients=[r.user.email], body=r.message)
                else:
                    msg = Message("Your Reminder", recipients=[r.user.email], body=r.message)
                
                mail.send(msg)
                r.sent = True
                print(f"Sent reminder to {r.user.email}: {r.message}")
            except Exception as e:
                print(f"Error sending reminder {r.id}: {e}")
        db.session.commit()


def send_periodic_notifications(app):
    """Send periodic notifications to logged-in users for their own tasks every 5 minutes."""
    from app.models import Task, User
    from datetime import datetime
    
    with app.app_context():
        try:
            last_notification_key = 'last_periodic_notification'
            last_sent = app.config.get(last_notification_key)
            now = datetime.utcnow()
            
            if last_sent and (now - last_sent).total_seconds() < 240:
                print("⏰ Skipping notification - sent recently")
                return
            
            users_with_tasks = User.query.join(Task).filter(
                Task.status.in_(['Pending', 'In Progress'])
            ).distinct().all()
            
            if not users_with_tasks:
                print("⚠️ No users with pending tasks found")
                return
            
            sent_count = 0
            for user in users_with_tasks:
                if not user.email or not user.email.endswith('@gmail.com'):
                    print(f"⚠️ Skipping {user.username} - no valid Gmail address")
                    continue
                
                user_tasks = Task.query.filter(
                    Task.user_id == user.id,
                    Task.status.in_(['Pending', 'In Progress'])
                ).all()
                
                if not user_tasks:
                    continue
                
                task_list = []
                for task in user_tasks:
                    priority_emoji = {
                        'Low': '🟢',
                        'Medium': '🟡', 
                        'High': '🟠',
                        'Urgent': '🔴'
                    }.get(task.priority, '⚪')
                    
                    task_list.append(f"""
{priority_emoji} {task.title} ({task.status})
   📅 Due: {task.scheduled_date.strftime('%B %d, %Y') if task.scheduled_date else 'No date set'}
   ⏰ Time: {task.scheduled_time.strftime('%I:%M %p') if task.scheduled_time else 'No time set'}
   ⏱️ Duration: {f'{task.estimated_duration} minutes' if task.estimated_duration else 'Not estimated'}""")
                
                email_body = f"""
Hello {user.first_name},

Here's your current task status update:

{''.join(task_list)}

You have {len(user_tasks)} pending task{'s' if len(user_tasks) != 1 else ''} to work on.

Keep up the great work! 🚀

Best regards,
Your Task Management System
                """.strip()
                
                try:
                    msg = Message(
                        f"📋 Your Task Update ({len(user_tasks)} tasks)",
                        recipients=[user.email],
                        body=email_body
                    )
                    mail.send(msg)
                    sent_count += 1
                    print(f"✅ Sent notification to {user.email} for {len(user_tasks)} tasks")
                except Exception as email_error:
                    print(f"❌ Failed to send email to {user.email}: {email_error}")
            
            app.config[last_notification_key] = now
            print(f"📧 Total notifications sent: {sent_count}")
                        
        except Exception as e:
            print(f"Error sending periodic notifications: {e}")


def cleanup_expired_otps(app):
    """Clean up expired OTPs every 5 minutes."""
    from app.models import LoginOTP
    from datetime import datetime
    
    with app.app_context():
        try:
            now = datetime.utcnow()
            expired_otps = LoginOTP.query.filter(LoginOTP.expires_at < now).all()
            
            if expired_otps:
                for otp in expired_otps:
                    db.session.delete(otp)
                db.session.commit()
                print(f"🧹 Cleaned up {len(expired_otps)} expired OTPs")
            else:
                print("🧹 No expired OTPs to clean up")
                
        except Exception as e:
            print(f"Error cleaning up expired OTPs: {e}")


def create_app():
    app = Flask(__name__)
    
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["WTF_CSRF_ENABLED"] = os.environ.get("WTF_CSRF_ENABLED", "True").lower() == "true"
    app.config["WTF_CSRF_TIME_LIMIT"] = int(os.environ.get("WTF_CSRF_TIME_LIMIT", "3600"))

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'site.db'))
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config.update(
        MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.environ.get("MAIL_PORT", "587")),
        MAIL_USE_TLS=os.environ.get("MAIL_USE_TLS", "True").lower() == "true",
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME", "noreply@example.com"))
    )

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

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    from app.routes.notify import notify_bp   # <-- register new blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(notify_bp)

    scheduler.init_app(app)
    scheduler.add_job(
        id="check_reminders",
        func=lambda: check_reminders(app),
        trigger="interval",
        minutes=1
    )
    scheduler.add_job(
        id="send_periodic_notifications",
        func=lambda: send_periodic_notifications(app),
        trigger="interval",
        minutes=5
    )
    scheduler.add_job(
        id="cleanup_expired_otps",
        func=lambda: cleanup_expired_otps(app),
        trigger="interval",
        minutes=5
    )
    scheduler.start()

    return app
