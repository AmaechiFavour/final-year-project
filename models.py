from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, func, Text
from sqlalchemy import ForeignKey
from datetime import datetime

db = SQLAlchemy()

# ==================== USER MANAGEMENT ====================
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(Text)
    profile_picture = db.Column(db.String(500))
    date_created = db.Column(DateTime, default=func.now())
    last_login = db.Column(DateTime)
    is_active = db.Column(db.Boolean, default=True)
    account = db.Column(db.String(20), default='student', nullable=False)  # 'student', 'teacher', 'admin'
    
    # Relationships
    courses_created = db.relationship("Course", backref="instructor", foreign_keys="Course.instructor_id")
    enrollments = db.relationship("Enrollment", backref="student", foreign_keys="Enrollment.student_id")
    submissions = db.relationship("Assignment_Submission", backref="student", foreign_keys="Assignment_Submission.student_id")
    quiz_attempts = db.relationship("Quiz_Attempt", backref="student", foreign_keys="Quiz_Attempt.student_id")
    lesson_progress = db.relationship("Lesson_Progress", backref="student", foreign_keys="Lesson_Progress.student_id")


# ==================== COURSE MANAGEMENT ====================
class Course(db.Model):
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    description = db.Column(Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    thumbnail = db.Column(db.String(500))
    price = db.Column(db.Float, default=0)
    summary = db.Column(db.String(1000))
    requirements = db.Column(Text)
    learning_outcomes = db.Column(Text)
    duration_hours = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(50), default='beginner')  # beginner, intermediate, advanced
    language = db.Column(db.String(50), default='English')
    
    instructor_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    is_published = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Relationships
    lessons = db.relationship("Lesson", backref="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", backref="course", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", backref="course", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="course", cascade="all, delete-orphan")
    chapters = db.relationship("Chapter", backref="course_rel", cascade="all, delete-orphan")
    
    @property
    def total_lessons(self):
        return len(self.lessons)
    
    @property
    def total_students(self):
        return len(self.enrollments)


# ==================== ENROLLMENT MANAGEMENT ====================
class Enrollment(db.Model):
    __tablename__ = "enrollment"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(DateTime, default=func.now())
    completed_at = db.Column(DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Float, default=0)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_student_course'),)


# ==================== LESSON MANAGEMENT ====================
class Lesson(db.Model):
    __tablename__ = "lesson"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    chapter_id = db.Column(db.Integer, ForeignKey('chapter.id'), nullable=True)  # Optional, for chapter-based organization
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    order = db.Column(db.Integer)
    content = db.Column(Text)  # HTML content
    video_url = db.Column(db.String(500))  # Path to uploaded video
    video_duration = db.Column(db.Integer)  # in seconds
    resources = db.relationship("Lesson_Resource", backref="lesson", cascade="all, delete-orphan")
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    is_published = db.Column(db.Boolean, default=True)
    
    # Relationships
    lesson_progress = db.relationship("Lesson_Progress", backref="lesson", cascade="all, delete-orphan")


class Lesson_Resource(db.Model):
    __tablename__ = "lesson_resource"
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, ForeignKey('lesson.id'), nullable=False)
    title = db.Column(db.String(200))
    file_path = db.Column(db.String(500))  # Path to uploaded file
    resource_type = db.Column(db.String(50))  # pdf, document, image, etc.
    created_at = db.Column(DateTime, default=func.now())


class Lesson_Progress(db.Model):
    __tablename__ = "lesson_progress"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, ForeignKey('lesson.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    video_watched_seconds = db.Column(db.Integer, default=0)
    completed_at = db.Column(DateTime)
    started_at = db.Column(DateTime, default=func.now())
    last_accessed_at = db.Column(DateTime, default=func.now(), onupdate=func.now())


# ==================== QUIZ MANAGEMENT ====================
class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    order = db.Column(db.Integer)
    passing_percentage = db.Column(db.Float, default=70)
    total_questions = db.Column(db.Integer)
    duration_minutes = db.Column(db.Integer)
    show_correct_answers = db.Column(db.Boolean, default=True)
    attempts_allowed = db.Column(db.Integer, default=1)  # -1 for unlimited
    created_at = db.Column(DateTime, default=func.now())
    is_published = db.Column(db.Boolean, default=True)
    
    # Relationships
    questions = db.relationship("Quiz_Question", backref="quiz", cascade="all, delete-orphan")
    attempts = db.relationship("Quiz_Attempt", backref="quiz", cascade="all, delete-orphan")


class Quiz_Question(db.Model):
    __tablename__ = "quiz_question"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')  # multiple_choice, true_false, short_answer
    order = db.Column(db.Integer)
    marks = db.Column(db.Float, default=1)
    
    # Relationships
    options = db.relationship("Quiz_Option", backref="question", cascade="all, delete-orphan")
    answers = db.relationship("Quiz_Answer", backref="question", cascade="all, delete-orphan")


class Quiz_Option(db.Model):
    __tablename__ = "quiz_option"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(Text, nullable=False)
    order = db.Column(db.Integer)
    is_correct = db.Column(db.Boolean, default=False)


class Quiz_Attempt(db.Model):
    __tablename__ = "quiz_attempt"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Float)
    percentage = db.Column(db.Float)
    is_passed = db.Column(db.Boolean)
    started_at = db.Column(DateTime, default=func.now())
    submitted_at = db.Column(DateTime)
    time_taken_seconds = db.Column(db.Integer)
    
    # Relationships
    answers = db.relationship("Quiz_Answer", backref="attempt", cascade="all, delete-orphan")


