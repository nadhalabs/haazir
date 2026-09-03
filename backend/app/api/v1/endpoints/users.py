from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User
from app.models.address import Address
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse
from app.api.deps import get_current_user
import uuid

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/profile", response_model=UserResponse)
def update_user_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.email is not None:
        current_user.email = data.email

    db.commit()
    db.refresh(current_user)
    return current_user


# --- Addresses Management (Safe & IDOR-protected) ---

@router.get("/addresses", response_model=List[AddressResponse])
def list_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Address).filter(Address.user_id == current_user.id).all()


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.is_default:
        # Reset existing defaults
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})

    address = Address(
        user_id=current_user.id,
        label=data.label,
        address_line1=data.address_line1,
        address_line2=data.address_line2,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
        latitude=data.latitude,
        longitude=data.longitude,
        is_default=data.is_default
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: uuid.UUID,
    data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(Address.id == address_id).first()
    if not address:
        raise NotFoundException("Address not found")
    if address.user_id != current_user.id:
        raise ForbiddenException("Address does not belong to you")

    if data.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(Address.id == address_id).first()
    if not address:
        raise NotFoundException("Address not found")
    if address.user_id != current_user.id:
        raise ForbiddenException("Address does not belong to you")

    db.delete(address)
    db.commit()
    return None
