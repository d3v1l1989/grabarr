# Standard library imports
from typing import Optional

# Third-party imports
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

# Local application imports
from app.config import settings
from app.core.session import get_session, delete_session, create_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user against admin credentials"""
    if username != settings.ADMIN_USERNAME:
        return False
    return verify_password(password, get_password_hash(settings.ADMIN_PASSWORD))

async def login(username: str, password: str) -> str:
    """Login user and return session ID"""
    if not await authenticate_user(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_session(username)

async def get_current_user(session_id: str = Cookie(None)) -> str:
    """Get current user from session cookie"""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = get_session(session_id)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return username

async def logout(session_id: str = Cookie(None)) -> None:
    """Logout user by deleting their session"""
    if session_id:
        delete_session(session_id) 