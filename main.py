import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from models import (db, User, Course, Enrollment, Enrolled, Lesson, Lesson_Progress,
                    Quiz, Quiz_Question, Quiz_Option, Quiz_Attempt, Quiz_Answer,
                    Assignment, Assignment_Submission, Announcement, Chapter,
                    Certificate, Discussion, DiscussionReply, CourseReview)
import random
import string
from flask_mail import Mail, Message
import stripe
from datetime import datetime, timedelta
from sqlalchemy import func as sa_func

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learn.db'
app.secret_key = 'Secret Key'
db.init_app(app)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEBUG'] = True
mail = Mail(app)
stripe.api_key = os.getenv('STRIPE_API_KEY', '')

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)


# ==================== HELPERS ====================

def get_current_user():
    """Get logged-in user or None."""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_courses():
    return Course.query.all()

def compute_streak(user_id):
    """Compute learning streak days from lesson progress and quiz attempts."""
    today = datetime.utcnow().date()
    active_dates = set()

    # Lesson progress dates
    progress_records = Lesson_Progress.query.filter_by(student_id=user_id).all()
    for p in progress_records:
        if p.last_accessed_at:
            active_dates.add(p.last_accessed_at.date())
        if p.completed_at:
            active_dates.add(p.completed_at.date())

    # Quiz attempt dates
    attempts = Quiz_Attempt.query.filter_by(student_id=user_id).all()
    for a in attempts:
        if a.started_at:
            active_dates.add(a.started_at.date())

    if not active_dates:
        return 0

    # Count consecutive days ending today or yesterday
    streak = 0
    check_date = today
    if check_date not in active_dates:
        check_date = today - timedelta(days=1)
        if check_date not in active_dates:
            return 0

    while check_date in active_dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak

def send_course_added_notification(student_email, teacher, course):
    subject = f'New Course Added by {teacher.first_name} {teacher.last_name}'
    message = f"Dear student,\n\nA new course titled '{course.title}' has been added by {teacher.first_name} {teacher.last_name}." \
              f" You are currently enrolled in one of the courses by this teacher.\n\nYou can view the new course details on the platform."
    try:
        msg = Message(subject=subject, sender=app.config['MAIL_USERNAME'], recipients=[student_email])
        msg.body = message
        mail.send(msg)
    except Exception as e:
        print(f"Email error (course notification): {str(e)}")


# ==================== AUTH & HOME ROUTES ====================

