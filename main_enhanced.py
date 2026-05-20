"""
FCLS - Faculty of Computing Learning System
A comprehensive offline LMS built with Flask
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from models import (
    db, User, Course, Lesson, Lesson_Progress, Quiz, Quiz_Question, Quiz_Option,
    Quiz_Attempt, Quiz_Answer, Assignment, Assignment_Submission, Enrollment,
    Lesson_Resource, Announcement, Chapter, Batch, BatchEnrollment,
    Certificate, Discussion, DiscussionReply, CourseReview, LiveClass
)
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import json
from pathlib import Path

# ==================== APPLICATION SETUP ====================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elearning.db'
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

db.init_app(app)

# Create upload folder
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# ==================== UTILITY FUNCTIONS ====================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.account != 'teacher':
            flash('You must be a teacher to access this resource', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.account != 'admin':
            flash('You must be an admin to access this resource', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_progress_for_course(student_id, course_id):
    """Calculate student progress for a course"""
    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    if total_lessons == 0:
        return 0
    
    completed = Lesson_Progress.query.filter_by(
        student_id=student_id,
        is_completed=True
    ).join(Lesson).filter(Lesson.course_id == course_id).count()
    
    return (completed / total_lessons) * 100

# ==================== AUTHENTICATION ROUTES ====================
@app.route('/')
def index():
    """Landing page / Home"""
    logged_in = 'user_id' in session
    user = None
    if logged_in:
        user = User.query.get(session['user_id'])
        # Clear session if user doesn't exist in database
        if user is None:
            session.clear()
            logged_in = False
    
    # Get all published courses
    featured_courses = Course.query.filter_by(is_published=True, is_archived=False).limit(6).all()
    
    # Calculate statistics
    total_courses = Course.query.filter_by(is_published=True).count()
    total_students = User.query.filter_by(account='student').count()
    total_teachers = User.query.filter_by(account='teacher').count()
    courses_empty = total_courses == 0
    
    # Calculate total learning hours from course durations
    from sqlalchemy import func as sa_func
    total_learning_hours = db.session.query(sa_func.coalesce(sa_func.sum(Course.duration_hours), 0)).filter(
        Course.is_published == True
    ).scalar() or 0
    
    # Prepare course data with counts
    course_data = []
    for course in featured_courses:
        instructor_name = 'Instructor'
        if hasattr(course, 'instructor') and course.instructor:
            instructor_name = course.instructor.first_name
        
        course_dict = {
            'id': course.id,
            'title': course.title,
            'summary': course.summary,
            'lessons_count': len(course.lessons),
            'enrollment_count': len(course.enrollments),
            'instructor_name': instructor_name,
            'image': course.image if hasattr(course, 'image') else None
        }
        course_data.append(course_dict)
    
    return render_template('index.html', 
        featured_courses=course_data,
        total_courses=total_courses,
        total_students=total_students,
        total_teachers=total_teachers,
        total_learning_hours=total_learning_hours,
        courses_empty=courses_empty,
        logged_in=logged_in, 
        user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        account_type = request.form.get('account_type', 'student')

        # Validation
        if not all([first_name, last_name, email, password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register.html')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        else:
            try:
                new_user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password,  # In production, use werkzeug.security hash_password
                    account=account_type,
                    is_active=True
                )
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error during registration: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            user.last_login = datetime.now()
            db.session.commit()
            
            if user.account == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user.account == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


# ==================== PROFILE ROUTES ====================
@app.route('/profile')
@login_required
def profile():
    """View/edit user profile"""
    user = User.query.get(session['user_id'])
    
    # Get user stats
    if user.account == 'student':
        course_count = Enrollment.query.filter_by(student_id=user.id).count()
        completed_count = Enrollment.query.filter_by(student_id=user.id, is_completed=True).count()
    elif user.account == 'teacher':
        course_count = Course.query.filter_by(instructor_id=user.id).count()
        completed_count = 0
    else:
        course_count = Course.query.count()
        completed_count = 0

    cert_count = Certificate.query.filter_by(student_id=user.id).count() if user.account == 'student' else 0
    
    return render_template('profile.html',
                         user=user,
                         logged_in=True,
                         course_count=course_count,
                         completed_count=completed_count,
                         cert_count=cert_count)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile info"""
    user = User.query.get(session['user_id'])
    
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    bio = request.form.get('bio', '').strip()
    
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.bio = bio
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/upload-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Upload profile picture"""
    user = User.query.get(session['user_id'])
    
    if 'profile_picture' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create unique filename with user id
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"profile_{user.id}_{int(datetime.now().timestamp())}.{ext}"
        
        # Save to uploads/profiles/
        profiles_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
        Path(profiles_dir).mkdir(parents=True, exist_ok=True)
        
        filepath = os.path.join(profiles_dir, unique_filename)
        file.save(filepath)
        
        # Update user record
        user.profile_picture = f"/uploads/profiles/{unique_filename}"
        db.session.commit()
        
        flash('Profile picture updated!', 'success')
    else:
        flash('Invalid file type. Please upload an image (png, jpg, jpeg, gif).', 'error')
    
    return redirect(url_for('profile'))

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


# ==================== STUDENT ROUTES ====================
@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect to appropriate dashboard based on user role"""
    user = User.query.get(session['user_id'])
    if user.account == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif user.account == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('student_dashboard'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student main dashboard"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get enrolled courses
    enrollments = Enrollment.query.filter_by(student_id=user_id).all()
    enrolled_courses = [e.course for e in enrollments]
    
    # Get progress for each course
    progress_data = {}
    completed_count = 0
    in_progress_count = 0
    
    for enrollment in enrollments:
        progress = get_user_progress_for_course(user_id, enrollment.course_id)
        progress_data[enrollment.course_id] = progress
        enrollment.progress_percentage = progress
        
        # Count courses based on progress
        if progress >= 100:
            completed_count += 1
        elif progress > 0:
            in_progress_count += 1
    
    db.session.commit()
    
    # Get recommended courses (not enrolled)
    all_courses = Course.query.filter_by(is_published=True, is_archived=False).all()
    recommended_courses = [c for c in all_courses if c.id not in [e.course_id for e in enrollments]]
    
    return render_template('student_dashboard.html', 
                         user=user, 
                         enrolled_courses=enrolled_courses,
                         recommended_courses=recommended_courses[:6],
                         progress_data=progress_data,
                         enrolled_count=len(enrolled_courses),
                         completed_count=completed_count,
                         in_progress_count=in_progress_count,
                         streak=0)

@app.route('/student/browse-courses')
@login_required
def browse_courses():
    """Browse all available courses"""
    user = User.query.get(session.get('user_id'))
    courses = Course.query.filter_by(is_published=True, is_archived=False).all()
    
    # Prepare course data
    course_data = []
    for course in courses:
        # Check if user is enrolled
        is_enrolled = any(e.student_id == user.id for e in course.enrollments) if user else False
        
        instructor_name = 'Instructor'
        if hasattr(course, 'instructor') and course.instructor:
            instructor_name = course.instructor.first_name
        
        course_dict = {
            'id': course.id,
            'title': course.title,
            'summary': course.summary,
            'category': course.category,
            'lessons_count': len(course.lessons),
            'enrollment_count': len(course.enrollments),
            'instructor_name': instructor_name,
            'image': course.image if hasattr(course, 'image') else None,
            'is_enrolled': is_enrolled
        }
        course_data.append(course_dict)
    
    return render_template('courses.html', 
                         courses=course_data,
                         current_user=user)

@app.route('/course/<int:course_id>')
def view_course(course_id):
    """View course details"""
    course = Course.query.get_or_404(course_id)
    is_enrolled = False
    is_logged_in = 'user_id' in session
    
    if is_logged_in:
        enrollment = Enrollment.query.filter_by(
            student_id=session['user_id'],
            course_id=course_id
        ).first()
        is_enrolled = enrollment is not None
    
    # Get instructor info
    instructor = course.instructor
    
    # Get course stats
    total_students = len(course.enrollments)
    total_lessons = len(course.lessons)
    
    return render_template('course_detail.html',
                         course=course,
                         is_enrolled=is_enrolled,
                         is_logged_in=is_logged_in,
                         instructor=instructor,
                         total_students=total_students,
                         total_lessons=total_lessons)

@app.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    """Enroll student in a course"""
    course = Course.query.get_or_404(course_id)
    user_id = session['user_id']
    
    # Check if already enrolled
    existing = Enrollment.query.filter_by(student_id=user_id, course_id=course_id).first()
    if existing:
        flash('You are already enrolled in this course', 'warning')
    else:
        try:
            enrollment = Enrollment(student_id=user_id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()
            flash(f'Successfully enrolled in {course.title}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Enrollment failed: {str(e)}', 'danger')
    
    return redirect(url_for('view_course_content', course_id=course_id))

@app.route('/course/<int:course_id>/content')
@login_required
def view_course_content(course_id):
    """View course content (lessons, quizzes, assignments)"""
    course = Course.query.get_or_404(course_id)
    user_id = session['user_id']
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=course_id).first()
    if not enrollment:
        flash('You must enroll in this course first', 'warning')
        return redirect(url_for('view_course', course_id=course_id))
    
    # Get lessons
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
    
    # Get progress
    progress_lessons = {
        lp.lesson_id: lp for lp in 
        Lesson_Progress.query.filter_by(student_id=user_id).all()
    }
    
    # Get quizzes
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.order).all()
    
    # Get assignments
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.order).all()
    
    return render_template('course_content.html',
                         course=course,
                         lessons=lessons,
                         progress_lessons=progress_lessons,
                         quizzes=quizzes,
                         assignments=assignments)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    """View a particular lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    user_id = session['user_id']
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=user_id,
        course_id=lesson.course_id
    ).first()
    if not enrollment:
        flash('You must enroll in this course first', 'warning')
        return redirect(url_for('view_course', course_id=lesson.course_id))
    
    # Get or create lesson progress
    progress = Lesson_Progress.query.filter_by(
        student_id=user_id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = Lesson_Progress(student_id=user_id, lesson_id=lesson_id)
        db.session.add(progress)
        db.session.commit()
    
    # Get other lessons in course for navigation
    all_lessons = Lesson.query.filter_by(course_id=lesson.course_id).order_by(Lesson.order).all()
    current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson_id), 0)
    
    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None
    
    return render_template('lesson.html',
                         lesson=lesson,
                         progress=progress,
                         prev_lesson=prev_lesson,
                         next_lesson=next_lesson)

@app.route('/lesson/<int:lesson_id>/mark-complete', methods=['POST'])
@login_required
def mark_lesson_complete(lesson_id):
    """Mark lesson as completed"""
    lesson = Lesson.query.get_or_404(lesson_id)
    user_id = session['user_id']
    
    progress = Lesson_Progress.query.filter_by(
        student_id=user_id,
        lesson_id=lesson_id
    ).first()
    
    if progress:
        progress.is_completed = True
        progress.completed_at = datetime.now()
        db.session.commit()
        flash('Lesson marked as completed!', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    
    return redirect(url_for('view_lesson', lesson_id=lesson_id))

# ==================== QUIZ ROUTES ====================
@app.route('/quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    """View quiz details and start quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = session['user_id']
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=user_id,
        course_id=quiz.course_id
    ).first()
    if not enrollment:
        flash('You must enroll in this course first', 'warning')
        return redirect(url_for('view_course', course_id=quiz.course_id))
    
    # Get previous attempts
    attempts = Quiz_Attempt.query.filter_by(student_id=user_id, quiz_id=quiz_id).all()
    
    can_attempt = (quiz.attempts_allowed == -1 or 
                  len(attempts) < quiz.attempts_allowed)
    
    return render_template('quiz_start.html',
                         quiz=quiz,
                         attempts=attempts,
                         can_attempt=can_attempt)

