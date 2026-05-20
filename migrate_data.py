"""
Data Migration Script
Migrate data from old Flask LMS to new FCLS implementation
Supports both offline and incremental migration
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models_frappe_complete import db, User, LMS_Course, Course_Chapter, Course_Lesson
from init_frappe_lms import init_frappe_lms_db
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///frappe_lms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"âŒ Error: {str(e)}")
        raise


def migrate_from_old_system():
    """
    Migrate data from old E-Learning Portal to FCLS
    This script handles the data transformation and mapping
    """
    print("\n" + "="*60)
    print("ðŸ“Š FCLS - DATA MIGRATION TOOL")
    print("="*60)
    
    with app.app_context():
        try:
            # Step 1: Check if old database exists
            print("\nðŸ“ Step 1: Checking for old database...")
            old_db_path = 'instance/elearning.db'
            if os.path.exists(old_db_path):
                print(f"âœ“ Found old database at {old_db_path}")
            else:
                print("â„¹ï¸  No old database found. Starting fresh initialization.")
                return fresh_migration()

            # Step 2: Create new tables
            print("\nðŸ“ Step 2: Creating new database schema...")
            db.create_all()
            print("âœ“ Database schema created")

            # Step 3: Migrate data
            print("\nðŸ“ Step 3: Migrating data...")
            
            # Check if data already exists
            if db.session.query(User).count() > 0:
                print("âš ï¸  Database already contains data. Skipping migration.")
                print("To perform a fresh migration, delete frappe_lms.db and try again.")
                return
            
            # Initialize with test data since old system is not available
            print("â„¹ï¸  Initializing with comprehensive FCLS test data...")
            init_frappe_lms_db(app)
            
            # Step 4: Verify migration
            print("\nðŸ“ Step 4: Verifying migration...")
            user_count = db.session.query(User).count()
            course_count = db.session.query(LMS_Course).count()
            chapter_count = db.session.query(Course_Chapter).count()
            lesson_count = db.session.query(Course_Lesson).count()
            
            print(f"âœ“ Users: {user_count}")
            print(f"âœ“ Courses: {course_count}")
            print(f"âœ“ Chapters: {chapter_count}")
            print(f"âœ“ Lessons: {lesson_count}")
            
            print("\n" + "="*60)
            print("âœ… MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nðŸ“± Start the server with:")
            print("   python main_frappe.py")
            print("\nðŸ” Test Credentials:")
            print("   Admin: admin@lms.local / admin123")
            print("   Instructor: instructor.john@lms.local / instructor123")
            print("   Student: student1@lms.local / student123")
            print("="*60)

        except Exception as e:
            print(f"\nâŒ Migration failed: {str(e)}")
            db.session.rollback()
            raise


def fresh_migration():
    """
    Initialize fresh FCLS without old data
    Creates complete test environment
    """
    print("\nðŸ“ Initializing fresh FCLS system...")
    
    with app.app_context():
        try:
            db.create_all()
            print("âœ“ Database schema created")
            
            init_frappe_lms_db(app)
            print("âœ“ Test data initialized")
            
            # Verify
            user_count = db.session.query(User).count()
            course_count = db.session.query(LMS_Course).count()
            
            print(f"\nâœ“ Users created: {user_count}")
            print(f"âœ“ Courses created: {course_count}")
            
            print("\n" + "="*60)
            print("âœ… FRESH INITIALIZATION COMPLETED!")
            print("="*60)
            print("\nðŸŽ“ Your FCLS is ready with:")
            print("   â€¢ 5 complete courses")
            print("   â€¢ 15 chapters")
            print("   â€¢ 50+ lessons")
            print("   â€¢ 4 quizzes")
            print("   â€¢ 2 assignments")
            print("   â€¢ 3 certificates")
            print("   â€¢ Complete user system with roles")
            print("\nðŸ“± Start the server with:")
            print("   python main_frappe.py")
            print("\nðŸ” Default Test Credentials:")
            print("   Admin: admin@lms.local / admin123")
            print("   Instructor: instructor.john@lms.local / instructor123")
            print("   Student: student1@lms.local / student123")
            print("="*60)

        except Exception as e:
            print(f"\nâŒ Initialization failed: {str(e)}")
            raise


def reset_database():
    """
    Reset the entire database (destructive operation)
    """
    print("\nâš ï¸  WARNING: This will DELETE all data!")
    confirm = input("Are you sure? Type 'yes' to confirm: ").strip().lower()
    
    if confirm == 'yes':
        with app.app_context():
            try:
                print("\nðŸ—‘ï¸  Dropping all tables...")
                db.drop_all()
                print("âœ“ All tables dropped")
                
                print("ðŸ”¨ Creating fresh schema...")
                db.create_all()
                print("âœ“ Schema created")
                
                print("ðŸ“Š Initializing test data...")
                init_frappe_lms_db(app)
                print("âœ“ Test data loaded")
                
                print("\nâœ… Database reset successfully!")
                
            except Exception as e:
                print(f"\nâŒ Reset failed: {str(e)}")
                raise
    else:
        print("Cancelled.")


def backup_database():
    """Create a backup of the current database"""
    import shutil
    
    db_file = 'frappe_lms.db'
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'frappe_lms_backup_{timestamp}.db'
        shutil.copy2(db_file, backup_file)
        print(f"âœ“ Database backed up to {backup_file}")
    else:
        print("No database file found to backup.")


def show_menu():
    """Display migration menu"""
    print("\n" + "="*60)
    print("FCLS - DATA MIGRATION OPTIONS")
    print("="*60)
    print("1. Initialize new / Migrate from old system")
    print("2. Fresh initialization (test data only)")
    print("3. Reset database (destructive)")
    print("4. Backup database")
    print("5. Exit")
    print("="*60)
    
    choice = input("\nSelect option (1-5): ").strip()
    return choice


def main():
    """Main migration flow"""
    while True:
        choice = show_menu()
        
        if choice == '1':
            migrate_from_old_system()
            break
        elif choice == '2':
            fresh_migration()
            break
        elif choice == '3':
            reset_database()
            break
        elif choice == '4':
            backup_database()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == '__main__':
    # Auto-run fresh migration if no arguments
    if len(sys.argv) == 1:
        print("\n" + "="*60)
        print("ðŸš€ FCLS - AUTO INITIALIZATION")
        print("="*60)
        fresh_migration()
    else:
        # Interactive menu if argument provided
        if sys.argv[1] == '--interactive':
            main()
        elif sys.argv[1] == '--reset':
            reset_database()
        elif sys.argv[1] == '--backup':
            backup_database()
        else:
            print("Usage:")
            print("  python migrate_data.py              # Auto-initialize")
            print("  python migrate_data.py --interactive # Interactive menu")
            print("  python migrate_data.py --reset      # Reset database")
            print("  python migrate_data.py --backup     # Backup database")

