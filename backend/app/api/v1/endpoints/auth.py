from datetime import timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedException, ConflictException, BadRequestException
from app.core.config import settings
from app.models.user import User
from app.models.provider import ProviderProfile
from app.models.enums import UserRole
from app.schemas.auth import UserRegister, UserLogin, Token, TokenRefresh
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    # Check if phone already registered
    existing_phone = db.query(User).filter(User.phone == data.phone).first()
    if existing_phone:
        raise ConflictException("A user with this phone number already exists")

    if data.email:
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            raise ConflictException("A user with this email already exists")

    # Prevent self-registration of ADMIN
    if data.role == UserRole.ADMIN:
        raise BadRequestException("Admin accounts cannot be self-registered")

    user = User(
        phone=data.phone,
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        is_active=True,
        is_suspended=False
    )
    db.add(user)
    db.flush()

    # If registered as PROVIDER, initialize empty provider profile
    if data.role == UserRole.PROVIDER:
        profile = ProviderProfile(
            user_id=user.id,
            business_name=user.full_name
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedException("Incorrect phone number or password")

    if not user.is_active:
        raise UnauthorizedException("Account is inactive")
    if user.is_suspended:
        raise UnauthorizedException("Account has been suspended. Please contact support.")

    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_token = create_refresh_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(data: TokenRefresh, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active or user.is_suspended:
        raise UnauthorizedException("Invalid user status")

    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