@app.route('/quiz/<int:quiz_id>/take', methods=['POST'])
@login_required
def take_quiz(quiz_id):
    """Start a new quiz attempt"""
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = session['user_id']
    
    # Create attempt record
    attempt = Quiz_Attempt(student_id=user_id, quiz_id=quiz_id)
    db.session.add(attempt)
    db.session.commit()
    
    return redirect(url_for('quiz_question', quiz_id=quiz_id, attempt_id=attempt.id, question_num=1))

@app.route('/quiz/<int:quiz_id>/attempt/<int:attempt_id>/question/<int:question_num>')
@login_required
def quiz_question(quiz_id, attempt_id, question_num):
    """Display quiz question"""
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt = Quiz_Attempt.query.get_or_404(attempt_id)
    
    # Check ownership
    if attempt.student_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    questions = quiz.questions
    if question_num < 1 or question_num > len(questions):
        # Submit quiz
        return redirect(url_for('submit_quiz', quiz_id=quiz_id, attempt_id=attempt_id))
    
    current_question = questions[question_num - 1]
    
    return render_template('quiz_question.html',
                         quiz=quiz,
                         attempt=attempt,
                         question=current_question,
                         question_num=question_num,
                         total_questions=len(questions))

@app.route('/quiz/<int:quiz_id>/attempt/<int:attempt_id>/answer', methods=['POST'])
@login_required
def save_quiz_answer(quiz_id, attempt_id):
    """Save quiz answer"""
    attempt = Quiz_Attempt.query.get_or_404(attempt_id)
    question_id = request.form.get('question_id', type=int)
    selected_option_id = request.form.get('option_id', type=int)
    text_answer = request.form.get('text_answer', '')
    
    question = Quiz_Question.query.get_or_404(question_id)
    
    # Delete existing answer if present
    existing = Quiz_Answer.query.filter_by(
        attempt_id=attempt_id,
        question_id=question_id
    ).first()
    if existing:
        db.session.delete(existing)
    
    # Create new answer
    answer = Quiz_Answer(
        attempt_id=attempt_id,
        question_id=question_id,
        selected_option_id=selected_option_id,
        text_answer=text_answer
    )
    db.session.add(answer)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'next_question': request.form.get('next_question')})
    
    return redirect(url_for('quiz_question', 
                           quiz_id=quiz_id, 
                           attempt_id=attempt_id,
                           question_num=request.form.get('next_question', 1)))