@app.route("/")
def home():
    courses = get_courses()
    user = get_current_user()
    logged_in = user is not None
    
    total_courses = Course.query.count()
    total_students = User.query.filter_by(account='student').count()
    total_teachers = User.query.filter_by(account='teacher').count()
    
    # Calculate learning hours
    total_learning_hours = 0
    for c in courses:
        if c.duration_hours:
            total_learning_hours += c.duration_hours
    
    # Featured courses
    featured_courses = Course.query.filter_by(is_published=True).limit(6).all()
    course_data = []
    for course in featured_courses:
        instructor_name = 'Instructor'
        if course.instructor:
            instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}"
        course_data.append({
            'id': course.id,
            'title': course.title,
            'summary': course.summary,
            'lessons_count': len(course.lessons),
            'enrollment_count': len(course.enrollments),
            'instructor_name': instructor_name,
            'image': None
        })
    
    return render_template('index.html', courses=courses, logged_in=logged_in, user=user,
                         featured_courses=course_data,
                         total_courses=total_courses, total_students=total_students,
                         total_teachers=total_teachers, total_learning_hours=total_learning_hours)

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if user.account == "teacher":
        return redirect(url_for('teacher_dashboard'))
    elif user.account == "admin":
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('student_dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        account_type = 'teacher' if 'is_teacher' in request.form else 'student'

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            account=account_type
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp' in session and 'user_data' in session:
        if request.method == 'POST':
            user_entered_otp = request.form['otp']
            stored_otp = session['otp']
            if user_entered_otp == stored_otp:
                new_user = User(
                    first_name=session['user_data']['first_name'],
                    last_name=session['user_data']['last_name'],
                    email=session['user_data']['email'],
                    password=session['user_data']['password'],
                    account=session['user_data']['account']
                )
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect OTP. Please try again.', 'error')
        return render_template('verify_otp.html')
    return render_template('index.html')

@app.route('/success')
@login_required
def success():
    user = get_current_user()
    message = flash('success')
    return render_template('success.html', message=message, logged_in=True, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['user_id'] = user.id

            if user.account == "teacher":
                return redirect(url_for('teacher_dashboard'))
            elif user.account == "admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


# ==================== PROFILE ROUTES ====================
@app.route('/profile')
@login_required
def profile():
    """View/edit user profile"""
    user = get_current_user()
    
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
                         user=user, logged_in=True,
                         course_count=course_count,
                         completed_count=completed_count,
                         cert_count=cert_count)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
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
    user = get_current_user()
    if 'profile_picture' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        filename = secure_filename(file.filename)
        unique_filename = f"profile_{user.id}_{int(datetime.utcnow().timestamp())}.{ext}"
        profiles_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
        Path(profiles_dir).mkdir(parents=True, exist_ok=True)
        file.save(os.path.join(profiles_dir, unique_filename))
        user.profile_picture = f"/uploads/profiles/{unique_filename}"
        db.session.commit()
        flash('Profile picture updated!', 'success')
    else:
        flash('Invalid file type. Please upload an image (png, jpg, jpeg, gif).', 'error')
    
    return redirect(url_for('profile'))

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


# ==================== STUDENT DASHBOARD ====================

@app.route('/student_dashboard', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    user = get_current_user()
    user_id = user.id

    # Get enrollments with course data
    enrollments = Enrollment.query.filter_by(student_id=user_id).all()
    enrolled_courses = []
    for enr in enrollments:
        course = Course.query.get(enr.course_id)
        if course:
            course.progress = enr.progress_percentage or 0
            course.instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}" if course.instructor else "Unknown"
            enrolled_courses.append(course)

    # Stats
    enrolled_count = len(enrolled_courses)
    completed_count = Enrollment.query.filter_by(student_id=user_id, is_completed=True).count()
    in_progress_count = enrolled_count - completed_count
    streak = compute_streak(user_id)

    # Quiz stats (Peerup style)
    quizzes_taken = Quiz_Attempt.query.filter_by(student_id=user_id).count()
    avg_score_val = db.session.query(sa_func.avg(Quiz_Attempt.percentage))\
        .filter(Quiz_Attempt.student_id == user_id, Quiz_Attempt.percentage.isnot(None)).scalar()
    avg_score = round(avg_score_val or 0, 1)

    # Learning progress stats
    total_lessons_available = 0
    total_lessons_completed = 0
    for enr in enrollments:
        course_lesson_count = Lesson.query.filter_by(course_id=enr.course_id, is_published=True).count()
        total_lessons_available += course_lesson_count
        completed_lessons = db.session.query(Lesson_Progress).join(Lesson)\
            .filter(Lesson.course_id == enr.course_id, Lesson_Progress.student_id == user_id,
                    Lesson_Progress.is_completed == True).count()
        total_lessons_completed += completed_lessons

    lessons_progress_pct = round((total_lessons_completed / total_lessons_available * 100) if total_lessons_available > 0 else 0, 1)
    overall_progress_pct = round(sum(c.progress for c in enrolled_courses) / len(enrolled_courses) if enrolled_courses else 0, 1)

    # Assignments stats
    total_assignments = 0
    submitted_assignments = 0
    for enr in enrollments:
        course_assignments = Assignment.query.filter_by(course_id=enr.course_id, is_published=True).count()
        total_assignments += course_assignments
        submitted = Assignment_Submission.query.join(Assignment)\
            .filter(Assignment.course_id == enr.course_id, Assignment_Submission.student_id == user_id,
                    Assignment_Submission.is_submitted == True).count()
        submitted_assignments += submitted
    assignments_pct = round((submitted_assignments / total_assignments * 100) if total_assignments > 0 else 0, 1)

    # Recent activity — last 10 lesson progress + quiz attempts
    recent_activity = []
    recent_lessons = Lesson_Progress.query.filter_by(student_id=user_id)\
        .order_by(Lesson_Progress.last_accessed_at.desc()).limit(5).all()
    for lp in recent_lessons:
        lesson = Lesson.query.get(lp.lesson_id)
        if lesson:
            action = "Completed" if lp.is_completed else "Studied"
            ts = lp.last_accessed_at or lp.started_at or datetime.utcnow()
            recent_activity.append({
                'title': f'{action} lesson: {lesson.title}',
                'date': ts.strftime('%b %d, %Y'),
                'timestamp': ts,
                'icon': '✅' if lp.is_completed else '📖',
                'type': 'lesson'
            })

    recent_quizzes = Quiz_Attempt.query.filter_by(student_id=user_id)\
        .order_by(Quiz_Attempt.started_at.desc()).limit(5).all()
    for qa in recent_quizzes:
        quiz = Quiz.query.get(qa.quiz_id)
        if quiz:
            status = "Passed" if qa.is_passed else "Attempted"
            score_str = f" ({qa.percentage:.0f}%)" if qa.percentage is not None else ""
            ts = qa.started_at or datetime.utcnow()
            recent_activity.append({
                'title': f'{status} quiz: {quiz.title}{score_str}',
                'date': ts.strftime('%b %d, %Y'),
                'timestamp': ts,
                'icon': '🏆' if qa.is_passed else '📝',
                'type': 'quiz'
            })

    # Add enrollment activities
    for enr in enrollments:
        course = Course.query.get(enr.course_id)
        if course and enr.enrolled_at:
            recent_activity.append({
                'title': f'Enrolled in: {course.title}',
                'date': enr.enrolled_at.strftime('%b %d, %Y'),
                'timestamp': enr.enrolled_at,
                'icon': '📚',
                'type': 'enrollment'
            })

    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:10]

    # Upcoming deadlines (assignments with due dates)
    upcoming_deadlines = []
    now = datetime.utcnow()
    for enr in enrollments:
        assignments = Assignment.query.filter(
            Assignment.course_id == enr.course_id,
            Assignment.is_published == True,
            Assignment.due_date > now
        ).order_by(Assignment.due_date).all()
        for a in assignments:
            course = Course.query.get(a.course_id)
            existing_sub = Assignment_Submission.query.filter_by(
                assignment_id=a.id, student_id=user_id, is_submitted=True
            ).first()
            if not existing_sub:
                upcoming_deadlines.append({
                    'title': a.title,
                    'course': course.title if course else 'Unknown',
                    'due_date': a.due_date.strftime('%b %d, %Y'),
                    'days_left': (a.due_date - now).days
                })
    upcoming_deadlines.sort(key=lambda x: x['days_left'])
    upcoming_deadlines = upcoming_deadlines[:5]

    # Recommended courses — courses not enrolled in
    enrolled_ids = [c.id for c in enrolled_courses]
    recommended_courses = Course.query.filter(
        Course.is_published == True,
        ~Course.id.in_(enrolled_ids) if enrolled_ids else True
    ).limit(5).all()
    for rc in recommended_courses:
        rc.instructor_name = f"{rc.instructor.first_name} {rc.instructor.last_name}" if rc.instructor else "Unknown"
        rc.enrollment_count = len(rc.enrollments)
        rc.lessons_count = len(rc.lessons)

    # Certificates earned
    certificates_earned = Certificate.query.filter_by(student_id=user_id).count()

    return render_template('student_dashboard.html',
        user=user,
        logged_in=True,
        enrolled_courses=enrolled_courses,
        enrolled_count=enrolled_count,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        streak=streak,
        quizzes_taken=quizzes_taken,
        avg_score=avg_score,
        total_lessons_completed=total_lessons_completed,
        total_lessons_available=total_lessons_available,
        lessons_progress_pct=lessons_progress_pct,
        overall_progress_pct=overall_progress_pct,
        assignments_pct=assignments_pct,
        submitted_assignments=submitted_assignments,
        total_assignments=total_assignments,
        recent_activity=recent_activity,
        upcoming_deadlines=upcoming_deadlines,
        recommended_courses=recommended_courses,
        certificates_earned=certificates_earned
    )


