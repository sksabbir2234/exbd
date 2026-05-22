from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.session import get_db
from schemas import (
    QuestionCreate, QuestionResponse, MCQOptionBase, 
    MCQOptionResponse, ExamStatus
)
from models import Question, MCQOption, Topic, User
from utils.deps import get_current_user, require_role, UserRole

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question_data: QuestionCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Create a new question with options (Teacher/Admin only)."""
    # Verify topic exists
    if question_data.topic_id:
        topic = db.query(Topic).filter(Topic.id == question_data.topic_id).first()
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
    
    # Create question
    question = Question(
        question_text=question_data.question_text,
        explanation=question_data.explanation,
        topic_id=question_data.topic_id,
        difficulty=question_data.difficulty,
        question_type=question_data.question_type,
        marks=question_data.marks,
        negative_marks=question_data.negative_marks,
        time_limit_seconds=question_data.time_limit_seconds,
        created_by=current_user.id
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    # Create options
    for idx, option_data in enumerate(question_data.options):
        option = MCQOption(
            question_id=question.id,
            option_text=option_data.option_text,
            is_correct=option_data.is_correct,
            order_index=option_data.order_index or idx
        )
        db.add(option)
    
    db.commit()
    db.refresh(question)
    
    return question


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single question by ID."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Students should not see correct answers unless exam is completed
    if current_user.role == UserRole.STUDENT:
        # Hide is_correct field for students
        for option in question.options:
            option.is_correct = False
    
    return question


@router.get("", response_model=List[QuestionResponse])
def list_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    topic_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List questions with filters."""
    query = db.query(Question).filter(Question.is_active == True)
    
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if question_type:
        query = query.filter(Question.question_type == question_type)
    if search:
        query = query.filter(Question.question_text.ilike(f"%{search}%"))
    
    questions = query.offset(skip).limit(limit).all()
    
    # Hide correct answers for students
    if current_user.role == UserRole.STUDENT:
        for question in questions:
            for option in question.options:
                option.is_correct = False
    
    return questions


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    question_data: QuestionCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Update a question (Teacher/Admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Update fields
    question.question_text = question_data.question_text
    question.explanation = question_data.explanation
    question.topic_id = question_data.topic_id
    question.difficulty = question_data.difficulty
    question.question_type = question_data.question_type
    question.marks = question_data.marks
    question.negative_marks = question_data.negative_marks
    question.time_limit_seconds = question_data.time_limit_seconds
    
    # Delete old options and create new ones
    db.query(MCQOption).filter(MCQOption.question_id == question_id).delete()
    
    for idx, option_data in enumerate(question_data.options):
        option = MCQOption(
            question_id=question.id,
            option_text=option_data.option_text,
            is_correct=option_data.is_correct,
            order_index=option_data.order_index or idx
        )
        db.add(option)
    
    db.commit()
    db.refresh(question)
    
    return question


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete a question (Admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Soft delete
    question.is_active = False
    db.commit()
    
    return {"message": "Question deleted"}


@router.patch("/{question_id}/toggle-status")
def toggle_question_status(
    question_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Toggle question active status (Teacher/Admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    question.is_active = not question.is_active
    db.commit()
    
    return {"is_active": question.is_active}
