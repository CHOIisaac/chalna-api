"""
Event 스키마 - 경조사 이벤트 데이터 검증
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.constants import EventType


class EventBase(BaseModel):
    """이벤트 기본 스키마"""
    title: str = Field(..., max_length=200, description="이벤트 제목")
    event_type: EventType = Field(..., description="이벤트 타입")
    event_date: datetime = Field(..., description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: bool = Field(False, description="외부 이벤트 여부")


class EventCreate(EventBase):
    """이벤트 생성 스키마"""
    pass


class EventUpdate(BaseModel):
    """이벤트 수정 스키마"""
    title: Optional[str] = Field(None, max_length=200, description="이벤트 제목")
    event_type: Optional[EventType] = Field(None, description="이벤트 타입")
    event_date: Optional[datetime] = Field(None, description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: Optional[bool] = Field(None, description="외부 이벤트 여부")


class EventResponse(EventBase):
    """이벤트 응답 스키마"""
    id: int
    user_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class EventInDB(EventBase):
    """데이터베이스 이벤트 스키마"""
    id: int
    user_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# 캘린더 관련 스키마
class CalendarEventBase(BaseModel):
    """캘린더 이벤트 기본 스키마"""
    title: str = Field(..., max_length=200, description="이벤트 제목")
    event_type: EventType = Field(..., description="이벤트 타입")
    event_date: datetime = Field(..., description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: bool = Field(False, description="외부 이벤트 여부")


class CalendarEventCreate(CalendarEventBase):
    """캘린더 이벤트 생성 스키마"""
    pass


class CalendarEventUpdate(BaseModel):
    """캘린더 이벤트 수정 스키마"""
    title: Optional[str] = Field(None, max_length=200, description="이벤트 제목")
    event_type: Optional[EventType] = Field(None, description="이벤트 타입")
    event_date: Optional[datetime] = Field(None, description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: Optional[bool] = Field(None, description="외부 이벤트 여부")


class CalendarEventResponse(CalendarEventBase):
    """캘린더 이벤트 응답 스키마"""
    id: int
    user_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CalendarEventInDB(CalendarEventBase):
    """데이터베이스 캘린더 이벤트 스키마"""
    id: int
    user_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# 이벤트 목록 조회용 스키마
class EventListResponse(BaseModel):
    """이벤트 목록 응답 스키마"""
    id: int
    title: str
    event_type: EventType
    event_date: datetime
    location: Optional[str]
    is_external: bool
    created_at: str

    class Config:
        from_attributes = True


class EventCalendarResponse(BaseModel):
    """이벤트 캘린더 응답 스키마"""
    id: int
    title: str
    event_type: EventType
    event_date: datetime
    location: Optional[str]
    description: Optional[str]
    is_external: bool

    class Config:
        from_attributes = True


# 이벤트 통계 스키마
class EventStatistics(BaseModel):
    """이벤트 통계 스키마"""
    total_events: int
    upcoming_events: int
    past_events: int
    event_type_counts: dict
    external_events_count: int
    internal_events_count: int


# 이벤트 검색 스키마
class EventSearch(BaseModel):
    """이벤트 검색 스키마"""
    q: Optional[str] = Field(None, description="검색어 (제목, 설명, 메모)")
    event_type: Optional[EventType] = Field(None, description="이벤트 타입")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    is_external: Optional[bool] = Field(None, description="외부 이벤트 여부")
    location: Optional[str] = Field(None, description="장소")


# 예시 데이터
event_examples = {
    "create": {
        "summary": "결혼식 이벤트 생성",
        "value": {
            "title": "김철수 결혼식",
            "event_type": EventType.WEDDING,
            "event_date": "2024-06-15T14:00:00",
            "location": "그랜드 호텔 3층 그랜드볼룸",
            "description": "대학동기 김철수의 결혼식",
            "memo": "축의금 10만원 준비",
            "is_external": False
        }
    },
    "update": {
        "summary": "이벤트 정보 수정",
        "value": {
            "title": "김철수 결혼식 (수정)",
            "location": "그랜드 호텔 5층 로얄볼룸",
            "memo": "축의금 10만원, 선물 준비"
        }
    },
    "search": {
        "summary": "이벤트 검색",
        "value": {
            "q": "결혼식",
            "event_type": EventType.WEDDING,
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59"
        }
    }
}
