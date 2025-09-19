from typing import Optional
from datetime import datetime

from pydantic import Field
from app.core.pydantic_config import BaseModelWithDatetime


class UserSettingsBase(BaseModelWithDatetime):
    """사용자 설정 기본 스키마"""
    notification_enabled: Optional[bool] = Field(None, description="전체 알림 켜시/끄기")
    event_reminders: bool = Field(True, description="일정 알림")
    reminder_hours_before: int = Field(24, ge=1, le=168, description="몇 시간 전에 알림 (1~168시간)")


class UserSettingsCreate(UserSettingsBase):
    """사용자 설정 생성 스키마"""
    pass


class UserSettingsUpdate(BaseModelWithDatetime):
    """사용자 설정 수정 스키마 (부분 업데이트)"""
    notifications_enabled: Optional[bool] = Field(None, description="전체 알림 켜기/끄기")
    event_reminders: Optional[bool] = Field(None, description="일정 알림")
    reminder_hours_before: Optional[int] = Field(None, ge=1, le=168, description="몇 시간 전에 알림")


class UserSettingsResponse(UserSettingsBase):
    """사용자 설정 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 예시 데이터
user_settings_examples = {
    "default": {
        "summary": "기본 설정",
        "value": {
            "notifications_enabled": True,
            "event_reminders": True,
            "reminder_hours_before": 24
        }
    },
    "update": {
        "summary": "설정 업데이트",
        "value": {
            "notifications_enabled": False,
            "reminder_hours_before": 48
        }
    }
}