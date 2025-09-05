"""
User 스키마 - 사용자 데이터 검증 및 직렬화
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """사용자 기본 스키마"""

    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일")
    full_name: str = Field(..., min_length=1, max_length=100, description="실명")
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")


class UserCreate(UserBase):
    """사용자 생성 스키마"""

    password: str = Field(..., min_length=8, description="비밀번호")


class UserUpdate(BaseModel):
    """사용자 수정 스키마"""

    username: Optional[str] = Field(
        None, min_length=3, max_length=50, description="사용자명"
    )
    email: Optional[EmailStr] = Field(None, description="이메일")
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="실명"
    )
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")


class UserInDB(UserBase):
    """데이터베이스 사용자 스키마"""

    id: int
    is_active: bool
    is_verified: bool
    push_notification_enabled: bool
    notification_advance_hours: int

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """사용자 응답 스키마"""

    id: int
    is_active: bool
    is_verified: bool
    push_notification_enabled: bool
    notification_advance_hours: int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """사용자 로그인 스키마"""

    username: str = Field(..., description="사용자명 또는 이메일")
    password: str = Field(..., description="비밀번호")


class Token(BaseModel):
    """토큰 스키마"""

    access_token: str
    token_type: str = "bearer"


class UserPasswordChange(BaseModel):
    """비밀번호 변경 스키마"""

    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호")


class NotificationSettings(BaseModel):
    """알림 설정 스키마"""

    push_notification_enabled: bool = Field(..., description="푸시 알림 활성화")
    notification_advance_hours: int = Field(
        ..., ge=1, le=24, description="알림 시간 (시간 단위, 1-24)"
    )


class NotificationSettingsUpdate(BaseModel):
    """알림 설정 수정 스키마"""

    push_notification_enabled: Optional[bool] = Field(
        None, description="푸시 알림 활성화"
    )
    notification_advance_hours: Optional[int] = Field(
        None, ge=1, le=24, description="알림 시간 (시간 단위, 1-24)"
    )


# 예시 데이터
user_examples = {
    "create": {
        "summary": "새 사용자 등록",
        "value": {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "테스트 사용자",
            "phone": "010-1234-5678",
            "password": "testpass123",
        },
    },
    "update": {
        "summary": "사용자 정보 수정",
        "value": {"full_name": "수정된 이름", "phone": "010-9876-5432"},
    },
    "login": {
        "summary": "사용자 로그인",
        "value": {"username": "testuser", "password": "testpass123"},
    },
    "notification_settings": {
        "summary": "알림 설정 변경",
        "value": {"push_notification_enabled": True, "notification_advance_hours": 3},
    },
}
