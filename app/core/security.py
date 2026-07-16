from app.helpers.datetime_utils import utc_naive_now
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from sqlalchemy import select


# Використовуємо Argon2 напряму через argon2-cffi - без passlib та bcrypt
# Переваги Argon2:
# - Немає обмежень на довжину пароля (як у bcrypt 72 байти)
# - Краще захищений від атак (memory-hard)
# - Простіший у використанні (не потрібні додаткові pre-hash кроки)
# - Рекомендований OWASP як найкращий алгоритм для паролів
# - Повністю позбавляє від проблем з bcrypt та passlib
ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
http_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """
    Хешує пароль використовуючи Argon2 напряму через argon2-cffi.
    Argon2 не має обмежень на довжину пароля і не потребує pre-hash.
    """
    import logging
    logger = logging.getLogger("debug")
    logger.warning("🔥 hash_password CALLED 🔥")
    
    if not password:
        logger.error("🔥 hash_password: Password is empty!")
        raise ValueError("Password cannot be empty")
    
    logger.warning(f"🔥 hash_password: password length={len(password)}")
    
    try:
        # Argon2 може працювати з паролями будь-якої довжини без pre-hash
        result = ph.hash(password)
        logger.warning(f"🔥 hash_password: SUCCESS! Final hash prefix: {result[:30]}")
        return result
    except HashingError as e:
        logger.error(f"🔥 hash_password: Hashing error: {e}")
        raise ValueError(f"Failed to hash password: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Перевіряє пароль проти хешу.
    Використовує Argon2 напряму через argon2-cffi.
    """
    import logging
    logger = logging.getLogger("debug")
    logger.warning("🔥 verify_password CALLED 🔥")
    
    if not plain_password or not hashed_password:
        logger.warning(f"🔥 verify_password: Empty password or hash! password={bool(plain_password)}, hash={bool(hashed_password)}")
        return False
    
    hash_prefix = hashed_password[:30] if hashed_password else "None"
    logger.warning(f"🔥 verify_password: password_len={len(plain_password)}, hash_prefix={hash_prefix}")
    
    try:
        logger.warning("🔥 verify_password: Verifying with Argon2")
        ph.verify(hashed_password, plain_password)
        logger.warning("🔥 verify_password: Verify result=True")
        return True
    except VerifyMismatchError:
        logger.warning("🔥 verify_password: Verify result=False (password mismatch)")
        return False
    except Exception as e:
        logger.warning(f"🔥 verify_password: Verify failed: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = utc_naive_now() + expires_delta
    else:
        expire = utc_naive_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encode_jwt

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    bearer_token = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Поддержка как OAuth2 токена, так и HTTPBearer токена
    token_value = token
    if not token_value and bearer_token:
        token_value = bearer_token.credentials
    
    if not token_value:
        raise credentials_exception
    
    user_id = verify_token(token_value)
    if not user_id:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user



    