@app.route('/quiz/<int:quiz_id>/attempt/<int:attempt_id>/submit')
@login_required
def submit_quiz(quiz_id, attempt_id):
    """Submit quiz and calculate score"""
    attempt = Quiz_Attempt.query.get_or_404(attempt_id)
    quiz = attempt.quiz
    
    if attempt.submitted_at is not None:
        flash('This quiz has already been submitted', 'warning')
        return redirect(url_for('quiz_results', attempt_id=attempt_id))
    
    # Calculate score
    total_marks = 0
    obtained_marks = 0
    
    for question in quiz.questions:
        total_marks += question.marks
        answer = Quiz_Answer.query.filter_by(
            attempt_id=attempt_id,
            question_id=question.id
        ).first()
        
        if answer and answer.selected_option_id:
            option = Quiz_Option.query.get(answer.selected_option_id)
            if option and option.is_correct:
                marks = question.marks
                obtained_marks += marks
                answer.is_correct = True
                answer.marks_obtained = marks
            else:
                answer.is_correct = False
                answer.marks_obtained = 0
        elif answer and answer.text_answer:
            # For short answer, mark as pending review
            answer.is_correct = None
            answer.marks_obtained = 0
    
    # Update attempt
    attempt.score = obtained_marks
    attempt.percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
    attempt.is_passed = attempt.percentage >= quiz.passing_percentage
    attempt.submitted_at = datetime.now()
    attempt.time_taken_seconds = int((attempt.submitted_at - attempt.started_at).total_seconds())
    
    db.session.commit()
    
    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('quiz_results', attempt_id=attempt_id))

@app.route('/quiz/attempt/<int:attempt_id>/results')
@login_required
def quiz_results(attempt_id):
    """View quiz results"""
    attempt = Quiz_Attempt.query.get_or_404(attempt_id)
    
    if attempt.student_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    return render_template('quiz_results.html', attempt=attempt)

