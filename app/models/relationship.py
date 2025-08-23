"""
🤝 관계 모델

사용자 간의 인간관계 네트워크를 관리합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
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
    NEIGHBOR = "neighbor"       # 이웃
    BUSINESS = "business"       # 비즈니스
    OTHER = "other"             # 기타


class Relationship(Base):
    """
    관계 모델 - 실용적인 인간관계 관리
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
    
    # 🏷️ 분류 정보
    category = Column(String(50))  # 카테고리 (예: 회사, 학교, 동호회 등)
    
    # 📅 중요 날짜들
    birthday = Column(DateTime)
    anniversary = Column(DateTime)  # 기념일 (첫만남, 결혼기념일 등)
    
    # 🎯 상태 정보
    is_favorite = Column(Boolean, default=False)  # 즐겨찾기
    is_active = Column(Boolean, default=True)     # 활성 상태
    
    # 💬 통계 정보 (자동 계산)
    total_events = Column(Integer, default=0)
    total_ceremonial_money_given = Column(Integer, default=0)
    total_ceremonial_money_received = Column(Integer, default=0)
    
    # 📝 메모
    memo = Column(Text)
    
    # 🔔 알림 설정
    birthday_alert = Column(Boolean, default=True)
    anniversary_alert = Column(Boolean, default=True)
    
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
            "category": self.category,
            "birthday": self.birthday,
            "anniversary": self.anniversary,
            "is_favorite": self.is_favorite,
            "is_active": self.is_active,
            "total_events": self.total_events,
            "total_ceremonial_money_given": self.total_ceremonial_money_given,
            "total_ceremonial_money_received": self.total_ceremonial_money_received,
            "memo": self.memo,
            "birthday_alert": self.birthday_alert,
            "anniversary_alert": self.anniversary_alert,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def ceremonial_money_balance(self):
        """경조사비 수지 (받은 것 - 준 것)"""
        return self.total_ceremonial_money_received - self.total_ceremonial_money_given
    
    def update_stats(self, db):
        """통계 정보 업데이트"""
        from app.models.event import Event
        from app.models.ceremonial_money import CeremonialMoney, CeremonialMoneyDirection
        
        # 이벤트 수 업데이트
        self.total_events = db.query(Event).filter(Event.relationship_id == self.id).count()
        
        # 경조사비 통계 업데이트
        ceremonial_money_given = db.query(CeremonialMoney).filter(
            CeremonialMoney.relationship_id == self.id, 
            CeremonialMoney.user_id == self.user_id,
            CeremonialMoney.direction == CeremonialMoneyDirection.GIVEN
        ).count()
        
        ceremonial_money_received = db.query(CeremonialMoney).filter(
            CeremonialMoney.relationship_id == self.id, 
            CeremonialMoney.user_id == self.user_id,
            CeremonialMoney.direction == CeremonialMoneyDirection.RECEIVED
        ).count()
        
        self.total_ceremonial_money_given = ceremonial_money_given
        self.total_ceremonial_money_received = ceremonial_money_received
        
        db.commit() 