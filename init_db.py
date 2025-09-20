#!/usr/bin/env python3
"""
Initialize the database with all required tables.
"""

import os
from app import create_app, db

def init_database():
    """Initialize the database with all tables."""
    # Set development environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Creating database tables...")
            
            # Create all tables
            db.create_all()
            
            print("✅ Database tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables created: {tables}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return False

if __name__ == '__main__':
    success = init_database()
    if success:
        print("\n🎉 Database initialization completed successfully!")
        print("🚀 You can now start your Flask server with: flask run --debug")
    else:
        print("\n💥 Database initialization failed!")
        print("Please check the error messages above.")
