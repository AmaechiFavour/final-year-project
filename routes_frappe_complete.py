# FCLS API Routes for Flask
# Comprehensive endpoints for the learning management system

from flask import Blueprint, request, jsonify, send_file, render_template, session, redirect, url_for
from models_frappe_complete import *
from datetime import datetime, timedelta
from functools import wraps
import json
from sqlalchemy import and_, or_, func as db_func

# ==================== HELPER DECORATORS ====================
def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def instructor_required(f):
    """Require user to be an instructor"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.user_type not in [UserType.INSTRUCTOR.value, UserType.ADMIN.value]:
            return jsonify({'error': 'Instructor role required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ==================== USER ENDPOINTS ====================
@api_bp.route('/user/info', methods=['GET'])
@login_required
def get_user_info():
    """Get current user information"""
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'full_name': user.full_name,
        'bio': user.bio,
        'headline': user.headline,
        'user_image': user.user_image,
        'user_type': user.user_type,
        'roles': [user.user_type]  # Simplified role system
    })

@api_bp.route('/user/profile', methods=['GET', 'PUT'])
@login_required
def user_profile():
    """Get or update user profile"""
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if request.method == 'GET':
        enrollments = Enrollment.query.filter_by(member_id=user.id).count()
        completed = Enrollment.query.filter_by(member_id=user.id, status='completed').count()
        certificates = Certificate.query.filter_by(member_id=user.id).count()
        
        return jsonify({
            'user': {
                'name': user.name,
                'email': user.email,
                'full_name': user.full_name,
                'bio': user.bio,
                'headline': user.headline,
                'user_image': user.user_image,
            },
            'stats': {
                'enrollments': enrollments,
                'completed_courses': completed,
                'certificates': certificates
            }
        })
    
    elif request.method == 'PUT':
        data = request.json
        user.full_name = data.get('full_name', user.full_name)
        user.bio = data.get('bio', user.bio)
        user.headline = data.get('headline', user.headline)
        user.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'})

# ==================== COURSE ENDPOINTS ====================
@api_bp.route('/courses', methods=['GET'])
def get_courses():
    """Get all published courses"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category')
    featured = request.args.get('featured', False, type=bool)
    search = request.args.get('search')
    
    query = Course.query.filter_by(published=True)
    
    if featured:
        query = query.filter_by(featured=True)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(or_(
            Course.title.ilike(f'%{search}%'),
            Course.description.ilike(f'%{search}%'),
            Course.tags.ilike(f'%{search}%')
        ))
    
    courses = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'courses': [{
            'id': c.id,
            'title': c.title,
            'slug': c.slug,
            'description': c.short_introduction,
            'image': c.image,
            'category': c.category,
            'enrollment_count': len(c.enrollments_list),
            'lesson_count': len(c.chapters),
            'rating': c.rating,
            'price': c.course_price if c.paid_course else 0,
            'paid': c.paid_course
        } for c in courses.items],
        'total': courses.total,
        'pages': courses.pages,
        'current_page': page
    })

@api_bp.route('/course/<int:course_id>', methods=['GET'])
def get_course_details(course_id):
    """Get detailed course information"""
    course = Course.query.get(course_id)
    if not course or not course.published:
        return jsonify({'error': 'Course not found'}), 404
    
    instructor = User.query.get(course.instructor_id)
    chapters_data = []
    
    for chapter in course.chapters:
        lessons_data = [{
            'id': lesson.id,
            'title': lesson.title,
            'duration': lesson.duration,
            'has_quiz': lesson.quiz_id is not None,
            'has_assignment': False  # Would check assignments table
        } for lesson in chapter.lessons]
        
        chapters_data.append({
            'id': chapter.id,
            'title': chapter.title,
            'description': chapter.description,
            'lessons': lessons_data
        })
    
    return jsonify({
        'id': course.id,
        'title': course.title,
        'slug': course.slug,
        'description': course.description,
        'short_introduction': course.short_introduction,
        'image': course.image,
        'category': course.category,
        'instructor': {
            'id': instructor.id,
            'name': instructor.full_name,
            'email': instructor.email,
            'bio': instructor.bio
        },
        'chapters': chapters_data,
        'stats': {
            'enrollment_count': len(course.enrollments_list),
            'lesson_count': sum(len(ch.lessons) for ch in course.chapters),
            'quiz_count': len(course.quizzes),
            'rating': course.rating
        },
        'pricing': {
            'paid': course.paid_course,
            'price': course.course_price,
            'currency': course.currency
        }
    })

