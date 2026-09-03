from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User
from app.models.provider import ProviderProfile
from app.models.enums import UserRole
import uuid

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    cred: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = cred.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired access token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing user id")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Malformed user id in token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User no longer exists")

    if not user.is_active:
        raise ForbiddenException("User account is inactive")

    if user.is_suspended:
        raise ForbiddenException("User account has been suspended")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_role(allowed_roles: list[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(f"User does not have necessary permission ({', '.join(r.value for r in allowed_roles)})")
        return current_user
    return role_checker


get_current_customer = require_role([UserRole.CUSTOMER, UserRole.ADMIN])
get_current_provider_user = require_role([UserRole.PROVIDER, UserRole.ADMIN])
get_current_admin = require_role([UserRole.ADMIN])


def get_current_provider_profile(
    current_user: User = Depends(get_current_provider_user),
    db: Session = Depends(get_db)
) -> ProviderProfile:
    profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == current_user.id).first()
    if not profile:
        raise ForbiddenException("Provider profile does not exist for this account")
    return profile