# ==================== ASSIGNMENT ROUTES ====================
@app.route('/assignment/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    """View assignment details"""
    assignment = Assignment.query.get_or_404(assignment_id)
    user_id = session['user_id']
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=user_id,
        course_id=assignment.course_id
    ).first()
    if not enrollment:
        flash('You must enroll in this course first', 'warning')
        return redirect(url_for('view_course', course_id=assignment.course_id))
    
    # Get student submission
    submission = Assignment_Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=user_id
    ).first()
    
    return render_template('assignment.html',
                         assignment=assignment,
                         submission=submission)

@app.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    """Submit assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    user_id = session['user_id']
    
    submission_text = request.form.get('submission_text', '')
    file = request.files.get('file')
    
    # Get or create submission
    submission = Assignment_Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=user_id
    ).first()
    
    if not submission:
        submission = Assignment_Submission(
            assignment_id=assignment_id,
            student_id=user_id
        )
        db.session.add(submission)
    
    submission.submission_text = submission_text
    submission.is_submitted = True
    submission.submitted_at = datetime.now()
    
    # Handle file upload
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 
                              f'assignment_{assignment_id}_{user_id}_{filename}')
        file.save(filepath)
        submission.file_path = filepath
    
    db.session.commit()
    
    flash('Assignment submitted successfully!', 'success')
    return redirect(url_for('view_assignment', assignment_id=assignment_id))

# ==================== TEACHER ROUTES ====================
@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    """Teacher main dashboard"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get instructor's courses
    courses = Course.query.filter_by(instructor_id=user_id).all()
    
    # Calculate statistics
    total_students = sum(len(c.enrollments) for c in courses)
    total_enrollments = sum(len(c.enrollments) for c in courses)
    
    # Calculate average completion rate
    total_lessons = sum(len(c.lessons) for c in courses)
    if total_enrollments > 0 and total_lessons > 0:
        total_progress = 0
        for course in courses:
            for enrollment in course.enrollments:
                progress = get_user_progress_for_course(enrollment.student_id, course.id)
                total_progress += progress
        avg_completion = int(total_progress / (total_enrollments * len([c for c in courses if len(c.lessons) > 0]))) if any(c.lessons for c in courses) else 0
    else:
        avg_completion = 0
    
    return render_template('teacher_dashboard.html',
                         user=user,
                         courses=courses,
                         courses_count=len(courses),
                         total_students=total_students,
                         total_enrollments=total_enrollments,
                         avg_completion=avg_completion)

