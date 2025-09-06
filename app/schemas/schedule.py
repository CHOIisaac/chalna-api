"""
Schedule 스키마 - 경조사 일정 관리 (MVP)
"""

from datetime import datetime, date, time
from typing import Optional

from pydantic import Field
from app.core.pydantic_config import BaseModelWithDatetime

from app.core.constants import EventType


class ScheduleBase(BaseModelWithDatetime):
    """일정 기본 스키마"""

    title: str = Field(..., min_length=1, max_length=200, description="일정 제목")
    event_date: date = Field(..., description="일정 날짜")
    event_time: time = Field(..., description="일정 시간")
    location: Optional[str] = Field(
        None, max_length=500, description="위치 (경조사 장소)"
    )
    # event_id: Optional[int] = Field(None, description="경조사 ID (선택적)")
    event_type: Optional[EventType] = Field(
        None, description="경조사 타입 (결혼식, 장례식 등)"
    )
    memo: Optional[str] = Field(None, description="간단한 메모")


class ScheduleCreate(ScheduleBase):
    """일정 생성 스키마"""

    pass


class ScheduleUpdate(BaseModelWithDatetime):
    """일정 수정 스키마"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="일정 제목"
    )
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    location: Optional[str] = Field(
        None, max_length=500, description="위치 (경조사 장소)"
    )
    event_id: Optional[int] = Field(None, description="경조사 ID (선택적)")
    event_type: Optional[EventType] = Field(
        None, description="경조사 타입 (결혼식, 장례식 등)"
    )
    memo: Optional[str] = Field(None, description="간단한 메모")


class ScheduleResponse(ScheduleBase):
    """일정 응답 스키마"""

    id: int
    user_id: int
    title: str
    event_date: datetime
    event_time: time
    location: Optional[str]
    event_type: Optional[EventType]
    memo: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleInDB(ScheduleBase):
    """데이터베이스 일정 스키마"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleSummary(BaseModelWithDatetime):
    """일정 요약 스키마"""

    id: int
    title: str
    start_time: datetime
    location: Optional[str]
    event_type: Optional[EventType]
    is_today: bool
    is_upcoming: bool


class DailySchedule(BaseModelWithDatetime):
    """일별 일정 스키마"""

    date: str
    schedules: list[ScheduleSummary]


class WeeklySchedule(BaseModelWithDatetime):
    """주별 일정 스키마"""

    week_start: str
    week_end: str
    daily_schedules: list[DailySchedule]


class ScheduleQuickAdd(BaseModelWithDatetime):
    """일정 빠른 추가 스키마"""

    title: str = Field(..., min_length=1, max_length=200, description="일정 제목")
    start_time: datetime = Field(..., description="시작 시간")
    location: Optional[str] = Field(
        None, max_length=500, description="위치 (경조사 장소)"
    )
    event_type: Optional[EventType] = Field(
        None, description="경조사 타입 (결혼식, 장례식 등)"
    )
    memo: Optional[str] = Field(None, description="간단한 메모")


# 예시 데이터
schedule_examples = {
    "create": {
        "summary": "결혼식 일정 등록",
        "value": {
            "title": "김철수 결혼식",
            "start_time": "2024-06-15T14:00:00",
            "location": "그랜드 호텔 3층 그랜드볼룸",
            "event_type": EventType.WEDDING,
            "memo": "축의금 10만원 준비",
        },
    },
    "quick_add": {
        "summary": "빠른 일정 등록",
        "value": {
            "title": "박영희 장례식",
            "start_time": "2024-06-20T10:00:00",
            "event_type": EventType.FUNERAL,
            "memo": "조의금 5만원 준비",
        },
    },
    "search": {
        "summary": "일정 검색",
        "value": {
            "q": "결혼식",
            "event_type": EventType.WEDDING,
            "start_date": "2024-06-01T00:00:00",
            "end_date": "2024-06-30T23:59:59",
        },
    },
}
