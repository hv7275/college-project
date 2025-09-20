from flask import Blueprint, render_template, request, flash, url_for, redirect, session
from flask_login import login_required, current_user
from app import db
from app.models import Task, TaskHistory
from app.forms import TaskForm
from datetime import datetime, date, time


tasks_bp = Blueprint("tasks", __name__)

def log_task_history(task, action, details=None):
    """Helper function to log task history"""
    history = TaskHistory(
        task_id=task.id if task else None,
        user_id=current_user.id,
        action=action,
        details=details
    )
    if task:
        history.set_task_data(task)
    db.session.add(history)

@tasks_bp.route('/')
@login_required
def view_task():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.priority.desc(), Task.scheduled_date.asc(), Task.scheduled_time.asc()).all()
    form = TaskForm()
    return render_template('tasks.html', tasks=tasks, form=form)

@tasks_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        # Parse form data
        scheduled_date = form.scheduled_date.data
        scheduled_time = form.scheduled_time.data
        estimated_duration = form.estimated_duration.data
        priority = form.priority.data
        
        new_task = Task(
            title=form.title.data,
            status='Pending',
            user_id=current_user.id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            estimated_duration=estimated_duration,
            priority=priority
        )
        db.session.add(new_task)
        db.session.flush()  # Get the task ID before committing
        
        # Log task creation
        log_task_history(new_task, 'created', f'Task "{new_task.title}" created')
        
        db.session.commit()
        flash('Task added successfully', 'success')
    else:
        # Handle form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
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
    
    old_status = task.status
    if task.status == "Pending":
        task.status = "In Progress"
    elif task.status == "In Progress":
        task.status = "Completed"
    else:
        task.status = "Pending"
    
    # Log status change
    log_task_history(task, 'status_changed', f'Status changed from {old_status} to {task.status}')
    
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
    
    # Log task deletion before deleting
    log_task_history(task, 'deleted', f'Task "{task.title}" deleted')
    
    db.session.delete(task)
    db.session.commit()
    flash('Task cleared successfully', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/edit', methods=['POST'])
@login_required
def edit_task():
    task_id = request.form.get('task_id')
    if not task_id:
        flash('Task ID is required', 'danger')
        return redirect(url_for('tasks.view_task'))
    
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You can only edit your own tasks', 'danger')
        return redirect(url_for('tasks.view_task'))
    
    # Store original values for comparison
    original_title = task.title
    original_priority = task.priority
    original_scheduled_date = task.scheduled_date
    original_scheduled_time = task.scheduled_time
    original_estimated_duration = task.estimated_duration
    
    # Update task fields
    task.title = request.form.get('title', task.title)
    
    # Handle date and time fields
    scheduled_date = request.form.get('scheduled_date')
    if scheduled_date:
        from datetime import datetime
        task.scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
    else:
        task.scheduled_date = None
    
    scheduled_time = request.form.get('scheduled_time')
    if scheduled_time:
        from datetime import datetime
        task.scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
    else:
        task.scheduled_time = None
    
    # Handle estimated duration
    estimated_duration = request.form.get('estimated_duration')
    if estimated_duration:
        task.estimated_duration = int(estimated_duration)
    else:
        task.estimated_duration = None
    
    # Update priority
    task.priority = request.form.get('priority', task.priority)
    
    # Update timestamp
    from datetime import datetime
    task.updated_at = datetime.utcnow()
    
    # Check what changed and log accordingly
    changes = []
    if original_title != task.title:
        changes.append(f"title from '{original_title}' to '{task.title}'")
    if original_priority != task.priority:
        changes.append(f"priority from '{original_priority}' to '{task.priority}'")
    if original_scheduled_date != task.scheduled_date:
        changes.append(f"scheduled date from '{original_scheduled_date}' to '{task.scheduled_date}'")
    if original_scheduled_time != task.scheduled_time:
        changes.append(f"scheduled time from '{original_scheduled_time}' to '{task.scheduled_time}'")
    if original_estimated_duration != task.estimated_duration:
        changes.append(f"estimated duration from '{original_estimated_duration}' to '{task.estimated_duration}'")
    
    if changes:
        details = f"Updated: {', '.join(changes)}"
        log_task_history(task, 'updated', details)
    
    db.session.commit()
    flash('Task updated successfully', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/clear_all', methods=['POST'])
@login_required
def clear_all_tasks():
    # Get all tasks before deleting to log them
    tasks_to_delete = Task.query.filter_by(user_id=current_user.id).all()
    
    # Log deletion for each task
    for task in tasks_to_delete:
        log_task_history(task, 'deleted', f'Task "{task.title}" deleted (bulk delete)')
    
    Task.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All tasks cleared successfully', 'success')
    return redirect(url_for('tasks.view_task'))

@tasks_bp.route('/history')
@login_required
def task_history():
    """View task history for the current user"""
    history = TaskHistory.query.filter_by(user_id=current_user.id)\
        .order_by(TaskHistory.created_at.desc())\
        .limit(100).all()  # Limit to last 100 entries
    
    return render_template('task_history.html', history=history)