@api_bp.route('/course', methods=['POST'])
@instructor_required
def create_course():
    """Create a new course"""
    data = request.json
    user_id = session.get('user_id')
    
    course = Course(
        title=data.get('title'),
        slug=data.get('slug') or data.get('title').lower().replace(' ', '-'),
        description=data.get('description'),
        short_introduction=data.get('short_introduction'),
        instructor_id=user_id,
        category=data.get('category'),
        video_link=data.get('video_link'),
        published=data.get('published', False),
        image=data.get('image'),
        paid_course=data.get('paid_course', False),
        course_price=data.get('course_price', 0),
        enable_certification=data.get('enable_certification', True)
    )
    
    db.session.add(course)
    db.session.commit()
    
    return jsonify({
        'message': 'Course created successfully',
        'course_id': course.id
    }), 201

@api_bp.route('/course/<int:course_id>', methods=['PUT'])
@instructor_required
def update_course(course_id):
    """Update course details"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    if course.instructor_id != session.get('user_id'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.json
    course.title = data.get('title', course.title)
    course.description = data.get('description', course.description)
    course.short_introduction = data.get('short_introduction', course.short_introduction)
    course.category = data.get('category', course.category)
    course.image = data.get('image', course.image)
    course.published = data.get('published', course.published)
    course.updated_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': 'Course updated successfully'})

@api_bp.route('/course/<int:course_id>', methods=['DELETE'])
@instructor_required
def delete_course(course_id):
    """Delete a course"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    if course.instructor_id != session.get('user_id'):
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({'message': 'Course deleted successfully'})

# ==================== CHAPTER ENDPOINTS ====================
@api_bp.route('/course/<int:course_id>/chapters', methods=['POST'])
@instructor_required
def create_chapter(course_id):
    """Create a chapter in a course"""
    course = Course.query.get(course_id)
    if not course or course.instructor_id != session.get('user_id'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.json
    chapter = CourseChapter(
        course_id=course_id,
        title=data.get('title'),
        description=data.get('description'),
        order=data.get('order', 0)
    )
    
    db.session.add(chapter)
    db.session.commit()
    
    return jsonify({
        'message': 'Chapter created successfully',
        'chapter_id': chapter.id
    }), 201

@api_bp.route('/chapter/<int:chapter_id>/lessons', methods=['POST'])
@instructor_required
def create_lesson(chapter_id):
    """Create a lesson in a chapter"""
    chapter = CourseChapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404
    
    course = chapter.course_ref
    if course.instructor_id != session.get('user_id'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.json
    lesson = CourseLesson(
        chapter_id=chapter_id,
        title=data.get('title'),
        body=data.get('body'),
        youtube=data.get('youtube'),
        order=data.get('order', 0),
        duration=data.get('duration', 0)
    )
    
    db.session.add(lesson)
    db.session.commit()
    
    return jsonify({
        'message': 'Lesson created successfully',
        'lesson_id': lesson.id
    }), 201

# ==================== ENROLLMENT ENDPOINTS ====================
@api_bp.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    """Enroll user in a course"""
    user_id = session.get('user_id')
    course = Course.query.get(course_id)
    
    if not course or not course.published:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if already enrolled
    existing = Enrollment.query.filter_by(member_id=user_id, course_id=course_id).first()
    if existing:
        return jsonify({'error': 'Already enrolled in this course'}), 400
    
    enrollment = Enrollment(
        member_id=user_id,
        course_id=course_id,
        status=EnrollmentStatus.ACTIVE.value,
        progress=0
    )
    
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully enrolled in course',
        'enrollment_id': enrollment.id
    }), 201

@api_bp.route('/my-courses', methods=['GET'])
@login_required
def my_courses():
    """Get user's enrolled courses"""
    user_id = session.get('user_id')
    
    enrollments = Enrollment.query.filter_by(member_id=user_id).all()
    
    courses = []
    for enrollment in enrollments:
        course = enrollment.course_rel
        courses.append({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'image': course.image,
            'progress': enrollment.progress,
            'status': enrollment.status,
            'enrolled_date': enrollment.enrolled_on.isoformat() if enrollment.enrolled_on else None,
            'completed_date': enrollment.completed_on.isoformat() if enrollment.completed_on else None
        })
    
    return jsonify({'courses': courses})

