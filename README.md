# Task Management System

A Flask-based web application for managing tasks with user authentication, password reset functionality, and email notifications.

## Features

- User registration and authentication
- Task management (create, edit, delete, mark as complete)
- Password reset via email
- Task history tracking
- Priority-based task organization
- Responsive web interface

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd college-project
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your configuration:
```bash
nano .env  # or use your preferred editor
```

### 5. Required Environment Variables

Update the following variables in your `.env` file:

#### Flask Configuration
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=1
```

#### Database Configuration
```env
DATABASE_URL=sqlite:///instance/site.db
```

#### Email Configuration (Gmail)
```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-here
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Note**: For Gmail, you need to use an App Password, not your regular password:
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password for this application
3. Use the App Password in the `MAIL_PASSWORD` field

### 6. Initialize Database
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
```

### 7. Run the Application
```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000`

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Required |
| `FLASK_ENV` | Flask environment (development/production) | development |
| `FLASK_DEBUG` | Enable debug mode | 1 |
| `DATABASE_URL` | Database connection string | sqlite:///instance/site.db |
| `MAIL_SERVER` | SMTP server | smtp.gmail.com |
| `MAIL_PORT` | SMTP port | 587 |
| `MAIL_USE_TLS` | Use TLS for email | True |
| `MAIL_USERNAME` | Email username | Required |
| `MAIL_PASSWORD` | Email password/app password | Required |
| `MAIL_DEFAULT_SENDER` | Default sender email | MAIL_USERNAME |
| `PASSWORD_RESET_EXPIRY_HOURS` | Password reset token expiry | 1 |
| `WTF_CSRF_ENABLED` | Enable CSRF protection | True |
| `WTF_CSRF_TIME_LIMIT` | CSRF token expiry (seconds) | 3600 |

## Security Notes

- **Never commit the `.env` file** to version control
- **Change the SECRET_KEY** in production
- **Use strong passwords** for email accounts
- **Enable 2FA** on email accounts
- **Use App Passwords** for Gmail

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

## Production Deployment

1. Set `FLASK_ENV=production`
2. Set `FLASK_DEBUG=0`
3. Use a production WSGI server (e.g., Gunicorn)
4. Use a production database (PostgreSQL, MySQL)
5. Set up proper email configuration
6. Use environment variables for all sensitive data

## License

This project is for educational purposes.
