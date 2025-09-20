from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, TimeField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=150)]
    )

    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=1, max=150)]
    )

    last_name = StringField(
        'Last Name',
        validators=[DataRequired(), Length(min=1, max=150)]
    )

    email = StringField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=150)]
    )

    phone_no = StringField(
        'Phone Number',
        validators=[DataRequired(), Length(min=10, max=20)]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, max=100)]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), Length(min=6, max=100), EqualTo('password')]
    )

    submit = SubmitField('Register')

    # --- Custom validators for uniqueness ---
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

    def validate_phone_no(self, phone_no):
        user = User.query.filter_by(phone_no=phone_no.data).first()
        if user:
            raise ValidationError('That phone number is already registered.')


class LoginForm(FlaskForm):
    username = StringField(
        'Username or Email',
        validators=[DataRequired(), Length(min=2, max=150)]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, max=100)]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class TaskForm(FlaskForm):
    title = StringField(
        'Task Title',
        validators=[DataRequired(), Length(min=1, max=100)],
        render_kw={'placeholder': 'Enter task title'}
    )
    
    scheduled_date = DateField(
        'Scheduled Date',
        validators=[Optional()],
        render_kw={'class': 'form-control'}
    )
    
    scheduled_time = TimeField(
        'Scheduled Time',
        validators=[Optional()],
        render_kw={'class': 'form-control'}
    )
    
    estimated_duration = IntegerField(
        'Estimated Duration (minutes)',
        validators=[Optional(), NumberRange(min=1, max=1440)],
        render_kw={'placeholder': 'e.g., 30', 'class': 'form-control'}
    )
    
    priority = SelectField(
        'Priority',
        choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Urgent', 'Urgent')],
        default='Medium',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )
    
    submit = SubmitField('Add Task')


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=150)],
        render_kw={'placeholder': 'Enter your email address'}
    )
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=6, max=100)],
        render_kw={'placeholder': 'Enter new password'}
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), Length(min=6, max=100), EqualTo('password')],
        render_kw={'placeholder': 'Confirm new password'}
    )
    submit = SubmitField('Reset Password')


class OTPVerificationForm(FlaskForm):
    otp_code = StringField(
        'OTP Code',
        validators=[DataRequired(), Length(min=6, max=6)],
        render_kw={'placeholder': 'Enter 6-digit OTP', 'maxlength': '6', 'pattern': '[0-9]{6}'}
    )
    submit = SubmitField('Verify OTP')
    resend_otp = SubmitField('Resend OTP')
