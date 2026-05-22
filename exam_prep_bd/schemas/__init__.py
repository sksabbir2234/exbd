from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class ExamStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(str, Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto_submitted"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


# ==================== AUTH SCHEMAS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    phone: Optional[str] = None


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
    new_password: str = Field(..., min_length=6)


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str
    purpose: str


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.STUDENT


class UserResponse(UserBase):
    id: int
    subscription_tier: SubscriptionTier
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserSubscriptionUpdate(BaseModel):
    subscription_tier: SubscriptionTier
    subscription_expires_at: datetime


# ==================== CONTENT SCHEMAS ====================

class StudentTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class StudentTypeResponse(StudentTypeBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FolderBase(BaseModel):
    name: str
    description: Optional[str] = None
    student_type_id: int
    parent_id: Optional[int] = None
    order_index: int = 0


class FolderResponse(FolderBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: List['FolderResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None
    folder_id: int
    order_index: int = 0


class TopicResponse(TopicBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    topic_id: Optional[int] = None
    folder_id: Optional[int] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_premium: bool = False


class LessonResponse(LessonBase):
    id: int
    slug: str
    view_count: int
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FlashcardBase(BaseModel):
    question: str
    answer: str
    hint: Optional[str] = None
    difficulty: str = "medium"
    topic_id: int


class FlashcardResponse(FlashcardBase):
    id: int
    order_index: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== EXAM SCHEMAS ====================

class MCQOptionBase(BaseModel):
    option_text: str
    is_correct: bool = False
    order_index: int = 0


class MCQOptionResponse(MCQOptionBase):
    id: int
    question_id: int

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    question_text: str
    explanation: Optional[str] = None
    topic_id: Optional[int] = None
    difficulty: str = "medium"
    question_type: str = "mcq"
    marks: float = 1.0
    negative_marks: float = 0.0
    time_limit_seconds: Optional[int] = None
    options: List[MCQOptionBase] = []


class QuestionCreate(QuestionBase):
    """Schema for creating a question."""
    pass


class QuestionResponse(QuestionBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    options: List[MCQOptionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ExamQuestionBase(BaseModel):
    question_id: int
    marks: Optional[float] = None
    negative_marks: Optional[float] = None
    time_limit_seconds: Optional[int] = None
    order_index: int = 0


class ExamQuestionResponse(ExamQuestionBase):
    id: int
    exam_id: int
    question: QuestionResponse

    model_config = ConfigDict(from_attributes=True)


class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    exam_type: str = "model_test"
    total_marks: float = 100.0
    passing_marks: Optional[float] = None
    duration_minutes: int = 60
    negative_marking_enabled: bool = False
    is_premium: bool = False
    show_results_immediately: bool = True
    randomize_questions: bool = True
    randomize_options: bool = True
    proctoring_enabled: bool = False
    max_tab_switches: int = 3
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None


class ExamResponse(ExamBase):
    id: int
    slug: str
    status: ExamStatus
    attempt_count: int
    average_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExamAttemptBase(BaseModel):
    exam_id: int


class ExamAttemptResponse(ExamAttemptBase):
    id: int
    user_id: int
    status: AttemptStatus
    total_score: Optional[float] = None
    correct_answers: int
    wrong_answers: int
    unanswered: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class StudentAnswerBase(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None


class StudentAnswerResponse(StudentAnswerBase):
    id: int
    attempt_id: int
    is_correct: Optional[bool] = None
    time_taken_seconds: Optional[int] = None
    answered_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== NEWS SCHEMAS ====================

class SourceBase(BaseModel):
    name: str
    url: str
    rss_feed_url: Optional[str] = None
    category: Optional[str] = None
    language: str = "bn"
    scrape_priority: int = 5


class SourceResponse(SourceBase):
    id: int
    is_active: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime
    children: List['CategoryResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class TagBase(BaseModel):
    name: str


class TagResponse(TagBase):
    id: int
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    source_id: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    source_url: str
    published_at: Optional[datetime] = None
    tags: List[str] = []


class ArticleResponse(ArticleBase):
    id: int
    slug: str
    language: str
    view_count: int
    ai_summary: Optional[str] = None
    is_featured: bool
    is_active: bool
    scraped_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScrapeLogResponse(BaseModel):
    id: int
    source_id: int
    status: str
    articles_found: int
    articles_saved: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== JOB SCHEMAS ====================

class JobCircularBase(BaseModel):
    title: str
    organization: str
    post_name: Optional[str] = None
    vacancy_count: Optional[int] = None
    application_deadline: Optional[datetime] = None
    job_location: Optional[str] = None
    salary_range: Optional[str] = None
    education_required: Optional[str] = None
    experience_required: Optional[str] = None
    age_limit_min: Optional[int] = None
    age_limit_max: Optional[int] = None
    description: Optional[str] = None
    application_url: Optional[str] = None
    circular_pdf_url: Optional[str] = None


class JobCircularResponse(JobCircularBase):
    id: int
    slug: str
    source_url: Optional[str] = None
    source_type: str = "manual"
    is_featured: bool
    is_active: bool
    view_count: int
    application_count: int
    created_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== COMMERCE SCHEMAS ====================

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    currency: str = "BDT"
    duration_hours: Optional[float] = None
    thumbnail_url: Optional[str] = None
    is_premium: bool = False


class CourseResponse(CourseBase):
    id: int
    slug: str
    instructor_id: Optional[int] = None
    lecture_count: int
    student_count: int
    rating: float
    review_count: int
    is_published: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrollment_date: datetime
    progress_percentage: float
    is_completed: bool
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    currency: str = "BDT"
    cover_image_url: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    isbn: Optional[str] = None


class BookResponse(BookBase):
    id: int
    slug: str
    page_count: Optional[int] = None
    download_count: int
    rating: float
    review_count: int
    is_published: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    user_id: int
    items: List[dict]  # Course or Book IDs and types


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str
    payment_status: PaymentStatus
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== BLOG SCHEMAS ====================

class BlogPostBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    thumbnail_url: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class BlogPostResponse(BlogPostBase):
    id: int
    slug: str
    author_id: Optional[int] = None
    is_published: bool
    is_featured: bool
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    content: str
    blog_post_id: int
    parent_id: Optional[int] = None


class CommentResponse(CommentBase):
    id: int
    user_id: int
    is_approved: bool
    is_deleted: bool
    created_at: datetime
    replies: List['CommentResponse'] = []

    model_config = ConfigDict(from_attributes=True)


# ==================== ANALYTICS SCHEMAS ====================

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PAYMENT SCHEMAS ====================

class PaymentInitiateRequest(BaseModel):
    order_id: int
    payment_method: str  # bKash, Nagad, Rocket, card


class PaymentCallbackRequest(BaseModel):
    val_id: str
    bank_tran_id: Optional[str] = None
    card_type: Optional[str] = None
