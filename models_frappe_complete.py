# FCLS - Faculty of Computing Learning System Models
# Complete data models for the learning management system

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, func, Text, Float, Integer, String, Boolean, ForeignKey, Table
from datetime import datetime
import json
from enum import Enum

db = SQLAlchemy()

# ==================== ENUMS ====================
class UserType(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor" 
    MODERATOR = "moderator"
    EVALUATOR = "evaluator"
    ADMIN = "admin"

class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    ON_HOLD = "on_hold"

class QuizType(str, Enum):
    SINGLE_CHOICE = "single_select"
    MULTIPLE_CHOICE = "multiple_select"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

# ==================== USER & ROLES ====================
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)  # Email/username
    email = db.Column(db.String(120), nullable=False, unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    bio = db.Column(Text)
    headline = db.Column(db.String(255))  # Professional tagline
    user_image = db.Column(db.String(500))  # Profile picture URL
    user_type = db.Column(db.String(50), default=UserType.STUDENT)  # student, instructor, etc.
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    enrollments = db.relationship("Enrollment", backref="member", foreign_keys="Enrollment.member_id")
    batch_enrollments = db.relationship("BatchEnrollment", backref="member", foreign_keys="BatchEnrollment.member_id")
    quiz_submissions = db.relationship("QuizSubmission", backref="member")
    assignments_submitted = db.relationship("AssignmentSubmission", backref="member")
    certificates = db.relationship("Certificate", backref="member_rel")
    created_courses = db.relationship("Course", backref="instructor_rel", foreign_keys="Course.instructor_id")
    batch_enrollee_feedback = db.relationship("BatchFeedback", backref="member")
    
# ==================== COURSE STRUCTURE ====================
class Course(db.Model):
    __tablename__ = "lms_course"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(Text, nullable=False)
    short_introduction = db.Column(db.String(500), nullable=False)
    video_link = db.Column(db.String(500))  # Embed link
    
    # Instructors (can be multiple)
    instructor_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    
    # Course settings
    published = db.Column(db.Boolean, default=False)
    published_on = db.Column(DateTime)
    featured = db.Column(db.Boolean, default=False)
    upcoming = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default=CourseStatus.DRAFT)
    
    # Pricing
    paid_course = db.Column(db.Boolean, default=False)
    course_price = db.Column(Float, default=0)
    currency = db.Column(db.String(10), default="USD")
    amount_usd = db.Column(Float, default=0)
    
    # Certification
    enable_certification = db.Column(db.Boolean, default=True)
    paid_certificate = db.Column(db.Boolean, default=False)
    
    # Category & Tags
    category = db.Column(db.String(100))
    tags = db.Column(db.String(500))  # Comma-separated
    
    # Settings
    disable_self_learning = db.Column(db.Boolean, default=False)
    timezone = db.Column(db.String(50), default="UTC")
    
    # Images
    image = db.Column(db.String(500))
    card_gradient = db.Column(db.String(50))  # For UI
    
    # Stats (cached)
    enrollments = db.Column(db.Integer, default=0)
    lessons = db.Column(db.Integer, default=0)
    rating = db.Column(Float, default=0)
    notification_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    chapters = db.relationship("CourseChapter", backref="course_rel", cascade="all, delete-orphan", foreign_keys="CourseChapter.course_id")
    related_courses_list = db.relationship("RelatedCourse", backref="course_ref", foreign_keys="RelatedCourse.course_id")
    enrollments_list = db.relationship("Enrollment", backref="course_rel", cascade="all, delete-orphan")
    batches = db.relationship("Batch", backref="course_ref", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", backref="course_ref", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="course_ref", cascade="all, delete-orphan")
    course_progress = db.relationship("CourseProgress", backref="course_ref", cascade="all, delete-orphan")
    course_reviews = db.relationship("CourseReview", backref="course_ref", cascade="all, delete-orphan")

class CourseChapter(db.Model):
    __tablename__ = "course_chapter"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    description = db.Column(Text)
    is_scorm_package = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    lessons = db.relationship("CourseLesson", backref="chapter_ref", cascade="all, delete-orphan", foreign_keys="CourseLesson.chapter_id")

class CourseLesson(db.Model):
    __tablename__ = "course_lesson"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    chapter_id = db.Column(db.Integer, ForeignKey('course_chapter.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    
    # Content
    body = db.Column(Text)  # HTML content
    youtube = db.Column(db.String(500))  # YouTube video ID
    
    # Assessment
    quiz_id = db.Column(db.Integer, ForeignKey('lms_quiz.id'))
    question_id = db.Column(db.Integer, ForeignKey('lms_question.id'))
    
    # Settings
    status = db.Column(db.String(20), default="Draft")
    duration = db.Column(db.Integer, default=0)  # In minutes
    
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    quiz = db.relationship("Quiz", backref="lesson_quiz")
    question = db.relationship("Question", backref="lesson_question")

class RelatedCourse(db.Model):
    __tablename__ = "related_courses"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    related_course_id = db.Column(db.Integer, ForeignKey('lms_course.id'))
    
    related = db.relationship("Course", foreign_keys=[related_course_id])

# ==================== ENROLLMENT & BATCHES ====================
class Enrollment(db.Model):
    __tablename__ = "lms_enrollment"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    
    # Progress tracking
    progress = db.Column(Float, default=0)  # Percentage
    current_lesson_id = db.Column(db.Integer)  # Last accessed lesson
    status = db.Column(db.String(50), default=EnrollmentStatus.ACTIVE)
    
    # Milestones
    enrolled_on = db.Column(DateTime, default=func.now())
    completed_on = db.Column(DateTime)
    certificate_issued = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('member_id', 'course_id', name='unique_enrollment'),)

class Batch(db.Model):
    __tablename__ = "lms_batch"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    description = db.Column(Text)
    
    # Batch details
    status = db.Column(db.String(50), default="Not Started")
    start_date = db.Column(DateTime, nullable=False)
    end_date = db.Column(DateTime, nullable=False)
    max_students = db.Column(db.Integer)
    
    # Timetable
    timetable_template_id = db.Column(db.Integer, ForeignKey('lms_timetable_template.id'))
    
    # Settings
    published = db.Column(db.Boolean, default=False)
    enable_self_learning = db.Column(db.Boolean, default=False)
    enable_certification = db.Column(db.Boolean, default=True)
    paid = db.Column(db.Boolean, default=False)
    batch_price = db.Column(Float, default=0)
    
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    batch_details = db.Column(db.String(500))  # JSON: course titles and instructors
    batch_enrollments = db.relationship("BatchEnrollment", backref="batch_ref", cascade="all, delete-orphan")
    timetable = db.relationship("TimetableTemplate", backref="batch_timetables")
    live_classes = db.relationship("LiveClass", backref="batch_ref", cascade="all, delete-orphan")

class BatchEnrollment(db.Model):
    __tablename__ = "lms_batch_enrollment"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    batch_id = db.Column(db.Integer, ForeignKey('lms_batch.id'), nullable=False)
    
    # Payment
    payment_id = db.Column(db.Integer, ForeignKey('lms_payment.id'))
    paid = db.Column(db.Boolean, default=False)
    paid_on = db.Column(DateTime)
    
    # Enrollment tracking
    source = db.Column(db.String(100))  # How they enrolled (direct, coupon, etc.)
    enrolled_on = db.Column(DateTime, default=func.now())
    
    __table_args__ = (db.UniqueConstraint('member_id', 'batch_id', name='unique_batch_enrollment'),)

class BatchFeedback(db.Model):
    __tablename__ = "lms_batch_feedback"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    batch_id = db.Column(db.Integer, ForeignKey('lms_batch.id'), nullable=False)
    
    rating = db.Column(db.Integer)  # 1-5
    feedback = db.Column(Text)
    submitted_on = db.Column(DateTime, default=func.now())

# ==================== ASSESSMENTS ====================
class Quiz(db.Model):
    __tablename__ = "lms_quiz"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    
    # Quiz settings
    passing_percentage = db.Column(Float, default=70)
    max_attempts = db.Column(db.Integer, default=1)  # -1 for unlimited
    duration_minutes = db.Column(db.Integer)
    show_answers = db.Column(db.Boolean, default=True)
    randomize_questions = db.Column(db.Boolean, default=False)
    one_question_per_page = db.Column(db.Boolean, default=False)
    
    # Meta
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    questions = db.relationship("QuizQuestion", backref="quiz_ref", cascade="all, delete-orphan")
    submissions = db.relationship("QuizSubmission", backref="quiz_ref", cascade="all, delete-orphan")

class QuizQuestion(db.Model):
    __tablename__ = "lms_quiz_question"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, ForeignKey('lms_quiz.id'), nullable=False)
    question_id = db.Column(db.Integer, ForeignKey('lms_question.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    
    # Relationships
    question = db.relationship("Question", backref="quiz_questions")

class Question(db.Model):
    __tablename__ = "lms_question"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    question_type = db.Column(db.String(50), default=QuizType.SINGLE_CHOICE)  # single_select, multiple_select, short_answer, essay
    marks = db.Column(Float, default=1)
    hint = db.Column(Text)
    explanation = db.Column(Text)
    is_mandatory = db.Column(db.Boolean, default=True)
    
    # Relationships
    options = db.relationship("Option", backref="question_ref", cascade="all, delete-orphan")

class Option(db.Model):
    __tablename__ = "lms_option"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, ForeignKey('lms_question.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)
    is_correct = db.Column(db.Boolean, default=False)

class QuizSubmission(db.Model):
    __tablename__ = "lms_quiz_submission"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, ForeignKey('lms_quiz.id'), nullable=False)
    
    # Results
    score = db.Column(Float)
    percentage = db.Column(Float)
    is_pass = db.Column(db.Boolean)
    
    # Timing
    started_on = db.Column(DateTime, default=func.now())
    submitted_on = db.Column(DateTime)
    time_taken_seconds = db.Column(db.Integer)
    
    # Relationships
    quiz_result = db.relationship("QuizResult", backref="submission_ref", cascade="all, delete-orphan")

class QuizResult(db.Model):
    __tablename__ = "lms_quiz_result"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, ForeignKey('lms_quiz_submission.id'), nullable=False)
    question_id = db.Column(db.Integer, ForeignKey('lms_question.id'), nullable=False)
    
    # Answer
    answer = db.Column(Text)  # User's answer
    correct = db.Column(db.Boolean)
    marks_obtained = db.Column(Float)

# ==================== ASSIGNMENTS ====================
class Assignment(db.Model):
    __tablename__ = "lms_assignment"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    
    # Details
    question = db.Column(Text, nullable=False)  # Assignment prompt
    description = db.Column(Text)
    
    # Type & Submission
    assignment_type = db.Column(db.String(50))  # File upload, code, text, etc.
    answer_template = db.Column(Text)  # Template for students
    
    # Due date & grading
    due_date = db.Column(DateTime)
    total_marks = db.Column(Float, default=100)
    published = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    submissions = db.relationship("AssignmentSubmission", backref="assignment_ref", cascade="all, delete-orphan")

class AssignmentSubmission(db.Model):
    __tablename__ = "lms_assignment_submission"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, ForeignKey('lms_assignment.id'), nullable=False)
    
    # Submission
    submission_text = db.Column(Text)
    submission_file = db.Column(db.String(500))  # File path
    submitted_on = db.Column(DateTime, default=func.now())
    is_submitted = db.Column(db.Boolean, default=False)
    
    # Grading
    graded_on = db.Column(DateTime)
    is_graded = db.Column(db.Boolean, default=False)
    marks_obtained = db.Column(Float)
    feedback = db.Column(Text)

# ==================== CERTIFICATES & CREDENTIALS ====================
class Certificate(db.Model):
    __tablename__ = "lms_certificate"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    
    # Issued for
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'))
    batch_id = db.Column(db.Integer, ForeignKey('lms_batch.id'))
    
    # Certificate details
    name = db.Column(db.String(255))  # Certificate title
    template = db.Column(db.String(500))  # Template ID
    issue_date = db.Column(DateTime, default=func.now())
    expiry_date = db.Column(DateTime)
    
    # Verification
    certificate_number = db.Column(db.String(255), unique=True)
    qr_code = db.Column(db.String(500))
    certificate_hash = db.Column(db.String(500))  # For verification
    
    # Status
    status = db.Column(db.String(50), default="Active")  # Active, Revoked, Expired
    
    created_at = db.Column(DateTime, default=func.now())

class CertificateEvaluation(db.Model):
    __tablename__ = "lms_certificate_evaluation"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    
    # Evaluation criteria
    required_completion_percentage = db.Column(Float, default=80)
    required_quiz_score = db.Column(Float)
    required_assignment_score = db.Column(Float)
    
    # Status
    is_eligible = db.Column(db.Boolean, default=False)
    evaluation_date = db.Column(DateTime, default=func.now())

# ==================== LIVE CLASSES ====================
class LiveClass(db.Model):
    __tablename__ = "lms_live_class"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    batch_id = db.Column(db.Integer, ForeignKey('lms_batch.id'), nullable=False)
    
    # Meeting details
    meeting_url = db.Column(db.String(500))  # Zoom/Meet link
    meeting_id = db.Column(db.String(100))
    meeting_password = db.Column(db.String(100))
    recording_url = db.Column(db.String(500))  # Post-event recording
    
    # Scheduling
    scheduled_at = db.Column(DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    # Settings
    description = db.Column(Text)
    is_recorded = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(DateTime, default=func.now())
    
    # Relationships
    participants = db.relationship("LiveClassParticipant", backref="live_class", cascade="all, delete-orphan")

class LiveClassParticipant(db.Model):
    __tablename__ = "lms_live_class_participant"
    id = db.Column(db.Integer, primary_key=True)
    live_class_id = db.Column(db.Integer, ForeignKey('lms_live_class.id'), nullable=False)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    
    # Attendance
    joined_at = db.Column(DateTime)
    left_at = db.Column(DateTime)
    attended = db.Column(db.Boolean, default=False)

# ==================== REVIEWS & RATINGS ====================
class CourseReview(db.Model):
    __tablename__ = "lms_course_review"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    
    # Review
    rating = db.Column(db.Integer)  # 1-5
    title = db.Column(db.String(255))
    review_text = db.Column(Text)
    
    # Engagement
    helpful_count = db.Column(db.Integer, default=0)
    unhelpful_count = db.Column(db.Integer, default=0)
    
    submitted_on = db.Column(DateTime, default=func.now())
    
    __table_args__ = (db.UniqueConstraint('course_id', 'member_id'),)

# ==================== PROGRESS TRACKING ====================
class CourseProgress(db.Model):
    __tablename__ = "lms_course_progress"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'), nullable=False)
    
    progress_percentage = db.Column(Float, default=0)
    last_lesson_id = db.Column(db.Integer)
    last_accessed = db.Column(DateTime, default=func.now(), onupdate=func.now())
    completed = db.Column(db.Boolean, default=False)

# ==================== TIMETABLE ====================
class TimetableTemplate(db.Model):
    __tablename__ = "lms_timetable_template"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(Text)
    
    timetable_details = db.Column(db.String(500))  # JSON: schedule details

class TimetableLegend(db.Model):
    __tablename__ = "lms_timetable_legend"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50))
    color = db.Column(db.String(20))