# ==================== TEACHER DASHBOARD ====================

@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    user = get_current_user()
    user_id = user.id

    courses = Course.query.filter_by(instructor_id=user_id).all()
    courses_count = len(courses)

    # Total unique students across all courses
    course_ids = [c.id for c in courses]
    if course_ids:
        total_enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).count()
        total_students = db.session.query(sa_func.count(sa_func.distinct(Enrollment.student_id)))\
            .filter(Enrollment.course_id.in_(course_ids)).scalar() or 0

        # Average completion percentage
        avg_completion_val = db.session.query(sa_func.avg(Enrollment.progress_percentage))\
            .filter(Enrollment.course_id.in_(course_ids)).scalar()
        avg_completion = round(avg_completion_val or 0, 1)

        # Average rating from course reviews
        avg_rating_val = db.session.query(sa_func.avg(CourseReview.rating))\
            .filter(CourseReview.course_id.in_(course_ids)).scalar()
        avg_rating = round(avg_rating_val or 0, 1)
        total_reviews = CourseReview.query.filter(CourseReview.course_id.in_(course_ids)).count()

        # Total quizzes and questions created
        total_quizzes = Quiz.query.filter(Quiz.course_id.in_(course_ids)).count()
        total_lessons = Lesson.query.filter(Lesson.course_id.in_(course_ids)).count()

        # Pending assignment submissions (ungraded)
        pending_submissions = db.session.query(Assignment_Submission)\
            .join(Assignment).filter(
                Assignment.course_id.in_(course_ids),
                Assignment_Submission.is_submitted == True,
                Assignment_Submission.is_graded == False
            ).order_by(Assignment_Submission.submitted_at.desc()).all()

        # Enrich pending submissions
        pending_subs_data = []
        for sub in pending_submissions[:10]:
            student = User.query.get(sub.student_id)
            assignment = Assignment.query.get(sub.assignment_id)
            course = Course.query.get(assignment.course_id) if assignment else None
            pending_subs_data.append({
                'id': sub.id,
                'student_name': f"{student.first_name} {student.last_name}" if student else "Unknown",
                'assignment_title': assignment.title if assignment else "Unknown",
                'course_title': course.title if course else "Unknown",
                'submitted_at': sub.submitted_at.strftime('%b %d, %Y') if sub.submitted_at else 'N/A',
                'assignment_id': sub.assignment_id
            })

        # Recent activity
        recent_activity = []

        # Recent enrollments
        recent_enrollments = db.session.query(Enrollment, User, Course)\
            .join(User, Enrollment.student_id == User.id)\
            .join(Course, Enrollment.course_id == Course.id)\
            .filter(Course.instructor_id == user_id)\
            .order_by(Enrollment.enrolled_at.desc()).limit(5).all()
        for enr, student, course in recent_enrollments:
            recent_activity.append({
                'icon': '👤',
                'title': f'{student.first_name} {student.last_name} enrolled in {course.title}',
                'date': enr.enrolled_at.strftime('%b %d, %Y') if enr.enrolled_at else 'N/A',
                'timestamp': enr.enrolled_at or datetime.utcnow(),
                'type': 'enrollment'
            })

        # Recent quiz attempts on teacher's courses
        recent_quiz_attempts = db.session.query(Quiz_Attempt, User, Quiz)\
            .join(User, Quiz_Attempt.student_id == User.id)\
            .join(Quiz, Quiz_Attempt.quiz_id == Quiz.id)\
            .filter(Quiz.course_id.in_(course_ids))\
            .order_by(Quiz_Attempt.started_at.desc()).limit(5).all()
        for attempt, student, quiz in recent_quiz_attempts:
            score_str = f" - {attempt.percentage:.0f}%" if attempt.percentage is not None else ""
            recent_activity.append({
                'icon': '📝',
                'title': f'{student.first_name} took quiz: {quiz.title}{score_str}',
                'date': attempt.started_at.strftime('%b %d, %Y') if attempt.started_at else 'N/A',
                'timestamp': attempt.started_at or datetime.utcnow(),
                'type': 'quiz'
            })

        # Recent reviews
        recent_reviews = db.session.query(CourseReview, User, Course)\
            .join(User, CourseReview.student_id == User.id)\
            .join(Course, CourseReview.course_id == Course.id)\
            .filter(Course.instructor_id == user_id)\
            .order_by(CourseReview.created_at.desc()).limit(3).all()
        for review, student, course in recent_reviews:
            stars = '⭐' * review.rating
            recent_activity.append({
                'icon': '⭐',
                'title': f'{student.first_name} rated {course.title}: {stars}',
                'date': review.created_at.strftime('%b %d, %Y') if review.created_at else 'N/A',
                'timestamp': review.created_at or datetime.utcnow(),
                'type': 'review'
            })

        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activity = recent_activity[:10]

        # Enrich courses with stats
        for course in courses:
            course.student_count = len(course.enrollments)
            course.lesson_count = len(course.lessons)
            course.quiz_count = len(course.quizzes)
            course_reviews = CourseReview.query.filter_by(course_id=course.id).all()
            course.avg_rating = round(sum(r.rating for r in course_reviews) / len(course_reviews), 1) if course_reviews else 0
            course.review_count = len(course_reviews)

    else:
        total_enrollments = 0
        total_students = 0
        avg_completion = 0
        avg_rating = 0
        total_reviews = 0
        total_quizzes = 0
        total_lessons = 0
        pending_subs_data = []
        recent_activity = []

    return render_template('teacher_dashboard.html',
        user=user,
        logged_in=True,
        courses=courses,
        courses_count=courses_count,
        total_students=total_students,
        total_enrollments=total_enrollments,
        avg_completion=avg_completion,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        total_quizzes=total_quizzes,
        total_lessons=total_lessons,
        pending_submissions=pending_subs_data,
        pending_count=len(pending_subs_data),
        recent_activity=recent_activity
    )


