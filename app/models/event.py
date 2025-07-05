"""
🎉 이벤트 모델

경조사 이벤트 정보를 관리합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EventType(enum.Enum):
    """이벤트 유형"""
    WEDDING = "wedding"               # 결혼식
    FUNERAL = "funeral"               # 장례식
    BIRTHDAY = "birthday"             # 생일
    BABY_SHOWER = "baby_shower"       # 돌잔치
    GRADUATION = "graduation"         # 졸업식
    PROMOTION = "promotion"           # 승진
    HOUSEWARMING = "housewarming"     # 새집들이
    ENGAGEMENT = "engagement"         # 약혼식
    ANNIVERSARY = "anniversary"       # 기념일
    RETIREMENT = "retirement"         # 퇴직
    OPENING = "opening"               # 개업
    OTHER = "other"                   # 기타


class EventStatus(enum.Enum):
    """이벤트 상태"""
    PLANNED = "planned"               # 예정
    CONFIRMED = "confirmed"           # 확정
    ATTENDED = "attended"             # 참석완료
    NOT_ATTENDED = "not_attended"     # 불참
    CANCELLED = "cancelled"           # 취소


class ParticipationStatus(enum.Enum):
    """참석 상태"""
    WILL_ATTEND = "will_attend"       # 참석예정
    WILL_NOT_ATTEND = "will_not_attend"  # 불참예정
    MAYBE = "maybe"                   # 미정
    NOT_DECIDED = "not_decided"       # 미결정


class Event(Base):
    """
    이벤트 모델 - 경조사 이벤트 관리
    """
    __tablename__ = "events"
    
    # 🔑 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    
    # 🎉 이벤트 정보
    title = Column(String(200), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    description = Column(Text)
    
    # 📅 일정 정보
    event_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # 📍 장소 정보
    venue_name = Column(String(200))
    venue_address = Column(Text)
    venue_phone = Column(String(20))
    
    # 🎯 참석 정보
    participation_status = Column(Enum(ParticipationStatus), default=ParticipationStatus.NOT_DECIDED)
    status = Column(Enum(EventStatus), default=EventStatus.PLANNED)
    
    # 💰 예산 및 비용 정보
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    gift_amount = Column(Float, default=0.0)
    
    # 👥 동행 정보
    companion_count = Column(Integer, default=1)  # 동행자 수 (본인 포함)
    companion_names = Column(Text)  # 동행자 이름들
    
    # 🎁 선물 정보
    gift_type = Column(String(50))  # 현금, 상품권, 물품 등
    gift_description = Column(Text)
    
    # 📝 메모 및 기록
    memo = Column(Text)
    preparation_notes = Column(Text)
    follow_up_notes = Column(Text)
    
    # 📱 리마인더 설정
    reminder_enabled = Column(Boolean, default=True)
    reminder_days_before = Column(Integer, default=3)
    
    # 📸 미디어 정보
    photos = Column(Text)  # 사진 URL들 (JSON 형태)
    documents = Column(Text)  # 관련 문서들 (JSON 형태)
    
    # 🔄 반복 이벤트 설정
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50))  # yearly, monthly 등
    
    # 🏷️ 태그 및 분류
    tags = Column(Text)  # 태그들 (JSON 형태)
    category = Column(String(50))
    
    # 📊 평가 정보
    satisfaction_rating = Column(Integer)  # 1-5 점수
    would_attend_again = Column(Boolean)
    
    # 🕐 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 🔗 관계 설정
    user = relationship("User", back_populates="events")
    relationship_info = relationship("Relationship", back_populates="events")
    gifts = relationship("Gift", back_populates="event")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, type={self.event_type}, date={self.event_date})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "relationship_id": self.relationship_id,
            "title": self.title,
            "event_type": self.event_type.value,
            "description": self.description,
            "event_date": self.event_date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "venue_name": self.venue_name,
            "venue_address": self.venue_address,
            "venue_phone": self.venue_phone,
            "participation_status": self.participation_status.value,
            "status": self.status.value,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "gift_amount": self.gift_amount,
            "companion_count": self.companion_count,
            "companion_names": self.companion_names,
            "gift_type": self.gift_type,
            "gift_description": self.gift_description,
            "memo": self.memo,
            "preparation_notes": self.preparation_notes,
            "follow_up_notes": self.follow_up_notes,
            "reminder_enabled": self.reminder_enabled,
            "reminder_days_before": self.reminder_days_before,
            "photos": self.photos,
            "documents": self.documents,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "tags": self.tags,
            "category": self.category,
            "satisfaction_rating": self.satisfaction_rating,
            "would_attend_again": self.would_attend_again,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def days_until_event(self):
        """이벤트까지 남은 일수"""
        if self.event_date:
            delta = self.event_date - func.now()
            return delta.days
        return None
    
    @property
    def is_past_event(self):
        """과거 이벤트인지 여부"""
        if self.event_date:
            return self.event_date < func.now()
        return False
    
    @property
    def is_upcoming(self):
        """다가오는 이벤트인지 여부 (30일 이내)"""
        days_until = self.days_until_event
        return days_until is not None and 0 <= days_until <= 30
    
    @property
    def cost_difference(self):
        """예상 비용과 실제 비용의 차이"""
        return self.actual_cost - self.estimated_cost
    
    @property
    def is_high_cost(self):
        """고비용 이벤트인지 여부 (10만원 이상)"""
        return self.actual_cost >= 100000
    
    def get_recommended_gift_amount(self):
        """추천 축의금 계산"""
        from app.core.config import settings
        
        if not self.relationship_info:
            return 0
        
        # 관계 유형에 따른 기본 금액
        relationship_type = str(self.relationship_info.relationship_type.value)
        event_type = str(self.event_type.value)
        
        base_amounts = settings.DEFAULT_GIFT_AMOUNTS
        
        if relationship_type in base_amounts and event_type in base_amounts[relationship_type]:
            base_amount = base_amounts[relationship_type][event_type]
        else:
            base_amount = 30000  # 기본값
        
        # 친밀도에 따른 조정
        intimacy_score = self.relationship_info.intimacy_score
        if intimacy_score >= 90:
            base_amount *= 1.5
        elif intimacy_score >= 70:
            base_amount *= 1.2
        elif intimacy_score >= 50:
            pass  # 기본값 유지
        elif intimacy_score >= 30:
            base_amount *= 0.8
        else:
            base_amount *= 0.6
        
        return int(base_amount)
    
    def get_preparation_checklist(self):
        """이벤트 준비 체크리스트 생성"""
        checklist = []
        
        # 공통 체크리스트
        checklist.extend([
            "축의금/선물 준비",
            "복장 준비",
            "교통편 확인",
            "동행자 확인",
        ])
        
        # 이벤트 유형별 추가 항목
        if self.event_type == EventType.WEDDING:
            checklist.extend([
                "하객 복장 확인 (화려한 색상 피하기)",
                "축하 메시지 준비",
                "포토타임 예의 숙지",
            ])
        elif self.event_type == EventType.FUNERAL:
            checklist.extend([
                "검은색 정장 준비",
                "조화 또는 조의금 준비",
                "위로 인사말 준비",
            ])
        elif self.event_type == EventType.BABY_SHOWER:
            checklist.extend([
                "아기용품 선물 준비",
                "축하 카드 작성",
            ])
        
        return checklist
    
    def calculate_total_cost(self):
        """총 비용 계산 (축의금 + 기타 비용)"""
        return (self.gift_amount or 0) + (self.actual_cost or 0)
    
    def update_status_after_event(self):
        """이벤트 후 상태 업데이트"""
        if self.is_past_event and self.status in [EventStatus.PLANNED, EventStatus.CONFIRMED]:
            if self.participation_status == ParticipationStatus.WILL_ATTEND:
                self.status = EventStatus.ATTENDED
            else:
                self.status = EventStatus.NOT_ATTENDED 