# ==================== BATCH ENDPOINTS ====================
@api_bp.route('/batch', methods=['POST'])
@instructor_required
def create_batch():
    """Create a batch"""
    data = request.json
    user_id = session.get('user_id')
    
    batch = Batch(
        title=data.get('title'),
        course_id=data.get('course_id'),
        description=data.get('description'),
        start_date=datetime.fromisoformat(data.get('start_date')),
        end_date=datetime.fromisoformat(data.get('end_date')),
        max_students=data.get('max_students'),
        published=data.get('published', False),
        enable_certification=data.get('enable_certification', True),
        enable_self_learning=data.get('enable_self_learning', False)
    )
    
    db.session.add(batch)
    db.session.commit()
    
    return jsonify({
        'message': 'Batch created successfully',
        'batch_id': batch.id
    }), 201

@api_bp.route('/batch/<int:batch_id>/enroll', methods=['POST'])
@login_required
def enroll_batch(batch_id):
    """Enroll user in a batch"""
    user_id = session.get('user_id')
    batch = Batch.query.get(batch_id)
    
    if not batch or not batch.published:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Check if already enrolled
    existing = BatchEnrollment.query.filter_by(member_id=user_id, batch_id=batch_id).first()
    if existing:
        return jsonify({'error': 'Already enrolled in this batch'}), 400
    
    enrollment = BatchEnrollment(
        member_id=user_id,
        batch_id=batch_id,
        enrolled_on=datetime.now()
    )
    
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully enrolled in batch',
        'enrollment_id': enrollment.id
    }), 201

# ==================== QUIZ ENDPOINTS ====================
@api_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
@login_required
def get_quiz(quiz_id):
    """Get quiz details"""
    quiz = Quiz.query.get(quiz_id)
    if not quiz or not quiz.published:
        return jsonify({'error': 'Quiz not found'}), 404
    
    questions = [{
        'id': q.id,
        'question_id': q.question_id,
        'order': q.order
    } for q in quiz.questions]
    
    return jsonify({
        'id': quiz.id,
        'title': quiz.title,
        'passing_percentage': quiz.passing_percentage,
        'max_attempts': quiz.max_attempts,
        'duration_minutes': quiz.duration_minutes,
        'show_answers': quiz.show_answers,
        'question_count': len(questions),
        'questions': questions
    })

@api_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    """Submit quiz answers"""
    user_id = session.get('user_id')
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    data = request.json
    answers = data.get('answers', {})
    
    # Create submission
    submission = QuizSubmission(
        member_id=user_id,
        quiz_id=quiz_id,
        started_on=datetime.now(),
        submitted_on=datetime.now()
    )
    
    db.session.add(submission)
    db.session.flush()
    
    # Calculate score
    score = 0
    total_marks = 0
    
    for quiz_q in quiz.questions:
        question = quiz_q.question
        total_marks += question.marks
        
        # Check answer
        user_answer = answers.get(str(question.id))
        correct = False
        
        if question.question_type == QuizType.SINGLE_CHOICE.value:
            # Check if selected option is correct
            for option in question.options:
                if option.is_correct and str(option.id) == user_answer:
                    correct = True
                    score += question.marks
                    break
        
        # Store result
        result = QuizResult(
            submission_id=submission.id,
            question_id=question.id,
            answer=user_answer,
            correct=correct,
            marks_obtained=question.marks if correct else 0
        )
        db.session.add(result)
    
    # Calculate percentage
    percentage = (score / total_marks * 100) if total_marks > 0 else 0
    is_pass = percentage >= quiz.passing_percentage
    
    submission.score = score
    submission.percentage = percentage
    submission.is_pass = is_pass
    
    db.session.commit()
    
    return jsonify({
        'submission_id': submission.id,
        'score': score,
        'percentage': percentage,
        'is_pass': is_pass,
        'message': 'Quiz submitted successfully'
    }), 201

