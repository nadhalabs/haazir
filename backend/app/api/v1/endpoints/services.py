from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.service import ServiceCategory, Service
from app.schemas.service import ServiceCategoryResponse, ServiceResponse
import uuid

router = APIRouter()


@router.get("/categories", response_model=List[ServiceCategoryResponse])
def get_categories(
    db: Session = Depends(get_db)
):
    return (
        db.query(ServiceCategory)
        .filter(ServiceCategory.is_active == True)
        .order_by(ServiceCategory.display_order.asc())
        .all()
    )


@router.get("", response_model=List[ServiceResponse])
def list_services(
    category_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Service).filter(Service.is_active == True)
    if category_id:
        query = query.filter(Service.category_id == category_id)
    return query.all()


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise NotFoundException("Service not found")
    return service
