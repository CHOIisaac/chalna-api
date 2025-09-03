"""
Schedule 스키마 - 경조사 일정 관리 (MVP)
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ScheduleBase(BaseModel):
    """일정 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="일정 제목")
    start_time: datetime = Field(..., description="시작 시간")
    location: Optional[str] = Field(None, max_length=500, description="위치 (경조사 장소)")
    event_id: Optional[int] = Field(None, description="경조사 ID (선택적)")
    event_type: Optional[str] = Field(None, max_length=50, description="경조사 타입 (결혼식, 장례식 등)")
    memo: Optional[str] = Field(None, description="간단한 메모")


class ScheduleCreate(ScheduleBase):
    """일정 생성 스키마"""
    pass


class ScheduleUpdate(BaseModel):
    """일정 수정 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="일정 제목")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    location: Optional[str] = Field(None, max_length=500, description="위치 (경조사 장소)")
    event_id: Optional[int] = Field(None, description="경조사 ID (선택적)")
    event_type: Optional[str] = Field(None, max_length=50, description="경조사 타입 (결혼식, 장례식 등)")
    memo: Optional[str] = Field(None, description="간단한 메모")


class ScheduleResponse(ScheduleBase):
    """일정 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleInDB(ScheduleBase):
    """데이터베이스 일정 스키마"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleSummary(BaseModel):
    """일정 요약 스키마"""
    id: int
    title: str
    start_time: datetime
    location: Optional[str]
    event_type: Optional[str]
    is_today: bool
    is_upcoming: bool


class DailySchedule(BaseModel):
    """일별 일정 스키마"""
    date: str
    schedules: List[ScheduleSummary]


class WeeklySchedule(BaseModel):
    """주별 일정 스키마"""
    week_start: str
    week_end: str
    daily_schedules: List[DailySchedule]


class ScheduleQuickAdd(BaseModel):
    """일정 빠른 추가 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="일정 제목")
    start_time: datetime = Field(..., description="시작 시간")
    location: Optional[str] = Field(None, max_length=500, description="위치 (경조사 장소)")
    event_type: Optional[str] = Field(None, max_length=50, description="경조사 타입 (결혼식, 장례식 등)")
    memo: Optional[str] = Field(None, description="간단한 메모")


# 예시 데이터
schedule_examples = {
    "create": {
        "summary": "결혼식 일정 등록",
        "value": {
            "title": "김철수 결혼식",
            "start_time": "2024-06-15T14:00:00",
            "location": "그랜드 호텔 3층 그랜드볼룸",
            "event_type": "결혼식",
            "memo": "축의금 10만원 준비"
        }
    },
    "update": {
        "summary": "일정 수정",
        "value": {
            "title": "김철수 결혼식 (수정)",
            "location": "그랜드 호텔 3층 그랜드볼룸",
            "memo": "축의금 10만원 준비, 선물도 추가"
        }
    },
    "quick_add": {
        "summary": "빠른 일정 추가",
        "value": {
            "title": "박영희 장례식",
            "start_time": "2024-06-20T10:00:00",
            "location": "서울추모공원",
            "event_type": "장례식",
            "memo": "조의금 5만원"
        }
    }
}
