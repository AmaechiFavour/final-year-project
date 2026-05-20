"""
FCLS - Faculty of Computing Learning System
Complete LMS built with Flask, running completely offline with no Docker.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from models_frappe_complete import (
    db, User, UserType, EnrollmentStatus, CourseStatus,
    Course, CourseChapter, CourseLesson,
    Enrollment, CourseProgress,
    Batch, BatchEnrollment, BatchFeedback,
    Quiz, QuizQuestion, Question, Option, QuizSubmission, QuizResult,
    Assignment, AssignmentSubmission,
    Certificate, CertificateEvaluation,
    LiveClass, LiveClassParticipant,
    CourseReview, Payment, Coupon, LmsSettings
)
from routes_frappe_complete import register_api_routes
from init_frappe_lms import init_frappe_lms_db
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import re
import uuid

# ==================== APP SETUP ====================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///frappe_lms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'frappe-lms-secret-key-2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
register_api_routes(app)


# ==================== AUTH HELPERS ====================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user = db.session.get(User, session['user_id'])
            if not user or user.user_type not in roles:
                return render_template('frappe_lms/403.html'), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_globals():
    user = get_current_user()
    return {
        'logged_in': user is not None,
        'current_user': user,
        'user_role': user.user_type if user else None,
        'UserType': UserType,
    }


# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session.permanent = True
            return redirect(url_for('dashboard'))
        return render_template('frappe_lms/login.html', error='Invalid email or password')
    return render_template('frappe_lms/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if password != confirm:
            return render_template('frappe_lms/register.html', error='Passwords do not match')
        if User.query.filter_by(email=email).first():
            return render_template('frappe_lms/register.html', error='Email already registered')

        user = User(
            name=email,
            email=email,
            full_name=full_name,
            password=password,
            user_type=UserType.STUDENT.value,
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session.permanent = True
        return redirect(url_for('dashboard'))
    return render_template('frappe_lms/register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==================== PUBLIC PAGES ====================

@app.route('/')
def index():
    user = get_current_user()
    featured = Course.query.filter_by(published=True, featured=True).limit(6).all()
    total_courses = Course.query.filter_by(published=True).count()
    total_students = User.query.filter_by(user_type=UserType.STUDENT.value).count()
    total_instructors = User.query.filter_by(user_type=UserType.INSTRUCTOR.value).count()

    enrolled_count = 0
    if user:
        enrolled_count = Enrollment.query.filter_by(member_id=user.id).count()

    return render_template('frappe_lms/index.html',
                           featured_courses=featured,
                           total_courses=total_courses,
                           total_students=total_students,
                           total_instructors=total_instructors,
                           enrolled_count=enrolled_count)


@app.route('/courses')
def courses():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    q = Course.query.filter_by(published=True)
    if search:
        q = q.filter(Course.title.ilike(f'%{search}%') | Course.description.ilike(f'%{search}%'))

    pagination = q.order_by(Course.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('frappe_lms/courses_list.html',
                           courses=pagination.items,
                           total=pagination.total,
                           pages=pagination.pages,
                           current_page=page,
                           search=search)


@app.route('/course/<slug>')
def course_detail(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    chapters = CourseChapter.query.filter_by(course_id=course.id).order_by(CourseChapter.order).all()
    reviews = CourseReview.query.filter_by(course_id=course.id).all()

    user = get_current_user()
    enrolled = False
    if user:
        enrolled = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first() is not None

    total_lessons = sum(len(ch.lessons) for ch in chapters)

    return render_template('frappe_lms/course_detail.html',
                           course=course,
                           chapters=chapters,
                           reviews=reviews,
                           enrolled=enrolled,
                           total_lessons=total_lessons)


@app.route('/course/<slug>/enroll', methods=['POST'])
@login_required
def enroll_course(slug):
    user = get_current_user()
    course = Course.query.filter_by(slug=slug).first_or_404()

    # Block enrollment for paid courses — must go through payment
    if course.paid_course and course.course_price and course.course_price > 0:
        # Check if they already paid
        paid = Payment.query.filter_by(
            member_id=user.id, course_id=course.id, status='Completed'
        ).first()
        if not paid:
            flash('This is a paid course. Please complete payment first.', 'warning')
            return redirect(url_for('course_detail', slug=slug))

    existing = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if not existing:
        enrollment = Enrollment(
            member_id=user.id,
            course_id=course.id,
            status=EnrollmentStatus.ACTIVE.value,
        )
        db.session.add(enrollment)
        db.session.commit()

    # If came from registration page, go back there
    if request.form.get('from') == 'register':
        return redirect(url_for('course_registration'))
    return redirect(url_for('course_progress', slug=slug))


# ==================== COURSE CREATION (Instructor) ====================

def _pdf_to_html(pdf_path):
    """Extract text from a PDF and return simple HTML content."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ''
            # Clean up and convert to paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if paragraphs:
                parts.append(f'<h3 class="text-lg font-bold text-surface-900 mt-6 mb-2">Page {i+1}</h3>')
                for para in paragraphs:
                    # Escape HTML entities
                    para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    parts.append(f'<p class="mb-3 text-surface-800/80 leading-relaxed">{para}</p>')
        return '\n'.join(parts) if parts else '<p>No text content could be extracted from this PDF.</p>'
    except Exception as e:
        return f'<p class="text-red-500">Error reading PDF: {str(e)}</p>'


