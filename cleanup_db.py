#!/usr/bin/env python
"""Cleanup script to drop and recreate all database tables with fresh schema"""

from main_enhanced import app, db

with app.app_context():
    print("Dropping all existing tables...")
    db.drop_all()
    print("Tables dropped successfully!")
    
    print("\nCreating fresh database schema...")
    db.create_all()
    print("Fresh database schema created successfully!")
    
    print("\nDatabase cleanup complete. Run 'python main_enhanced.py' to start the application.")
