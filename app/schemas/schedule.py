"""
📅 일정 Pydantic 스키마

일정 데이터 검증 및 직렬화
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from app.models.schedule import ScheduleType, SchedulePriority, ScheduleStatus


class ScheduleBase(BaseModel):
    """일정 기본 스키마"""
    
    # 📝 일정 정보
    title: str = Field(..., min_length=1, max_length=200, description="일정 제목")
    description: Optional[str] = Field(None, max_length=1000, description="일정 상세 설명")
    schedule_type: ScheduleType = Field(ScheduleType.PERSONAL, description="일정 타입")
    
    # 📅 시간 정보
    start_time: datetime = Field(..., description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    all_day: bool = Field(False, description="종일 일정 여부")
    
    # 🎯 우선순위 및 상태
    priority: SchedulePriority = Field(SchedulePriority.MEDIUM, description="우선순위")
    status: ScheduleStatus = Field(ScheduleStatus.PENDING, description="일정 상태")
    
    # 🔔 알림 설정
    reminder_enabled: bool = Field(True, description="알림 사용 여부")
    reminder_time: Optional[datetime] = Field(None, description="알림 시간")
    reminder_type: str = Field("push", max_length=50, description="알림 타입")
    
    # 📍 위치 정보
    location: Optional[str] = Field(None, max_length=200, description="장소")
    
    # 🔗 관련 정보
    event_id: Optional[int] = Field(None, description="관련 경조사 이벤트 ID")
    
    # 🏷️ 태그 및 분류
    tags: Optional[str] = Field(None, max_length=500, description="태그 (쉼표로 구분)")
    category: Optional[str] = Field(None, max_length=100, description="카테고리")
    
    # 🔄 반복 설정
    is_recurring: bool = Field(False, description="반복 일정 여부")
    recurrence_rule: Optional[str] = Field(None, max_length=200, description="반복 규칙")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        """종료 시간은 시작 시간보다 늦어야 함"""
        if v and "start_time" in values and values["start_time"]:
            if v <= values["start_time"]:
                raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다")
        return v
    
    @validator("reminder_time")
    def validate_reminder_time(cls, v, values):
        """알림 시간은 시작 시간보다 빨라야 함"""
        if v and "start_time" in values and values["start_time"]:
            if v >= values["start_time"]:
                raise ValueError("알림 시간은 시작 시간보다 빨라야 합니다")
        return v


class ScheduleCreate(ScheduleBase):
    """일정 생성 스키마"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "의사 예약",
                "description": "정기 건강검진",
                "schedule_type": "health",
                "start_time": "2024-03-20T14:00:00",
                "end_time": "2024-03-20T15:00:00",
                "priority": "high",
                "location": "서울대병원",
                "reminder_time": "2024-03-20T13:30:00",
                "category": "건강관리"
            }
        }


class ScheduleUpdate(BaseModel):
    """일정 수정 스키마"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    schedule_type: Optional[ScheduleType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    priority: Optional[SchedulePriority] = None
    status: Optional[ScheduleStatus] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[datetime] = None
    reminder_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=200)
    event_id: Optional[int] = None
    tags: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = Field(None, max_length=200)


class ScheduleResponse(ScheduleBase):
    """일정 응답 스키마"""
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    # 계산된 필드
    duration_minutes: Optional[int] = None
    is_overdue: bool = False
    is_today: bool = False
    is_upcoming: bool = False
    formatted_time: str = ""
    priority_color: str = ""
    
    # 관련 정보
    event_title: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "의사 예약",
                "description": "정기 건강검진",
                "schedule_type": "health",
                "start_time": "2024-03-20T14:00:00",
                "end_time": "2024-03-20T15:00:00",
                "all_day": False,
                "priority": "high",
                "status": "pending",
                "reminder_enabled": True,
                "reminder_time": "2024-03-20T13:30:00",
                "reminder_type": "push",
                "location": "서울대병원",
                "event_id": None,
                "tags": "건강,검진",
                "category": "건강관리",
                "is_recurring": False,
                "recurrence_rule": None,
                "created_at": "2024-03-15T10:00:00",
                "updated_at": "2024-03-15T10:00:00",
                "duration_minutes": 60,
                "is_overdue": False,
                "is_today": False,
                "is_upcoming": True,
                "formatted_time": "2024-03-20 14:00 ~ 2024-03-20 15:00",
                "priority_color": "#fd7e14"
            }
        }


class ScheduleInDB(ScheduleBase):
    """데이터베이스 일정 스키마"""
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 📊 일정 통계 및 요약 스키마

class ScheduleSummary(BaseModel):
    """일정 요약 정보"""
    
    total_schedules: int = 0
    completed_schedules: int = 0
    overdue_schedules: int = 0
    completion_rate: float = 0.0
    today_schedules: int = 0
    upcoming_schedules: int = 0
    
    # 타입별 통계
    schedules_by_type: dict = {}
    schedules_by_priority: dict = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_schedules": 25,
                "completed_schedules": 18,
                "overdue_schedules": 2,
                "completion_rate": 72.0,
                "today_schedules": 3,
                "upcoming_schedules": 5,
                "schedules_by_type": {
                    "personal": 10,
                    "work": 8,
                    "health": 4,
                    "study": 3
                },
                "schedules_by_priority": {
                    "low": 5,
                    "medium": 12,
                    "high": 6,
                    "urgent": 2
                }
            }
        }


class DailySchedule(BaseModel):
    """일별 일정"""
    
    date: date
    schedules: List[ScheduleResponse]
    total_count: int
    completed_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-03-20",
                "schedules": [],
                "total_count": 3,
                "completed_count": 1
            }
        }


class WeeklySchedule(BaseModel):
    """주별 일정"""
    
    week_start: date
    week_end: date
    daily_schedules: List[DailySchedule]
    total_schedules: int
    completed_schedules: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "week_start": "2024-03-18",
                "week_end": "2024-03-24",
                "daily_schedules": [],
                "total_schedules": 15,
                "completed_schedules": 8
            }
        }


class ScheduleQuickAdd(BaseModel):
    """빠른 일정 추가"""
    
    title: str = Field(..., min_length=1, max_length=200)
    start_time: datetime
    end_time: Optional[datetime] = None
    priority: SchedulePriority = SchedulePriority.MEDIUM
    location: Optional[str] = None
    memo: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "미팅",
                "start_time": "2024-03-20T15:00:00",
                "end_time": "2024-03-20T16:00:00",
                "priority": "high",
                "location": "회의실 A",
                "memo": "프로젝트 진행상황 논의"
            }
        }