def _make_slug(title):
    """Generate a URL-safe slug from a title."""
    slug = re.sub(r'[^\w\s-]', '', title.lower().strip())
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    # Ensure uniqueness
    base = slug
    counter = 1
    while Course.query.filter_by(slug=slug).first():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


@app.route('/instructor/create-course', methods=['GET', 'POST'])
@login_required
@role_required(UserType.INSTRUCTOR.value, UserType.ADMIN.value)
def create_course():
    user = get_current_user()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        short_intro = request.form.get('short_introduction', '').strip()
        category = request.form.get('category', '').strip()
        is_paid = request.form.get('is_paid') == '1'
        price = 0
        if is_paid:
            try:
                price = float(request.form.get('price', 0))
            except (ValueError, TypeError):
                price = 0

        if not title or not description or not short_intro:
            flash('Title, description and short introduction are required.', 'error')
            return redirect(url_for('create_course'))

        slug = _make_slug(title)

        course = Course(
            title=title,
            slug=slug,
            description=description,
            short_introduction=short_intro,
            instructor_id=user.id,
            category=category or 'General',
            paid_course=is_paid,
            course_price=price,
            currency='NGN',
            published=True,
            status=CourseStatus.PUBLISHED.value,
        )
        db.session.add(course)
        db.session.flush()  # get course.id

        # Handle PDF upload — create a chapter + lesson from PDF content
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename:
            filename = secure_filename(pdf_file.filename)
            if filename.lower().endswith('.pdf'):
                save_name = f'{uuid.uuid4().hex}_{filename}'
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
                pdf_file.save(save_path)

                html_content = _pdf_to_html(save_path)

                chapter = CourseChapter(
                    title='Course Material',
                    course_id=course.id,
                    order=0,
                    description='Auto-generated from uploaded PDF',
                )
                db.session.add(chapter)
                db.session.flush()

                lesson = CourseLesson(
                    title=f'{title} — Reading Material',
                    chapter_id=chapter.id,
                    order=0,
                    body=html_content,
                    status='Published',
                )
                db.session.add(lesson)
                course.lessons = 1
            else:
                flash('Only PDF files are accepted.', 'error')

        db.session.commit()
        flash(f'Course "{title}" created successfully!', 'success')
        return redirect(url_for('instructor_dashboard'))

    return render_template('frappe_lms/create_course_instructor.html', user=user)


# ==================== PAYSTACK PAYMENT ====================

PAYSTACK_PUBLIC_KEY = 'pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'


