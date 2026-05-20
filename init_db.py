"""
Initialize database with sample data
Run this once to populate the database with demo content
"""

from main_enhanced import app, db
from models import (
    User, Course, Lesson, Quiz, Assignment, Quiz_Question, Quiz_Option,
    Enrollment, Lesson_Progress, Announcement, Chapter, Batch, BatchEnrollment,
    Certificate, Discussion, DiscussionReply, CourseReview, LiveClass
)
from datetime import datetime, timedelta

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        print("Creating database tables...")
        db.drop_all()
        db.create_all()
        
        # ==================== CREATE USERS ====================
        print("\nCreating sample users...")
        
        # Admin user
        admin = User(
            first_name="Admin",
            last_name="User",
            email="admin@elearning.local",
            password="admin123",  # Change this in production!
            account="admin",
            bio="System administrator"
        )
        
        # Teacher users
        teacher1 = User(
            first_name="Dr. John",
            last_name="Smith",
            email="john.smith@faculty.local",
            password="teacher123",
            account="teacher",
            bio="Senior Lecturer in Computer Science"
        )
        
        teacher2 = User(
            first_name="Prof. Sarah",
            last_name="Johnson",
            email="sarah.johnson@faculty.local",
            password="teacher123",
            account="teacher",
            bio="Associate Professor in Software Engineering"
        )
        
        # Student users
        students = [
            User(
                first_name=f"Student{i}",
                last_name=f"User{i}",
                email=f"student{i}@faculty.local",
                password="student123",
                account="student",
                bio=f"Computer Science Student - Year {(i % 4) + 1}"
            ) for i in range(1, 11)
        ]
        
        db.session.add(admin)
        db.session.add(teacher1)
        db.session.add(teacher2)
        for student in students:
            db.session.add(student)
        db.session.commit()
        
        print(f"Created 1 admin, 2 teachers, and {len(students)} students")
        
        # ==================== CREATE COURSES ====================
        print("\nCreating sample courses...")
        
        courses = [
            Course(
                title="Introduction to Python Programming",
                slug="intro-python",
                description="Learn the basics of Python programming including variables, data types, control structures, and functions.",
                category="Programming",
                price=0,
                duration_hours=40,
                difficulty_level="beginner",
                instructor_id=teacher1.id,
                is_published=True
            ),
            Course(
                title="Web Development with Flask",
                slug="flask-web-dev",
                description="Building web applications using Flask framework, working with databases, and deployment.",
                category="Web Development",
                price=0,
                duration_hours=50,
                difficulty_level="intermediate",
                instructor_id=teacher1.id,
                is_published=True
            ),
            Course(
                title="Data Structures and Algorithms",
                slug="dsa",
                description="Comprehensive course on data structures, algorithms, and their applications.",
                category="Computer Science",
                price=0,
                duration_hours=60,
                difficulty_level="intermediate",
                instructor_id=teacher2.id,
                is_published=True
            ),
            Course(
                title="Object-Oriented Programming",
                slug="oop",
                description="Master object-oriented design principles, patterns, and best practices.",
                category="Programming",
                price=0,
                duration_hours=45,
                difficulty_level="intermediate",
                instructor_id=teacher2.id,
                is_published=True
            ),
            Course(
                title="Database Design & SQL",
                slug="database-sql",
                description="Design robust databases and write efficient SQL queries.",
                category="Databases",
                price=0,
                duration_hours=35,
                difficulty_level="beginner",
                instructor_id=teacher1.id,
                is_published=True
            ),
        ]
        
        for course in courses:
            db.session.add(course)
        db.session.commit()
        
        print(f"Created {len(courses)} courses")
        
        # ==================== CREATE LESSONS ====================
        print("\nCreating sample lessons...")
        
        # Python course lessons
        python_lessons = [
            Lesson(
                course_id=courses[0].id,
                title="Getting Started with Python",
                description="Introduction to Python and setting up your environment",
                order=1,
                content="<h2>Welcome to Python!</h2><p>Python is a versatile programming language...</p>",
                is_published=True
            ),
            Lesson(
                course_id=courses[0].id,
                title="Variables and Data Types",
                description="Understanding Python variables and data types",
                order=2,
                content="<h2>Variables and Data Types</h2><p>In Python, variables are used to store data...</p>",
                is_published=True
            ),
            Lesson(
                course_id=courses[0].id,
                title="Control Structures",
                description="If statements, loops, and more",
                order=3,
                content="<h2>Control Structures</h2><p>Control structures allow you to run different code...</p>",
                is_published=True
            ),
        ]
        
        # Flask course lessons
        flask_lessons = [
            Lesson(
                course_id=courses[1].id,
                title="Flask Basics",
                description="Introduction to Flask framework",
                order=1,
                content="<h2>Flask Overview</h2><p>Flask is a lightweight web framework...</p>",
                is_published=True
            ),
            Lesson(
                course_id=courses[1].id,
                title="Routing and Views",
                description="Understanding Flask routes and view functions",
                order=2,
                content="<h2>Routing in Flask</h2><p>Routes map URLs to Python functions...</p>",
                is_published=True
            ),
        ]
        
        all_lessons = python_lessons + flask_lessons
        for lesson in all_lessons:
            db.session.add(lesson)
        db.session.commit()
        
        print(f"Created {len(all_lessons)} lessons")
        
        # ==================== CREATE CHAPTERS ====================
        print("\nCreating sample chapters...")
        
        chapters = [
            Chapter(
                course_id=courses[0].id,
                title="Chapter 1: Python Fundamentals",
                description="Introduction to Python basics and fundamentals",
                order=1
            ),
            Chapter(
                course_id=courses[0].id,
                title="Chapter 2: Object-Oriented Programming",
                description="Learn OOP concepts in Python",
                order=2
            ),
            Chapter(
                course_id=courses[1].id,
                title="Chapter 1: Web Framework Basics",
                description="Introduction to Flask and web frameworks",
                order=1
            ),
        ]
        
        for chapter in chapters:
            db.session.add(chapter)
        db.session.commit()
        
        print(f"Created {len(chapters)} chapters")
        
        # ==================== CREATE BATCHES ====================
        print("\nCreating sample batches...")
        
        batches = [
            Batch(
                course_id=courses[0].id,
                title=f"Python - Batch 2024-Q1",
                description="First batch of the year for Python course",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=60),
                max_students=30,
                instructor_id=teacher1.id,
                is_published=True
            ),
            Batch(
                course_id=courses[1].id,
                title=f"Flask - Batch 2024-Q1",
                description="Introduction batch for Flask web development",
                start_date=datetime.now() + timedelta(days=7),
                end_date=datetime.now() + timedelta(days=70),
                max_students=25,
                instructor_id=teacher1.id,
                is_published=True
            ),
        ]
        
        for batch in batches:
            db.session.add(batch)
        db.session.commit()
        
        print(f"Created {len(batches)} batches")
        
        # ==================== CREATE BATCH ENROLLMENTS ====================
        print("\nCreating sample batch enrollments...")
        
        batch_enrollments = []
        for batch in batches:
            for student in students[:5]:
                enrollment = BatchEnrollment(
                    batch_id=batch.id,
                    student_id=student.id,
                    progress_percentage=float((students.index(student) % 3) * 30)
                )
                batch_enrollments.append(enrollment)
                db.session.add(enrollment)
        
        db.session.commit()
        print(f"Created {len(batch_enrollments)} batch enrollments")
        
        # ==================== CREATE CERTIFICATES ====================
        print("\nCreating sample certificates...")
        
        certificates = [
            Certificate(
                student_id=students[0].id,
                course_id=courses[0].id,
                certificate_number=f"CERT-{students[0].id}-{courses[0].id}-2024",
                completion_date=datetime.now() - timedelta(days=30),
                is_issued=True,
                hash="abc123def456"
            ),
            Certificate(
                student_id=students[1].id,
                course_id=courses[1].id,
                certificate_number=f"CERT-{students[1].id}-{courses[1].id}-2024",
                completion_date=datetime.now() - timedelta(days=15),
                is_issued=True,
                hash="xyz789uvw012"
            ),
        ]
        
        for cert in certificates:
            db.session.add(cert)
        db.session.commit()
        
        print(f"Created {len(certificates)} certificates")
        
        # ==================== CREATE DISCUSSIONS ====================
        print("\nCreating sample discussions...")
        
        discussions = [
            Discussion(
                course_id=courses[0].id,
                created_by_id=students[0].id,
                title="How to install Python on Windows?",
                content="I'm having trouble installing Python. Can someone help?",
                is_solved=False,
                is_pinned=False
            ),
            Discussion(
                course_id=courses[0].id,
                created_by_id=students[1].id,
                title="Understanding list comprehensions",
                content="Can someone explain list comprehensions with examples?",
                is_solved=True,
                is_pinned=True
            ),
            Discussion(
                course_id=courses[1].id,
                created_by_id=students[2].id,
                title="Flask routing best practices",
                content="What are the best practices for organizing Flask routes?",
                is_solved=False,
                is_pinned=False
            ),
        ]
        
        for discussion in discussions:
            db.session.add(discussion)
        db.session.commit()
        
        print(f"Created {len(discussions)} discussions")
        
        # ==================== CREATE DISCUSSION REPLIES ====================
        print("\nCreating sample discussion replies...")
        
        replies = [
            DiscussionReply(
                discussion_id=discussions[0].id,
                created_by_id=students[3].id,
                content="You can download Python from python.org. Follow the installer.",
                upvotes=5
            ),
            DiscussionReply(
                discussion_id=discussions[1].id,
                created_by_id=teacher1.id,
                content="List comprehensions are a way to create lists using a more concise syntax...",
                is_marked_as_answer=True,
                upvotes=12
            ),
        ]
        
        for reply in replies:
            db.session.add(reply)
        db.session.commit()
        
        print(f"Created {len(replies)} discussion replies")
        
        # ==================== CREATE COURSE REVIEWS ====================
        print("\nCreating sample course reviews...")
        
        reviews = [
            CourseReview(
                course_id=courses[0].id,
                student_id=students[0].id,
                rating=5,
                title="Excellent Python course!",
                review_text="Great course for beginners. Very well structured and easy to follow.",
                helpful_count=8
            ),
            CourseReview(
                course_id=courses[0].id,
                student_id=students[1].id,
                rating=4,
                title="Good content, could use more examples",
                review_text="Content is good but would benefit from more practical examples.",
                helpful_count=3
            ),
            CourseReview(
                course_id=courses[1].id,
                student_id=students[2].id,
                rating=5,
                title="Best Flask tutorial ever!",
                review_text="Finally a clear and comprehensive Flask course!",
                helpful_count=15
            ),
        ]
        
        for review in reviews:
            db.session.add(review)
        db.session.commit()
        
        print(f"Created {len(reviews)} course reviews")
        
        # ==================== CREATE LIVE CLASSES ====================
        print("\nCreating sample live classes...")
        
        live_classes = [
            LiveClass(
                batch_id=batches[0].id,
                title="Python Basics - Live Session",
                description="Interactive session covering Python fundamentals",
                scheduled_at=datetime.now() + timedelta(days=2),
                duration_minutes=60,
                zoom_link="https://zoom.us/j/123456789"
            ),
            LiveClass(
                batch_id=batches[1].id,
                title="Flask Application Demo",
                description="Live demonstration of building a Flask application",
                scheduled_at=datetime.now() + timedelta(days=5),
                duration_minutes=90,
                zoom_link="https://zoom.us/j/987654321"
            ),
        ]
        
        for lc in live_classes:
            db.session.add(lc)
        db.session.commit()
        
        print(f"Created {len(live_classes)} live classes")
        print("\nCreating sample quizzes...")
        
        quiz1 = Quiz(
            course_id=courses[0].id,
            title="Python Basics Quiz",
            description="Test your knowledge of Python basics",
            passing_percentage=70,
            duration_minutes=30,
            attempts_allowed=3,
            order=1,
            is_published=True
        )
        
        db.session.add(quiz1)
        db.session.commit()
        
        # Create questions
        questions = [
            Quiz_Question(
                quiz_id=quiz1.id,
                question_text="What is Python?",
                question_type="multiple_choice",
                marks=1,
                order=1
            ),
            Quiz_Question(
                quiz_id=quiz1.id,
                question_text="Which of these is NOT a Python data type?",
                question_type="multiple_choice",
                marks=1,
                order=2
            ),
        ]
        
        for question in questions:
            db.session.add(question)
        db.session.commit()
        
        # Add options for question 1
        options1 = [
            Quiz_Option(question_id=questions[0].id, option_text="A programming language", order=1, is_correct=True),
            Quiz_Option(question_id=questions[0].id, option_text="A type of snake", order=2, is_correct=False),
            Quiz_Option(question_id=questions[0].id, option_text="A database", order=3, is_correct=False),
            Quiz_Option(question_id=questions[0].id, option_text="A web browser", order=4, is_correct=False),
        ]
        
        # Add options for question 2
        options2 = [
            Quiz_Option(question_id=questions[1].id, option_text="String", order=1, is_correct=False),
            Quiz_Option(question_id=questions[1].id, option_text="Integer", order=2, is_correct=False),
            Quiz_Option(question_id=questions[1].id, option_text="Float", order=3, is_correct=False),
            Quiz_Option(question_id=questions[1].id, option_text="Hamburger", order=4, is_correct=True),
        ]
        
        for option in options1 + options2:
            db.session.add(option)
        db.session.commit()
        
        quiz1.total_questions = len(questions)
        db.session.commit()
        
        print(f"Created 1 quiz with {len(questions)} questions")
        
        # ==================== CREATE ASSIGNMENTS ====================
        print("\nCreating sample assignments...")
        
        assignments = [
            Assignment(
                course_id=courses[0].id,
                title="Simple Python Programs",
                description="Write simple Python programs to practice basics",
                instructions="Create 3 simple programs demonstrating: 1) Variables, 2) Control structures, 3) Functions",
                total_marks=100,
                due_date=datetime.now() + timedelta(days=7),
                order=1,
                is_published=True
            ),
            Assignment(
                course_id=courses[1].id,
                title="Build a Simple Flask App",
                description="Create a basic Flask web application",
                instructions="Build a Flask app with at least 3 routes and basic HTML templates",
                total_marks=100,
                due_date=datetime.now() + timedelta(days=14),
                order=1,
                is_published=True
            ),
        ]
        
        for assignment in assignments:
            db.session.add(assignment)
        db.session.commit()
        
        print(f"Created {len(assignments)} assignments")
        
        # ==================== CREATE ENROLLMENTS ====================
        print("\nCreating sample enrollments...")
        
        enrollments = []
        for student in students:
            # Each student enrolls in 2-3 random courses
            for course in courses[:3]:
                enrollment = Enrollment(
                    student_id=student.id,
                    course_id=course.id
                )
                enrollments.append(enrollment)
                db.session.add(enrollment)
        
        db.session.commit()
        print(f"Created {len(enrollments)} enrollments")
        
        # ==================== CREATE LESSON PROGRESS ====================
        print("\nCreating sample lesson progress...")
        
        progress_count = 0
        for student in students:
            for lesson in python_lessons[:2]:
                progress = Lesson_Progress(
                    student_id=student.id,
                    lesson_id=lesson.id,
                    is_completed=True,
                    completed_at=datetime.now() - timedelta(days=5)
                )
                db.session.add(progress)
                progress_count += 1
        
        db.session.commit()
        print(f"Created {progress_count} lesson progress records")
        
        # ==================== CREATE ANNOUNCEMENTS ====================
        print("\nCreating sample announcements...")
        
        announcements = [
            Announcement(
                course_id=courses[0].id,
                title="Welcome to the course!",
                content="Welcome everyone! I'm excited to have you in this Python course.",
                created_by_id=teacher1.id
            ),
            Announcement(
                course_id=courses[1].id,
                title="Flask Framework Update",
                content="We're using Flask 3.0 in this course. Make sure to update your dependencies.",
                created_by_id=teacher1.id
            ),
        ]
        
        for announcement in announcements:
            db.session.add(announcement)
        db.session.commit()
        
        print(f"Created {len(announcements)} announcements")
        
        # ==================== DATABASE SUMMARY ====================
        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        print("\nTest Credentials:")
        print("-" * 40)
        print("Admin User:")
        print("  Email: admin@elearning.local")
        print("  Password: admin123")
        print("\nTeacher User:")
        print("  Email: john.smith@faculty.local")
        print("  Password: teacher123")
        print("\nStudent User:")
        print("  Email: student1@faculty.local")
        print("  Password: student123")
        print("-" * 40)
        print("\nDatabase Statistics:")
        print(f"  Users: {User.query.count()}")
        print(f"  Courses: {Course.query.count()}")
        print(f"  Lessons: {Lesson.query.count()}")
        print(f"  Chapters: {Chapter.query.count()}")
        print(f"  Quizzes: {Quiz.query.count()}")
        print(f"  Assignments: {Assignment.query.count()}")
        print(f"  Enrollments: {Enrollment.query.count()}")
        print(f"  Batches: {Batch.query.count()}")
        print(f"  Batch Enrollments: {BatchEnrollment.query.count()}")
        print(f"  Certificates: {Certificate.query.count()}")
        print(f"  Discussions: {Discussion.query.count()}")
        print(f"  Discussion Replies: {DiscussionReply.query.count()}")
        print(f"  Course Reviews: {CourseReview.query.count()}")
        print(f"  Live Classes: {LiveClass.query.count()}")
        print("="*60)

if __name__ == '__main__':
    init_database()
