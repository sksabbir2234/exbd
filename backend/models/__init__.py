"""
Database Models - Exam Prep BD
Merged schema from examWebsite, cse-pro, and scrapper
"""

from datetime import datetime
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, Float, ForeignKey, 
    Index, UniqueConstraint, Enum as SQLEnum, JSON, Table, Column
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from database.connection import Base


# ============== ENUMS ==============

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    DESCRIPTIVE = "descriptive"


class ExamStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExamAttemptStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto_submitted"


class ArticleCategory(str, enum.Enum):
    NATIONAL = "national"
    INTERNATIONAL = "international"
    POLITICS = "politics"
    ECONOMY = "economy"
    SPORTS = "sports"
    EDUCATION = "education"
    JOB_NEWS = "job_news"


# ============== ASSOCIATION TABLES ==============

exam_questions = Table(
    "exam_questions",
    Base.metadata,
    Column("exam_id", ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True),
    Column("question_id", ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("marks", Integer, default=1),
    Column("order", Integer, default=0),
)

lesson_tags = Table(
    "lesson_tags",
    Base.metadata,
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


# ============== USER & AUTH MODELS ==============

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.STUDENT)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    exam_attempts: Mapped[list["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="student"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="student"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user"
    )
    article_views: Mapped[list["ArticleView"]] = relationship(
        "ArticleView", back_populates="user"
    )
    
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class OTPCode(Base):
    __tablename__ = "otp_codes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50))  # verify_email, reset_password, etc.
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ============== CONTENT STRUCTURE MODELS ==============

class Folder(Base):
    __tablename__ = "folders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("folders.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    children: Mapped[list["Folder"]] = relationship(
        "Folder", backref="parent", remote_side=[id]
    )
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="folder")
    access_rules: Mapped[list["FolderAccess"]] = relationship(
        "FolderAccess", back_populates="folder"
    )


class StudentType(Base):
    __tablename__ = "student_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    folder_access: Mapped[list["FolderAccess"]] = relationship(
        "FolderAccess", back_populates="student_type"
    )


class FolderAccess(Base):
    __tablename__ = "folder_access"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False
    )
    student_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("student_types.id", ondelete="CASCADE"), nullable=False
    )
    access_level: Mapped[str] = mapped_column(String(50), default="read")
    
    # Relationships
    folder: Mapped["Folder"] = relationship("Folder", back_populates="access_rules")
    student_type: Mapped["StudentType"] = relationship("StudentType", back_populates="folder_access")
    
    __table_args__ = (
        UniqueConstraint("folder_id", "student_type_id", name="uq_folder_student_type"),
    )


class Topic(Base):
    __tablename__ = "topics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    folder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    folder: Mapped["Folder"] = relationship("Folder", back_populates="topics")
    lessons: Mapped[list["Lesson"]] = relationship("Lesson", back_populates="topic")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="topic")


# ============== LESSON & FLASHCARD MODELS (from cse-pro) ==============

class Lesson(Base):
    __tablename__ = "lessons"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="beginner")
    estimated_duration: Mapped[int] = mapped_column(Integer)  # minutes
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="lessons")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=lesson_tags)
    flashcards: Mapped[list["Flashcard"]] = relationship(
        "Flashcard", back_populates="lesson", cascade="all, delete-orphan"
    )


class Flashcard(Base):
    __tablename__ = "flashcards"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(String(1000), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="flashcards")


# ============== QUESTION & EXAM MODELS (from examWebsite) ==============

class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType), default=QuestionType.MCQ
    )
    explanation: Mapped[str | None] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="medium")
    marks: Mapped[int] = mapped_column(Integer, default=1)
    negative_marks: Mapped[float] = mapped_column(Float, default=0.0)
    time_limit: Mapped[int | None] = mapped_column(Integer)  # seconds per question
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="questions")
    options: Mapped[list["MCQOption"]] = relationship(
        "MCQOption", back_populates="question", cascade="all, delete-orphan"
    )
    exams: Mapped[list["Exam"]] = relationship(
        "Exam", secondary=exam_questions, back_populates="questions"
    )


class MCQOption(Base):
    __tablename__ = "mcq_options"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="options")