@app.route('/course/<slug>/pay', methods=['POST'])
@login_required
def initiate_payment(slug):
    user = get_current_user()
    course = Course.query.filter_by(slug=slug).first_or_404()

    if not course.paid_course or not course.course_price:
        return redirect(url_for('enroll_course', slug=slug))

    # Check if already paid
    existing_payment = Payment.query.filter_by(
        member_id=user.id, course_id=course.id, status='Completed'
    ).first()
    if existing_payment:
        # Already paid, just enroll
        existing_enrollment = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
        if not existing_enrollment:
            db.session.add(Enrollment(
                member_id=user.id, course_id=course.id,
                status=EnrollmentStatus.ACTIVE.value,
            ))
            db.session.commit()
        return redirect(url_for('course_progress', slug=slug))

    # Create a pending payment record
    ref = f'FCLS-{uuid.uuid4().hex[:12].upper()}'
    payment = Payment(
        member_id=user.id,
        amount=course.course_price,
        currency='NGN',
        course_id=course.id,
        transaction_id=ref,
        status='Pending',
        payment_method='Paystack',
    )
    db.session.add(payment)
    db.session.commit()

    # Render the Paystack inline checkout page
    return render_template('frappe_lms/paystack_checkout.html',
                           course=course,
                           user=user,
                           payment=payment,
                           paystack_public_key=PAYSTACK_PUBLIC_KEY)


@app.route('/payment/verify/<ref>')
@login_required
def verify_payment(ref):
    user = get_current_user()
    payment = Payment.query.filter_by(transaction_id=ref, member_id=user.id).first()
    if not payment:
        flash('Payment not found.', 'error')
        return redirect(url_for('courses'))

    # In demo mode we just mark it complete (real app would verify with Paystack API)
    payment.status = 'Completed'
    payment.completed_on = datetime.now()
    db.session.commit()

    # Auto-enroll after payment
    course = db.session.get(Course, payment.course_id)
    if course:
        existing = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
        if not existing:
            db.session.add(Enrollment(
                member_id=user.id, course_id=course.id,
                status=EnrollmentStatus.ACTIVE.value,
            ))
            db.session.commit()
        flash(f'Payment successful! You are now enrolled in "{course.title}".', 'success')
        return redirect(url_for('course_progress', slug=course.slug))

    flash('Payment processed.', 'success')
    return redirect(url_for('courses'))


@app.route('/course/<slug>/drop', methods=['POST'])
@login_required
def drop_course(slug):
    user = get_current_user()
    course = Course.query.filter_by(slug=slug).first_or_404()
    enrollment = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()

    if request.form.get('from') == 'register':
        return redirect(url_for('course_registration'))
    return redirect(url_for('courses'))


# ==================== COURSE REGISTRATION ====================

@app.route('/course-registration')
@login_required
def course_registration():
    user = get_current_user()
    if user.user_type not in (UserType.STUDENT.value,):
        return redirect(url_for('dashboard'))

    # Get all published courses grouped by category
    all_courses = Course.query.filter_by(published=True).order_by(Course.category, Course.title).all()

    # Get student's current enrollments
    enrolled_ids = {e.course_id for e in Enrollment.query.filter_by(member_id=user.id).all()}

    # Group courses by category
    categories = {}
    for course in all_courses:
        cat = course.category or 'General'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            'course': course,
            'enrolled': course.id in enrolled_ids,
        })

    total_enrolled = len(enrolled_ids)
    total_available = len(all_courses)

    return render_template('frappe_lms/course_registration.html',
                           user=user,
                           categories=categories,
                           total_enrolled=total_enrolled,
                           total_available=total_available)


@app.route('/course/<slug>/progress')
@login_required
def course_progress(slug):
    user = get_current_user()
    course = Course.query.filter_by(slug=slug).first_or_404()
    enrollment = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if not enrollment:
        return redirect(url_for('course_detail', slug=slug))

    chapters = CourseChapter.query.filter_by(course_id=course.id).order_by(CourseChapter.order).all()
    total_lessons = sum(len(ch.lessons) for ch in chapters)

    return render_template('frappe_lms/course_progress.html',
                           course=course,
                           chapters=chapters,
                           enrollment=enrollment,
                           total_lessons=total_lessons)


