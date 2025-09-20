from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_mail import Message
from app import mail

notify_bp = Blueprint("notify", __name__)

@notify_bp.route("/notify-me")
@login_required
def notify_me():
    """Send an email to the currently logged-in user."""
    try:
        msg = Message(
            subject="Hello from Task Manager",
            recipients=[current_user.email],
            body=f"Hi {current_user.first_name},\n\nThis is your personal notification."
        )
        mail.send(msg)
        flash("Email sent successfully!", "success")
    except Exception as e:
        flash(f"Error sending email: {e}", "error")
    return redirect(url_for("tasks.dashboard"))  # change to any page you like