class Exam(Base):
    __tablename__ = "exams"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    exam_type: Mapped[str] = mapped_column(String(100))  # model_test, job_exam, etc.
    total_marks: Mapped[int] = mapped_column(Integer, default=100)
    duration: Mapped[int] = mapped_column(Integer)  # minutes
    passing_marks: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[ExamStatus] = mapped_column(
        SQLEnum(ExamStatus), default=ExamStatus.DRAFT
    )
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_proctoring: Mapped[bool] = mapped_column(Boolean, default=False)
    max_tab_switches: Mapped[int | None] = mapped_column(Integer, default=3)
    require_fullscreen: Mapped[bool] = mapped_column(Boolean, default=False)
    show_results: Mapped[bool] = mapped_column(Boolean, default=True)
    randomize_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    randomize_options: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    questions: Mapped[list["Question"]] = relationship(
        "Question", secondary=exam_questions, back_populates="exams"
    )
    attempts: Mapped[list["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="exam", cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ExamAttemptStatus] = mapped_column(
        SQLEnum(ExamAttemptStatus), default=ExamAttemptStatus.ONGOING
    )
    total_score: Mapped[float | None] = mapped_column(Float)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    wrong_answers: Mapped[int] = mapped_column(Integer, default=0)
    unanswered: Mapped[int] = mapped_column(Integer, default=0)
    tab_switches: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    proctoring_violations: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="exam_attempts")
    answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_student_attempt"),
    )


class StudentAnswer(Base):
    __tablename__ = "student_answers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("mcq_options.id", ondelete="SET NULL")
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    time_taken: Mapped[int | None] = mapped_column(Integer)  # seconds
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="answers")
    selected_option: Mapped["MCQOption"] = relationship("MCQOption")


# ============== NEWS & SCRAPER MODELS (from scrapper) ==============

class Source(Base):
    __tablename__ = "sources"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    rss_url: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[ArticleCategory | None] = mapped_column(SQLEnum(ArticleCategory))
    language: Mapped[str] = mapped_column(String(10), default="bn")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scrape_interval: Mapped[int] = mapped_column(Integer, default=3600)  # seconds
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="source")
    scrape_logs: Mapped[list["ScrapeLog"]] = relationship(
        "ScrapeLog", back_populates="source", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    children: Mapped[list["Category"]] = relationship(
        "Category", backref="parent", remote_side=[id]
    )
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    lessons: Mapped[list["Lesson"]] = relationship("Lesson", secondary=lesson_tags)
    articles: Mapped[list["Article"]] = relationship("Article", secondary=article_tags)


class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    slug: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_ai_summarized: Mapped[bool] = mapped_column(Boolean, default=False)
    seo_keywords: Mapped[str | None] = mapped_column(Text)
    meta_description: Mapped[str | None] = mapped_column(String(500))
    
    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="articles")
    category: Mapped["Category"] = relationship("Category", back_populates="articles")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=article_tags)
    views: Mapped[list["ArticleView"]] = relationship(
        "ArticleView", back_populates="article", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_articles_published_source", "published_at", "source_id"),
        Index("idx_articles_category_published", "category_id", "published_at"),
    )


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50))  # success, failed, partial
    articles_found: Mapped[int] = mapped_column(Integer, default=0)
    articles_added: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[float | None] = mapped_column(Float)  # seconds
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="scrape_logs")


class ArticleView(Base):
    __tablename__ = "article_views"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="views")
    user: Mapped["User"] = relationship("User", back_populates="article_views")


# ============== JOB CIRCULAR MODELS ==============

class JobCircular(Base):
    __tablename__ = "job_circulars"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    posted_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    job_type: Mapped[str] = mapped_column(String(50))  # full_time, part_time, contract
    location: Mapped[str | None] = mapped_column(String(255))
    salary_range: Mapped[str | None] = mapped_column(String(100))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scraped: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    __table_args__ = (
        Index("idx_jobs_deadline_active", "application_deadline", "is_active"),
    )


# ============== COMMERCE MODELS ==============

class Course(Base):
    __tablename__ = "courses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    instructor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_price: Mapped[float | None] = mapped_column(Float)
    duration: Mapped[int | None] = mapped_column(Integer)  # hours
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    enrollment_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    student: Mapped["User"] = relationship("User", back_populates="enrollments")
    
    __table_args__ = (
        UniqueConstraint("course_id", "student_id", name="uq_course_student_enrollment"),
    )


class Book(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_price: Mapped[float | None] = mapped_column(Float)
    page_count: Mapped[int | None] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(50), default="pending")
    payment_method: Mapped[str | None] = mapped_column(String(50))
    transaction_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    items: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ============== BLOG MODELS ==============

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    featured_image: Mapped[str | None] = mapped_column(String(500))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    seo_keywords: Mapped[str | None] = mapped_column(Text)
    meta_description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), index=True
    )
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    post: Mapped["BlogPost"] = relationship("BlogPost", back_populates="comments")
    replies: Mapped[list["Comment"]] = relationship(
        "Comment", backref="parent_comment", remote_side=[id]
    )


# ============== ANALYTICS MODELS ==============

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")
    
    __table_args__ = (
        Index("idx_activity_user_created", "user_id", "created_at"),
    )
