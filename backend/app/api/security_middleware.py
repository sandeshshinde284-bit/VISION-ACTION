"""
Security Middleware - Authentication and Authorization for Protected Endpoints
Provides JWT token validation and role-based access control
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from app.core.config import settings
import jwt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Load JWT configuration from settings
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
ADMIN_ROLE = "admin"
USER_ROLE = "user"


class SecurityException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_admin_token(admin_name: str, expires_delta: timedelta = None) -> str:
    """
    Generate a JWT token for admin authentication.
    Usage: Can be called during login or testing
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "admin_name": admin_name,
        "role": ADMIN_ROLE,
        "exp": expire
    }

    try:
        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Created admin token for user: {admin_name}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        raise


def verify_admin_token(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    Verify JWT token and extract admin claims.
    Use as dependency: async def endpoint(..., current_user: dict = Depends(verify_admin_token))

    Raises: 401 Unauthorized if token is invalid or missing
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_name: str = payload.get("admin_name")
        role: str = payload.get("role")

        if admin_name is None:
            raise SecurityException("Invalid token: missing admin_name")

        if role != ADMIN_ROLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions: admin role required"
            )

        logger.info(f"Admin token verified for user: {admin_name}")
        return {"admin_name": admin_name, "role": role}

    except jwt.ExpiredSignatureError:
        raise SecurityException("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token attempt: {e}")
        raise SecurityException("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise SecurityException("Token verification failed")


def verify_user_token(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    Verify JWT token for regular users (less strict than admin).
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_name: str = payload.get("admin_name")

        if admin_name is None:
            raise SecurityException("Invalid token: missing admin_name")

        logger.info(f"User token verified for: {admin_name}")
        return {"admin_name": admin_name, "role": payload.get("role", USER_ROLE)}

    except jwt.ExpiredSignatureError:
        raise SecurityException("Token has expired")
    except jwt.InvalidTokenError:
        raise SecurityException("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise SecurityException("Token verification failed")


# ============================================================================
# OPTIONAL: For Development/Testing - Generate Demo Tokens
# ============================================================================
def get_demo_admin_token() -> str:
    """
    Create a demo admin token for testing (1 hour expiry).
    ONLY FOR DEVELOPMENT - Remove from production!
    """
    return create_admin_token("demo_admin", expires_delta=timedelta(hours=1))
