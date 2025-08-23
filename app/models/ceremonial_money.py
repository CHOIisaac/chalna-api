"""
💰 경조사비 모델

경조사비, 축의금, 조의금 및 선물 정보를 관리합니다.
이벤트 타입으로 자동 분류됩니다 (결혼식, 장례식, 생일 등)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class CeremonialMoneyDirection(enum.Enum):
    """경조사비 방향"""
    GIVEN = "given"                   # 준 것
    RECEIVED = "received"             # 받은 것


class CeremonialMoney(Base):
    """
    경조사비 모델 - 이벤트 타입으로 자동 분류
    """
    __tablename__ = "ceremonial_money"
    
    # 🔑 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)  # 필수로 변경
    
    # 👤 상대방 정보 (직접 저장)
    contact_name = Column(String(100), nullable=False)  # 상대방 이름
    contact_phone = Column(String(20))                  # 연락처 (선택)
    relationship_type = Column(String(50))              # 관계 (친구, 가족, 동료 등)
    
    # 💰 경조사비 정보
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 💰 금액 정보
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="KRW")
    
    # 📅 날짜 정보  
    given_date = Column(DateTime, nullable=False)  # 주고받은 날짜
    
    # 🎯 방향 정보
    direction = Column(Enum(CeremonialMoneyDirection), nullable=False)
    
    # 📝 메모 및 기록
    memo = Column(Text)
    occasion = Column(String(100))  # 경조사 계기 (결혼식, 장례식 등)
    
    # 🔄 답례 정보
    is_reciprocal = Column(Boolean, default=False)  # 답례인지 여부
    original_gift_id = Column(Integer, ForeignKey("ceremonial_money.id"))  # 원본 경조사비 ID
    reciprocal_required = Column(Boolean, default=False)  # 답례 필요 여부
    reciprocal_deadline = Column(DateTime)  # 답례 마감일
    
    # 🕐 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 🔗 관계 설정
    user = relationship("User", back_populates="ceremonial_money_given")
    event = relationship("Event", back_populates="ceremonial_money")
    
    # 답례 관계
    original_gift = relationship("CeremonialMoney", remote_side=[id], backref="reciprocal_gifts")
    
    def __repr__(self):
        return f"<CeremonialMoney(id={self.id}, title={self.title}, amount={self.amount}, direction={self.direction})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "relationship_type": self.relationship_type,
            "event_type": self.event.event_type.value if self.event else None,
            "title": self.title,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "given_date": self.given_date,
            "direction": self.direction.value,
            "memo": self.memo,
            "occasion": self.occasion,
            "is_reciprocal": self.is_reciprocal,
            "original_gift_id": self.original_gift_id,
            "reciprocal_required": self.reciprocal_required,
            "reciprocal_deadline": self.reciprocal_deadline,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def days_since_given(self):
        """경조사비 제공한 지 며칠 경과"""
        if self.given_date:
            delta = func.now() - self.given_date
            return delta.days
        return None
    
    def get_reciprocal_gifts(self, db):
        """관련 답례 경조사비 조회"""
        return db.query(CeremonialMoney).filter(
            CeremonialMoney.original_gift_id == self.id
        ).all()
    
    def needs_reciprocation(self, db):
        """답례가 필요한지 확인"""
        if not self.reciprocal_required or self.direction != CeremonialMoneyDirection.RECEIVED:
            return False
        
        # 이미 답례를 했는지 확인
        reciprocal_gifts = self.get_reciprocal_gifts(db)
        return len(reciprocal_gifts) == 0
    
    def calculate_recommended_reciprocal_amount(self):
        """추천 답례 금액 계산"""
        if self.direction != CeremonialMoneyDirection.RECEIVED:
            return 0
        
        # 기본적으로 받은 금액과 비슷하게
        base_amount = self.amount
        
        # 이벤트 타입에 따른 조정
        if self.event:
            from app.models.event import EventType
            event_type = self.event.event_type
            
            if event_type in [EventType.WEDDING, EventType.BABY_SHOWER, EventType.GRADUATION, 
                             EventType.HOUSEWARMING, EventType.ENGAGEMENT, EventType.OPENING]:
                # 축하 이벤트는 동일 금액 권장
                return int(base_amount)
            elif event_type == EventType.FUNERAL:
                # 조의금은 답례 불필요하거나 적게
                return int(base_amount * 0.3)
            elif event_type in [EventType.BIRTHDAY, EventType.ANNIVERSARY]:
                # 생일, 기념일은 비슷하게
                return int(base_amount * 0.8)
            else:
                # 기타 이벤트
                return int(base_amount * 0.7)
        
        # 관계에 따른 조정
        if self.relationship_info:
            relationship_type = self.relationship_info.relationship_type
            
            if relationship_type.value == "family":
                # 가족은 조금 더 넉넉하게
                return int(base_amount * 1.1)
            elif relationship_type.value == "friend":
                # 친구는 비슷하게
                return int(base_amount)
            elif relationship_type.value == "colleague":
                # 동료는 조금 적게
                return int(base_amount * 0.9)
            else:
                # 지인은 적게
                return int(base_amount * 0.8)
        
        return int(base_amount)
    
    def get_ceremonial_money_history_with_contact(self, db):
        """해당 연락처와의 경조사비 주고받기 기록"""
        if not self.relationship_info:
            return []
        
        return db.query(CeremonialMoney).filter(
            CeremonialMoney.relationship_id == self.relationship_id
        ).order_by(CeremonialMoney.created_at.desc()).all()
    
    def generate_thank_you_message(self):
        """감사 메시지 생성"""
        if self.direction != CeremonialMoneyDirection.RECEIVED:
            return ""
        
        title = self.title or "경조사비"
        
        if self.event:
            from app.models.event import EventType
            event_type = self.event.event_type
            
            if event_type == EventType.WEDDING:
                return f"결혼 축의금 {self.amount:,}원 감사히 받았습니다. 소중한 마음 정말 고맙습니다."
            elif event_type == EventType.FUNERAL:
                return f"조의금 {self.amount:,}원 감사히 받았습니다. 위로의 마음에 깊이 감사드립니다."
            elif event_type == EventType.BABY_SHOWER:
                return f"돌잔치 축의금 {self.amount:,}원 감사히 받았습니다. 아이의 성장을 축복해주셔서 고맙습니다."
            elif event_type == EventType.BIRTHDAY:
                return f"생일 축하금 {self.amount:,}원 감사히 받았습니다. 마음 깊이 고맙습니다."
            elif event_type in [EventType.GRADUATION, EventType.PROMOTION]:
                return f"축하금 {self.amount:,}원 감사히 받았습니다. 축하해주셔서 정말 고맙습니다."
            elif event_type == EventType.HOUSEWARMING:
                return f"새집 축하금 {self.amount:,}원 감사히 받았습니다. 새 출발을 축복해주셔서 고맙습니다."
            else:
                return f"{title} {self.amount:,}원 감사히 받았습니다."
        else:
            return f"{title} 감사히 받았습니다."
    

    
    @staticmethod
    def get_ceremonial_money_statistics(user_id: int, db):
        """사용자의 경조사비 통계"""
        given_money = db.query(CeremonialMoney).filter(
            CeremonialMoney.user_id == user_id,
            CeremonialMoney.direction == CeremonialMoneyDirection.GIVEN
        ).all()
        
        received_money = db.query(CeremonialMoney).filter(
            CeremonialMoney.user_id == user_id,
            CeremonialMoney.direction == CeremonialMoneyDirection.RECEIVED
        ).all()
        
        given_total = sum(money.amount for money in given_money)
        received_total = sum(money.amount for money in received_money)
        
        return {
            "given_count": len(given_money),
            "received_count": len(received_money),
            "given_total": given_total,
            "received_total": received_total,
            "balance": received_total - given_total,
            "average_given": given_total / len(given_money) if given_money else 0,
            "average_received": received_total / len(received_money) if received_money else 0,
        }
