"""
🔐 보안 및 인증 관련 유틸리티

JWT 토큰 생성, 비밀번호 해싱 등의 보안 기능
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간 (기본값: 설정에서 가져옴)
        
    Returns:
        str: JWT 토큰
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    JWT 토큰 검증
    
    Args:
        token: 검증할 JWT 토큰
        
    Returns:
        dict: 토큰 payload
        
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 원본 비밀번호
        
    Returns:
        str: 해싱된 비밀번호
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        plain_password: 원본 비밀번호
        hashed_password: 해싱된 비밀번호
        
    Returns:
        bool: 비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token(email: str) -> str:
    """
    비밀번호 재설정 토큰 생성
    
    Args:
        email: 사용자 이메일
        
    Returns:
        str: 비밀번호 재설정 토큰
    """
    delta = timedelta(minutes=30)  # 30분 유효
    now = datetime.utcnow()
    expires = now + delta
    
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "email": email, "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    비밀번호 재설정 토큰 검증
    
    Args:
        token: 비밀번호 재설정 토큰
        
    Returns:
        Optional[str]: 유효한 경우 이메일, 무효한 경우 None
    """
    try:
        decoded_token = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        if decoded_token.get("type") != "password_reset":
            return None
            
        return decoded_token.get("email")
    except JWTError:
        return None


def create_email_verification_token(email: str) -> str:
    """
    이메일 인증 토큰 생성
    
    Args:
        email: 사용자 이메일
        
    Returns:
        str: 이메일 인증 토큰
    """
    delta = timedelta(hours=24)  # 24시간 유효
    now = datetime.utcnow()
    expires = now + delta
    
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "email": email, "type": "email_verification"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    이메일 인증 토큰 검증
    
    Args:
        token: 이메일 인증 토큰
        
    Returns:
        Optional[str]: 유효한 경우 이메일, 무효한 경우 None
    """
    try:
        decoded_token = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        if decoded_token.get("type") != "email_verification":
            return None
            
        return decoded_token.get("email")
    except JWTError:
        return None


# 보안 헬퍼 함수들
def is_safe_url(url: str) -> bool:
    """
    URL 안전성 검사
    
    Args:
        url: 검사할 URL
        
    Returns:
        bool: 안전한 URL인지 여부
    """
    # 간단한 URL 검증 로직
    if not url:
        return False
        
    # 상대 경로이거나 허용된 도메인인지 확인
    if url.startswith('/'):
        return True
        
    # 추가 검증 로직 구현 가능
    return False


def sanitize_filename(filename: str) -> str:
    """
    파일명 안전화
    
    Args:
        filename: 원본 파일명
        
    Returns:
        str: 안전화된 파일명
    """
    # 위험한 문자 제거
    import re
    safe_chars = re.sub(r'[^\w\s-.]', '', filename)
    safe_chars = re.sub(r'[-\s]+', '-', safe_chars)
    return safe_chars.strip('-.')[:100]  # 최대 100자로 제한 