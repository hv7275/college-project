#!/usr/bin/env python3
"""
Setup script for Task Management System
This script helps initialize the database and check configuration.
"""

import os
import sys
from pathlib import Path

def setup_database():
    """Initialize the database with all tables."""
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            db.create_all()
            print("✅ Database initialized successfully!")
            return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def check_environment():
    """Check if environment variables are properly configured."""
    print("🔍 Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Please copy .env.example to .env and configure it.")
        return False
    
    print("✅ .env file found")
    
    # Check critical variables
    from dotenv import load_dotenv
    load_dotenv()
    
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key or secret_key == "your-super-secret-key-change-this-in-production-12345":
        print("⚠️  WARNING: Please change the SECRET_KEY in your .env file")
    
    mail_username = os.environ.get("MAIL_USERNAME")
    mail_password = os.environ.get("MAIL_PASSWORD")
    
    if not mail_username or mail_username == "your-email@gmail.com":
        print("⚠️  WARNING: Please configure MAIL_USERNAME in your .env file")
    
    if not mail_password or mail_password == "your-app-password-here":
        print("⚠️  WARNING: Please configure MAIL_PASSWORD in your .env file")
    
    if mail_username and mail_username != "your-email@gmail.com" and mail_password and mail_password != "your-app-password-here":
        print("✅ Email configuration looks good")
    
    return True

def main():
    """Main setup function."""
    print("🚀 Setting up Task Management System...")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Setup database
    print("\n📊 Initializing database...")
    if not setup_database():
        print("\n❌ Database setup failed.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Update your .env file with real email credentials")
    print("2. Run: python run.py")
    print("3. Open: http://127.0.0.1:5000")
    print("\n💡 For Gmail:")
    print("- Enable 2-Factor Authentication")
    print("- Generate an App Password")
    print("- Use the App Password in MAIL_PASSWORD")

if __name__ == "__main__":
    main()