# ==================== LESSON ====================

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    user = get_current_user()
    lesson = db.session.get(CourseLesson, lesson_id)
    if not lesson:
        return render_template('frappe_lms/404.html'), 404

    chapter = lesson.chapter_ref
    course = chapter.course_rel

    enrolled = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if not enrolled:
        return render_template('frappe_lms/403.html'), 403

    lessons_in_chapter = CourseLesson.query.filter_by(chapter_id=chapter.id).order_by(CourseLesson.order).all()
    current_index = next((i for i, l in enumerate(lessons_in_chapter) if l.id == lesson.id), 0)
    all_chapters = CourseChapter.query.filter_by(course_id=course.id).order_by(CourseChapter.order).all()

    return render_template('frappe_lms/lesson.html',
                           lesson=lesson,
                           chapter=chapter,
                           course=course,
                           lessons_in_chapter=lessons_in_chapter,
                           current_index=current_index,
                           all_chapters=all_chapters)


@app.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def mark_lesson_complete(lesson_id):
    user = get_current_user()
    lesson = db.session.get(CourseLesson, lesson_id)
    if not lesson:
        return jsonify({'error': 'not found'}), 404

    course = lesson.chapter_ref.course_rel
    enrollment = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if enrollment:
        enrollment.current_lesson_id = lesson.id
        chapters = CourseChapter.query.filter_by(course_id=course.id).all()
        total = sum(CourseLesson.query.filter_by(chapter_id=ch.id).count() for ch in chapters)
        if total > 0:
            enrollment.progress = min(enrollment.progress + (100.0 / total), 100.0)
        db.session.commit()
    return jsonify({'success': True})


# ==================== QUIZ ====================

@app.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    user = get_current_user()
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        return render_template('frappe_lms/404.html'), 404

    course = quiz.course_ref
    enrolled = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if not enrolled:
        return render_template('frappe_lms/403.html'), 403

    past = QuizSubmission.query.filter_by(member_id=user.id, quiz_id=quiz.id).first()
    if past and quiz.max_attempts == 1:
        return render_template('frappe_lms/quiz_result.html', quiz=quiz, submission=past,
                               results=QuizResult.query.filter_by(submission_id=past.id).all())

    quiz_questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()
    questions = [qq.question for qq in quiz_questions]

    return render_template('frappe_lms/quiz.html', quiz=quiz, questions=questions)


@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    user = get_current_user()
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        return render_template('frappe_lms/404.html'), 404

    answers = request.form.to_dict()
    quiz_questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()

    score = 0
    total_marks = 0
    submission = QuizSubmission(
        member_id=user.id,
        quiz_id=quiz.id,
        started_on=datetime.now(),
        submitted_on=datetime.now(),
    )
    db.session.add(submission)
    db.session.flush()

    for qq in quiz_questions:
        question = qq.question
        total_marks += question.marks
        user_answer = answers.get(f'question_{question.id}')
        correct = False

        if question.question_type == 'single_select' and user_answer:
            try:
                selected = db.session.get(Option, int(user_answer))
                if selected and selected.is_correct:
                    correct = True
                    score += question.marks
            except (ValueError, TypeError):
                pass

        result = QuizResult(
            submission_id=submission.id,
            question_id=question.id,
            answer=user_answer or '',
            correct=correct,
            marks_obtained=question.marks if correct else 0,
        )
        db.session.add(result)

    percentage = (score / total_marks * 100) if total_marks > 0 else 0
    submission.score = score
    submission.percentage = percentage
    submission.is_pass = percentage >= quiz.passing_percentage
    db.session.commit()

    return redirect(url_for('quiz_result', submission_id=submission.id))


@app.route('/quiz-result/<int:submission_id>')
@login_required
def quiz_result(submission_id):
    user = get_current_user()
    submission = db.session.get(QuizSubmission, submission_id)
    if not submission or submission.member_id != user.id:
        return render_template('frappe_lms/404.html'), 404

    quiz = submission.quiz_ref
    results = QuizResult.query.filter_by(submission_id=submission.id).all()
    return render_template('frappe_lms/quiz_result.html',
                           quiz=quiz,
                           submission=submission,
                           results=results)


# ==================== ASSIGNMENT ====================

