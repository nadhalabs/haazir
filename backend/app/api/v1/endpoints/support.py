from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.support import SupportCase
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.support import (
    SupportCaseCreate,
    SupportCaseResponse,
    SupportCaseUpdate
)
from app.api.deps import get_current_user, get_current_admin
import uuid

router = APIRouter()


@router.post("", response_model=SupportCaseResponse, status_code=status.HTTP_201_CREATED)
def create_support_case(
    data: SupportCaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = SupportCase(
        booking_id=data.booking_id,
        raised_by_user_id=current_user.id,
        issue_type=data.issue_type,
        description=data.description
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=List[SupportCaseResponse])
def list_support_cases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ADMIN:
        return db.query(SupportCase).all()
    return db.query(SupportCase).filter(SupportCase.raised_by_user_id == current_user.id).all()


@router.patch("/{case_id}", response_model=SupportCaseResponse)
def update_support_case(
    case_id: uuid.UUID,
    data: SupportCaseUpdate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    case = db.query(SupportCase).filter(SupportCase.id == case_id).first()
    if not case:
        raise NotFoundException("Support case not found")

    if data.status is not None:
        case.status = data.status
    if data.resolution_notes is not None:
        case.resolution_notes = data.resolution_notes

    db.commit()
    db.refresh(case)
    return case
