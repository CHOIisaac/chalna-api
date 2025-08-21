"""
🎉 이벤트 Pydantic 스키마

경조사 이벤트 데이터 검증 및 직렬화
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.event import EventType, EventStatus, ParticipationStatus


class EventBase(BaseModel):
    """이벤트 기본 스키마"""
    
    title: str = Field(..., min_length=1, max_length=200, description="이벤트 제목")
    event_type: EventType = Field(..., description="이벤트 유형")
    description: Optional[str] = Field(None, max_length=1000, description="이벤트 설명")
    
    # 📅 일정 정보
    event_date: datetime = Field(..., description="이벤트 날짜")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    
    # 📍 장소 정보
    venue_name: Optional[str] = Field(None, max_length=200, description="장소명")
    venue_address: Optional[str] = Field(None, max_length=500, description="장소 주소")
    venue_phone: Optional[str] = Field(None, max_length=20, description="장소 전화번호")
    
    # 🎯 참석 및 상태
    participation_status: ParticipationStatus = Field(
        default=ParticipationStatus.NOT_DECIDED, 
        description="참석 상태"
    )
    status: EventStatus = Field(default=EventStatus.PLANNED, description="이벤트 상태")
    
    # 💰 비용 정보
    estimated_cost: Optional[float] = Field(0.0, ge=0, description="예상 비용")
    actual_cost: Optional[float] = Field(0.0, ge=0, description="실제 비용")
    gift_amount: Optional[float] = Field(0.0, ge=0, description="축의금/조의금")
    
    # 👥 동행 정보
    companion_count: int = Field(1, ge=1, le=20, description="동행자 수 (본인 포함)")
    companion_names: Optional[str] = Field(None, max_length=500, description="동행자 이름들")
    
    # 🎁 선물 정보
    gift_type: Optional[str] = Field(None, max_length=50, description="선물 유형")
    gift_description: Optional[str] = Field(None, max_length=500, description="선물 설명")
    
    # 📝 메모
    memo: Optional[str] = Field(None, max_length=1000, description="메모")
    preparation_notes: Optional[str] = Field(None, max_length=1000, description="준비사항 메모")
    
    # 📱 리마인더
    reminder_enabled: bool = Field(True, description="리마인더 활성화")
    reminder_days_before: int = Field(3, ge=0, le=365, description="며칠 전 알림")
    
    # 🔄 반복 이벤트
    is_recurring: bool = Field(False, description="반복 이벤트 여부")
    recurrence_pattern: Optional[str] = Field(None, max_length=50, description="반복 패턴")
    
    # 🏷️ 태그
    tags: Optional[str] = Field(None, max_length=500, description="태그 (JSON 형태)")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        """종료 시간은 시작 시간보다 늦어야 함"""
        if v and "start_time" in values and values["start_time"]:
            if v <= values["start_time"]:
                raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다")
        return v

    @validator("gift_amount")
    def validate_gift_amount(cls, v, values):
        """축의금은 이벤트 유형에 따라 적절한 범위여야 함"""
        if v and v > 0:
            event_type = values.get("event_type")
            if event_type == EventType.WEDDING and v < 30000:
                raise ValueError("결혼식 축의금은 최소 3만원 이상을 권장합니다")
            elif event_type == EventType.FUNERAL and v < 10000:
                raise ValueError("장례식 조의금은 최소 1만원 이상을 권장합니다")
        return v


class EventCreate(EventBase):
    """이벤트 생성 스키마"""
    
    relationship_id: Optional[int] = Field(None, description="관련된 관계 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "홍길동 결혼식",
                "event_type": "wedding",
                "description": "대학 동기 홍길동의 결혼식",
                "event_date": "2024-03-15T14:00:00",
                "start_time": "2024-03-15T14:00:00",
                "end_time": "2024-03-15T17:00:00",
                "venue_name": "강남 웨딩홀",
                "venue_address": "서울시 강남구 역삼동 123-45",
                "venue_phone": "02-1234-5678",
                "participation_status": "attending",
                "gift_amount": 100000,
                "companion_count": 2,
                "companion_names": "아내",
                "gift_type": "cash",
                "memo": "축하 메시지 준비하기",
                "reminder_days_before": 3
            }
        }


class EventUpdate(BaseModel):
    """이벤트 수정 스키마"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    event_type: Optional[EventType] = None
    description: Optional[str] = Field(None, max_length=1000)
    
    event_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    venue_name: Optional[str] = Field(None, max_length=200)
    venue_address: Optional[str] = Field(None, max_length=500)
    venue_phone: Optional[str] = Field(None, max_length=20)
    
    participation_status: Optional[ParticipationStatus] = None
    status: Optional[EventStatus] = None
    
    estimated_cost: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    gift_amount: Optional[float] = Field(None, ge=0)
    
    companion_count: Optional[int] = Field(None, ge=1, le=20)
    companion_names: Optional[str] = Field(None, max_length=500)
    
    gift_type: Optional[str] = Field(None, max_length=50)
    gift_description: Optional[str] = Field(None, max_length=500)
    
    memo: Optional[str] = Field(None, max_length=1000)
    preparation_notes: Optional[str] = Field(None, max_length=1000)
    follow_up_notes: Optional[str] = Field(None, max_length=1000)
    
    reminder_enabled: Optional[bool] = None
    reminder_days_before: Optional[int] = Field(None, ge=0, le=365)
    
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = Field(None, max_length=50)
    
    tags: Optional[str] = Field(None, max_length=500)