@app.route('/assignment/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    user = get_current_user()
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return render_template('frappe_lms/404.html'), 404

    course = assignment.course_ref
    enrolled = Enrollment.query.filter_by(member_id=user.id, course_id=course.id).first()
    if not enrolled:
        return render_template('frappe_lms/403.html'), 403

    submission = AssignmentSubmission.query.filter_by(
        member_id=user.id, assignment_id=assignment.id
    ).first()

    return render_template('frappe_lms/assignment.html',
                           assignment=assignment,
                           course=course,
                           submission=submission)


@app.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    user = get_current_user()
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'error': 'not found'}), 404

    content = request.form.get('content', '')

    existing = AssignmentSubmission.query.filter_by(
        member_id=user.id, assignment_id=assignment.id
    ).first()

    if existing:
        existing.submission_text = content
        existing.submitted_on = datetime.now()
        existing.is_submitted = True
    else:
        sub = AssignmentSubmission(
            member_id=user.id,
            assignment_id=assignment.id,
            submission_text=content,
            submitted_on=datetime.now(),
            is_submitted=True,
        )
        db.session.add(sub)

    db.session.commit()
    return redirect(url_for('view_assignment', assignment_id=assignment_id))


# ==================== DASHBOARDS ====================

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    if user.user_type in (UserType.INSTRUCTOR.value, UserType.ADMIN.value):
        return redirect(url_for('instructor_dashboard'))

    enrollments = Enrollment.query.filter_by(member_id=user.id).all()
    courses_list = [db.session.get(Course, e.course_id) for e in enrollments]
    courses_list = [c for c in courses_list if c]
    certificates = Certificate.query.filter_by(member_id=user.id).all()

    # Peerup-style stats
    completed_enrollments = [e for e in enrollments if e.status == 'completed']
    in_progress = [e for e in enrollments if e.status == 'active']

    # Quiz stats
    quiz_submissions = QuizSubmission.query.filter_by(member_id=user.id).all()
    quizzes_taken = len(quiz_submissions)
    avg_score = round(sum(s.percentage or 0 for s in quiz_submissions) / max(len(quiz_submissions), 1), 1)

    # Learning streak
    today = datetime.now().date()
    active_dates = set()
    for s in quiz_submissions:
        if s.submitted_on:
            active_dates.add(s.submitted_on.date())
    for e in enrollments:
        if e.enrolled_on:
            active_dates.add(e.enrolled_on.date())
    streak = 0
    check = today
    if check not in active_dates:
        check = today - timedelta(days=1)
    while check in active_dates:
        streak += 1
        check -= timedelta(days=1)

    # Overall progress
    overall_progress = round(sum(e.progress or 0 for e in enrollments) / max(len(enrollments), 1), 1)

    # Upcoming assignments (deadlines)
    enrolled_course_ids = [e.course_id for e in enrollments]
    upcoming_deadlines = []
    if enrolled_course_ids:
        assignments = Assignment.query.filter(
            Assignment.course_id.in_(enrolled_course_ids),
            Assignment.due_date >= datetime.now()
        ).order_by(Assignment.due_date).limit(5).all()
        for a in assignments:
            days_left = (a.due_date - datetime.now()).days
            upcoming_deadlines.append({
                'title': a.title,
                'course_title': a.course_ref.title if a.course_ref else '',
                'due_date': a.due_date.strftime('%b %d, %Y'),
                'days_left': days_left,
                'color': 'red' if days_left <= 2 else 'amber' if days_left <= 5 else 'green',
            })

    # Recommended courses (not enrolled)
    recommended = Course.query.filter(
        Course.published == True,
        ~Course.id.in_(enrolled_course_ids) if enrolled_course_ids else True
    ).limit(3).all()

    return render_template('frappe_lms/student_dashboard.html',
                           user=user,
                           enrollments=enrollments,
                           courses=courses_list,
                           certificates=certificates,
                           completed_count=len(completed_enrollments),
                           in_progress_count=len(in_progress),
                           quizzes_taken=quizzes_taken,
                           avg_score=avg_score,
                           streak=streak,
                           overall_progress=overall_progress,
                           upcoming_deadlines=upcoming_deadlines,
                           recommended=recommended)


