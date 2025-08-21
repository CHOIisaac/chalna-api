"""
🎁 선물/축의금 Pydantic 스키마

선물 및 축의금 데이터 검증 및 직렬화 (가계부 기능 포함)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.gift import GiftType, GiftStatus, GiftDirection


class GiftBase(BaseModel):
    """선물 기본 스키마"""
    
    # 🎁 기본 정보
    title: str = Field(..., min_length=1, max_length=200, description="선물/축의금 제목")
    gift_type: GiftType = Field(..., description="선물 유형")
    direction: GiftDirection = Field(..., description="주고받은 방향")
    
    # 💰 금액 정보
    amount: float = Field(..., ge=0, description="금액")
    currency: str = Field("KRW", max_length=10, description="통화")
    
    # 📝 상세 정보
    description: Optional[str] = Field(None, max_length=1000, description="선물 설명")
    brand: Optional[str] = Field(None, max_length=100, description="브랜드")
    
    # 📅 날짜 정보
    given_date: datetime = Field(..., description="주고받은 날짜")
    
    # 🎯 상태 정보
    status: GiftStatus = Field(default=GiftStatus.COMPLETED, description="선물 상태")
    
    # 🔄 답례 정보
    is_reciprocal: bool = Field(False, description="답례 선물 여부")
    original_gift_id: Optional[int] = Field(None, description="원본 선물 ID (답례인 경우)")
    reciprocal_required: bool = Field(False, description="답례 필요 여부")
    reciprocal_deadline: Optional[datetime] = Field(None, description="답례 마감일")
    
    # 📍 구매/수령 정보
    purchase_location: Optional[str] = Field(None, max_length=200, description="구매처")
    purchase_method: Optional[str] = Field(None, max_length=50, description="구매 방법")
    delivery_address: Optional[str] = Field(None, max_length=500, description="배송지")
    
    # 📊 평가 정보
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5, description="만족도 (1-5점)")
    appropriateness_score: Optional[int] = Field(None, ge=1, le=5, description="적절성 (1-5점)")
    
    # 📝 메모
    memo: Optional[str] = Field(None, max_length=1000, description="메모")
    private_notes: Optional[str] = Field(None, max_length=1000, description="개인 메모")
    
    # 🏷️ 분류
    category: Optional[str] = Field(None, max_length=50, description="카테고리")
    tags: Optional[str] = Field(None, max_length=500, description="태그 (JSON 형태)")

    @validator("reciprocal_deadline")
    def validate_reciprocal_deadline(cls, v, values):
        """답례 마감일은 선물 받은 날짜보다 늦어야 함"""
        if v and "given_date" in values and values["given_date"]:
            if v <= values["given_date"]:
                raise ValueError("답례 마감일은 선물 받은 날짜보다 늦어야 합니다")
        return v

    @validator("amount")
    def validate_amount(cls, v, values):
        """금액은 선물 유형에 따라 적절한 범위여야 함"""
        if v > 0:
            gift_type = values.get("gift_type")
            if gift_type == GiftType.CASH:
                if v < 10000:
                    raise ValueError("현금 축의금은 최소 1만원 이상을 권장합니다")
                elif v > 10000000:
                    raise ValueError("현금 축의금이 너무 큽니다")
        return v


class GiftCreate(GiftBase):
    """선물 생성 스키마"""
    
    event_id: Optional[int] = Field(None, description="관련 이벤트 ID")
    relationship_id: Optional[int] = Field(None, description="관련 관계 ID")
    giver_id: Optional[int] = Field(None, description="선물 주는 사람 ID")
    receiver_id: Optional[int] = Field(None, description="선물 받는 사람 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "홍길동 결혼축하금",
                "gift_type": "cash",
                "direction": "given",
                "amount": 100000,
                "description": "결혼식 축의금",
                "given_date": "2024-03-15T14:00:00",
                "event_id": 1,
                "relationship_id": 5,
                "memo": "결혼식장에서 직접 전달",
                "category": "wedding_gift"
            }
        }


class GiftUpdate(BaseModel):
    """선물 수정 스키마"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    gift_type: Optional[GiftType] = None
    direction: Optional[GiftDirection] = None
    
    amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    
    description: Optional[str] = Field(None, max_length=1000)
    brand: Optional[str] = Field(None, max_length=100)
    
    given_date: Optional[datetime] = None
    status: Optional[GiftStatus] = None
    
    is_reciprocal: Optional[bool] = None
    reciprocal_required: Optional[bool] = None
    reciprocal_deadline: Optional[datetime] = None
    
    purchase_location: Optional[str] = Field(None, max_length=200)
    purchase_method: Optional[str] = Field(None, max_length=50)
    delivery_address: Optional[str] = Field(None, max_length=500)
    
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5)
    appropriateness_score: Optional[int] = Field(None, ge=1, le=5)
    
    memo: Optional[str] = Field(None, max_length=1000)
    private_notes: Optional[str] = Field(None, max_length=1000)
    
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=500)


