"""
Simple Session-Based Authentication
Users log in with username + password from database
Server creates session token (64-char random string)
Token stored in database, expires after 24 hours
"""

from fastapi import APIRouter, HTTPException, status, Header
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.db_service import db_service
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str


def hash_password(password: str) -> str:
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password matches hash"""
    return hash_password(plain) == hashed


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with username + password
    Creates session token stored in database
    Token valid for 24 hours
    """
    try:
        # 1. Get user from database
        user = db_service.get_user(request.username)

        if not user:
            logger.warning(f"Login failed: user not found - {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # 2. Verify password
        if not verify_password(request.password, user['password']):
            logger.warning(f"Login failed: wrong password - {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # 3. Create session token
        token = secrets.token_urlsafe(settings.SESSION_TOKEN_LENGTH)
        expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_TIMEOUT_HOURS)

        # 4. Store session in database
        db_service.create_session(token, request.username, expires_at)

        logger.info(f"✅ User logged in: {request.username}")

        # 5. Return response
        return LoginResponse(
            token=token,
            username=request.username,
            role=user['role']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """
    Logout - delete session token
    Token becomes invalid immediately
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No token provided")

        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token format")

        token = parts[1]

        # Delete session
        db_service.delete_session(token)

        logger.info("✅ User logged out")
        return {"status": "logged out"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


def verify_session_token(token: str) -> str:
    """
    Verify session token is valid
    Returns username if valid
    Raises 401 if invalid or expired
    """
    try:
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")

        # Get session from database
        session = db_service.get_session(token)

        if not session:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check if expired
        if datetime.utcnow() > session['expires_at']:
            db_service.delete_session(token)
            raise HTTPException(status_code=401, detail="Token expired")

        # Update last activity
        db_service.update_session_activity(token)

        return session['username']

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
