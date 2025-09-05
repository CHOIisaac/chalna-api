"""
Ledger 스키마 - 경조사비 수입지출 장부
"""

from datetime import date, datetime
from typing import Optional

from pydantic import Field
from app.core.pydantic_config import BaseModelWithDatetime

from app.core.constants import EntryType, EventType


class LedgerBase(BaseModelWithDatetime):
    """장부 기본 스키마"""

    amount: int = Field(..., gt=0, description="금액")
    entry_type: EntryType = Field(
        ..., description="기록 타입 (income: 수입, expense: 지출)"
    )
    event_type: Optional[EventType] = Field(
        None, description="경조사 타입 (결혼식, 장례식, 돌잔치 등)"
    )
    event_name: Optional[str] = Field(
        None, max_length=200, description="경조사 이름 (예: 김철수 결혼식)"
    )
    event_date: Optional[date] = Field(None, description="경조사 날짜")
    location: Optional[str] = Field(None, max_length=500, description="경조사 장소")
    counterparty_name: Optional[str] = Field(
        None, max_length=100, description="상대방 이름"
    )
    counterparty_phone: Optional[str] = Field(
        None, max_length=20, description="상대방 전화번호"
    )
    relationship_type: Optional[str] = Field(
        None, max_length=50, description="관계 타입"
    )
    memo: Optional[str] = Field(None, description="메모")


class LedgerCreate(LedgerBase):
    """장부 기록 생성 스키마"""

    pass


class LedgerUpdate(BaseModelWithDatetime):
    """장부 기록 수정 스키마"""

    amount: Optional[int] = Field(None, gt=0, description="금액")
    entry_type: Optional[EntryType] = Field(
        None, description="기록 타입 (income: 수입, expense: 지출)"
    )
    event_type: Optional[EventType] = Field(None, description="경조사 타입")
    event_name: Optional[str] = Field(None, max_length=200, description="경조사 이름")
    event_date: Optional[date] = Field(None, description="경조사 날짜")
    location: Optional[str] = Field(None, max_length=500, description="경조사 장소")
    counterparty_name: Optional[str] = Field(
        None, max_length=100, description="상대방 이름"
    )
    counterparty_phone: Optional[str] = Field(
        None, max_length=20, description="상대방 전화번호"
    )
    relationship_type: Optional[str] = Field(
        None, max_length=50, description="관계 타입"
    )
    memo: Optional[str] = Field(None, description="메모")


class LedgerResponse(LedgerBase):
    """장부 응답 스키마"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LedgerInDB(LedgerBase):
    """데이터베이스 장부 스키마"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LedgerSummary(BaseModelWithDatetime):
    """장부 요약 스키마"""

    id: int
    amount: int
    entry_type: EntryType
    event_type: Optional[EventType]
    event_name: Optional[str]
    event_date: Optional[date]
    counterparty_name: Optional[str]
    created_at: datetime



class LedgerStatistics(BaseModelWithDatetime):
    """장부 통계 스키마"""

    total_income: int
    total_expense: int
    balance: int
    event_type_stats: dict
    total_records: int


class LedgerQuickAdd(BaseModelWithDatetime):
    """장부 빠른 추가 스키마"""

    amount: int = Field(..., gt=0, description="금액")
    entry_type: EntryType = Field(
        ..., description="기록 타입 (income: 수입, expense: 지출)"
    )
    event_type: EventType = Field(..., description="경조사 타입")
    counterparty_name: str = Field(..., max_length=100, description="상대방 이름")
    event_date: Optional[date] = Field(None, description="경조사 날짜")
    memo: Optional[str] = Field(None, description="메모")


class LedgerSearch(BaseModelWithDatetime):
    """장부 검색 스키마"""

    q: Optional[str] = Field(None, description="검색어 (이름, 장소, 메모)")
    entry_type: Optional[EntryType] = Field(
        None, description="기록 타입 (income/expense)"
    )
    event_type: Optional[EventType] = Field(None, description="경조사 타입")
    start_date: Optional[date] = Field(None, description="시작 날짜")
    end_date: Optional[date] = Field(None, description="종료 날짜")
    relationship_type: Optional[str] = Field(None, description="관계 타입")


# 예시 데이터
ledger_examples = {
    "create": {
        "summary": "경조사비 지출 기록",
        "value": {
            "amount": 100000,
            "entry_type": EntryType.EXPENSE,
            "event_type": EventType.WEDDING,
            "event_name": "김철수 결혼식",
            "event_date": "2024-06-15",
            "location": "그랜드 호텔 3층 그랜드볼룸",
            "counterparty_name": "김철수",
            "counterparty_phone": "010-1234-5678",
            "relationship_type": "대학동기",
            "memo": "축의금 10만원",
        },
    },
    "quick_add": {
        "summary": "빠른 경조사비 기록",
        "value": {
            "amount": 50000,
            "entry_type": EntryType.EXPENSE,
            "event_type": EventType.FUNERAL,
            "counterparty_name": "박영희",
            "memo": "조의금 5만원",
        },
    },
    "search": {
        "summary": "장부 검색",
        "value": {
            "q": "김철수",
            "entry_type": EntryType.EXPENSE,
            "event_type": EventType.WEDDING,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        },
    },
}