@app.route('/instructor-dashboard')
@login_required
def instructor_dashboard():
    user = get_current_user()
    if user.user_type not in (UserType.INSTRUCTOR.value, UserType.ADMIN.value):
        return redirect(url_for('dashboard'))

    if user.user_type == UserType.ADMIN.value:
        my_courses = Course.query.all()
    else:
        my_courses = Course.query.filter_by(instructor_id=user.id).all()

    total_students = set()
    total_enrollments = 0
    total_lessons = 0
    total_quizzes = 0
    for c in my_courses:
        enrs = Enrollment.query.filter_by(course_id=c.id).all()
        total_enrollments += len(enrs)
        total_students.update(e.member_id for e in enrs)
        for ch in c.chapters:
            total_lessons += len(ch.lessons)
        total_quizzes += len(c.quizzes)

    # Average rating
    course_ids = [c.id for c in my_courses]
    reviews = []
    if course_ids:
        reviews = CourseReview.query.filter(CourseReview.course_id.in_(course_ids)).all()
    avg_rating = round(sum(r.rating or 0 for r in reviews) / max(len(reviews), 1), 1) if reviews else 0

    # Pending submissions (ungraded assignments)
    pending_submissions = []
    if course_ids:
        ungraded = db.session.query(AssignmentSubmission).join(Assignment).filter(
            Assignment.course_id.in_(course_ids),
            AssignmentSubmission.is_submitted == True,
            AssignmentSubmission.is_graded == False
        ).order_by(AssignmentSubmission.submitted_on.desc()).limit(10).all()
        for sub in ungraded:
            student = db.session.get(User, sub.member_id)
            pending_submissions.append({
                'student_name': student.full_name if student else 'Unknown',
                'assignment_title': sub.assignment_ref.title if sub.assignment_ref else '',
                'course_title': sub.assignment_ref.course_ref.title if sub.assignment_ref and sub.assignment_ref.course_ref else '',
                'submitted_at': sub.submitted_on.strftime('%b %d, %Y') if sub.submitted_on else '',
                'assignment_id': sub.assignment_id,
            })

    # Recent activity
    recent_activity = []
    if course_ids:
        recent_enrs = Enrollment.query.filter(
            Enrollment.course_id.in_(course_ids)
        ).order_by(Enrollment.enrolled_on.desc()).limit(5).all()
        for e in recent_enrs:
            student = db.session.get(User, e.member_id)
            course = db.session.get(Course, e.course_id)
            recent_activity.append({
                'icon': '👤',
                'title': f'{student.full_name if student else "Someone"} enrolled in {course.title if course else "a course"}',
                'date': e.enrolled_on.strftime('%b %d') if e.enrolled_on else '',
                'type': 'enrollment',
            })

        recent_quiz = QuizSubmission.query.join(Quiz).filter(
            Quiz.course_id.in_(course_ids)
        ).order_by(QuizSubmission.submitted_on.desc()).limit(5).all()
        for qs in recent_quiz:
            student = db.session.get(User, qs.member_id)
            recent_activity.append({
                'icon': '📝',
                'title': f'{student.full_name if student else "Someone"} completed quiz: {qs.quiz_ref.title if qs.quiz_ref else ""}',
                'date': qs.submitted_on.strftime('%b %d') if qs.submitted_on else '',
                'type': 'quiz',
            })

    recent_activity.sort(key=lambda x: x.get('date', ''), reverse=True)
    recent_activity = recent_activity[:8]

    stats = {
        'courses': len(my_courses),
        'students': len(total_students),
        'total_enrollments': total_enrollments,
        'active_batches': Batch.query.count(),
        'avg_rating': avg_rating,
        'total_reviews': len(reviews),
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
    }

    return render_template('frappe_lms/instructor_dashboard.html',
                           user=user,
                           courses=my_courses,
                           stats=stats,
                           pending_submissions=pending_submissions,
                           pending_count=len(pending_submissions),
                           recent_activity=recent_activity)