# ==================== ADMIN DASHBOARD ====================

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    user = get_current_user()
    if user.account != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    total_users = User.query.count()
    total_students = User.query.filter_by(account='student').count()
    total_teachers = User.query.filter_by(account='teacher').count()
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()

    # Growth calculations (this week vs last week) - Peerup style
    now = datetime.utcnow()
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

    # Recent teachers (for pending-style display)
    recent_teachers = User.query.filter_by(account='teacher').order_by(User.date_created.desc()).limit(5).all()
    for t in recent_teachers:
        t.courses_count = Course.query.filter_by(instructor_id=t.id).count()
        t_course_ids = [c.id for c in Course.query.filter_by(instructor_id=t.id).all()]
        t.student_count = db.session.query(sa_func.count(sa_func.distinct(Enrollment.student_id)))\
            .filter(Enrollment.course_id.in_(t_course_ids)).scalar() if t_course_ids else 0

    # Recent students (for registered students preview)
    recent_students = User.query.filter_by(account='student').order_by(User.date_created.desc()).limit(5).all()
    for s in recent_students:
        s.enrollment_count = Enrollment.query.filter_by(student_id=s.id).count()
        s.completed_courses = Enrollment.query.filter_by(student_id=s.id, is_completed=True).count()

    # Platform stats
    total_quiz_attempts = Quiz_Attempt.query.count()
    total_lessons_completed = Lesson_Progress.query.filter_by(is_completed=True).count()
    avg_course_rating_val = db.session.query(sa_func.avg(CourseReview.rating)).scalar()
    avg_course_rating = round(avg_course_rating_val or 0, 1)

    all_users = User.query.order_by(User.date_created.desc()).all()
    all_courses = Course.query.all()

    # Enrich courses for admin view
    for course in all_courses:
        course.student_count = len(course.enrollments)
        course.instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}" if course.instructor else "Unknown"

    return render_template('admin_dashboard.html',
        user=user,
        logged_in=True,
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
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
        avg_course_rating=avg_course_rating,
        all_users=all_users,
        all_courses=all_courses
    )


# ==================== COURSE BROWSING ====================

@app.route('/courses')
def browse_courses():
    user = get_current_user()
    logged_in = user is not None
    courses = Course.query.filter_by(is_published=True).all()

    # Add enrollment info if logged in
    if user:
        enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=user.id).all()]
        for course in courses:
            course.is_enrolled = course.id in enrolled_ids
    return render_template('courses.html', courses=courses, user=user, logged_in=logged_in)

@app.route('/course/<int:course_id>')
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    logged_in = True
    session["course_id"] = course_id
    user_enrolled = Enrollment.query.filter_by(student_id=user.id, course_id=course_id).first() is not None

    # Get lessons, quizzes, announcements for this course
    lessons = Lesson.query.filter_by(course_id=course_id, is_published=True).order_by(Lesson.order).all()
    quizzes = Quiz.query.filter_by(course_id=course_id, is_published=True).order_by(Quiz.order).all()
    announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
    assignments = Assignment.query.filter_by(course_id=course_id, is_published=True).order_by(Assignment.order).all()

    # Lesson progress for this student
    lesson_progress = {}
    if user_enrolled:
        for lp in Lesson_Progress.query.filter_by(student_id=user.id).all():
            lesson_progress[lp.lesson_id] = lp

    return render_template('course_detail.html',
        course=course, user=user, logged_in=logged_in,
        user_enrolled=user_enrolled,
        lessons=lessons, quizzes=quizzes,
        announcements=announcements, assignments=assignments,
        lesson_progress=lesson_progress
    )


# ==================== ENROLLMENT ====================

@app.route('/enroll/<int:course_id>')
@login_required
def enroll_course(course_id):
    user = get_current_user()
    existing = Enrollment.query.filter_by(student_id=user.id, course_id=course_id).first()
    if not existing:
        new_enroll = Enrollment(student_id=user.id, course_id=course_id)
        db.session.add(new_enroll)
        db.session.commit()
        flash('Successfully enrolled!', 'success')
    else:
        flash('Already enrolled in this course.', 'info')
    return redirect(url_for('view_course', course_id=course_id))

@app.route('/enroll', methods=['GET', 'POST'])
@login_required
def enroll():
    """Legacy enroll route for backward compatibility."""
    course_id = session.get('course_id')
    if course_id is None:
        return redirect(url_for('student_dashboard'))
    user = get_current_user()
    existing = Enrollment.query.filter_by(student_id=user.id, course_id=course_id).first()
    if not existing:
        new_enroll = Enrollment(student_id=user.id, course_id=course_id)
        db.session.add(new_enroll)
        db.session.commit()
    session.pop('course_id', None)
    return redirect(url_for('student_dashboard'))


