from flask import Blueprint, render_template, request, flash, url_for, redirect, session
from flask_login import login_required, current_user
from app import db
from app.models import Task


tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route('/')
@login_required
def view_task():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=tasks)

@tasks_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    if title:
        new_task = Task(title=title, status='Pending', user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/toggle', methods=['POST'])
@login_required
def toggle_task():
    task_id = request.form.get('task_id')
    if not task_id:
        flash('Task ID is required', 'danger')
        return redirect(url_for('tasks.view_task'))
    
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You can only modify your own tasks', 'danger')
        return redirect(url_for('tasks.view_task'))
    
    if task.status == "Pending":
        task.status = "In Progress"
    elif task.status == "In Progress":
        task.status = "Completed"
    else:
        task.status = "Pending"
    
    db.session.commit()
    flash('Task status updated', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/clear/<int:task_id>', methods=['POST'])
@login_required
def clear_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You can only delete your own tasks', 'danger')
        return redirect(url_for('tasks.view_task'))
    
    db.session.delete(task)
    db.session.commit()
    flash('Task cleared successfully', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/clear_all', methods=['POST'])
@login_required
def clear_all_tasks():
    Task.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All tasks cleared successfully', 'success')
    return redirect(url_for('tasks.view_task'))