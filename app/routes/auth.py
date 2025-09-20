from flask import Blueprint, render_template, request
from flask import flash, url_for, redirect, session


auth_bp = Blueprint("auth", __name__)

USER_CREDENTIALS ={
    'username':'admin',
    'password':'12345'
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USER_CREDENTIALS['username'] and password == USER_CREDENTIALS['password']:
            session['user'] = username
            flash('login successful', 'success')
        else:
            flash('login failed', 'danger')
            return redirect(url_for('auth.login'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('logout successful', 'info')
    return redirect(url_for('auth.login'))
