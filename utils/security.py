"""Security utilities for authentication and authorization"""
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import config


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_file_upload(filename: str, file_size: int) -> tuple[bool, str]:
    """
    Validate file upload
    
    Returns:
        (is_valid, error_message)
    """
    from pathlib import Path
    
    # Check file extension
    extension = Path(filename).suffix.lower()
    if extension not in config.ALLOWED_EXTENSIONS:
        return False, f"File type {extension} is not allowed. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}"
    
    # Check file size
    max_size_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File size exceeds maximum allowed size of {config.MAX_UPLOAD_SIZE_MB} MB"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks"""
    import re
    from pathlib import Path
    
    # Get just the filename without path
    filename = Path(filename).name
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1)
        filename = name[:250] + '.' + ext
    
    return filename


def check_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user has required permission
    
    Role hierarchy: admin > manager > user
    """
    role_hierarchy = {
        "admin": 3,
        "manager": 2,
        "user": 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 999)
    
    return user_level >= required_level