class GiftInDB(GiftBase):
    """데이터베이스 선물 스키마"""
    
    id: int
    user_id: int
    event_id: Optional[int] = None
    relationship_id: Optional[int] = None
    giver_id: Optional[int] = None
    receiver_id: Optional[int] = None
    
    # 📸 미디어 정보
    photos: Optional[str] = None
    receipts: Optional[str] = None
    
    # 🕐 타임스탬프
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GiftResponse(GiftInDB):
    """선물 응답 스키마"""
    
    # 관계 정보 포함 (선택적)
    event_title: Optional[str] = None
    relationship_name: Optional[str] = None
    relationship_type: Optional[str] = None
    
    # 계산된 필드들
    days_since_given: Optional[int] = None
    needs_reciprocation: bool = False
    recommended_reciprocal_amount: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "event_id": 1,
                "relationship_id": 5,
                "title": "홍길동 결혼축하금",
                "gift_type": "cash",
                "direction": "given",
                "amount": 100000,
                "given_date": "2024-03-15T14:00:00",
                "status": "completed",
                "event_title": "홍길동 결혼식",
                "relationship_name": "홍길동",
                "days_since_given": 15,
                "created_at": "2024-03-15T10:00:00",
                "updated_at": "2024-03-15T10:00:00"
            }
        }


# 💰 가계부 기능용 특별 스키마들

class FinancialTransactionBase(BaseModel):
    """가계부 거래 기본 스키마"""
    
    id: int
    title: str
    amount: float
    direction: GiftDirection  # 입금(received) / 출금(given)
    transaction_date: datetime
    category: Optional[str] = None
    event_title: Optional[str] = None
    relationship_name: Optional[str] = None
    memo: Optional[str] = None
    
    # UI 관련 필드들은 프론트엔드에서 처리
    # transaction_color, transaction_icon 제거


class FinancialSummary(BaseModel):
    """가계부 요약 정보"""
    
    # 📊 기본 통계
    total_income: float = 0.0      # 총 수입 (받은 금액)
    total_expense: float = 0.0     # 총 지출 (준 금액)
    net_amount: float = 0.0        # 순 금액
    transaction_count: int = 0      # 총 거래 수
    
    # 📅 기간 정보
    period_start: datetime
    period_end: datetime
    period_type: str  # "monthly", "yearly", "custom"
    
    # 📊 카테고리별 통계
    income_by_category: dict = {}   # 카테고리별 수입
    expense_by_category: dict = {}  # 카테고리별 지출
    
    # 🎯 이벤트 타입별 통계
    expense_by_event_type: dict = {}  # 이벤트 타입별 지출
    income_by_event_type: dict = {}   # 이벤트 타입별 수입
    
    # 📈 트렌드 정보
    average_monthly_expense: Optional[float] = None
    average_monthly_income: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_income": 200000,
                "total_expense": 450000,
                "net_amount": -250000,
                "transaction_count": 8,
                "period_start": "2024-03-01T00:00:00",
                "period_end": "2024-03-31T23:59:59",
                "period_type": "monthly",
                "expense_by_category": {
                    "wedding_gift": 300000,
                    "birthday_gift": 100000,
                    "funeral": 50000
                },
                "income_by_category": {
                    "birthday_gift": 150000,
                    "wedding_gift": 50000
                }
            }
        }


