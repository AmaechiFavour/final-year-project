# Initialization script for FCLS models with comprehensive test data
from models_frappe_complete import *
from datetime import datetime, timedelta
import json

def init_frappe_lms_db(app):
    """Initialize FCLS database with complete test data"""
    with app.app_context():
        print("=" * 60)
        print("FCLS DATABASE INITIALIZATION")
        print("=" * 60)
        
        # Drop and recreate all tables
        print("\n1. Creating database tables...")
        db.drop_all()
        db.create_all()
        print("   ✓ Database tables created")
        
        # ==================== CREATE USERS ====================
        print("\n2. Creating users...")
        
        admin = User(
            name="admin@lms.local",
            email="admin@lms.local",
            full_name="Admin User",
            password="admin123",
            user_type=UserType.ADMIN.value,
            bio="System Administrator",
            headline="Managing the LMS"
        )
        
        instructors = [
            User(
                name="instructor.john@lms.local",
                email="instructor.john@lms.local",
                full_name="Dr. John Smith",
                password="instructor123",
                user_type=UserType.INSTRUCTOR.value,
                bio="Senior instructor with 10+ years experience",
                headline="Python Expert"
            ),
            User(
                name="instructor.sarah@lms.local",
                email="instructor.sarah@lms.local",
                full_name="Prof. Sarah Johnson",
                password="instructor123",
                user_type=UserType.INSTRUCTOR.value,
                bio="Web development specialist",
                headline="Full Stack Developer"
            ),
        ]
        
        moderators = [
            User(
                name="moderator@lms.local",
                email="moderator@lms.local",
                full_name="Content Moderator",
                password="moderator123",
                user_type=UserType.MODERATOR.value,
                bio="Manages course content",
                headline="Content Manager"
            ),
        ]
        
        students = []
        for i in range(1, 21):
            student = User(
                name=f"student{i}@lms.local",
                email=f"student{i}@lms.local",
                full_name=f"Student {i}",
                password="student123",
                user_type=UserType.STUDENT.value,
                bio=f"Computer Science Student",
                headline=f"Learner #{i}"
            )
            students.append(student)
        
        db.session.add(admin)
        for instructor in instructors:
            db.session.add(instructor)
        for moderator in moderators:
            db.session.add(moderator)
        for student in students:
            db.session.add(student)
        db.session.commit()
        
        print(f"   ✓ Created 1 admin, {len(instructors)} instructors, {len(moderators)} moderators, {len(students)} students")
        
        # ==================== CREATE COURSES ====================
        print("\n3. Creating courses...")
        
        courses = [
            Course(
                title="Python Programming Fundamentals",
                slug="python-fundamentals",
                description="Learn Python from scratch. This comprehensive course covers variables, data types, control structures, functions, and object-oriented programming.",
                short_introduction="Master Python basics in 4 weeks",
                instructor_id=instructors[0].id,
                category="Programming",
                published=True,
                featured=True,
                video_link="https://www.youtube.com/embed/kqtZrmDKNC8",
                image="https://via.placeholder.com/400x300?text=Python+Fundamentals",
                rating=4.8,
                enrollments=15,
                lessons=4,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Web Development with Flask",
                slug="flask-web-development",
                description="Build modern web applications using Flask. Learn routing, templates, databases, authentication, and deployment.",
                short_introduction="Create production-ready web apps",
                instructor_id=instructors[0].id,
                category="Web Development",
                published=True,
                featured=True,
                video_link="https://www.youtube.com/embed/Z1RJmh_OqAE",
                image="https://via.placeholder.com/400x300?text=Flask+Development",
                rating=4.9,
                enrollments=18,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Advanced JavaScript & React",
                slug="javascript-react-advanced",
                description="Take your JavaScript skills to the next level with React. Build interactive UIs and master modern web development practices.",
                short_introduction="Master React for modern web development",
                instructor_id=instructors[1].id,
                category="Web Development",
                published=True,
                featured=False,
                video_link="https://www.youtube.com/embed/dQw4w9WgXcQ",
                image="https://via.placeholder.com/400x300?text=React+JavaScript",
                rating=4.7,
                enrollments=12,
                lessons=6,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Data Science with Python",
                slug="data-science-python",
                description="Learn data analysis, visualization, and machine learning using Python libraries like Pandas, NumPy, and Scikit-learn.",
                short_introduction="Data science from basics to advanced",
                instructor_id=instructors[1].id,
                category="Data Science",
                published=True,
                featured=False,
                image="https://via.placeholder.com/400x300?text=Data+Science",
                rating=4.6,
                enrollments=10,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Computer Networks & Protocols",
                slug="computer-networks",
                description="Understand how computer networks work. Learn TCP/IP, OSI model, routing, switching, DNS, HTTP, and network security fundamentals.",
                short_introduction="Master networking concepts and protocols",
                instructor_id=instructors[0].id,
                category="Networking",
                published=True,
                featured=False,
                rating=4.5,
                enrollments=8,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Database Management Systems",
                slug="database-management",
                description="Learn relational database design, SQL queries, normalization, transactions, indexing, and modern NoSQL databases.",
                short_introduction="Design and manage databases like a pro",
                instructor_id=instructors[1].id,
                category="Database Systems",
                published=True,
                featured=False,
                rating=4.7,
                enrollments=11,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Cyber Security Fundamentals",
                slug="cyber-security-fundamentals",
                description="Learn the fundamentals of cybersecurity including threat analysis, encryption, network security, ethical hacking, and security best practices.",
                short_introduction="Protect systems from cyber threats",
                instructor_id=instructors[0].id,
                category="Cyber Security",
                published=True,
                featured=True,
                rating=4.9,
                enrollments=20,
                lessons=6,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Software Engineering Principles",
                slug="software-engineering",
                description="Learn software development lifecycle, agile methodology, design patterns, testing, version control, and project management.",
                short_introduction="Build software the professional way",
                instructor_id=instructors[1].id,
                category="Software Engineering",
                published=True,
                featured=False,
                rating=4.6,
                enrollments=14,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Operating Systems Concepts",
                slug="operating-systems",
                description="Understand process management, memory management, file systems, I/O systems, and the internals of modern operating systems.",
                short_introduction="How OS manages hardware and software",
                instructor_id=instructors[0].id,
                category="Operating Systems",
                published=True,
                featured=False,
                rating=4.4,
                enrollments=9,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Artificial Intelligence & Machine Learning",
                slug="ai-machine-learning",
                description="Introduction to AI concepts, supervised and unsupervised learning, neural networks, natural language processing, and computer vision.",
                short_introduction="Build intelligent systems with AI/ML",
                instructor_id=instructors[1].id,
                category="Artificial Intelligence",
                published=True,
                featured=True,
                rating=4.8,
                enrollments=22,
                lessons=6,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Mobile App Development",
                slug="mobile-app-development",
                description="Build cross-platform mobile applications. Learn React Native, Flutter basics, UI/UX for mobile, and app deployment to stores.",
                short_introduction="Create mobile apps for iOS and Android",
                instructor_id=instructors[0].id,
                category="Mobile Development",
                published=True,
                featured=False,
                rating=4.5,
                enrollments=13,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Cloud Computing & DevOps",
                slug="cloud-computing-devops",
                description="Learn cloud platforms (AWS, Azure, GCP), containerization with Docker, CI/CD pipelines, and infrastructure as code.",
                short_introduction="Deploy and scale apps in the cloud",
                instructor_id=instructors[1].id,
                category="Cloud Computing",
                published=True,
                featured=False,
                rating=4.7,
                enrollments=16,
                lessons=5,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Data Structures & Algorithms",
                slug="data-structures-algorithms",
                description="Master arrays, linked lists, trees, graphs, sorting, searching, dynamic programming, and algorithm complexity analysis.",
                short_introduction="Core CS fundamentals for problem solving",
                instructor_id=instructors[0].id,
                category="Computer Science",
                published=True,
                featured=True,
                rating=4.9,
                enrollments=25,
                lessons=6,
                paid_course=False,
                enable_certification=True
            ),
            Course(
                title="Computer Architecture & Organization",
                slug="computer-architecture",
                description="Learn CPU design, instruction sets, memory hierarchy, pipelining, parallel processing, and modern processor architectures.",
                short_introduction="Understand how computers work inside",
                instructor_id=instructors[1].id,
                category="Computer Science",
                published=True,
                featured=False,
                rating=4.3,
                enrollments=7,
                lessons=4,
                paid_course=False,
                enable_certification=True
            ),
        ]
        
        for course in courses:
            db.session.add(course)
        db.session.commit()
        
        print(f"   ✓ Created {len(courses)} courses")
        
        # ==================== CREATE CHAPTERS ====================
        print("\n4. Creating chapters...")
        
        chapters_data = {
            courses[0].id: [  # Python Fundamentals
                {"title": "Chapter 1: Getting Started", "description": "Introduction and setup"},
                {"title": "Chapter 2: Core Concepts", "description": "Variables, data types, and operations"},
                {"title": "Chapter 3: Control Flow", "description": "If statements, loops, and functions"},
                {"title": "Chapter 4: OOP Basics", "description": "Classes and objects"},
            ],
            courses[1].id: [  # Flask
                {"title": "Chapter 1: Flask Basics", "description": "Setup and first application"},
                {"title": "Chapter 2: Routing & Templates", "description": "URL routing and Jinja2 templating"},
                {"title": "Chapter 3: Databases", "description": "SQLAlchemy and database design"},
                {"title": "Chapter 4: Authentication", "description": "User login and security"},
                {"title": "Chapter 5: Deployment", "description": "Deploy to production"},
            ],
        }
        
        all_chapters = []
        for course_id, chapter_list in chapters_data.items():
            for idx, chapter_data in enumerate(chapter_list, 1):
                chapter = CourseChapter(
                    course_id=course_id,
                    title=chapter_data['title'],
                    description=chapter_data['description'],
                    order=idx
                )
                all_chapters.append(chapter)
                db.session.add(chapter)
        
        db.session.commit()
        print(f"   ✓ Created {len(all_chapters)} chapters")
        
        # ==================== CREATE LESSONS ====================
        print("\n5. Creating lessons...")
        
        all_lessons = []
        for chapter in all_chapters:
            for i in range(2):  # 2 lessons per chapter
                lesson = CourseLesson(
                    chapter_id=chapter.id,
                    title=f"{chapter.title} - Lesson {i+1}",
                    body=f"<h2>Lesson Content</h2><p>This is the content for {chapter.title}. Students will learn important concepts here.</p>",
                    order=i+1,
                    duration=30  # 30 minutes
                )
                all_lessons.append(lesson)
                db.session.add(lesson)
        
        db.session.commit()
        print(f"   ✓ Created {len(all_lessons)} lessons")
        
        # ==================== CREATE QUIZZES ====================
        print("\n6. Creating quizzes...")
        
        quizzes = []
        for idx, course in enumerate(courses[:2]):  # Quiz for first 2 courses
            quiz = Quiz(
                title=f"{course.title} - Assessment",
                course_id=course.id,
                passing_percentage=70,
                max_attempts=3,
                duration_minutes=45,
                show_answers=True,
                published=True
            )
            quizzes.append(quiz)
            db.session.add(quiz)
        
        db.session.commit()
        print(f"   ✓ Created {len(quizzes)} quizzes")
        
        # ==================== CREATE QUESTIONS ====================
        print("\n7. Creating quiz questions...")
        
        all_questions = []
        for quiz in quizzes:
            for q_idx in range(3):  # 3 questions per quiz
                question = Question(
                    title=f"Question {q_idx+1} for {quiz.title}",
                    question_type=QuizType.SINGLE_CHOICE.value,
                    marks=1,
                    hint="Read carefully",
                    explanation="The correct answer is..."
                )
                all_questions.append(question)
                db.session.add(question)
                db.session.flush()
                
                # Add options
                for opt_idx in range(4):
                    option = Option(
                        question_id=question.id,
                        title=f"Option {chr(65 + opt_idx)}",
                        order=opt_idx + 1,
                        is_correct=(opt_idx == 0)  # First option is correct
                    )
                    db.session.add(option)
                
                # Link to quiz
                quiz_question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_id=question.id,
                    order=q_idx + 1
                )
                db.session.add(quiz_question)
        
        db.session.commit()
        print(f"   ✓ Created {len(all_questions)} questions with options")
        
        # ==================== CREATE ASSIGNMENTS ====================
        print("\n8. Creating assignments...")
        
        assignments = []
        for course in courses[:2]:
            assignment = Assignment(
                title=f"Assignment: {course.title}",
                course_id=course.id,
                question="Create a practical project based on what you learned. Submit your code and documentation.",
                description="Hands-on project work",
                assignment_type="file_upload",
                total_marks=100,
                due_date=datetime.now() + timedelta(days=30),
                published=True
            )
            assignments.append(assignment)
            db.session.add(assignment)
        
        db.session.commit()
        print(f"   ✓ Created {len(assignments)} assignments")
        
        # ==================== CREATE ENROLLMENTS ====================
        print("\n9. Creating enrollments...")
        
        enrollments = []
        for student in students[:10]:  # First 10 students
            for idx, course in enumerate(courses[:2]):  # Enroll in first 2 courses
                enrollment = Enrollment(
                    member_id=student.id,
                    course_id=course.id,
                    status=EnrollmentStatus.ACTIVE.value if idx == 0 else EnrollmentStatus.COMPLETED.value,
                    progress=50.0 if idx == 0 else 100.0,
                    enrolled_on=datetime.now() - timedelta(days=30),
                    completed_on=datetime.now() if idx > 0 else None,
                    current_lesson_id=all_lessons[0].id if idx == 0 else None
                )
                enrollments.append(enrollment)
                db.session.add(enrollment)
        
        db.session.commit()
        print(f"   ✓ Created {len(enrollments)} enrollments")
        
        # ==================== CREATE BATCHES ====================
        print("\n10. Creating batches...")
        
        batches = []
        for course in courses[:2]:
            batch = Batch(
                title=f"{course.title} - Batch A2024Q2",
                course_id=course.id,
                description=f"Cohort 1 of {course.title}",
                status="In Progress",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=90),
                max_students=30,
                published=True,
                enable_certification=True,
                enable_self_learning=False,
                paid=False,
                batch_price=0
            )
            batches.append(batch)
            db.session.add(batch)
        
        db.session.commit()
        print(f"   ✓ Created {len(batches)} batches")
        
        # ==================== CREATE BATCH ENROLLMENTS ====================
        print("\n11. Creating batch enrollments...")
        
        batch_enrollments = []
        for batch in batches:
            for student in students[10:15]:  # Students 10-14
                batch_enrollment = BatchEnrollment(
                    member_id=student.id,
                    batch_id=batch.id,
                    enrolled_on=datetime.now()
                )
                batch_enrollments.append(batch_enrollment)
                db.session.add(batch_enrollment)
        
        db.session.commit()
        print(f"   ✓ Created {len(batch_enrollments)} batch enrollments")
        
        # ==================== CREATE CERTIFICATES ====================
        print("\n12. Creating certificates...")
        
        certificates = []
        for student in students[:5]:  # First 5 students
            for course in courses[:1]:  # First course only
                certificate = Certificate(
                    member_id=student.id,
                    course_id=course.id,
                    name=f"{course.title} - Certificate",
                    template="default",
                    issue_date=datetime.now() - timedelta(days=10),
                    certificate_number=f"CERT-{student.id}-{course.id}-2024",
                    status="Active"
                )
                certificates.append(certificate)
                db.session.add(certificate)
        
        db.session.commit()
        print(f"   ✓ Created {len(certificates)} certificates")
        
        # ==================== CREATE LIVE CLASSES ====================
        print("\n13. Creating live classes...")
        
        live_classes = []
        for batch in batches:
            for i in range(2):
                live_class = LiveClass(
                    title=f"Live Class {i+1} - {batch.title}",
                    batch_id=batch.id,
                    description="Interactive live session with Q&A",
                    meeting_url=f"https://zoom.us/j/{1000000000 + batch.id + i}",
                    scheduled_at=datetime.now() + timedelta(days=7*(i+1)),
                    duration_minutes=60,
                    is_recorded=True
                )
                live_classes.append(live_class)
                db.session.add(live_class)
        
        db.session.commit()
        print(f"   ✓ Created {len(live_classes)} live classes")
        
        # ==================== CREATE COURSE REVIEWS ====================
        print("\n14. Creating course reviews...")
        
        reviews = []
        for student in students[:5]:
            for course in courses[:2]:
                review = CourseReview(
                    course_id=course.id,
                    member_id=student.id,
                    rating=4 + (student.id % 2),  # 4 or 5 stars
                    title=f"Great course - {course.title}",
                    review_text="Very informative and well structured. Highly recommended!",
                    helpful_count=5 + (student.id % 5)
                )
                reviews.append(review)
                db.session.add(review)
        
        db.session.commit()
        print(f"   ✓ Created {len(reviews)} course reviews")
        
        # ==================== SUMMARY ====================
        print("\n" + "=" * 60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("=" * 60)
        print(f"\nCreated:")
        print(f"  • {User.query.count()} users (1 admin, 2 instructors, 1 moderator, {len(students)} students)")
        print(f"  • {Course.query.count()} courses")
        print(f"  • {CourseChapter.query.count()} chapters")
        print(f"  • {CourseLesson.query.count()} lessons")
        print(f"  • {Quiz.query.count()} quizzes")
        print(f"  • {Question.query.count()} questions")
        print(f"  • {Assignment.query.count()} assignments")
        print(f"  • {Enrollment.query.count()} enrollments")
        print(f"  • {Batch.query.count()} batches")
        print(f"  • {BatchEnrollment.query.count()} batch enrollments")
        print(f"  • {Certificate.query.count()} certificates")
        print(f"  • {LiveClass.query.count()} live classes")
        print(f"  • {CourseReview.query.count()} course reviews")
        print("\nTest Credentials:")
        print("  Admin:      admin@lms.local / admin123")
        print("  Instructor: instructor.john@lms.local / instructor123")
        print("  Student:    student1@lms.local / student123")
        print("=" * 60 + "\n")
