"""
🔐 보안 및 인증 관련 유틸리티

JWT 토큰 생성, 비밀번호 해싱 등의 보안 기능
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)


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


async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> "User":
    """
    현재 로그인한 사용자 조회
    
    JWT 토큰에서 사용자 정보를 추출하고 데이터베이스에서 조회
    
    Args:
        token: JWT 액세스 토큰
        
    Returns:
        User: 현재 사용자 객체
        
    Raises:
        HTTPException: 인증 실패 시
    """
    # 순환 import 방지를 위해 함수 내부에서 import
    from app.core.database import get_db
    from app.models.user import User
    
    # 인증 예외 정의
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 검증 및 payload 추출
        payload = verify_token(token)
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # 데이터베이스 세션 가져오기
    db = next(get_db())
    
    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.email == email).first()
    
    if user is None:
        raise credentials_exception
    
    # 사용자 상태 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user)
) -> "User":
    """
    현재 활성 사용자 조회 (활성 상태 확인 추가)
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        User: 활성 사용자 객체
        
    Raises:
        HTTPException: 비활성 사용자인 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 계정입니다"
        )
    return current_user


def get_current_user_id(
    current_user: "User" = Depends(get_current_user)
) -> int:
    """
    현재 사용자 ID만 반환
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        int: 사용자 ID
    """
    return current_user.id


def require_verified_user(
    current_user: "User" = Depends(get_current_user)
) -> "User":
    """
    이메일 인증된 사용자만 허용
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        User: 인증된 사용자 객체
        
    Raises:
        HTTPException: 미인증 사용자인 경우
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 필요합니다"
        )
    return current_user 