from datetime import datetime
# avoid "from app import db" — import the extension relatively
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum
import json


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

    # Time and schedule fields
    scheduled_date = db.Column(db.Date, nullable=True)
    scheduled_time = db.Column(db.Time, nullable=True)
    estimated_duration = db.Column(db.Integer, nullable=True)  # in minutes
    priority = db.Column(
        Enum("Low", "Medium", "High", "Urgent", name="task_priority"),
        default="Medium",
        nullable=False,
    )

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    owner = db.relationship("User", back_populates="tasks")
    history = db.relationship('TaskHistory', back_populates='task', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Task {self.title} [{self.status}]>"


class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Task reference (nullable for deleted tasks)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=True)
    task = db.relationship("Task", back_populates="history")
    
    # User who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
    
    # Action type: 'created', 'updated', 'deleted', 'status_changed'
    action = db.Column(
        Enum("created", "updated", "deleted", "status_changed", name="task_action"),
        nullable=False
    )
    
    # Task data at the time of action (JSON format)
    task_data = db.Column(db.Text, nullable=True)  # JSON string of task data
    
    # Additional details for the action
    details = db.Column(db.String(500), nullable=True)  # e.g., "Status changed from Pending to In Progress"
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def set_task_data(self, task_obj):
        """Store task data as JSON"""
        if task_obj:
            data = {
                'title': task_obj.title,
                'status': task_obj.status,
                'priority': task_obj.priority,
                'scheduled_date': task_obj.scheduled_date.isoformat() if task_obj.scheduled_date else None,
                'scheduled_time': task_obj.scheduled_time.isoformat() if task_obj.scheduled_time else None,
                'estimated_duration': task_obj.estimated_duration,
                'created_at': task_obj.created_at.isoformat() if task_obj.created_at else None,
                'updated_at': task_obj.updated_at.isoformat() if task_obj.updated_at else None
            }
            self.task_data = json.dumps(data)
    
    def get_task_data(self):
        """Retrieve task data from JSON"""
        if self.task_data:
            return json.loads(self.task_data)
        return None
    
    def __repr__(self):
        return f"<TaskHistory {self.action} by {self.user.username} at {self.created_at}>"


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


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        """Check if the token is valid (not expired and not used)"""
        return not self.used and datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f"<PasswordResetToken for {self.user.username} expires at {self.expires_at}>"
