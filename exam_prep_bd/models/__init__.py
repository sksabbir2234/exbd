from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database.session import Base


# ==================== ENUMS ====================

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class ExamStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto_submitted"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


# ==================== AUTH & USERS ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    exam_attempts = relationship("ExamAttempt", back_populates="user", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    article_views = relationship("ArticleView", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_users_email_active', 'email', 'is_active'),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    user = relationship("User", back_populates="refresh_tokens")


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    code = Column(String(6), nullable=False)
    purpose = Column(String(50))  # verify_email, reset_password, login
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==================== CONTENT STRUCTURE ====================

class StudentType(Base):
    __tablename__ = "student_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "BCS", "Bank Jobs", "Primary Teacher"
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    folders = relationship("Folder", back_populates="student_type")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    student_type_id = Column(Integer, ForeignKey("student_types.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student_type = relationship("StudentType", back_populates="folders")
    parent = relationship("Folder", remote_side=[id], backref="children")
    topics = relationship("Topic", back_populates="folder", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="folder", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_folders_student_type_parent', 'student_type_id', 'parent_id'),
    )


# ==================== CONTENT: TOPICS, LESSONS, FLASHCARDS ====================

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    folder = relationship("Folder", back_populates="topics")
    lessons = relationship("Lesson", back_populates="topic", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="topic", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_topics_folder_active', 'folder_id', 'is_active'),
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"))
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"))
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True)
    content = Column(Text)  # HTML content
    summary = Column(Text)
    thumbnail_url = Column(String(500))
    video_url = Column(String(500))
    duration_minutes = Column(Integer)
    order_index = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    folder = relationship("Folder", back_populates="lessons")
    topic = relationship("Topic", back_populates="lessons")

    __table_args__ = (
        Index('ix_lessons_topic_published', 'topic_id', 'is_published'),
    )


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    hint = Column(Text)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    topic = relationship("Topic", back_populates="flashcards")


# ==================== EXAM SYSTEM ====================

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"))
    question_text = Column(Text, nullable=False)
    explanation = Column(Text)
    difficulty = Column(String(20), default="medium")
    question_type = Column(String(20), default="mcq")  # mcq, true_false, descriptive
    marks = Column(Float, default=1.0)
    negative_marks = Column(Float, default=0.0)
    time_limit_seconds = Column(Integer)  # Per-question time limit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    topic = relationship("Topic", back_populates="questions")
    options = relationship("MCQOption", back_populates="question", cascade="all, delete-orphan")
    exam_questions = relationship("ExamQuestion", back_populates="question", cascade="all, delete-orphan")
    student_answers = relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_questions_topic_active', 'topic_id', 'is_active'),
    )


class MCQOption(Base):
    __tablename__ = "mcq_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    question = relationship("Question", back_populates="options")

    __table_args__ = (
        Index('ix_options_question_correct', 'question_id', 'is_correct'),
    )


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True)
    description = Column(Text)
    exam_type = Column(String(50))  # model_test, previous_year, chapter_test
    total_marks = Column(Float, default=100.0)
    passing_marks = Column(Float)
    duration_minutes = Column(Integer, default=60)
    negative_marking_enabled = Column(Boolean, default=False)
    status = Column(SQLEnum(ExamStatus), default=ExamStatus.DRAFT)
    is_premium = Column(Boolean, default=False)
    show_results_immediately = Column(Boolean, default=True)
    randomize_questions = Column(Boolean, default=True)
    randomize_options = Column(Boolean, default=True)
    proctoring_enabled = Column(Boolean, default=False)  # Anti-cheat features
    max_tab_switches = Column(Integer, default=3)
    thumbnail_url = Column(String(500))
    scheduled_start_at = Column(DateTime(timezone=True))
    scheduled_end_at = Column(DateTime(timezone=True))
    attempt_count = Column(Integer, default=0)
    average_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    created_by = Column(Integer, ForeignKey("users.id"))

    exam_questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_exams_status_premium', 'status', 'is_premium'),
        Index('ix_exams_schedule', 'scheduled_start_at', 'scheduled_end_at'),
    )


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, default=0)
    marks = Column(Float)
    negative_marks = Column(Float)
    time_limit_seconds = Column(Integer)

    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")

    __table_args__ = (
        Index('ix_exam_questions_unique', 'exam_id', 'question_id', unique=True),
    )


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(AttemptStatus), default=AttemptStatus.ONGOING)
    total_score = Column(Float)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    unanswered = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True))
    time_taken_seconds = Column(Integer)
    tab_switch_count = Column(Integer, default=0)
    proctoring_violations = Column(Integer, default=0)
    device_info = Column(String(500))
    ip_address = Column(String(45))

    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", back_populates="exam_attempts")
    answers = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_attempts_exam_user', 'exam_id', 'user_id'),
        Index('ix_attempts_status', 'status'),
    )


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("mcq_options.id"))
    is_correct = Column(Boolean)
    time_taken_seconds = Column(Integer)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("Question", back_populates="student_answers")
    selected_option = relationship("MCQOption")

    __table_args__ = (
        Index('ix_answers_attempt_question', 'attempt_id', 'question_id', unique=True),
    )