@app.route('/teacher/course/create', methods=['GET', 'POST'])
@teacher_required
def create_course():
    """Create new course"""
    if request.method == 'POST':
        try:
            course = Course(
                title=request.form.get('title'),
                slug=request.form.get('title', '').lower().replace(' ', '-'),
                description=request.form.get('description'),
                category=request.form.get('category'),
                price=float(request.form.get('price', 0)),
                duration_hours=int(request.form.get('duration_hours', 0)),
                difficulty_level=request.form.get('difficulty_level', 'beginner'),
                instructor_id=session['user_id'],
                is_published=False
            )
            db.session.add(course)
            db.session.commit()
            flash('Course created successfully!', 'success')
            return redirect(url_for('edit_course', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating course: {str(e)}', 'danger')
    
    return render_template('create_course.html')

@app.route('/teacher/course/<int:course_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_course(course_id):
    """Edit course"""
    course = Course.query.get_or_404(course_id)
    
    # Check ownership
    if course.instructor_id != session['user_id']:
        flash('You do not have permission to edit this course', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            course.title = request.form.get('title')
            course.description = request.form.get('description')
            course.category = request.form.get('category')
            course.price = float(request.form.get('price', 0))
            course.duration_hours = int(request.form.get('duration_hours', 0))
            course.difficulty_level = request.form.get('difficulty_level')
            course.is_published = 'is_published' in request.form
            
            db.session.commit()
            flash('Course updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating course: {str(e)}', 'danger')
    
    return render_template('edit_course.html', course=course)

@app.route('/teacher/course/<int:course_id>/manage')
@teacher_required
def manage_course(course_id):
    """Manage course content (lessons, quizzes, assignments)"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('You do not have permission to manage this course', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('manage_course.html', course=course)

# Lessons
@app.route('/teacher/course/<int:course_id>/lesson/create', methods=['GET', 'POST'])
@teacher_required
def create_lesson(course_id):
    """Create lesson"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            lesson = Lesson(
                course_id=course_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                content=request.form.get('content'),
                order=request.form.get('order', type=int),
                is_published=True
            )
            
            # Handle video upload
            if 'video' in request.files:
                video = request.files['video']
                if video and allowed_file(video.filename):
                    filename = secure_filename(video.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'],
                                          f'lesson_{course_id}_{filename}')
                    video.save(filepath)
                    lesson.video_url = filepath
            
            db.session.add(lesson)
            db.session.commit()
            
            flash('Lesson created successfully!', 'success')
            return redirect(url_for('manage_course', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating lesson: {str(e)}', 'danger')
    
    return render_template('create_lesson.html', course=course)

@app.route('/teacher/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_lesson(lesson_id):
    """Edit lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            lesson.title = request.form.get('title')
            lesson.description = request.form.get('description')
            lesson.content = request.form.get('content')
            lesson.order = request.form.get('order', type=int)
            
            db.session.commit()
            flash('Lesson updated successfully!', 'success')
            return redirect(url_for('manage_course', course_id=lesson.course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating lesson: {str(e)}', 'danger')
    
    return render_template('edit_lesson.html', lesson=lesson)

@app.route('/teacher/lesson/<int:lesson_id>/delete', methods=['POST'])
@teacher_required
def delete_lesson(lesson_id):
    """Delete lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    
    if lesson.course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    try:
        db.session.delete(lesson)
        db.session.commit()
        flash('Lesson deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting lesson: {str(e)}', 'danger')
    
    return redirect(url_for('manage_course', course_id=course_id))

# Quizzes
@app.route('/teacher/course/<int:course_id>/quiz/create', methods=['GET', 'POST'])
@teacher_required
def create_quiz(course_id):
    """Create quiz"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            quiz = Quiz(
                course_id=course_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                passing_percentage=float(request.form.get('passing_percentage', 70)),
                duration_minutes=int(request.form.get('duration_minutes', 60)),
                attempts_allowed=int(request.form.get('attempts_allowed', 1)),
                order=request.form.get('order', type=int),
                is_published=True
            )
            db.session.add(quiz)
            db.session.commit()
            
            flash('Quiz created! Now add questions.', 'success')
            return redirect(url_for('manage_quiz', quiz_id=quiz.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating quiz: {str(e)}', 'danger')
    
    return render_template('create_quiz.html', course=course)

@app.route('/teacher/quiz/<int:quiz_id>/manage')
@teacher_required
def manage_quiz(quiz_id):
    """Manage quiz questions"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('manage_quiz.html', quiz=quiz)

@app.route('/teacher/quiz/<int:quiz_id>/question/add', methods=['GET', 'POST'])
@teacher_required
def add_quiz_question(quiz_id):
    """Add question to quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            question = Quiz_Question(
                quiz_id=quiz_id,
                question_text=request.form.get('question_text'),
                question_type=request.form.get('question_type', 'multiple_choice'),
                marks=float(request.form.get('marks', 1)),
                order=request.form.get('order', type=int)
            )
            db.session.add(question)
            db.session.commit()
            
            # Add options for multiple choice
            if question.question_type == 'multiple_choice':
                for i in range(1, 5):
                    option_text = request.form.get(f'option_{i}')
                    if option_text:
                        is_correct = request.form.get(f'correct_{i}') == 'on'
                        option = Quiz_Option(
                            question_id=question.id,
                            option_text=option_text,
                            is_correct=is_correct,
                            order=i
                        )
                        db.session.add(option)
            
            db.session.commit()
            quiz.total_questions = len(quiz.questions)
            db.session.commit()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('manage_quiz', quiz_id=quiz_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding question: {str(e)}', 'danger')
    
    return render_template('add_quiz_question.html', quiz=quiz)

# Assignments
@app.route('/teacher/course/<int:course_id>/assignment/create', methods=['GET', 'POST'])
@teacher_required
def create_assignment(course_id):
    """Create assignment"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            assignment = Assignment(
                course_id=course_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                instructions=request.form.get('instructions'),
                total_marks=float(request.form.get('total_marks', 100)),
                due_date=request.form.get('due_date'),
                order=request.form.get('order', type=int),
                is_published=True
            )
            db.session.add(assignment)
            db.session.commit()
            
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('manage_course', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating assignment: {str(e)}', 'danger')
    
    return render_template('create_assignment.html', course=course)

@app.route('/teacher/assignment/<int:assignment_id>/submissions')
@teacher_required
def view_submissions(assignment_id):
    """View assignment submissions"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    submissions = Assignment_Submission.query.filter_by(assignment_id=assignment_id).all()
    
    return render_template('view_submissions.html',
                         assignment=assignment,
                         submissions=submissions)

@app.route('/teacher/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@teacher_required
def grade_submission(submission_id):
    """Grade assignment submission"""
    submission = Assignment_Submission.query.get_or_404(submission_id)
    
    if submission.assignment.course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            submission.marks_obtained = float(request.form.get('marks', 0))
            submission.feedback = request.form.get('feedback')
            submission.is_graded = True
            submission.graded_at = datetime.now()
            submission.graded_by_id = session['user_id']
            
            db.session.commit()
            flash('Submission graded successfully!', 'success')
            return redirect(url_for('view_submissions', assignment_id=submission.assignment_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error grading submission: {str(e)}', 'danger')
    
    return render_template('grade_submission.html', submission=submission)

# Student management
@app.route('/teacher/course/<int:course_id>/students')
@teacher_required
def view_course_students(course_id):
    """View students enrolled in course"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    
    # Get progress for each student
    student_progress = {}
    for enrollment in enrollments:
        progress = get_user_progress_for_course(enrollment.student_id, course_id)
        student_progress[enrollment.student_id] = progress
    
    return render_template('course_students.html',
                         course=course,
                         enrollments=enrollments,
                         student_progress=student_progress)

# ==================== ADMIN ROUTES ====================
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    from sqlalchemy import func as sa_func
    user = User.query.get(session['user_id'])
    
    # Get all stats
    all_users = User.query.all()
    all_courses = Course.query.all()
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_students = User.query.filter_by(account='student').count()
    total_teachers = User.query.filter_by(account='teacher').count()
    total_enrollments = Enrollment.query.count()

    # Growth calculations (this week vs last week)
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    new_students_this_week = User.query.filter(User.account == 'student', User.date_created >= week_ago).count()
    new_students_last_week = User.query.filter(User.account == 'student', User.date_created >= two_weeks_ago, User.date_created < week_ago).count()
    student_growth = round(((new_students_this_week - new_students_last_week) / max(new_students_last_week, 1)) * 100, 1)

    new_teachers_this_week = User.query.filter(User.account == 'teacher', User.date_created >= week_ago).count()
    new_teachers_last_week = User.query.filter(User.account == 'teacher', User.date_created >= two_weeks_ago, User.date_created < week_ago).count()
    teacher_growth = round(((new_teachers_this_week - new_teachers_last_week) / max(new_teachers_last_week, 1)) * 100, 1)

    new_courses_this_week = Course.query.filter(Course.created_at >= week_ago).count()
    new_enrollments_this_week = Enrollment.query.filter(Enrollment.enrolled_at >= week_ago).count()

    # Recent registrations (last 10)
    recent_registrations = User.query.order_by(User.date_created.desc()).limit(10).all()

    # Recent teachers with stats
    recent_teachers = User.query.filter_by(account='teacher').order_by(User.date_created.desc()).limit(5).all()
    for t in recent_teachers:
        t.courses_count = Course.query.filter_by(instructor_id=t.id).count()
        t_course_ids = [c.id for c in Course.query.filter_by(instructor_id=t.id).all()]
        t.student_count = db.session.query(sa_func.count(sa_func.distinct(Enrollment.student_id)))\
            .filter(Enrollment.course_id.in_(t_course_ids)).scalar() if t_course_ids else 0
        t.date_joined = t.date_created

    # Recent students with stats
    recent_students = User.query.filter_by(account='student').order_by(User.date_created.desc()).limit(5).all()
    for s in recent_students:
        s.enrollment_count = Enrollment.query.filter_by(student_id=s.id).count()
        s.completed_courses = Enrollment.query.filter_by(student_id=s.id, is_completed=True).count()
        s.date_joined = s.date_created

    # Set date_joined on recent registrations too
    for reg in recent_registrations:
        reg.date_joined = reg.date_created

    # Platform stats
    total_quiz_attempts = Quiz_Attempt.query.count()
    total_lessons_completed = Lesson_Progress.query.filter_by(is_completed=True).count()
    avg_course_rating_val = db.session.query(sa_func.avg(CourseReview.rating)).scalar()
    avg_course_rating = round(avg_course_rating_val or 0, 1)

    # Enrich courses for admin view
    for course in all_courses:
        course.student_count = len(course.enrollments)
        course.instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}" if course.instructor else "Unknown"

    return render_template('admin_dashboard.html',
                         user=user,
                         logged_in=True,
                         all_users=all_users,
                         all_courses=all_courses,
                         total_users=total_users,
                         total_courses=total_courses,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_enrollments=total_enrollments,
                         student_growth=student_growth,
                         teacher_growth=teacher_growth,
                         new_students_this_week=new_students_this_week,
                         new_teachers_this_week=new_teachers_this_week,
                         new_courses_this_week=new_courses_this_week,
                         new_enrollments_this_week=new_enrollments_this_week,
                         recent_registrations=recent_registrations,
                         recent_teachers=recent_teachers,
                         recent_students=recent_students,
                         total_quiz_attempts=total_quiz_attempts,
                         total_lessons_completed=total_lessons_completed,
                         avg_course_rating=avg_course_rating)

@app.route('/admin/users')
@admin_required
def manage_users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.account = request.form.get('account')
            user.is_active = 'is_active' in request.form
            
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/courses')
@admin_required
def manage_courses():
    """Manage courses"""
    page = request.args.get('page', 1, type=int)
    courses = Course.query.paginate(page=page, per_page=20)
    
    return render_template('admin_courses.html', courses=courses)

@app.route('/admin/course/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    """Delete course"""
    course = Course.query.get_or_404(course_id)
    
    try:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course: {str(e)}', 'danger')
    
    return redirect(url_for('manage_courses'))

# ==================== CHAPTER ROUTES ====================
@app.route('/teacher/course/<int:course_id>/chapter/create', methods=['GET', 'POST'])
@teacher_required
def create_chapter(course_id):
    """Create a chapter for course"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            chapter = Chapter(
                course_id=course_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                order=request.form.get('order', type=int, default=1)
            )
            db.session.add(chapter)
            db.session.commit()
            flash('Chapter created successfully!', 'success')
            return redirect(url_for('manage_course', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating chapter: {str(e)}', 'danger')
    
    return render_template('create_chapter.html', course=course)

@app.route('/course/<int:course_id>/chapters')
@login_required
def view_course_chapters(course_id):
    """View course chapters and lessons hierarchy"""
    course = Course.query.get_or_404(course_id)
    
    # Check enrollment if not instructor
    user = User.query.get(session['user_id'])
    if user.account == 'student':
        enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=course_id).first()
        if not enrollment:
            flash('You must enroll in this course first', 'warning')
            return redirect(url_for('view_course', course_id=course_id))
    elif course.instructor_id != user.id and user.account != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    chapters = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order).all()
    
    return render_template('course_chapters.html', course=course, chapters=chapters)

# ==================== BATCH ROUTES ====================
@app.route('/teacher/course/<int:course_id>/batch/create', methods=['GET', 'POST'])
@teacher_required
def create_batch(course_id):
    """Create batch for learners"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
            batch = Batch(
                course_id=course_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
                max_students=int(request.form.get('max_students', 0)) or None,
                instructor_id=session['user_id'],
                is_published=True
            )
            db.session.add(batch)
            db.session.commit()
            flash('Batch created successfully!', 'success')
            return redirect(url_for('manage_batch', batch_id=batch.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating batch: {str(e)}', 'danger')
    
    return render_template('create_batch.html', course=course)

@app.route('/batch/<int:batch_id>')
@login_required
def view_batch(batch_id):
    """View batch details"""
    batch = Batch.query.get_or_404(batch_id)
    user = User.query.get(session['user_id'])
    
    # Check if user is enrolled or instructor
    is_enrolled = any(be.student_id == user.id for be in batch.enrollments)
    is_instructor = batch.instructor_id == user.id
    
    if not (is_enrolled or is_instructor or user.account == 'admin'):
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    batch_enrollments = BatchEnrollment.query.filter_by(batch_id=batch_id).all()
    live_classes = LiveClass.query.filter_by(batch_id=batch_id).all()
    
    return render_template('batch_detail.html',
                         batch=batch,
                         batch_enrollments=batch_enrollments,
                         live_classes=live_classes,
                         is_instructor=is_instructor)

@app.route('/batch/<int:batch_id>/enroll', methods=['POST'])
@login_required
def enroll_batch(batch_id):
    """Enroll student in batch"""
    batch = Batch.query.get_or_404(batch_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if user.account != 'student':
        flash('Only students can enroll in batches', 'warning')
        return redirect(url_for('view_batch', batch_id=batch_id))
    
    # Check if already enrolled
    existing = BatchEnrollment.query.filter_by(batch_id=batch_id, student_id=user_id).first()
    if existing:
        flash('You are already enrolled in this batch', 'warning')
    else:
        try:
            # Also enroll in the course if not already
            enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=batch.course_id).first()
            if not enrollment:
                enrollment = Enrollment(student_id=user_id, course_id=batch.course_id)
                db.session.add(enrollment)
            
            # Enroll in batch
            batch_enrollment = BatchEnrollment(batch_id=batch_id, student_id=user_id)
            db.session.add(batch_enrollment)
            db.session.commit()
            flash(f'Successfully enrolled in batch {batch.title}!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Enrollment failed: {str(e)}', 'danger')
    
    return redirect(url_for('view_batch', batch_id=batch_id))

@app.route('/teacher/batch/<int:batch_id>/manage')
@teacher_required
def manage_batch(batch_id):
    """Manage batch"""
    batch = Batch.query.get_or_404(batch_id)
    
    if batch.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    enrollments = BatchEnrollment.query.filter_by(batch_id=batch_id).all()
    live_classes = LiveClass.query.filter_by(batch_id=batch_id).all()
    
    return render_template('manage_batch.html',
                         batch=batch,
                         enrollments=enrollments,
                         live_classes=live_classes)

@app.route('/teacher/batch/<int:batch_id>/add-liveclass', methods=['GET', 'POST'])
@teacher_required
def add_live_class(batch_id):
    """Add live class to batch"""
    batch = Batch.query.get_or_404(batch_id)
    
    if batch.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            scheduled_at = request.form.get('scheduled_at')
            
            live_class = LiveClass(
                batch_id=batch_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                scheduled_at=datetime.strptime(scheduled_at, '%Y-%m-%dT%H:%M') if scheduled_at else None,
                duration_minutes=int(request.form.get('duration_minutes', 60)) or None,
                zoom_link=request.form.get('zoom_link')
            )
            db.session.add(live_class)
            db.session.commit()
            flash('Live class scheduled successfully!', 'success')
            return redirect(url_for('manage_batch', batch_id=batch_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error scheduling live class: {str(e)}', 'danger')
    
    return render_template('add_live_class.html', batch=batch)

# ==================== CERTIFICATE ROUTES ====================
@app.route('/student/certificates')
@login_required
def view_certificates():
    """View earned certificates"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    certificates = Certificate.query.filter_by(student_id=user_id, is_issued=True).all()
    
    return render_template('certificates.html', user=user, certificates=certificates)

@app.route('/certificate/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    """View certificate detail"""
    cert = Certificate.query.get_or_404(cert_id)
    
    # Check access
    if cert.student_id != session['user_id'] and User.query.get(session['user_id']).account != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    return render_template('certificate_detail.html', certificate=cert)

@app.route('/teacher/course/<int:course_id>/issue-certificates', methods=['GET', 'POST'])
@teacher_required
def issue_certificates(course_id):
    """Issue certificates to students who completed course"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            enrollments = Enrollment.query.filter_by(course_id=course_id).all()
            issued_count = 0
            
            for enrollment in enrollments:
                progress = get_user_progress_for_course(enrollment.student_id, course_id)
                
                # Issue cert if progress >= 80%
                if progress >= 80:
                    existing_cert = Certificate.query.filter_by(
                        student_id=enrollment.student_id,
                        course_id=course_id
                    ).first()
                    
                    if not existing_cert:
                        cert = Certificate(
                            student_id=enrollment.student_id,
                            course_id=course_id,
                            certificate_number=f"CERT-{enrollment.student_id}-{course_id}-{datetime.now().year}",
                            completion_date=datetime.now(),
                            is_issued=True,
                            hash=f"hash_{enrollment.student_id}_{course_id}_{datetime.now().timestamp()}"
                        )
                        db.session.add(cert)
                        issued_count += 1
            
            db.session.commit()
            flash(f'Issued {issued_count} certificate(s) successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error issuing certificates: {str(e)}', 'danger')
        
        return redirect(url_for('manage_course', course_id=course_id))
    
    # Get students with high progress
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    qualified_students = []
    
    for enrollment in enrollments:
        progress = get_user_progress_for_course(enrollment.student_id, course_id)
        if progress >= 80:
            student = User.query.get(enrollment.student_id)
            qualified_students.append({
                'student': student,
                'progress': progress
            })
    
    return render_template('issue_certificates.html',
                         course=course,
                         qualified_students=qualified_students)

# ==================== DISCUSSION / Q&A ROUTES ====================
@app.route('/course/<int:course_id>/discussions')
@login_required
def view_course_discussions(course_id):
    """View course discussions/Q&A forum"""
    course = Course.query.get_or_404(course_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=course_id).first()
    if not enrollment and course.instructor_id != user_id and user.account != 'admin':
        flash('You must enroll in this course first', 'warning')
        return redirect(url_for('view_course', course_id=course_id))
    
    discussions = Discussion.query.filter_by(course_id=course_id).order_by(
        Discussion.is_pinned.desc(),
        Discussion.updated_at.desc()
    ).all()
    
    return render_template('course_discussions.html',
                         course=course,
                         discussions=discussions,
                         user=user)

@app.route('/course/<int:course_id>/discussion/create', methods=['GET', 'POST'])
@login_required
def create_discussion(course_id):
    """Create new discussion/question"""
    course = Course.query.get_or_404(course_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=course_id).first()
    if not enrollment and course.instructor_id != user_id and user.account != 'admin':
        flash('You must enroll in this course first', 'warning')
        return redirect(url_for('view_course', course_id=course_id))
    
    if request.method == 'POST':
        try:
            discussion = Discussion(
                course_id=course_id,
                created_by_id=user_id,
                title=request.form.get('title'),
                content=request.form.get('content')
            )
            db.session.add(discussion)
            db.session.commit()
            flash('Discussion created successfully!', 'success')
            return redirect(url_for('view_discussion', discussion_id=discussion.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating discussion: {str(e)}', 'danger')
    
    return render_template('create_discussion.html', course=course)

@app.route('/discussion/<int:discussion_id>')
@login_required
def view_discussion(discussion_id):
    """View discussion thread"""
    discussion = Discussion.query.get_or_404(discussion_id)
    
    # Check enrollment
    user_id = session['user_id']
    user = User.query.get(user_id)
    enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=discussion.course_id).first()
    
    if not enrollment and discussion.course.instructor_id != user_id and user.account != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    replies = DiscussionReply.query.filter_by(discussion_id=discussion_id).order_by(
        DiscussionReply.is_marked_as_answer.desc(),
        DiscussionReply.upvotes.desc(),
        DiscussionReply.created_at
    ).all()
    
    return render_template('discussion_detail.html',
                         discussion=discussion,
                         replies=replies,
                         user=user)

@app.route('/discussion/<int:discussion_id>/reply', methods=['POST'])
@login_required
def reply_discussion(discussion_id):
    """Reply to discussion"""
    discussion = Discussion.query.get_or_404(discussion_id)
    user_id = session['user_id']
    
    try:
        reply = DiscussionReply(
            discussion_id=discussion_id,
            created_by_id=user_id,
            content=request.form.get('content')
        )
        db.session.add(reply)
        db.session.commit()
        flash('Reply added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding reply: {str(e)}', 'danger')
    
    return redirect(url_for('view_discussion', discussion_id=discussion_id))

# ==================== COURSE REVIEW ROUTES ====================
@app.route('/course/<int:course_id>/reviews')
def view_course_reviews(course_id):
    """View course reviews and ratings"""
    course = Course.query.get_or_404(course_id)
    
    reviews = CourseReview.query.filter_by(course_id=course_id).order_by(
        CourseReview.helpful_count.desc(),
        CourseReview.created_at.desc()
    ).all()
    
    # Calculate average rating
    ratings = [r.rating for r in reviews]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    return render_template('course_reviews.html',
                         course=course,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         total_reviews=len(reviews))

@app.route('/course/<int:course_id>/review/add', methods=['GET', 'POST'])
@login_required
def add_course_review(course_id):
    """Add review to course"""
    course = Course.query.get_or_404(course_id)
    user_id = session['user_id']
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=course_id).first()
    if not enrollment:
        flash('You must be enrolled in this course to leave a review', 'warning')
        return redirect(url_for('view_course', course_id=course_id))
    
    # Check if already reviewed
    existing_review = CourseReview.query.filter_by(course_id=course_id, student_id=user_id).first()
    if existing_review and request.method == 'GET':
        flash('You have already reviewed this course', 'warning')
        return redirect(url_for('view_course_reviews', course_id=course_id))
    
    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating', 5))
            if rating < 1 or rating > 5:
                rating = 5
            
            if existing_review:
                existing_review.rating = rating
                existing_review.title = request.form.get('title')
                existing_review.review_text = request.form.get('review_text')
                existing_review.updated_at = datetime.now()
                message = 'Review updated successfully!'
            else:
                review = CourseReview(
                    course_id=course_id,
                    student_id=user_id,
                    rating=rating,
                    title=request.form.get('title'),
                    review_text=request.form.get('review_text')
                )
                db.session.add(review)
                message = 'Review added successfully!'
            
            db.session.commit()
            flash(message, 'success')
            return redirect(url_for('view_course_reviews', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving review: {str(e)}', 'danger')
    
    return render_template('add_course_review.html', course=course, existing_review=existing_review)

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ==================== INITIALIZATION ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Check if database is empty, if so load sample data
        user_count = User.query.count()
        if user_count == 0:
            print("Database is empty. Loading sample data...")
            try:
                from init_db import init_database
                init_database()
                print("Sample data loaded successfully!")
            except Exception as e:
                print(f"Error loading sample data: {e}")
                print("Database initialized but without sample data.")
        else:
            print("Database initialized successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)