# ==================== PAYMENTS ====================
class Payment(db.Model):
    __tablename__ = "lms_payment"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    
    # Payment details
    amount = db.Column(Float, nullable=False)
    currency = db.Column(db.String(10), default="USD")
    payment_method = db.Column(db.String(50))  # Card, UPI, PayPal, etc.
    
    # Transaction
    transaction_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.String(50), default="Pending")  # Pending, Completed, Failed
    
    # What's being paid for
    course_id = db.Column(db.Integer, ForeignKey('lms_course.id'))
    batch_id = db.Column(db.Integer, ForeignKey('lms_batch.id'))
    coupon_code = db.Column(db.String(100))
    
    created_on = db.Column(DateTime, default=func.now())
    completed_on = db.Column(DateTime)

class Coupon(db.Model):
    __tablename__ = "lms_coupon"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(Float, default=0)
    discount_amount = db.Column(Float, default=0)
    max_usage = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(DateTime)
    valid_until = db.Column(DateTime)
    
    # Relationships
    applicable_items = db.relationship("CouponItem", backref="coupon_ref", cascade="all, delete-orphan")

class CouponItem(db.Model):
    __tablename__ = "lms_coupon_item"
    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(db.Integer, ForeignKey('lms_coupon.id'), nullable=False)
    item_type = db.Column(db.String(50))  # Course, Batch, etc.
    item_id = db.Column(db.Integer)

# ==================== SETTINGS ====================
class LmsSettings(db.Model):
    __tablename__ = "lms_settings"
    id = db.Column(db.Integer, primary_key=True)
    settings_key = db.Column(db.String(255), unique=True)
    settings_value = db.Column(Text)  # JSON if needed

class ZoomSettings(db.Model):
    __tablename__ = "zoom_settings"
    id = db.Column(db.Integer, primary_key=True)
    zoom_api_key = db.Column(db.String(500))
    zoom_api_secret = db.Column(db.String(500))
    enable_zoom_integration = db.Column(db.Boolean, default=False)

class GoogleMeetSettings(db.Model):
    __tablename__ = "lms_google_meet_settings"
    id = db.Column(db.Integer, primary_key=True)
    google_api_key = db.Column(db.String(500))
    enable_google_meet = db.Column(db.Boolean, default=False)
