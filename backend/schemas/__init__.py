"""
Pydantic Schemas - Exam Prep BD
Request/Response models for API validation
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============== ENUMS ==============

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class SubscriptionTierEnum(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


class QuestionTypeEnum(str, Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    DESCRIPTIVE = "descriptive"


class ExamStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExamAttemptStatusEnum(str, Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto_submitted"


# ============== COMMON SCHEMAS ==============

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


# ============== AUTH SCHEMAS ==============

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=100)


class OTPVerifyRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str = Field(min_length=6, max_length=6)
    purpose: str


# ============== USER SCHEMAS ==============

class UserResponse(BaseSchema):
    id: int
    email: str
    phone: Optional[str]
    full_name: str
    role: UserRoleEnum
    subscription_tier: SubscriptionTierEnum
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class UserAdminUpdate(BaseModel):
    role: Optional[UserRoleEnum] = None
    subscription_tier: Optional[SubscriptionTierEnum] = None
    is_active: Optional[bool] = None
    subscription_expires_at: Optional[datetime] = None


# ============== TOPIC & FOLDER SCHEMAS ==============

class FolderCreate(BaseModel):
    name: str = Field(max_length=255)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=100)
    order: int = 0


class FolderResponse(BaseSchema):
    id: int
    name: str
    parent_id: Optional[int]
    description: Optional[str]
    icon: Optional[str]
    order: int
    is_active: bool
    created_at: datetime
    children: List["FolderResponse"] = []


class TopicCreate(BaseModel):
    name: str = Field(max_length=255)
    folder_id: int
    description: Optional[str] = None
    slug: str
    order: int = 0


class TopicResponse(BaseSchema):
    id: int
    name: str
    folder_id: int
    description: Optional[str]
    slug: str
    order: int
    is_active: bool
    created_at: datetime


# ============== LESSON SCHEMAS ==============

class LessonCreate(BaseModel):
    title: str = Field(max_length=500)
    topic_id: int
    content: str
    summary: Optional[str] = None
    difficulty_level: str = "beginner"
    estimated_duration: Optional[int] = None
    is_premium: bool = False
    tag_ids: List[int] = []


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_premium: Optional[bool] = None
    is_published: Optional[bool] = None


class LessonResponse(BaseSchema):
    id: int
    title: str
    topic_id: int
    content: str
    summary: Optional[str]
    difficulty_level: str
    estimated_duration: Optional[int]
    view_count: int
    is_premium: bool
    is_published: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class FlashcardCreate(BaseModel):
    lesson_id: int
    question: str = Field(max_length=1000)
    answer: str
    order: int = 0


class FlashcardResponse(BaseSchema):
    id: int
    lesson_id: int
    question: str
    answer: str
    order: int
    created_at: datetime


# ============== QUESTION SCHEMAS ==============

class MCQOptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False
    order: int = 0


class MCQOptionResponse(BaseSchema):
    id: int
    question_id: int
    option_text: str
    is_correct: bool
    order: int


class QuestionCreate(BaseModel):
    topic_id: Optional[int] = None
    question_text: str
    question_type: QuestionTypeEnum = QuestionTypeEnum.MCQ
    explanation: Optional[str] = None
    difficulty_level: str = "medium"
    marks: int = 1
    negative_marks: float = 0.0
    time_limit: Optional[int] = None
    is_premium: bool = False
    options: List[MCQOptionCreate] = []


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    explanation: Optional[str] = None
    difficulty_level: Optional[str] = None
    marks: Optional[int] = None
    negative_marks: Optional[float] = None
    time_limit: Optional[int] = None
    is_active: Optional[bool] = None


class QuestionResponse(BaseSchema):
    id: int
    topic_id: Optional[int]
    question_text: str
    question_type: QuestionTypeEnum
    explanation: Optional[str]
    difficulty_level: str
    marks: int
    negative_marks: float
    time_limit: Optional[int]
    is_active: bool
    is_premium: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    options: List[MCQOptionResponse] = []


# ============== EXAM SCHEMAS ==============

class ExamQuestionLink(BaseModel):
    question_id: int
    marks: int = 1
    order: int = 0


class ExamCreate(BaseModel):
    title: str = Field(max_length=500)
    description: Optional[str] = None
    exam_type: str
    total_marks: int = 100
    duration: int  # minutes
    passing_marks: Optional[int] = None
    is_premium: bool = False
    enable_proctoring: bool = False
    max_tab_switches: Optional[int] = 3
    require_fullscreen: bool = False
    show_results: bool = True
    randomize_questions: bool = True
    randomize_options: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    question_ids: List[int] = []


class ExamUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    total_marks: Optional[int] = None
    duration: Optional[int] = None
    passing_marks: Optional[int] = None
    status: Optional[ExamStatusEnum] = None
    is_premium: Optional[bool] = None
    enable_proctoring: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class ExamResponse(BaseSchema):
    id: int
    title: str
    description: Optional[str]
    exam_type: str
    total_marks: int
    duration: int
    passing_marks: Optional[int]
    status: ExamStatusEnum
    is_premium: bool
    enable_proctoring: bool
    max_tab_switches: Optional[int]
    require_fullscreen: bool
    show_results: bool
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    question_count: int = 0


class ExamAttemptCreate(BaseModel):
    exam_id: int


class ExamAttemptResponse(BaseSchema):
    id: int
    exam_id: int
    student_id: int
    status: ExamAttemptStatusEnum
    total_score: Optional[float]
    correct_answers: int
    wrong_answers: int
    unanswered: int
    tab_switches: int
    started_at: datetime
    submitted_at: Optional[datetime]


class StudentAnswerCreate(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    time_taken: Optional[int] = None


class StudentAnswerResponse(BaseSchema):
    id: int
    attempt_id: int
    question_id: int
    selected_option_id: Optional[int]
    is_correct: Optional[bool]
    time_taken: Optional[int]
    answered_at: datetime


# ============== NEWS SCHEMAS ==============

class SourceCreate(BaseModel):
    name: str = Field(max_length=255)
    url: str = Field(max_length=500)
    rss_url: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = None
    language: str = "bn"
    scrape_interval: int = 3600


class SourceResponse(BaseSchema):
    id: int
    name: str
    url: str
    rss_url: Optional[str]
    category: Optional[str]
    language: str
    is_active: bool
    scrape_interval: int
    last_scraped_at: Optional[datetime]
    created_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(max_length=100)
    slug: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class CategoryResponse(BaseSchema):
    id: int
    name: str
    slug: str
    parent_id: Optional[int]
    description: Optional[str]
    created_at: datetime
    children: List["CategoryResponse"] = []


class TagCreate(BaseModel):
    name: str = Field(max_length=100)
    slug: str


class TagResponse(BaseSchema):
    id: int
    name: str
    slug: str
    created_at: datetime


class ArticleCreate(BaseModel):
    title: str = Field(max_length=1000)
    slug: str
    source_id: int
    category_id: Optional[int] = None
    content: str
    summary: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    author: Optional[str] = Field(default=None, max_length=255)
    published_at: Optional[datetime] = None
    tag_ids: List[int] = []


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=1000)
    content: Optional[str] = None
    summary: Optional[str] = None
    is_ai_summarized: Optional[bool] = None
    seo_keywords: Optional[str] = None
    meta_description: Optional[str] = Field(default=None, max_length=500)


class ArticleResponse(BaseSchema):
    id: int
    title: str
    slug: str
    source_id: int
    category_id: Optional[int]
    content: str
    summary: Optional[str]
    image_url: Optional[str]
    author: Optional[str]
    published_at: Optional[datetime]
    scraped_at: datetime
    view_count: int
    is_ai_summarized: bool
    seo_keywords: Optional[str]
    meta_description: Optional[str]


class ArticleListViewItem(BaseSchema):
    id: int
    title: str
    slug: str
    image_url: Optional[str]
    summary: Optional[str]
    published_at: Optional[datetime]
    view_count: int
    source_name: str
    category_name: Optional[str]


class ScrapeLogResponse(BaseSchema):
    id: int
    source_id: int
    status: str
    articles_found: int
    articles_added: int
    error_message: Optional[str]
    duration: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]


# ============== JOB SCHEMAS ==============

class JobCircularCreate(BaseModel):
    title: str = Field(max_length=500)
    organization: str = Field(max_length=255)
    description: str
    requirements: Optional[str] = None
    application_deadline: Optional[datetime] = None
    posted_date: datetime
    source_url: str = Field(max_length=500)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    job_type: str = "full_time"
    location: Optional[str] = Field(default=None, max_length=255)
    salary_range: Optional[str] = Field(default=None, max_length=100)


class JobCircularUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    requirements: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class JobCircularResponse(BaseSchema):
    id: int
    title: str
    organization: str
    description: str
    requirements: Optional[str]
    application_deadline: Optional[datetime]
    posted_date: datetime
    source_url: str
    logo_url: Optional[str]
    job_type: str
    location: Optional[str]
    salary_range: Optional[str]
    is_featured: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============== COURSE SCHEMAS ==============

class CourseCreate(BaseModel):
    title: str = Field(max_length=500)
    description: str
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    instructor_id: Optional[int] = None
    price: float
    discount_price: Optional[float] = None
    duration: Optional[int] = None  # hours


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    is_published: Optional[bool] = None


class CourseResponse(BaseSchema):
    id: int
    title: str
    description: str
    thumbnail_url: Optional[str]
    instructor_id: Optional[int]
    price: float
    discount_price: Optional[float]
    duration: Optional[int]
    is_published: bool
    is_premium: bool
    enrollment_count: int
    rating: Optional[float]
    created_at: datetime
    updated_at: datetime


class EnrollmentResponse(BaseSchema):
    id: int
    course_id: int
    student_id: int
    enrolled_at: datetime
    progress: float
    completed: bool


# ============== BOOK SCHEMAS ==============

class BookCreate(BaseModel):
    title: str = Field(max_length=500)
    description: str
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    file_url: str = Field(max_length=500)
    price: float
    discount_price: Optional[float] = None
    page_count: Optional[int] = None


class BookResponse(BaseSchema):
    id: int
    title: str
    description: str
    cover_image_url: Optional[str]
    file_url: str
    price: float
    discount_price: Optional[float]
    page_count: Optional[int]
    is_published: bool
    download_count: int
    created_at: datetime


# ============== ORDER SCHEMAS ==============

class OrderCreate(BaseModel):
    items: dict
    payment_method: Optional[str] = None


class OrderResponse(BaseSchema):
    id: int
    user_id: int
    order_number: str
    total_amount: float
    payment_status: str
    payment_method: Optional[str]
    transaction_id: Optional[str]
    items: dict
    status: str
    created_at: datetime
    updated_at: datetime


# ============== BLOG SCHEMAS ==============

class BlogPostCreate(BaseModel):
    title: str = Field(max_length=500)
    slug: str
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = Field(default=None, max_length=500)
    seo_keywords: Optional[str] = None
    meta_description: Optional[str] = Field(default=None, max_length=500)


class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = None
    excerpt: Optional[str] = None
    is_published: Optional[bool] = None
    seo_keywords: Optional[str] = None
    meta_description: Optional[str] = Field(default=None, max_length=500)


class BlogPostResponse(BaseSchema):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    author_id: int
    featured_image: Optional[str]
    is_published: bool
    published_at: Optional[datetime]
    view_count: int
    seo_keywords: Optional[str]
    meta_description: Optional[str]
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    post_id: int
    content: str
    parent_id: Optional[int] = None


class CommentResponse(BaseSchema):
    id: int
    post_id: int
    user_id: int
    content: str
    parent_id: Optional[int]
    is_approved: bool
    created_at: datetime


# ============== ANALYTICS SCHEMAS ==============

class ActivityLogResponse(BaseSchema):
    id: int
    user_id: int
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    ip_address: Optional[str]
    metadata: Optional[dict]
    created_at: datetime


# Update forward references
FolderResponse.model_rebuild()
CategoryResponse.model_rebuild()