class Quiz_Answer(db.Model):
    __tablename__ = "quiz_answer"
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, ForeignKey('quiz_question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, ForeignKey('quiz_option.id'))
    text_answer = db.Column(Text)
    is_correct = db.Column(db.Boolean)
    marks_obtained = db.Column(db.Float)


# ==================== ASSIGNMENT MANAGEMENT ====================
class Assignment(db.Model):
    __tablename__ = "assignment"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    instructions = db.Column(Text)
    order = db.Column(db.Integer)
    total_marks = db.Column(db.Float, default=100)
    due_date = db.Column(DateTime)
    created_at = db.Column(DateTime, default=func.now())
    is_published = db.Column(db.Boolean, default=True)
    
    # Relationships
    submissions = db.relationship("Assignment_Submission", backref="assignment", cascade="all, delete-orphan")


class Assignment_Submission(db.Model):
    __tablename__ = "assignment_submission"
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    submission_text = db.Column(Text)
    file_path = db.Column(db.String(500))
    submitted_at = db.Column(DateTime, default=func.now())
    is_submitted = db.Column(db.Boolean, default=False)
    is_graded = db.Column(db.Boolean, default=False)
    marks_obtained = db.Column(db.Float)
    feedback = db.Column(Text)
    graded_at = db.Column(DateTime)
    graded_by_id = db.Column(db.Integer, ForeignKey('user.id'))
    
    # Relationships - only define the graded_by relationship (assignment already has submissions backref)
    graded_by = db.relationship("User", backref="graded_submissions", foreign_keys=[graded_by_id])


# ==================== ANNOUNCEMENTS ====================
class Announcement(db.Model):
    __tablename__ = "announcement"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(Text)
    created_by_id = db.Column(db.Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.now())
    
    course = db.relationship("Course", backref="announcements")
    created_by = db.relationship("User", backref="announcements")


# ==================== CHAPTER MANAGEMENT ====================
class Chapter(db.Model):
    __tablename__ = "chapter"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    order = db.Column(db.Integer, default=1)
    created_at = db.Column(DateTime, default=func.now())
    
    # Relationships - use primaryjoin to explicitly specify the join condition
    lessons = db.relationship("Lesson", backref="chapter", foreign_keys="Lesson.chapter_id", cascade="all, delete-orphan")


# ==================== BATCH MANAGEMENT ====================
class Batch(db.Model):
    __tablename__ = "batch"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    start_date = db.Column(DateTime, nullable=False)
    end_date = db.Column(DateTime, nullable=False)
    max_students = db.Column(db.Integer)
    instructor_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(DateTime, default=func.now())
    
    # Relationships
    enrollments = db.relationship("BatchEnrollment", backref="batch", cascade="all, delete-orphan")
    live_classes = db.relationship("LiveClass", backref="batch", cascade="all, delete-orphan")
    instructor_rel = db.relationship("User", backref="created_batches", foreign_keys=[instructor_id])


class BatchEnrollment(db.Model):
    __tablename__ = "batch_enrollment"
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, ForeignKey('batch.id'), nullable=False)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    enrolled_at = db.Column(DateTime, default=func.now())
    completed_at = db.Column(DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Float, default=0)
    
    student_rel = db.relationship("User", backref="batch_enrollments", foreign_keys=[student_id])
    
    __table_args__ = (db.UniqueConstraint('batch_id', 'student_id', name='unique_batch_student'),)


# ==================== CERTIFICATE MANAGEMENT ====================
class Certificate(db.Model):
    __tablename__ = "certificate"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    certificate_number = db.Column(db.String(100), unique=True)
    completion_date = db.Column(DateTime, nullable=False)
    issued_at = db.Column(DateTime, default=func.now())
    is_issued = db.Column(db.Boolean, default=True)
    hash = db.Column(db.String(500))  # For certificate verification
    
    # Relationships
    student_rel = db.relationship("User", backref="certificates", foreign_keys=[student_id])
    course_rel = db.relationship("Course", backref="certificates", foreign_keys=[course_id])


# ==================== DISCUSSION MANAGEMENT ====================
class Discussion(db.Model):
    __tablename__ = "discussion"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    created_by_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(Text, nullable=False)
    is_solved = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    replies = db.relationship("DiscussionReply", backref="discussion", cascade="all, delete-orphan")
    course_rel = db.relationship("Course", backref="discussions")
    created_by = db.relationship("User", backref="discussions")


class DiscussionReply(db.Model):
    __tablename__ = "discussion_reply"
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, ForeignKey('discussion.id'), nullable=False)
    created_by_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    content = db.Column(Text, nullable=False)
    is_marked_as_answer = db.Column(db.Boolean, default=False)
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    upvotes = db.Column(db.Integer, default=0)
    
    # Relationships
    created_by = db.relationship("User", backref="discussion_replies")


# ==================== COURSE REVIEW MANAGEMENT ====================
class CourseReview(db.Model):
    __tablename__ = "course_review"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id'), nullable=False)
    student_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    review_text = db.Column(Text)
    created_at = db.Column(DateTime, default=func.now())
    updated_at = db.Column(DateTime, default=func.now(), onupdate=func.now())
    helpful_count = db.Column(db.Integer, default=0)
    
    # Relationships
    course_rel = db.relationship("Course", backref="reviews", foreign_keys=[course_id])
    student_rel = db.relationship("User", backref="course_reviews", foreign_keys=[student_id])
    
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='unique_course_student_review'),)


# ==================== LIVE CLASS MANAGEMENT ====================
class LiveClass(db.Model):
    __tablename__ = "live_class"
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, ForeignKey('batch.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    scheduled_at = db.Column(DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer)
    zoom_link = db.Column(db.String(500))
    recording_url = db.Column(db.String(500))
    created_at = db.Column(DateTime, default=func.now())


# Keep old model name for compatibility
class Enrolled(Enrollment):
    pass