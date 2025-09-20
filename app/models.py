from datetime import datetime
# avoid "from app import db" — import the extension relatively
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone_no = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    tasks = db.relationship('Task', back_populates='owner', lazy=True)
    reminders = db.relationship('Reminder', back_populates='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

    status = db.Column(
        Enum("Pending", "In Progress", "Completed", name="task_status"),
        default="Pending",
        nullable=False,
    )

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    owner = db.relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.title} [{self.status}]>"


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="reminders")

    message = db.Column(db.String(255))
    remind_at = db.Column(db.DateTime, nullable=False, index=True)
    sent = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Reminder for {self.user.username} at {self.remind_at}>"
