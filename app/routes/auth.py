from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, mail
from app.models import User, PasswordResetToken, EmailVerificationToken, LoginOTP
from app.forms import ForgotPasswordForm, ResetPasswordForm, OTPVerificationForm
from datetime import datetime, timedelta
import secrets
import os
import random

auth_bp = Blueprint("auth", __name__)

def send_authentication_notification(user, notification_type="registration"):
    """Send authentication notification to user's email"""
    try:
        from flask_mail import Message
        
        if notification_type == "registration":
            subject = "🔐 New Account Registration - Authentication Required"
            body = f'''
🔐 AUTHENTICATION NOTIFICATION 🔐

Hello {user.first_name} {user.last_name},

A new account has been registered with your email address on our Task Management System.

📋 ACCOUNT DETAILS:
• Username: {user.username}
• Email: {user.email}
• Phone: {user.phone_no}
• Registration Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

🔒 SECURITY STEPS REQUIRED:
1. Verify your email address by clicking the verification link
2. Complete the authentication process
3. Set up your account security preferences

⚠️  IMPORTANT SECURITY NOTES:
• If you did not create this account, please contact our support immediately
• Never share your login credentials with anyone
• Always log out from shared devices
• Enable two-factor authentication when available

For security reasons, please verify your email address within the next 24 hours to activate your account.

If you have any questions or concerns, please contact our support team.

Best regards,
Your Task Management Team
Security Department
            '''
        elif notification_type == "suspicious_activity":
            subject = "⚠️ Suspicious Activity Detected - Security Alert"
            body = f'''
⚠️ SECURITY ALERT ⚠️

Hello {user.first_name},

We have detected suspicious activity on your account.

📋 ACCOUNT DETAILS:
• Username: {user.username}
• Email: {user.email}
• Activity Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

🔒 IMMEDIATE ACTION REQUIRED:
1. Change your password immediately
2. Review your recent account activity
3. Contact support if you notice any unauthorized access

If you did not perform this activity, please contact our security team immediately.

Best regards,
Your Task Management Team
Security Department
            '''
        
        msg = Message(subject, recipients=[user.email], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Authentication notification sending error: {e}")
        return False


def delete_user_data(user_id):
    """Delete all data related to a user"""
    try:
        from app.models import Task, TaskHistory, Reminder, PasswordResetToken, EmailVerificationToken, LoginOTP
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        # Store user info for notification
        user_email = user.email
        user_name = f"{user.first_name} {user.last_name}"
        
        # Delete all user-related data
        deleted_items = []
        
        # Delete tasks and task history
        tasks = Task.query.filter_by(user_id=user_id).all()
        task_count = len(tasks)
        for task in tasks:
            # Delete task history first (due to foreign key constraint)
            TaskHistory.query.filter_by(task_id=task.id).delete()
            db.session.delete(task)
        deleted_items.append(f"{task_count} tasks and their history")
        
        # Delete reminders
        reminders = Reminder.query.filter_by(user_id=user_id).all()
        reminder_count = len(reminders)
        for reminder in reminders:
            db.session.delete(reminder)
        deleted_items.append(f"{reminder_count} reminders")
        
        # Delete authentication tokens
        password_tokens = PasswordResetToken.query.filter_by(user_id=user_id).all()
        email_tokens = EmailVerificationToken.query.filter_by(user_id=user_id).all()
        otp_tokens = LoginOTP.query.filter_by(user_id=user_id).all()
        
        for token in password_tokens + email_tokens + otp_tokens:
            db.session.delete(token)
        
        token_count = len(password_tokens) + len(email_tokens) + len(otp_tokens)
        deleted_items.append(f"{token_count} authentication tokens")
        
        # Delete user
        db.session.delete(user)
        
        # Commit all deletions
        db.session.commit()
        
        # Send account deletion notification
        try:
            from flask_mail import Message
            deletion_msg = Message(
                '✅ Account Successfully Deleted - Confirmation',
                recipients=[user_email],
                body=f'''
✅ ACCOUNT DELETION CONFIRMED ✅

Hello {user_name},

Your account has been successfully deleted from our Task Management System.

📋 DELETION SUMMARY:
• Username: {user.username}
• Email: {user_email}
• Deletion Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

🗑️ DATA DELETED:
{chr(10).join(f"• {item}" for item in deleted_items)}

✅ CONFIRMATION:
All your personal data, tasks, reminders, and account information have been permanently removed from our systems.

If you did not request this account deletion, please contact our support team immediately as this may indicate unauthorized access to your account.

Thank you for using our Task Management System.

Best regards,
Your Task Management Team
Data Protection Department
                '''
            )
            mail.send(deletion_msg)
        except Exception as e:
            print(f"Account deletion notification error: {e}")
        
        return True, f"Successfully deleted user and {', '.join(deleted_items)}"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting user data: {str(e)}"

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # Generate email authentication token
            auth_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes expiry
            
            # Delete any existing authentication tokens for this user
            LoginOTP.query.filter_by(user_id=user.id).delete()
            
            # Create new authentication token
            login_auth = LoginOTP(
                user_id=user.id,
                otp_code=auth_token,  # Reusing otp_code field for auth token
                expires_at=expires_at
            )
            db.session.add(login_auth)
            db.session.commit()
            
            # Send email authentication notification
            try:
                from flask_mail import Message
                auth_url = url_for('auth.authenticate_email', token=auth_token, _external=True)
                
                email_subject = '🔐 Login Authentication Required - Task Management System'
                if not user.email_verified:
                    email_subject = '🔐 Email Verification & Login Authentication - Task Management System'
                
                msg = Message(
                    email_subject,
                    recipients=[user.email],
                    body=f'''
🔐 LOGIN AUTHENTICATION REQUIRED 🔐

Hello {user.first_name},

Someone is trying to log into your Task Management System account.

📋 LOGIN DETAILS:
• Username: {user.username}
• Email: {user.email}
• Login Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
• IP Address: {request.remote_addr if request.remote_addr else 'Unknown'}

🔒 TO COMPLETE LOGIN:
Click the authentication link below to log in securely:
{auth_url}

This link will expire in 15 minutes.

{f"Note: This will also verify your email address." if not user.email_verified else ""}

⚠️  SECURITY ALERT:
• If you did not request this login, please ignore this email
• Never share this authentication link with anyone
• Contact support immediately if you suspect unauthorized access

Best regards,
Your Task Management Team
Security Department
                    '''
                )
                mail.send(msg)
                
                # Store user ID in session for authentication
                session['auth_user_id'] = user.id
                flash('Authentication email sent! Please check your inbox and click the link to complete login.', 'success')
                return redirect(url_for('auth.auth_pending'))
            except Exception as e:
                flash(f'Failed to send authentication email. Please try again later.', 'danger')
                print(f"Authentication email sending error: {e}")
        else:
            # Check if user exists but wrong password (potential security issue)
            user = User.query.filter_by(username=username).first()
            if user:
                # Send security alert for failed login attempt
                send_authentication_notification(user, "suspicious_activity")
                flash('Invalid username or password', 'danger')
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
        
        # Send authentication email for account activation and login
        try:
            # Generate authentication token for direct login
            auth_token = secrets.token_urlsafe(32)
            auth_expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hours expiry
            
            # Create authentication token
            login_auth = LoginOTP(
                user_id=new_user.id,
                otp_code=auth_token,
                expires_at=auth_expires_at
            )
            db.session.add(login_auth)
            db.session.commit()
            
            # Send authentication email
            auth_url = url_for('auth.authenticate_email', token=auth_token, _external=True)
            from flask_mail import Message
            
            auth_msg = Message(
                '🔐 Account Created - Authentication Required',
                recipients=[new_user.email],
                body=f'''
🔐 ACCOUNT CREATED - AUTHENTICATION REQUIRED 🔐

Hello {new_user.first_name} {new_user.last_name},

Welcome to our Task Management System! Your account has been successfully created.

📋 ACCOUNT DETAILS:
• Username: {new_user.username}
• Email: {new_user.email}
• Phone: {new_user.phone_no}
• Registration Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

🔒 TO ACTIVATE YOUR ACCOUNT:
Click the authentication link below to verify your email and log in:
{auth_url}

This link will expire in 24 hours.

✅ WHAT HAPPENS NEXT:
• Your email will be verified automatically
• You'll be logged in immediately
• You can start using all features
• Your account will be fully activated

⚠️  IMPORTANT SECURITY NOTES:
• If you didn't create this account, please contact our support immediately
• Never share this authentication link with anyone
• This link can only be used once for security

Best regards,
Your Task Management Team
Account Activation Department
                '''
            )
            mail.send(auth_msg)
            
            # Store user ID in session for authentication pending
            session['auth_user_id'] = new_user.id
            
            flash('Account created successfully! Please check your email and click the authentication link to activate your account and log in.', 'success')
            return redirect(url_for('auth.auth_pending'))
        except Exception as e:
            flash(f'Account created, but email sending failed. Please contact support for account activation.', 'warning')
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
    
    # Send email verification success notification
    try:
        from flask_mail import Message
        success_msg = Message(
            '✅ Email Verification Successful - Account Activated',
            recipients=[user.email],
            body=f'''
✅ EMAIL VERIFICATION SUCCESSFUL ✅

Hello {user.first_name},

Your email address has been successfully verified!

📋 ACCOUNT STATUS:
• Username: {user.username}
• Email: {user.email}
• Status: ✅ VERIFIED
• Verification Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

🎉 WELCOME TO YOUR TASK MANAGEMENT SYSTEM!

Your account is now fully activated and ready to use. You can now:
• Log in to your account
• Create and manage tasks
• Set up reminders and notifications
• Access all features of the system

🔒 SECURITY REMINDER:
• Keep your login credentials secure
• Log out from shared devices
• Report any suspicious activity immediately

Thank you for joining us!

Best regards,
Your Task Management Team
            '''
        )
        mail.send(success_msg)
    except Exception as e:
        print(f"Email verification success notification error: {e}")
    
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


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    # Check if user has a pending OTP
    user_id = session.get('otp_user_id')
    if not user_id:
        flash('No OTP verification in progress. Please login first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('Invalid session. Please login again.', 'danger')
        session.pop('otp_user_id', None)
        return redirect(url_for('auth.login'))
    
    form = OTPVerificationForm()
    
    if form.validate_on_submit():
        if form.submit.data:  # Verify OTP button clicked
            otp_code = form.otp_code.data
            
            # Find valid OTP for this user
            login_otp = LoginOTP.query.filter_by(
                user_id=user_id,
                otp_code=otp_code
            ).first()
            
            if login_otp and login_otp.is_valid():
                # Mark OTP as used
                login_otp.used = True
                
                # If user's email is not verified, verify it now
                if not user.email_verified:
                    user.email_verified = True
                    flash('Email verified and login successful!', 'success')
                else:
                    flash('Login successful!', 'success')
                
                db.session.commit()
                
                # Clear session
                session.pop('otp_user_id', None)
                
                # Login user
                login_user(user)
                return redirect(url_for('tasks.view_task'))
            else:
                flash('Invalid or expired OTP code. Please try again.', 'danger')
        
        elif form.resend_otp.data:  # Resend OTP button clicked
            # Generate new OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = datetime.utcnow() + timedelta(minutes=1)
            
            # Delete any existing OTPs for this user
            LoginOTP.query.filter_by(user_id=user_id).delete()
            
            # Create new OTP
            login_otp = LoginOTP(
                user_id=user_id,
                otp_code=otp_code,
                expires_at=expires_at
            )
            db.session.add(login_otp)
            db.session.commit()
            
            # Send new OTP email
            try:
                from flask_mail import Message
                email_subject = 'New Login OTP - Task Management System'
                if not user.email_verified:
                    email_subject = 'New Email Verification & Login OTP - Task Management System'
                
                msg = Message(
                    email_subject,
                    recipients=[user.email],
                    body=f'''
Hello {user.first_name},

Your new login OTP code is: {otp_code}

This code will expire in 1 minute.

{f"Note: This OTP will also verify your email address." if not user.email_verified else ""}

If you didn't request this login, please ignore this email.

Best regards,
Your Task Management Team
                    '''
                )
                mail.send(msg)
                flash('New OTP sent to your email.', 'success')
            except Exception as e:
                flash('Failed to resend OTP. Please try again later.', 'danger')
                print(f"OTP resend error: {e}")
    
    return render_template('verify_otp.html', form=form, user_email=user.email)


@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Handle account deletion with confirmation"""
    if request.method == 'POST':
        username_confirmation = request.form.get('username_confirmation', '').strip()
        confirm_deletion = request.form.get('confirm_deletion')
        
        # Validate confirmation
        if username_confirmation != current_user.username:
            flash('Username confirmation does not match. Please try again.', 'danger')
            return render_template('delete_account.html')
        
        if not confirm_deletion:
            flash('Please confirm that you understand this action is permanent.', 'danger')
            return render_template('delete_account.html')
        
        # Proceed with account deletion
        user_id = current_user.id
        success, message = delete_user_data(user_id)
        
        if success:
            # Logout user before redirecting
            logout_user()
            flash('Your account has been successfully deleted. All your data has been permanently removed.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(f'Error deleting account: {message}', 'danger')
            return render_template('delete_account.html')
    
    return render_template('delete_account.html')


@auth_bp.route('/authenticate-email/<token>')
def authenticate_email(token):
    """Handle email authentication and direct login"""
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    # Find the authentication token
    auth_token = LoginOTP.query.filter_by(otp_code=token).first()
    
    if not auth_token or not auth_token.is_valid():
        flash('Invalid or expired authentication link. Please try logging in again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get the user
    user = auth_token.user
    if not user:
        flash('Invalid authentication token. Please try logging in again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Mark token as used
    auth_token.used = True
    
    # If user's email is not verified, verify it now
    if not user.email_verified:
        user.email_verified = True
        flash('Email verified and login successful!', 'success')
    else:
        flash('Login successful!', 'success')
    
    db.session.commit()
    
    # Clear any pending authentication session
    session.pop('auth_user_id', None)
    
    # Login user
    login_user(user)
    
    # Send login success notification
    try:
        from flask_mail import Message
        success_msg = Message(
            '✅ Login Successful - Security Notification',
            recipients=[user.email],
            body=f'''
✅ LOGIN SUCCESSFUL ✅

Hello {user.first_name},

You have successfully logged into your Task Management System account.

📋 LOGIN DETAILS:
• Username: {user.username}
• Email: {user.email}
• Login Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
• IP Address: {request.remote_addr if request.remote_addr else 'Unknown'}

🔒 SECURITY CONFIRMATION:
Your login was authenticated via email verification.

If you did not perform this login, please contact our security team immediately.

Best regards,
Your Task Management Team
Security Department
            '''
        )
        mail.send(success_msg)
    except Exception as e:
        print(f"Login success notification error: {e}")
    
    return redirect(url_for('tasks.view_task'))


@auth_bp.route('/auth-pending')
def auth_pending():
    """Show authentication pending page"""
    if current_user.is_authenticated:
        return redirect(url_for('tasks.view_task'))
    
    # Check if user has a pending authentication
    user_id = session.get('auth_user_id')
    if not user_id:
        flash('No authentication in progress. Please login first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('Invalid session. Please login again.', 'danger')
        session.pop('auth_user_id', None)
        return redirect(url_for('auth.login'))
    
    return render_template('auth_pending.html', user_email=user.email)