@app.route('/admin-dashboard')
@login_required
@role_required(UserType.ADMIN.value)
def admin_dashboard():
    total_students = User.query.filter_by(user_type=UserType.STUDENT.value).count()
    total_instructors = User.query.filter_by(user_type=UserType.INSTRUCTOR.value).count()

    # Growth calculations
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    new_students_this_week = User.query.filter(
        User.user_type == UserType.STUDENT.value,
        User.created_at >= week_ago
    ).count()
    students_last_week = User.query.filter(
        User.user_type == UserType.STUDENT.value,
        User.created_at >= two_weeks_ago,
        User.created_at < week_ago
    ).count()
    student_growth = round(((new_students_this_week - students_last_week) / max(students_last_week, 1)) * 100) if students_last_week > 0 else (100 if new_students_this_week > 0 else 0)

    new_instructors_this_week = User.query.filter(
        User.user_type == UserType.INSTRUCTOR.value,
        User.created_at >= week_ago
    ).count()

    stats = {
        'total_courses': Course.query.count(),
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_batches': Batch.query.count(),
        'total_quizzes': Quiz.query.count(),
        'certificates_issued': Certificate.query.count(),
        'total_enrollments': Enrollment.query.count(),
        'student_growth': student_growth,
        'new_students_this_week': new_students_this_week,
        'new_instructors_this_week': new_instructors_this_week,
        'new_courses_this_week': Course.query.filter(Course.created_at >= week_ago).count(),
        'new_enrollments_this_week': Enrollment.query.filter(Enrollment.enrolled_on >= week_ago).count(),
        'total_quiz_attempts': QuizSubmission.query.count(),
    }

    recent_enrollments = Enrollment.query.order_by(Enrollment.enrolled_on.desc()).limit(10).all()

    # Recent instructors
    recent_instructors = User.query.filter_by(user_type=UserType.INSTRUCTOR.value).order_by(User.created_at.desc()).limit(5).all()
    # Recent students
    recent_students = User.query.filter_by(user_type=UserType.STUDENT.value).order_by(User.created_at.desc()).limit(5).all()

    # All users and courses for management tabs
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_courses = Course.query.order_by(Course.created_at.desc()).all()

    return render_template('frappe_lms/admin_dashboard.html',
                           stats=stats,
                           recent_enrollments=recent_enrollments,
                           recent_instructors=recent_instructors,
                           recent_students=recent_students,
                           all_users=all_users,
                           all_courses=all_courses)


# ==================== BATCHES ====================

@app.route('/batches')
@login_required
def batches():
    all_batches = Batch.query.filter_by(published=True).all()
    return render_template('frappe_lms/batches.html', batches=all_batches)


@app.route('/batch/<int:batch_id>')
@login_required
def view_batch(batch_id):
    batch = db.session.get(Batch, batch_id)
    if not batch:
        return render_template('frappe_lms/404.html'), 404

    members = BatchEnrollment.query.filter_by(batch_id=batch.id).all()
    live_classes = LiveClass.query.filter_by(batch_id=batch.id).order_by(LiveClass.scheduled_at).all()

    return render_template('frappe_lms/batch_detail.html',
                           batch=batch,
                           members=members,
                           live_classes=live_classes)


# ==================== CERTIFICATES ====================

@app.route('/certificates')
@login_required
def certificates():
    user = get_current_user()
    certs = Certificate.query.filter_by(member_id=user.id).all()
    return render_template('frappe_lms/certificates.html', certificates=certs)


@app.route('/certificate/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        return render_template('frappe_lms/404.html'), 404
    return render_template('frappe_lms/certificate_view.html', certificate=cert)


# ==================== PROFILE ====================

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    course_count = Enrollment.query.filter_by(member_id=user.id).count()
    cert_count = Certificate.query.filter_by(member_id=user.id).count()
    return render_template('frappe_lms/profile.html',
                           user=user,
                           course_count=course_count,
                           cert_count=cert_count)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
    user.full_name = request.form.get('full_name', user.full_name)
    user.bio = request.form.get('bio', user.bio)
    user.headline = request.form.get('headline', user.headline)
    db.session.commit()
    return redirect(url_for('profile'))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('frappe_lms/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('frappe_lms/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('frappe_lms/403.html'), 403


# ==================== STARTUP ====================

def init_app():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            print("Initializing FCLS with test data...")
            init_frappe_lms_db(app)
            print("Done!")
        else:
            print(f"Database ready — {User.query.count()} users, {Course.query.count()} courses")


if __name__ == '__main__':
    init_app()
    print("\n" + "=" * 60)
    print("  FCLS — http://127.0.0.1:5001")
    print("=" * 60)
    print("  Admin:      admin@lms.local / admin123")
    print("  Instructor: instructor.john@lms.local / instructor123")
    print("  Student:    student1@lms.local / student123")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=True)