# ==================== CERTIFICATE ENDPOINTS ====================
@api_bp.route('/my-certificates', methods=['GET'])
@login_required
def my_certificates():
    """Get user's certificates"""
    user_id = session.get('user_id')
    
    certificates = Certificate.query.filter_by(member_id=user_id).all()
    
    cert_list = []
    for cert in certificates:
        course = Course.query.get(cert.course_id) if cert.course_id else None
        cert_list.append({
            'id': cert.id,
            'name': cert.name,
            'course': course.title if course else 'N/A',
            'issue_date': cert.issue_date.isoformat() if cert.issue_date else None,
            'certificate_number': cert.certificate_number,
            'status': cert.status
        })
    
    return jsonify({'certificates': cert_list})

@api_bp.route('/certificate/<int:certificate_id>', methods=['GET'])
@login_required
def get_certificate(certificate_id):
    """Get certificate details"""
    certificate = Certificate.query.get(certificate_id)
    
    if not certificate or (certificate.member_id != session.get('user_id') and 
                          User.query.get(session.get('user_id')).user_type != UserType.ADMIN.value):
        return jsonify({'error': 'Not authorized'}), 403
    
    user = certificate.member_rel
    course = Course.query.get(certificate.course_id) if certificate.course_id else None
    
    return jsonify({
        'id': certificate.id,
        'member_name': user.full_name,
        'course_name': course.title if course else 'N/A',
        'certificate_number': certificate.certificate_number,
        'issue_date': certificate.issue_date.isoformat() if certificate.issue_date else None,
        'template': certificate.template,
        'qr_code': certificate.qr_code,
        'status': certificate.status
    })

# ==================== PROGRESS TRACKING ====================
@api_bp.route('/progress/<int:course_id>', methods=['GET'])
@login_required
def get_progress(course_id):
    """Get user's course progress"""
    user_id = session.get('user_id')
    
    enrollment = Enrollment.query.filter_by(member_id=user_id, course_id=course_id).first()
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 404
    
    course = Course.query.get(course_id)
    
    return jsonify({
        'course_id': course_id,
        'progress': enrollment.progress,
        'status': enrollment.status,
        'current_lesson': enrollment.current_lesson_id,
        'enrolled_date': enrollment.enrolled_on.isoformat() if enrollment.enrolled_on else None,
        'completed_date': enrollment.completed_on.isoformat() if enrollment.completed_on else None
    })

@api_bp.route('/progress/<int:course_id>/update', methods=['POST'])
@login_required
def update_progress(course_id):
    """Update course progress"""
    user_id = session.get('user_id')
    data = request.json
    
    enrollment = Enrollment.query.filter_by(member_id=user_id, course_id=course_id).first()
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 404
    
    enrollment.progress = data.get('progress', enrollment.progress)
    enrollment.current_lesson_id = data.get('current_lesson_id', enrollment.current_lesson_id)
    
    if data.get('completed'):
        enrollment.status = EnrollmentStatus.COMPLETED.value
        enrollment.completed_on = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': 'Progress updated successfully'})

# ==================== STATISTICS ENDPOINTS ====================
@api_bp.route('/stats/dashboard', methods=['GET'])
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if user.user_type == UserType.STUDENT.value:
        # Student dashboard
        enrollments = Enrollment.query.filter_by(member_id=user_id).count()
        completed = Enrollment.query.filter_by(member_id=user_id, status='completed').count()
        certificates = Certificate.query.filter_by(member_id=user_id).count()
        
        return jsonify({
            'enrollments': enrollments,
            'completed_courses': completed,
            'certificates': certificates,
            'hours_spent': 0  # Would calculate from lesson views
        })
    
    elif user.user_type == UserType.INSTRUCTOR.value:
        # Instructor dashboard
        courses = Course.query.filter_by(instructor_id=user_id).count()
        total_students = db.session.query(db_func.count(db_func.distinct(Enrollment.member_id))).\
                        filter(Course.instructor_id == user_id).scalar()
        
        return jsonify({
            'courses': courses,
            'total_students': total_students or 0,
            'batches': Batch.query.filter_by(course_id=None).count(),  # Simplified
            'certifications_issued': 0
        })

# Register blueprint
def register_api_routes(app):
    """Register API routes with the Flask app"""
    app.register_blueprint(api_bp)
