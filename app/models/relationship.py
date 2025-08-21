"""
🤝 관계 모델

사용자 간의 인간관계 네트워크를 관리합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class RelationshipType(enum.Enum):
    """관계 유형"""
    FAMILY = "family"           # 가족
    FRIEND = "friend"           # 친구
    COLLEAGUE = "colleague"     # 동료
    ACQUAINTANCE = "acquaintance"  # 지인
    CLASSMATE = "classmate"     # 동창
    NEIGHBOR = "neighbor"       # 이웃
    BUSINESS = "business"       # 비즈니스
    OTHER = "other"             # 기타


class RelationshipStatus(enum.Enum):
    """관계 상태"""
    ACTIVE = "active"           # 활성
    INACTIVE = "inactive"       # 비활성
    BLOCKED = "blocked"         # 차단
    LOST_CONTACT = "lost_contact"  # 연락두절


class Relationship(Base):
    """
    관계 모델 - 인간관계 네트워크의 핵심
    """
    __tablename__ = "relationships"
    
    # 🔑 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 👤 상대방 정보
    contact_name = Column(String(100), nullable=False)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    
    # 🤝 관계 정보
    relationship_type = Column(Enum(RelationshipType), nullable=False)
    relationship_detail = Column(String(100))  # 상세 관계 (예: 대학동기, 직장동료 등)
    
    # 📊 친밀도 점수 (0-100)
    intimacy_score = Column(Float, default=50.0)
    
    # 🏷️ 분류 정보
    category = Column(String(50))  # 카테고리 (예: 회사, 학교, 동호회 등)
    tags = Column(Text)  # 태그들 (JSON 형태로 저장)
    
    # 📍 위치 정보
    location = Column(String(100))  # 거주지역
    workplace = Column(String(100))  # 직장
    
    # 📅 중요 날짜들
    first_met_date = Column(DateTime)
    birthday = Column(DateTime)
    anniversary = Column(DateTime)
    
    # 🎯 상태 정보
    status = Column(Enum(RelationshipStatus), default=RelationshipStatus.ACTIVE)
    is_favorite = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    
    # 💬 상호작용 정보
    last_contact_date = Column(DateTime)
    contact_frequency = Column(Integer, default=0)  # 월 평균 연락 빈도
    total_events = Column(Integer, default=0)
    total_gifts_given = Column(Integer, default=0)
    total_gifts_received = Column(Integer, default=0)
    
    # 📝 메모
    memo = Column(Text)
    private_notes = Column(Text)
    
    # 🔔 알림 설정
    birthday_alert = Column(Boolean, default=True)
    anniversary_alert = Column(Boolean, default=True)
    regular_contact_alert = Column(Boolean, default=False)
    
    # 🕐 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 🔗 관계 설정
    user = relationship("User", back_populates="relationships")
    events = relationship("Event", back_populates="relationship")
    ceremonial_money = relationship("CeremonialMoney", back_populates="relationship_info")
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, user_id={self.user_id}, contact={self.contact_name}, type={self.relationship_type})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "relationship_type": self.relationship_type.value,
            "relationship_detail": self.relationship_detail,
            "intimacy_score": self.intimacy_score,
            "category": self.category,
            "tags": self.tags,
            "location": self.location,
            "workplace": self.workplace,
            "first_met_date": self.first_met_date,
            "birthday": self.birthday,
            "anniversary": self.anniversary,
            "status": self.status.value,
            "is_favorite": self.is_favorite,
            "is_important": self.is_important,
            "last_contact_date": self.last_contact_date,
            "contact_frequency": self.contact_frequency,
            "total_events": self.total_events,
            "total_gifts_given": self.total_gifts_given,
            "total_gifts_received": self.total_gifts_received,
            "memo": self.memo,
            "birthday_alert": self.birthday_alert,
            "anniversary_alert": self.anniversary_alert,
            "regular_contact_alert": self.regular_contact_alert,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def gift_balance(self):
        """선물 수지 (받은 것 - 준 것)"""
        return self.total_gifts_received - self.total_gifts_given
    
    @property
    def relationship_duration(self):
        """관계 지속 기간 (일수)"""
        if self.first_met_date:
            return (func.now() - self.first_met_date).days
        return 0
    
    @property
    def contact_level(self):
        """연락 수준 평가"""
        if self.contact_frequency >= 4:
            return "매우 자주"
        elif self.contact_frequency >= 2:
            return "자주"
        elif self.contact_frequency >= 1:
            return "보통"
        else:
            return "드물게"
    
    def calculate_intimacy_score(self, db):
        """친밀도 점수 계산"""
        score = 0
        
        # 기본 관계 점수
        base_scores = {
            RelationshipType.FAMILY: 80,
            RelationshipType.FRIEND: 60,
            RelationshipType.COLLEAGUE: 40,
            RelationshipType.CLASSMATE: 50,
            RelationshipType.NEIGHBOR: 30,
            RelationshipType.BUSINESS: 35,
            RelationshipType.ACQUAINTANCE: 20,
            RelationshipType.OTHER: 25,
        }
        score += base_scores.get(self.relationship_type, 25)
        
        # 연락 빈도 점수 (최대 20점)
        if self.contact_frequency >= 4:
            score += 20
        elif self.contact_frequency >= 2:
            score += 15
        elif self.contact_frequency >= 1:
            score += 10
        else:
            score += 5
        
        # 이벤트 참여도 (최대 15점)
        if self.total_events >= 5:
            score += 15
        elif self.total_events >= 3:
            score += 10
        elif self.total_events >= 1:
            score += 5
        
        # 선물 교환 (최대 10점)
        total_gifts = self.total_gifts_given + self.total_gifts_received
        if total_gifts >= 5:
            score += 10
        elif total_gifts >= 3:
            score += 7
        elif total_gifts >= 1:
            score += 5
        
        # 관계 지속 기간 보너스 (최대 5점)
        if self.relationship_duration >= 365 * 5:  # 5년 이상
            score += 5
        elif self.relationship_duration >= 365 * 2:  # 2년 이상
            score += 3
        elif self.relationship_duration >= 365:  # 1년 이상
            score += 1
        
        # 특별 플래그 보너스
        if self.is_favorite:
            score += 5
        if self.is_important:
            score += 3
        
        # 0-100 범위로 제한
        self.intimacy_score = max(0, min(100, score))
        db.commit()
        
        return self.intimacy_score
    
    def update_stats(self, db):
        """통계 정보 업데이트"""
        from app.models.event import Event
        from app.models.ceremonial_money import CeremonialMoney
        
        # 이벤트 수 업데이트
        self.total_events = db.query(Event).filter(Event.relationship_id == self.id).count()
        
        # 경조사비 통계 업데이트
        ceremonial_money_given = db.query(CeremonialMoney).filter(CeremonialMoney.relationship_id == self.id, CeremonialMoney.giver_id == self.user_id).count()
        ceremonial_money_received = db.query(CeremonialMoney).filter(CeremonialMoney.relationship_id == self.id, CeremonialMoney.receiver_id == self.user_id).count()
        
        self.total_gifts_given = ceremonial_money_given
        self.total_gifts_received = ceremonial_money_received
        
        # 친밀도 점수 재계산
        self.calculate_intimacy_score(db)
        
        db.commit() 