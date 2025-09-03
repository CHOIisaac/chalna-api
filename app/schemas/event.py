"""
Event 스키마 - 경조사 이벤트 데이터 검증
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.core.constants import EventType


class EventBase(BaseModel):
    """이벤트 기본 스키마"""
    title: str = Field(..., max_length=200, description="이벤트 제목")
    event_type: str = Field(..., max_length=50, description="이벤트 타입")
    event_date: datetime = Field(..., description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: bool = Field(False, description="외부 이벤트 여부")

    @validator('event_type')
    def validate_event_type(cls, v):
        """이벤트 타입 검증"""
        try:
            EventType(v)
            return v
        except ValueError:
            raise ValueError(f'유효하지 않은 이벤트 타입입니다: {v}')


class EventCreate(EventBase):
    """이벤트 생성 스키마"""
    pass


class EventUpdate(BaseModel):
    """이벤트 수정 스키마"""
    title: Optional[str] = Field(None, max_length=200, description="이벤트 제목")
    event_type: Optional[str] = Field(None, max_length=50, description="이벤트 타입")
    event_date: Optional[datetime] = Field(None, description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: Optional[bool] = Field(None, description="외부 이벤트 여부")

    @validator('event_type')
    def validate_event_type(cls, v):
        """이벤트 타입 검증"""
        if v is not None:
            try:
                EventType(v)
                return v
            except ValueError:
                raise ValueError(f'유효하지 않은 이벤트 타입입니다: {v}')
        return v


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
    event_type: str = Field(..., max_length=50, description="이벤트 타입")
    event_date: datetime = Field(..., description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: bool = Field(False, description="외부 이벤트 여부")

    @validator('event_type')
    def validate_event_type(cls, v):
        """이벤트 타입 검증"""
        try:
            EventType(v)
            return v
        except ValueError:
            raise ValueError(f'유효하지 않은 이벤트 타입입니다: {v}')


class CalendarEventCreate(CalendarEventBase):
    """캘린더 이벤트 생성 스키마"""
    pass


class CalendarEventUpdate(BaseModel):
    """캘린더 이벤트 수정 스키마"""
    title: Optional[str] = Field(None, max_length=200, description="이벤트 제목")
    event_type: Optional[str] = Field(None, max_length=50, description="이벤트 타입")
    event_date: Optional[datetime] = Field(None, description="이벤트 날짜")
    location: Optional[str] = Field(None, max_length=500, description="이벤트 장소")
    description: Optional[str] = Field(None, description="이벤트 설명")
    memo: Optional[str] = Field(None, description="메모")
    is_external: Optional[bool] = Field(None, description="외부 이벤트 여부")

    @validator('event_type')
    def validate_event_type(cls, v):
        """이벤트 타입 검증"""
        if v is not None:
            try:
                EventType(v)
                return v
            except ValueError:
                raise ValueError(f'유효하지 않은 이벤트 타입입니다: {v}')
        return v


class CalendarEventResponse(CalendarEventBase):
    """캘린더 이벤트 응답 스키마"""
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# 예시 데이터
event_examples = {
    "create": {
        "summary": "결혼식 이벤트 생성",
        "value": {
            "title": "김철수 결혼식",
            "event_type": "결혼식",
            "event_date": "2024-06-15T14:00:00",
            "location": "그랜드 호텔 3층 그랜드볼룸",
            "description": "대학 동기 김철수 결혼식",
            "memo": "축의금 10만원 준비",
            "is_external": False
        }
    },
    "update": {
        "summary": "이벤트 정보 수정",
        "value": {
            "title": "김철수 결혼식 (수정됨)",
            "location": "그랜드 호텔 5층 로얄볼룸",
            "memo": "축의금 10만원 준비, 정장 차림"
        }
    },
    "calendar": {
        "summary": "캘린더 이벤트 생성",
        "value": {
            "title": "회사 회의",
            "event_type": "기타",
            "event_date": "2024-01-15T09:00:00",
            "location": "회사 3층 회의실",
            "description": "월간 실적 회의",
            "is_external": False
        }
    }
}