# ==================== NEWS & SCRAPER ====================

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    rss_feed_url = Column(String(500))
    category = Column(String(100))
    language = Column(String(20), default="bn")
    is_active = Column(Boolean, default=True)
    scrape_priority = Column(Integer, default=5)
    last_scraped_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship("Article", back_populates="source")
    scrape_logs = relationship("ScrapeLog", back_populates="source")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("Category", remote_side=[id], backref="children")
    articles = relationship("Article", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    articles = relationship("Article", secondary="article_tags", back_populates="tags")


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    title = Column(String(500), nullable=False)
    slug = Column(String(550), index=True)
    summary = Column(Text)
    content = Column(Text)
    author = Column(String(200))
    published_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    image_url = Column(String(500))
    source_url = Column(String(500), unique=True)
    language = Column(String(20), default="bn")
    view_count = Column(Integer, default=0)
    ai_summary = Column(Text)
    ai_keywords = Column(Text)  # JSON array
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    source = relationship("Source", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary="article_tags", back_populates="articles")
    views = relationship("ArticleView", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_articles_published_active', 'published_at', 'is_active'),
        Index('ix_articles_source_scraped', 'source_id', 'scraped_at'),
    )


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"))
    status = Column(String(20))  # success, failed, partial
    articles_found = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)

    source = relationship("Source", back_populates="scrape_logs")


class ArticleView(Base):
    __tablename__ = "article_views"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    referrer = Column(String(500))

    article = relationship("Article", back_populates="views")
    user = relationship("User", back_populates="article_views")

    __table_args__ = (
        Index('ix_views_article_time', 'article_id', 'viewed_at'),
    )


# ==================== JOBS ====================

class JobCircular(Base):
    __tablename__ = "job_circulars"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True)
    organization = Column(String(200), nullable=False)
    post_name = Column(String(200))
    vacancy_count = Column(Integer)
    application_deadline = Column(DateTime(timezone=True))
    job_location = Column(String(200))
    salary_range = Column(String(100))
    education_required = Column(Text)
    experience_required = Column(String(200))
    age_limit_min = Column(Integer)
    age_limit_max = Column(Integer)
    description = Column(Text)
    application_url = Column(String(500))
    circular_pdf_url = Column(String(500))
    source_url = Column(String(500))
    source_type = Column(String(50))  # scraped, manual
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('ix_jobs_deadline_active', 'application_deadline', 'is_active'),
    )


# ==================== COMMERCE: COURSES, BOOKS, ORDERS ====================

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True)
    description = Column(Text)
    thumbnail_url = Column(String(500))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    price = Column(Float, nullable=False)
    discount_price = Column(Float)
    currency = Column(String(10), default="BDT")
    duration_hours = Column(Float)
    lecture_count = Column(Integer, default=0)
    student_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
    progress_percentage = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    order_id = Column(Integer, ForeignKey("orders.id"))

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    __table_args__ = (
        Index('ix_enrollments_user_course', 'user_id', 'course_id', unique=True),
    )


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True)
    author = Column(String(200))
    publisher = Column(String(200))
    description = Column(Text)
    cover_image_url = Column(String(500))
    pdf_url = Column(String(500))
    price = Column(Float, nullable=False)
    discount_price = Column(Float)
    currency = Column(String(10), default="BDT")
    page_count = Column(Integer)
    edition = Column(String(50))
    publication_year = Column(Integer)
    isbn = Column(String(20))
    is_published = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_number = Column(String(50), unique=True, index=True)
    subtotal = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String(10), default="BDT")
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50))
    payment_transaction_id = Column(String(200))
    payment_data = Column(Text)  # JSON response from SSLCommerz
    status = Column(String(20), default="pending")  # pending, completed, cancelled, refunded
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="orders")
    enrollments = relationship("Enrollment", back_populates="order")

    __table_args__ = (
        Index('ix_orders_user_status', 'user_id', 'status'),
    )


# ==================== BLOG ====================

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True)
    content = Column(Text)
    excerpt = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    thumbnail_url = Column(String(500))
    category = Column(String(100))
    tags = Column(Text)  # JSON array
    is_published = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    seo_title = Column(String(70))
    seo_description = Column(String(160))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    comments = relationship("Comment", back_populates="blog_post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    blog_post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    blog_post = relationship("BlogPost", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")


# ==================== ANALYTICS ====================

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(Text)  # JSON
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")

    __table_args__ = (
        Index('ix_activity_user_time', 'user_id', 'created_at'),
        Index('ix_activity_action_time', 'action', 'created_at'),
    )
