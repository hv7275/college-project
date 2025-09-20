from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('tasks.view_task'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone_no = request.form.get('phone_no')

        # Check if user already exists
        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))

        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username, 
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_no=phone_no
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful, please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))