class MonthlyFinancialReport(BaseModel):
    """월별 가계부 리포트"""
    
    year: int
    month: int
    summary: FinancialSummary
    transactions: List[FinancialTransactionBase]
    
    # 📊 추가 월별 분석
    busiest_day: Optional[int] = None  # 가장 많은 거래가 있었던 날
    biggest_expense: Optional[FinancialTransactionBase] = None
    biggest_income: Optional[FinancialTransactionBase] = None
    
    # 📈 전월 대비
    expense_change_percent: Optional[float] = None
    income_change_percent: Optional[float] = None


class YearlyFinancialReport(BaseModel):
    """연별 가계부 리포트"""
    
    year: int
    summary: FinancialSummary
    monthly_summaries: List[FinancialSummary]
    
    # 📊 연간 분석
    peak_expense_month: Optional[int] = None  # 지출이 가장 많았던 월
    peak_income_month: Optional[int] = None   # 수입이 가장 많았던 월
    
    # 📈 성장률
    year_over_year_expense_change: Optional[float] = None
    year_over_year_income_change: Optional[float] = None


class GiftQuickAdd(BaseModel):
    """빠른 선물/축의금 추가"""
    
    title: str = Field(..., min_length=1, max_length=100)
    gift_type: GiftType
    direction: GiftDirection
    amount: float = Field(..., ge=0)
    given_date: Optional[datetime] = None  # 기본값: 현재 시간
    memo: Optional[str] = Field(None, max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "김영희 생일선물",
                "gift_type": "physical",
                "direction": "given",
                "amount": 50000,
                "memo": "향수 선물"
            }
        }


class PendingReciprocals(BaseModel):
    """답례 대기 목록"""
    
    gift_id: int
    original_gift_title: str
    giver_name: str
    amount_received: float
    received_date: datetime
    reciprocal_deadline: Optional[datetime] = None
    days_overdue: Optional[int] = None
    recommended_amount: Optional[float] = None
    urgency_level: str  # "low", "medium", "high", "overdue"
    
    class Config:
        json_schema_extra = {
            "example": {
                "gift_id": 5,
                "original_gift_title": "김철수 결혼축하금",
                "giver_name": "김철수",
                "amount_received": 100000,
                "received_date": "2024-02-14T15:00:00",
                "reciprocal_deadline": "2024-03-14T23:59:59",
                "days_overdue": 5,
                "recommended_amount": 100000,
                "urgency_level": "overdue"
            }
        }


class GiftRecommendation(BaseModel):
    """선물 추천 정보"""
    
    relationship_id: int
    relationship_name: str
    event_type: str
    recommended_amount_min: float
    recommended_amount_max: float
    recommended_amount_avg: float
    
    # 추천 근거
    basis_factors: List[str] = []  # ["relationship_closeness", "past_gifts", "social_norm"]
    confidence_score: float = Field(..., ge=0, le=1, description="추천 신뢰도 (0-1)")
    
    # 과거 기록
    past_gifts_given: List[dict] = []
    past_gifts_received: List[dict] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "relationship_id": 5,
                "relationship_name": "홍길동",
                "event_type": "wedding",
                "recommended_amount_min": 80000,
                "recommended_amount_max": 150000,
                "recommended_amount_avg": 100000,
                "basis_factors": ["relationship_closeness", "social_norm"],
                "confidence_score": 0.85,
                "past_gifts_given": [],
                "past_gifts_received": []
            }
        }
