#!/usr/bin/env python3
"""
Development server script with live reloading enabled.
Run this script to start Flask with automatic reloading of templates and static files.
"""

import os
from app import create_app

if __name__ == '__main__':
    # Set development environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    app = create_app()
    
    print("🚀 Starting Flask development server with live reloading...")
    print("📝 Templates and static files will auto-reload on changes")
    print("🚫 Cache-busting enabled - CSS changes will appear immediately")
    print("🌐 Server will be available at: http://127.0.0.1:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    
    app.run(debug=True, use_reloader=True)