class EventInDB(EventBase):
    """데이터베이스 이벤트 스키마"""
    
    id: int
    user_id: int
    relationship_id: Optional[int] = None
    
    # 📸 미디어 정보
    photos: Optional[str] = None
    documents: Optional[str] = None
    
    # 📝 후속 메모
    follow_up_notes: Optional[str] = None
    
    # 🕐 타임스탬프
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EventResponse(EventInDB):
    """이벤트 응답 스키마"""
    
    # 관계 정보 포함 (선택적)
    relationship_name: Optional[str] = None
    relationship_type: Optional[str] = None
    
    # 계산된 필드들
    days_until_event: Optional[int] = None
    is_past_event: bool = False
    cost_difference: Optional[float] = None  # 예상 비용 vs 실제 비용
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "relationship_id": 5,
                "title": "홍길동 결혼식",
                "event_type": "wedding",
                "event_date": "2024-03-15T14:00:00",
                "gift_amount": 100000,
                "status": "completed",
                "relationship_name": "홍길동",
                "relationship_type": "college_friend",
                "days_until_event": -10,
                "is_past_event": True,
                "created_at": "2024-01-15T10:00:00",
                "updated_at": "2024-03-16T09:00:00"
            }
        }


# 📅 달력 UI용 특별 스키마들

class CalendarEventBase(BaseModel):
    """달력 표시용 간소화된 이벤트 스키마"""
    
    id: int
    title: str
    event_type: EventType
    event_date: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: EventStatus
    participation_status: ParticipationStatus
    gift_amount: Optional[float] = None
    venue_name: Optional[str] = None
    
    # 달력 표시용 추가 정보
    is_all_day: bool = True  # 종일 이벤트 여부
    # color 제거 - 프론트엔드에서 event_type 기반으로 처리


class CalendarEventsResponse(BaseModel):
    """달력용 이벤트 목록 응답"""
    
    events: List[CalendarEventBase]
    total_count: int
    period_start: datetime
    period_end: datetime
    
    # 📊 기간별 통계
    total_expenses: float = 0.0  # 총 지출
    total_income: float = 0.0    # 총 수입 (받은 축의금)
    net_amount: float = 0.0      # 순 금액
    event_count_by_type: dict = {}  # 이벤트 타입별 개수


class MonthlyCalendarResponse(CalendarEventsResponse):
    """월별 달력 응답"""
    
    year: int
    month: int
    
    # 📅 월별 추가 정보
    days_with_events: List[int] = []  # 이벤트가 있는 날짜들
    busy_days: List[int] = []         # 이벤트가 많은 날짜들 (2개 이상)


class EventQuickCreate(BaseModel):
    """달력에서 빠른 이벤트 생성용"""
    
    title: str = Field(..., min_length=1, max_length=100)
    event_type: EventType
    event_date: datetime
    gift_amount: Optional[float] = Field(0.0, ge=0)
    memo: Optional[str] = Field(None, max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "김철수 생일",
                "event_type": "birthday",
                "event_date": "2024-03-20T19:00:00",
                "gift_amount": 50000,
                "memo": "생일선물 준비"
            }
        }
