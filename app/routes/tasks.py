from flask import Blueprint, render_template, request
from flask import flash, url_for, redirect, session

from app import db
from app.models import Task

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route('/')
def view_task():
    if 'user' not in session:
        flash('Please log in to view tasks', 'warning')
        return redirect(url_for('auth.login'))
    tasks = Task.query.all()
    return render_template('tasks.html', tasks=tasks)

@tasks_bp.route('/add', methods=['POST'])
def add_task():
    if 'user' not in session:
        flash('Please log in to add tasks', 'danger')
        return redirect(url_for('auth.login'))
    title = request.form.get('title')
    if title:
        new_task = Task(title=title, status='pending')
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    if 'user' not in session:
        flash('Please log in to toggle tasks', 'danger')
        return redirect(url_for('auth.login'))
    task = Task.query.get_or_404(task_id)
    if task.status == "Pending":
        task.status = "Working"
    elif task.status == "Working":
        task.status = 'Done'
    else:
        task.status == "Pending"
    db.session.commit()
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/clear/<int:task_id>', methods=['POST'])
def clear_task(task_id):
    if 'user' not in session:
        flash('Please log in to clear tasks', 'danger')
        return redirect(url_for('auth.login'))
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task cleared successfully', 'success')
    return redirect(url_for('tasks.view_task', task_id = task.id))
