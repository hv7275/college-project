from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, mail
from app.models import User, PasswordResetToken, EmailVerificationToken
from app.forms import ForgotPasswordForm, ResetPasswordForm
from datetime import datetime, timedelta
import secrets
import os

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
            if not user.email_verified:
                flash('Please verify your email before logging in. Check your email for verification link.', 'warning')
                return render_template('login.html')
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

        user_by_phone = User.query.filter_by(phone_no=phone_no).first()
        if user_by_phone:
            flash('Phone number already registered', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username, 
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_no=phone_no,
            email_verified=False
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # Get the user ID
        
        # Generate email verification token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hours expiry
        
        verification_token = EmailVerificationToken(
            user_id=new_user.id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(verification_token)
        db.session.commit()
        
        # Send verification email
        try:
            verification_url = url_for('auth.verify_email', token=token, _external=True)
            from flask_mail import Message
            msg = Message(
                'Verify Your Email - Task Management System',
                recipients=[new_user.email],
                body=f'''
Hello {new_user.first_name},

Welcome to our Task Management System!

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account with us, please ignore this email.

Best regards,
Your Task Management Team
                '''
            )
            mail.send(msg)
            flash('Registration successful! Please check your email and click the verification link to activate your account.', 'success')
        except Exception as e:
            flash(f'Registration successful, but email sending failed. Please contact support for account activation.', 'warning')
            print(f"Email sending error: {e}")
        
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a secure token
            token = secrets.token_urlsafe(32)
            expiry_hours = int(os.environ.get("PASSWORD_RESET_EXPIRY_HOURS", "1"))
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Create password reset token
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(reset_token)
            db.session.commit()
            
            # Send reset email
            try:
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                from flask_mail import Message
                msg = Message(
                    'Password Reset Request',
                    recipients=[user.email],
                    body=f'''
Hello {user.first_name},

You requested a password reset for your account.

Click the following link to reset your password:
{reset_url}

This link will expire in {expiry_hours} hour{"s" if expiry_hours != 1 else ""}.

If you didn't request this password reset, please ignore this email.

Best regards,
Your Task Management Team
                    '''
                )
                mail.send(msg)
                flash('Password reset link has been sent to your email.', 'success')
            except Exception as e:
                # If email fails, show the reset link directly (for development)
                flash(f'Email sending failed. Please use this link to reset your password: {reset_url}', 'warning')
                print(f"Email sending error: {e}")
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    # Find the token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update user password
        user = reset_token.user
        user.set_password(form.password.data)
        
        # Mark token as used
        reset_token.used = True
        
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form, token=token)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    # Find the verification token
    verification_token = EmailVerificationToken.query.filter_by(token=token).first()
    
    if not verification_token or not verification_token.is_valid():
        flash('Invalid or expired verification token.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Mark email as verified
    user = verification_token.user
    user.email_verified = True
    
    # Mark token as used
    verification_token.used = True
    
    db.session.commit()
    
    flash('Your email has been verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user and not user.email_verified:
            # Delete any existing verification tokens for this user
            EmailVerificationToken.query.filter_by(user_id=user.id).delete()
            
            # Generate new verification token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            verification_token = EmailVerificationToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(verification_token)
            db.session.commit()
            
            # Send verification email
            try:
                verification_url = url_for('auth.verify_email', token=token, _external=True)
                from flask_mail import Message
                msg = Message(
                    'Verify Your Email - Task Management System',
                    recipients=[user.email],
                    body=f'''
Hello {user.first_name},

You requested a new verification link for your account.

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
Your Task Management Team
                    '''
                )
                mail.send(msg)
                flash('Verification email has been sent. Please check your email.', 'success')
            except Exception as e:
                flash('Failed to send verification email. Please try again later.', 'danger')
                print(f"Email sending error: {e}")
        else:
            flash('Email not found or already verified.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('resend_verification.html')