# ==================== LESSON ROUTES ====================

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    user = get_current_user()
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)

    # Track progress
    progress = Lesson_Progress.query.filter_by(student_id=user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = Lesson_Progress(student_id=user.id, lesson_id=lesson_id)
        db.session.add(progress)
        db.session.commit()
    else:
        progress.last_accessed_at = datetime.utcnow()
        db.session.commit()

    # Get all lessons in the course for navigation
    all_lessons = Lesson.query.filter_by(course_id=course.id, is_published=True).order_by(Lesson.order).all()

    return render_template('lesson.html',
        lesson=lesson, course=course, user=user, logged_in=True,
        all_lessons=all_lessons, progress=progress
    )

@app.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def mark_lesson_complete(lesson_id):
    user = get_current_user()
    progress = Lesson_Progress.query.filter_by(student_id=user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = Lesson_Progress(student_id=user.id, lesson_id=lesson_id)
        db.session.add(progress)

    progress.is_completed = True
    progress.completed_at = datetime.utcnow()
    db.session.commit()

    # Update enrollment progress percentage
    lesson = Lesson.query.get(lesson_id)
    if lesson:
        total_lessons = Lesson.query.filter_by(course_id=lesson.course_id, is_published=True).count()
        completed_lessons = db.session.query(Lesson_Progress).join(Lesson)\
            .filter(Lesson.course_id == lesson.course_id,
                    Lesson_Progress.student_id == user.id,
                    Lesson_Progress.is_completed == True).count()

        enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=lesson.course_id).first()
        if enrollment and total_lessons > 0:
            enrollment.progress_percentage = round((completed_lessons / total_lessons) * 100, 1)
            if enrollment.progress_percentage >= 100:
                enrollment.is_completed = True
                enrollment.completed_at = datetime.utcnow()
            db.session.commit()

    flash('Lesson marked as complete!', 'success')
    return redirect(url_for('view_lesson', lesson_id=lesson_id))


# ==================== QUIZ ROUTES ====================

@app.route('/quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    user = get_current_user()
    quiz = Quiz.query.get_or_404(quiz_id)

    # Check attempts
    attempt_count = Quiz_Attempt.query.filter_by(student_id=user.id, quiz_id=quiz_id).count()
    if quiz.attempts_allowed != -1 and attempt_count >= quiz.attempts_allowed:
        flash('You have used all your attempts for this quiz.', 'error')
        return redirect(url_for('view_course', course_id=quiz.course_id))

    if request.method == 'POST':
        # Create a new attempt
        attempt = Quiz_Attempt(student_id=user.id, quiz_id=quiz_id)
        db.session.add(attempt)
        db.session.commit()
        session['quiz_attempt_id'] = attempt.id
        session['quiz_question_index'] = 0

        # Redirect to first question
        questions = Quiz_Question.query.filter_by(quiz_id=quiz_id).order_by(Quiz_Question.order).all()
        if questions:
            return redirect(url_for('quiz_question', quiz_id=quiz_id, question_index=0))
        else:
            flash('This quiz has no questions.', 'error')
            return redirect(url_for('view_course', course_id=quiz.course_id))

    return render_template('quiz_start.html', quiz=quiz, user=user, logged_in=True,
                         attempt_count=attempt_count)

@app.route('/quiz/<int:quiz_id>/question/<int:question_index>', methods=['GET', 'POST'])
@login_required
def quiz_question(quiz_id, question_index):
    user = get_current_user()
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Quiz_Question.query.filter_by(quiz_id=quiz_id).order_by(Quiz_Question.order).all()

    if question_index < 0 or question_index >= len(questions):
        return redirect(url_for('view_course', course_id=quiz.course_id))

    question = questions[question_index]
    attempt_id = session.get('quiz_attempt_id')

    if not attempt_id:
        return redirect(url_for('start_quiz', quiz_id=quiz_id))

    return render_template('quiz_question.html',
        quiz=quiz, question=question, user=user, logged_in=True,
        question_index=question_index, total_questions=len(questions),
        is_last=(question_index == len(questions) - 1)
    )

@app.route('/quiz/<int:quiz_id>/answer/<int:question_index>', methods=['POST'])
@login_required
def submit_quiz_answer(quiz_id, question_index):
    user = get_current_user()
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Quiz_Question.query.filter_by(quiz_id=quiz_id).order_by(Quiz_Question.order).all()
    question = questions[question_index]
    attempt_id = session.get('quiz_attempt_id')

    if not attempt_id:
        return redirect(url_for('start_quiz', quiz_id=quiz_id))

    # Save the answer
    selected_option_id = request.form.get('selected_option')
    text_answer = request.form.get('text_answer', '')

    is_correct = False
    marks = 0
    if question.question_type in ('multiple_choice', 'true_false') and selected_option_id:
        option = Quiz_Option.query.get(int(selected_option_id))
        if option and option.is_correct:
            is_correct = True
            marks = question.marks
    elif question.question_type == 'short_answer':
        # For short answer, save as-is (teacher grades manually)
        pass

    answer = Quiz_Answer(
        attempt_id=attempt_id,
        question_id=question.id,
        selected_option_id=int(selected_option_id) if selected_option_id else None,
        text_answer=text_answer,
        is_correct=is_correct,
        marks_obtained=marks
    )
    db.session.add(answer)
    db.session.commit()

    # Move to next question or finish
    if question_index + 1 < len(questions):
        return redirect(url_for('quiz_question', quiz_id=quiz_id, question_index=question_index + 1))
    else:
        # Finish quiz — calculate results
        attempt = Quiz_Attempt.query.get(attempt_id)
        answers = Quiz_Answer.query.filter_by(attempt_id=attempt_id).all()
        total_marks = sum(q.marks for q in questions)
        obtained_marks = sum(a.marks_obtained or 0 for a in answers)

        attempt.score = obtained_marks
        attempt.percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        attempt.is_passed = attempt.percentage >= quiz.passing_percentage
        attempt.submitted_at = datetime.utcnow()
        if attempt.started_at:
            attempt.time_taken_seconds = int((attempt.submitted_at - attempt.started_at).total_seconds())

        db.session.commit()
        session.pop('quiz_attempt_id', None)
        session.pop('quiz_question_index', None)

        return redirect(url_for('quiz_results', quiz_id=quiz_id, attempt_id=attempt_id))

@app.route('/quiz/<int:quiz_id>/results/<int:attempt_id>')
@login_required
def quiz_results(quiz_id, attempt_id):
    user = get_current_user()
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt = Quiz_Attempt.query.get_or_404(attempt_id)

    if attempt.student_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    # Get answers with questions
    answers = Quiz_Answer.query.filter_by(attempt_id=attempt_id).all()
    questions = Quiz_Question.query.filter_by(quiz_id=quiz_id).order_by(Quiz_Question.order).all()

    return render_template('quiz_results.html',
        quiz=quiz, attempt=attempt, user=user, logged_in=True,
        answers=answers, questions=questions,
        show_answers=quiz.show_correct_answers
    )


# ==================== COURSE MANAGEMENT (TEACHER) ====================

@app.route('/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    user = get_current_user()
    if user.account != 'teacher':
        flash('Only teachers can create courses.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        summary = request.form.get('summary', '').strip()
        price = float(request.form.get('price', 0) or 0)
        requirements = request.form.get('requirements', '')
        difficulty_level = request.form.get('difficulty_level', 'beginner')

        if not title or not category or not description:
            flash('Title, category, and description are required.', 'error')
            return render_template('create_course.html', user=user, logged_in=True)

        new_course = Course(
            title=title,
            category=category,
            description=description,
            summary=summary,
            price=price,
            requirements=requirements,
            difficulty_level=difficulty_level,
            instructor_id=user.id,
            is_published=True
        )
        db.session.add(new_course)
        db.session.commit()

        # Notify enrolled students of this teacher
        teacher_courses = Course.query.filter_by(instructor_id=user.id).all()
        notified = set()
        for c in teacher_courses:
            for enr in Enrollment.query.filter_by(course_id=c.id).all():
                student = User.query.get(enr.student_id)
                if student and student.email not in notified:
                    send_course_added_notification(student.email, user, new_course)
                    notified.add(student.email)

        flash('Course created successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('create_course.html', user=user, logged_in=True)

@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != user.id and user.account != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        course.title = request.form.get('newTitle') or request.form.get('title') or course.title
        course.category = request.form.get('newCategory') or request.form.get('category') or course.category
        course.summary = request.form.get('newSummary') or request.form.get('summary') or course.summary
        course.requirements = request.form.get('newRequirements') or request.form.get('requirements') or course.requirements
        price_val = request.form.get('newPrice') or request.form.get('price')
        if price_val:
            course.price = float(price_val)
        course.description = request.form.get('description') or course.description

        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('edit_course.html', course=course, user=user, logged_in=True)

@app.route('/delete_course/<int:course_id>', methods=['POST', 'GET'])
@login_required
def delete_course(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != user.id and user.account != 'admin':
        flash('Failed to delete course', 'error')
        return redirect(url_for('teacher_dashboard'))

    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully', 'success')

    if user.account == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('teacher_dashboard'))

@app.route('/add_course', methods=['POST'])
@login_required
def add_course():
    """Legacy add_course route — redirects to create_course."""
    return redirect(url_for('create_course'), code=307)

@app.route('/manage_course/<int:course_id>')
@login_required
def manage_course(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
    chapters = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order).all()
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.order).all()

    return render_template('manage_course.html',
        course=course, user=user, logged_in=True,
        lessons=lessons, chapters=chapters, quizzes=quizzes
    )


# ==================== LESSON MANAGEMENT (TEACHER) ====================

@app.route('/course/<int:course_id>/lesson/create', methods=['GET', 'POST'])
@login_required
def create_lesson(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '')
        description = request.form.get('description', '')
        video_url = request.form.get('video_url', '')
        order = Lesson.query.filter_by(course_id=course_id).count() + 1

        lesson = Lesson(
            course_id=course_id,
            title=title,
            content=content,
            description=description,
            video_url=video_url,
            order=order
        )
        db.session.add(lesson)
        db.session.commit()
        flash('Lesson created!', 'success')
        return redirect(url_for('manage_course', course_id=course_id))

    return render_template('create_lesson.html', course=course, user=user, logged_in=True)

@app.route('/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lesson(lesson_id):
    user = get_current_user()
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)

    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        lesson.title = request.form.get('title', lesson.title)
        lesson.content = request.form.get('content', lesson.content)
        lesson.description = request.form.get('description', lesson.description)
        lesson.video_url = request.form.get('video_url', lesson.video_url)
        db.session.commit()
        flash('Lesson updated!', 'success')
        return redirect(url_for('manage_course', course_id=course.id))

    return render_template('edit_lesson.html', lesson=lesson, course=course, user=user, logged_in=True)

@app.route('/lesson/<int:lesson_id>/delete')
@login_required
def delete_lesson(lesson_id):
    user = get_current_user()
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)

    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash('Lesson deleted.', 'success')
    return redirect(url_for('manage_course', course_id=course_id))


# ==================== QUIZ MANAGEMENT (TEACHER) ====================

@app.route('/course/<int:course_id>/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '')
        passing_pct = float(request.form.get('passing_percentage', 70))
        duration = request.form.get('duration_minutes')
        duration = int(duration) if duration else None
        attempts = int(request.form.get('attempts_allowed', 1))

        quiz = Quiz(
            course_id=course_id,
            title=title,
            description=description,
            passing_percentage=passing_pct,
            duration_minutes=duration,
            attempts_allowed=attempts,
            order=Quiz.query.filter_by(course_id=course_id).count() + 1
        )
        db.session.add(quiz)
        db.session.commit()

        # Add questions
        q_index = 0
        while True:
            q_text = request.form.get(f'question_{q_index}_text')
            if not q_text:
                break
            q_type = request.form.get(f'question_{q_index}_type', 'multiple_choice')
            q_marks = float(request.form.get(f'question_{q_index}_marks', 1))

            question = Quiz_Question(
                quiz_id=quiz.id,
                question_text=q_text,
                question_type=q_type,
                marks=q_marks,
                order=q_index + 1
            )
            db.session.add(question)
            db.session.commit()

            # Add options for multiple choice
            if q_type in ('multiple_choice', 'true_false'):
                opt_index = 0
                while True:
                    opt_text = request.form.get(f'question_{q_index}_option_{opt_index}')
                    if not opt_text:
                        break
                    is_correct = request.form.get(f'question_{q_index}_correct') == str(opt_index)
                    option = Quiz_Option(
                        question_id=question.id,
                        option_text=opt_text,
                        order=opt_index,
                        is_correct=is_correct
                    )
                    db.session.add(option)
                    opt_index += 1

            q_index += 1

        quiz.total_questions = q_index
        db.session.commit()

        flash('Quiz created successfully!', 'success')
        return redirect(url_for('manage_course', course_id=course_id))

    return render_template('create_quiz.html', course=course, user=user, logged_in=True)


# ==================== ANNOUNCEMENTS (TEACHER BROADCAST) ====================

@app.route('/course/<int:course_id>/announcement', methods=['POST'])
@login_required
def create_announcement(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if title and content:
        announcement = Announcement(
            course_id=course_id,
            title=title,
            content=content,
            created_by_id=user.id
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement posted!', 'success')
    else:
        flash('Title and content are required.', 'error')

    return redirect(url_for('view_course', course_id=course_id))

@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast_message():
    """Teacher broadcasts a message to all enrolled students across all courses."""
    user = get_current_user()
    if user.account != 'teacher':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if title and content:
            # Create announcement for each course owned by teacher
            courses = Course.query.filter_by(instructor_id=user.id).all()
            for course in courses:
                announcement = Announcement(
                    course_id=course.id,
                    title=title,
                    content=content,
                    created_by_id=user.id
                )
                db.session.add(announcement)
            db.session.commit()
            flash('Broadcast sent to all your students!', 'success')
        else:
            flash('Title and content are required.', 'error')

    return redirect(url_for('teacher_dashboard'))


# ==================== ASSIGNMENT ROUTES ====================

@app.route('/assignment/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    user = get_current_user()
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.get(assignment.course_id)
    submission = Assignment_Submission.query.filter_by(
        assignment_id=assignment_id, student_id=user.id
    ).first()

    return render_template('assignment.html',
        assignment=assignment, course=course, user=user,
        logged_in=True, submission=submission
    )

@app.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    user = get_current_user()
    assignment = Assignment.query.get_or_404(assignment_id)

    submission_text = request.form.get('submission_text', '')

    existing = Assignment_Submission.query.filter_by(
        assignment_id=assignment_id, student_id=user.id
    ).first()

    if existing:
        existing.submission_text = submission_text
        existing.submitted_at = datetime.utcnow()
        existing.is_submitted = True
    else:
        submission = Assignment_Submission(
            assignment_id=assignment_id,
            student_id=user.id,
            submission_text=submission_text,
            is_submitted=True
        )
        db.session.add(submission)

    db.session.commit()
    flash('Assignment submitted!', 'success')
    return redirect(url_for('view_course', course_id=assignment.course_id))


# ==================== DISCUSSION ROUTES ====================

@app.route('/course/<int:course_id>/discussions')
@login_required
def course_discussions(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    discussions = Discussion.query.filter_by(course_id=course_id).order_by(Discussion.created_at.desc()).all()
    return render_template('course_discussions.html',
        course=course, discussions=discussions, user=user, logged_in=True
    )

@app.route('/course/<int:course_id>/discussion/create', methods=['GET', 'POST'])
@login_required
def create_discussion(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if title and content:
            discussion = Discussion(
                course_id=course_id,
                created_by_id=user.id,
                title=title,
                content=content
            )
            db.session.add(discussion)
            db.session.commit()
            flash('Discussion created!', 'success')
            return redirect(url_for('course_discussions', course_id=course_id))
        flash('Title and content are required.', 'error')

    return render_template('create_discussion.html', course=course, user=user, logged_in=True)

@app.route('/discussion/<int:discussion_id>')
@login_required
def discussion_detail(discussion_id):
    user = get_current_user()
    discussion = Discussion.query.get_or_404(discussion_id)
    replies = DiscussionReply.query.filter_by(discussion_id=discussion_id).order_by(DiscussionReply.created_at).all()
    return render_template('discussion_detail.html',
        discussion=discussion, replies=replies, user=user, logged_in=True
    )


# ==================== REVIEW ROUTES ====================

@app.route('/course/<int:course_id>/review', methods=['GET', 'POST'])
@login_required
def add_course_review(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        title = request.form.get('title', '').strip()
        review_text = request.form.get('review_text', '').strip()

        existing = CourseReview.query.filter_by(course_id=course_id, student_id=user.id).first()
        if existing:
            existing.rating = rating
            existing.title = title
            existing.review_text = review_text
        else:
            review = CourseReview(
                course_id=course_id,
                student_id=user.id,
                rating=rating,
                title=title,
                review_text=review_text
            )
            db.session.add(review)

        db.session.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('view_course', course_id=course_id))

    return render_template('add_course_review.html', course=course, user=user, logged_in=True)

@app.route('/course/<int:course_id>/reviews')
def course_reviews(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    reviews = CourseReview.query.filter_by(course_id=course_id).order_by(CourseReview.created_at.desc()).all()
    return render_template('course_reviews.html',
        course=course, reviews=reviews, user=user, logged_in=user is not None
    )


# ==================== CHAPTER ROUTES ====================

@app.route('/course/<int:course_id>/chapter/create', methods=['GET', 'POST'])
@login_required
def create_chapter(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '')
        order = Chapter.query.filter_by(course_id=course_id).count() + 1

        chapter = Chapter(course_id=course_id, title=title, description=description, order=order)
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter created!', 'success')
        return redirect(url_for('manage_course', course_id=course_id))

    return render_template('create_chapter.html', course=course, user=user, logged_in=True)

@app.route('/course/<int:course_id>/content')
@login_required
def view_course_content(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    chapters = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order).all()
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
    return render_template('course_chapters.html',
        course=course, chapters=chapters, lessons=lessons, user=user, logged_in=True
    )


# ==================== CERTIFICATE ROUTES ====================

@app.route('/certificates')
@login_required
def certificates():
    user = get_current_user()
    certs = Certificate.query.filter_by(student_id=user.id).all()
    return render_template('certificates.html', certificates=certs, user=user, logged_in=True)

@app.route('/certificate/<int:cert_id>')
@login_required
def certificate_detail(cert_id):
    user = get_current_user()
    cert = Certificate.query.get_or_404(cert_id)
    return render_template('certificate_detail.html', certificate=cert, user=user, logged_in=True)

@app.route('/course/<int:course_id>/issue_certificates', methods=['GET', 'POST'])
@login_required
def issue_certificates(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    completed_enrollments = Enrollment.query.filter_by(course_id=course_id, is_completed=True).all()

    if request.method == 'POST':
        for enr in completed_enrollments:
            existing = Certificate.query.filter_by(student_id=enr.student_id, course_id=course_id).first()
            if not existing:
                cert = Certificate(
                    student_id=enr.student_id,
                    course_id=course_id,
                    certificate_number=f"CERT-{course_id}-{enr.student_id}-{random.randint(1000,9999)}",
                    completion_date=enr.completed_at or datetime.utcnow()
                )
                db.session.add(cert)
        db.session.commit()
        flash('Certificates issued!', 'success')
        return redirect(url_for('manage_course', course_id=course_id))

    return render_template('issue_certificates.html',
        course=course, enrollments=completed_enrollments, user=user, logged_in=True
    )


# ==================== BATCH & LIVE CLASS ROUTES ====================

@app.route('/course/<int:course_id>/batch/create', methods=['GET', 'POST'])
@login_required
def create_batch(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))

    from models import Batch
    if request.method == 'POST':
        batch = Batch(
            course_id=course_id,
            title=request.form.get('title', ''),
            description=request.form.get('description', ''),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d'),
            max_students=int(request.form.get('max_students', 30)),
            instructor_id=user.id
        )
        db.session.add(batch)
        db.session.commit()
        flash('Batch created!', 'success')
        return redirect(url_for('manage_course', course_id=course_id))

    return render_template('create_batch.html', course=course, user=user, logged_in=True)

@app.route('/batch/<int:batch_id>')
@login_required
def batch_detail(batch_id):
    user = get_current_user()
    from models import Batch, LiveClass
    batch = Batch.query.get_or_404(batch_id)
    live_classes = LiveClass.query.filter_by(batch_id=batch_id).order_by(LiveClass.scheduled_at).all()
    return render_template('batch_detail.html',
        batch=batch, live_classes=live_classes, user=user, logged_in=True
    )

@app.route('/batch/<int:batch_id>/live_class', methods=['GET', 'POST'])
@login_required
def add_live_class(batch_id):
    user = get_current_user()
    from models import Batch, LiveClass
    batch = Batch.query.get_or_404(batch_id)

    if request.method == 'POST':
        live_class = LiveClass(
            batch_id=batch_id,
            title=request.form.get('title', ''),
            description=request.form.get('description', ''),
            scheduled_at=datetime.strptime(request.form.get('scheduled_at'), '%Y-%m-%dT%H:%M'),
            duration_minutes=int(request.form.get('duration_minutes', 60)),
            zoom_link=request.form.get('zoom_link', '')
        )
        db.session.add(live_class)
        db.session.commit()
        flash('Live class scheduled!', 'success')
        return redirect(url_for('batch_detail', batch_id=batch_id))

    return render_template('add_live_class.html', batch=batch, user=user, logged_in=True)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    user = get_current_user()
    return render_template('404.html', user=user, logged_in=user is not None), 404

@app.errorhandler(500)
def internal_error(e):
    user = get_current_user()
    return render_template('500.html', user=user, logged_in=user is not None), 500


# ==================== DATABASE INIT ====================

with app.app_context():
    db.create_all()

    # Create default admin if not exists
    admin = User.query.filter_by(account='admin').first()
    if not admin:
        admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@elearning.com',
            password='admin123',
            account='admin'
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
