"""
알림 관련 Pydantic 스키마
"""

from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """알림 기본 스키마"""
    title: str = Field(..., description="알림 제목", max_length=255)
    message: str = Field(..., description="알림 메시지")
    type: str = Field(..., description="알림 타입", max_length=50)
    event_date: Optional[date] = Field(None, description="알림과 관련된 날짜")
    event_time: Optional[time] = Field(None, description="알림과 관련된 시간")
    location: Optional[str] = Field(None, description="장소 정보", max_length=255)


class NotificationCreate(NotificationBase):
    """알림 생성 스키마"""
    pass


class NotificationUpdate(BaseModel):
    """알림 수정 스키마"""
    read: Optional[bool] = Field(None, description="읽음 상태")


class NotificationResponse(NotificationBase):
    """알림 응답 스키마"""
    id: str = Field(..., description="알림 ID")
    time: str = Field(..., description="알림 시간 (HH:MM)")
    read: bool = Field(..., description="읽음 상태")
    date: str = Field(..., description="알림과 관련된 날짜 (ISO 8601)")
    created_at: str = Field(..., description="생성일시 (ISO 8601)")
    updated_at: str = Field(..., description="수정일시 (ISO 8601)")
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """알림 목록 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    data: dict = Field(..., description="알림 목록 데이터")
    message: str = Field("알림 목록 조회 성공", description="응답 메시지")
    
    class Config:
        from_attributes = True


class NotificationListData(BaseModel):
    """알림 목록 데이터 스키마"""
    notifications: list[NotificationResponse] = Field(..., description="알림 목록")
    total_count: int = Field(..., description="전체 알림 개수")
