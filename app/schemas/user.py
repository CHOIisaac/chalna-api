"""
👤 사용자 Pydantic 스키마

사용자 데이터 검증 및 직렬화
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.user import UserStatus


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    
    email: EmailStr = Field(..., description="이메일 주소")
    full_name: str = Field(..., min_length=1, max_length=100, description="전체 이름")
    nickname: Optional[str] = Field(None, max_length=50, description="닉네임")
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")
    city: Optional[str] = Field(None, max_length=50, description="도시")
    region: Optional[str] = Field(None, max_length=50, description="지역")
    language: str = Field("ko", max_length=10, description="언어 설정")
    timezone: str = Field("Asia/Seoul", max_length=50, description="시간대")
    currency: str = Field("KRW", max_length=10, description="통화")


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    
    @validator("password")
    def validate_password(cls, v):
        """비밀번호 유효성 검사"""
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다")
        if not any(c.isupper() for c in v):
            raise ValueError("비밀번호에 대문자가 포함되어야 합니다")
        if not any(c.islower() for c in v):
            raise ValueError("비밀번호에 소문자가 포함되어야 합니다")
        if not any(c.isdigit() for c in v):
            raise ValueError("비밀번호에 숫자가 포함되어야 합니다")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "홍길동",
                "nickname": "길동이",
                "password": "SecurePass123",
                "phone": "010-1234-5678",
                "city": "서울",
                "region": "강남구"
            }
        }


class UserUpdate(BaseModel):
    """사용자 수정 스키마"""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="전체 이름")
    nickname: Optional[str] = Field(None, max_length=50, description="닉네임")
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")
    city: Optional[str] = Field(None, max_length=50, description="도시")
    region: Optional[str] = Field(None, max_length=50, description="지역")
    language: Optional[str] = Field(None, max_length=10, description="언어 설정")
    timezone: Optional[str] = Field(None, max_length=50, description="시간대")
    currency: Optional[str] = Field(None, max_length=10, description="통화")
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "홍길동",
                "nickname": "길동이",
                "phone": "010-1234-5678",
                "city": "서울",
                "region": "강남구"
            }
        }


class UserInDB(UserBase):
    """데이터베이스 사용자 스키마"""
    
    id: int = Field(..., description="사용자 ID")
    is_active: bool = Field(True, description="활성 상태")
    is_verified: bool = Field(False, description="이메일 인증 상태")
    status: Optional[UserStatus] = Field(None, description="사용자 상태")
    total_events: int = Field(0, description="총 이벤트 수")
    total_gifts_given: int = Field(0, description="준 선물 수")
    total_gifts_received: int = Field(0, description="받은 선물 수")
    created_at: datetime = Field(..., description="가입일")
    updated_at: Optional[datetime] = Field(None, description="수정일")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """사용자 응답 스키마 (비밀번호 제외)"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "홍길동",
                "nickname": "길동이",
                "phone": "010-1234-5678",
                "city": "서울",
                "region": "강남구",
                "is_active": True,
                "is_verified": True,
                "status": "active",
                "total_events": 5,
                "total_gifts_given": 10,
                "total_gifts_received": 8,
                "created_at": "2024-01-01T00:00:00",
                "language": "ko",
                "timezone": "Asia/Seoul",
                "currency": "KRW"
            }
        }


class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=1, description="비밀번호")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserPasswordChange(BaseModel):
    """비밀번호 변경 스키마"""
    
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, max_length=100, description="새 비밀번호")
    
    @validator("new_password")
    def validate_new_password(cls, v):
        """새 비밀번호 유효성 검사"""
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다")
        if not any(c.isupper() for c in v):
            raise ValueError("비밀번호에 대문자가 포함되어야 합니다")
        if not any(c.islower() for c in v):
            raise ValueError("비밀번호에 소문자가 포함되어야 합니다")
        if not any(c.isdigit() for c in v):
            raise ValueError("비밀번호에 숫자가 포함되어야 합니다")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPass123",
                "new_password": "NewSecurePass456"
            }
        }


class Token(BaseModel):
    """토큰 응답 스키마"""
    
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")
    user: UserResponse = Field(..., description="사용자 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "홍길동",
                    "nickname": "길동이"
                }
            }
        }
