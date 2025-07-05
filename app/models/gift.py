"""
🎁 선물 모델

선물 및 축의금 정보를 관리합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class GiftType(enum.Enum):
    """선물 유형"""
    CASH = "cash"                     # 현금
    GIFT_CARD = "gift_card"           # 상품권
    PRODUCT = "product"               # 물품
    FLOWERS = "flowers"               # 꽃
    FOOD = "food"                     # 음식
    SERVICE = "service"               # 서비스
    OTHER = "other"                   # 기타


class GiftStatus(enum.Enum):
    """선물 상태"""
    PLANNED = "planned"               # 계획됨
    PURCHASED = "purchased"           # 구매완료
    DELIVERED = "delivered"           # 전달완료
    RECEIVED = "received"             # 수령완료
    CANCELLED = "cancelled"           # 취소됨


class GiftDirection(enum.Enum):
    """선물 방향"""
    GIVEN = "given"                   # 준 선물
    RECEIVED = "received"             # 받은 선물


class Gift(Base):
    """
    선물 모델 - 주고받은 선물 관리
    """
    __tablename__ = "gifts"
    
    # 🔑 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    
    # 👥 주고받는 사람
    giver_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    
    # 🎁 선물 정보
    gift_type = Column(Enum(GiftType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 💰 금액 정보
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="KRW")
    
    # 🛒 구매 정보
    purchase_date = Column(DateTime)
    purchase_location = Column(String(200))
    receipt_url = Column(String(500))
    
    # 📦 배송 정보
    delivery_date = Column(DateTime)
    delivery_method = Column(String(100))  # 직접전달, 택배, 우편 등
    tracking_number = Column(String(100))
    
    # 🎯 상태 정보
    status = Column(Enum(GiftStatus), default=GiftStatus.PLANNED)
    direction = Column(Enum(GiftDirection), nullable=False)
    
    # 📝 메모 및 기록
    memo = Column(Text)
    occasion = Column(String(100))  # 선물 계기
    
    # 📸 미디어 정보
    photos = Column(Text)  # 사진 URL들 (JSON 형태)
    
    # 🏷️ 태그 및 분류
    tags = Column(Text)  # 태그들 (JSON 형태)
    category = Column(String(50))
    
    # 📊 평가 정보
    satisfaction_rating = Column(Integer)  # 1-5 점수
    reaction_rating = Column(Integer)  # 상대방 반응 1-5 점수
    
    # 🔄 답례 정보
    is_reciprocal = Column(Boolean, default=False)  # 답례인지 여부
    original_gift_id = Column(Integer, ForeignKey("gifts.id"))  # 원본 선물 ID
    expects_reciprocation = Column(Boolean, default=True)  # 답례 기대 여부
    
    # 🔔 리마인더 설정
    reminder_enabled = Column(Boolean, default=False)
    reminder_date = Column(DateTime)
    
    # 🕐 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 🔗 관계 설정
    user = relationship("User", foreign_keys=[user_id], back_populates="gifts_given")
    giver = relationship("User", foreign_keys=[giver_id], back_populates="gifts_given")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="gifts_received")
    relationship_info = relationship("Relationship", back_populates="gifts")
    event = relationship("Event", back_populates="gifts")
    
    # 답례 관계
    original_gift = relationship("Gift", remote_side=[id], backref="reciprocal_gifts")
    
    def __repr__(self):
        return f"<Gift(id={self.id}, name={self.name}, amount={self.amount}, direction={self.direction})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "relationship_id": self.relationship_id,
            "event_id": self.event_id,
            "giver_id": self.giver_id,
            "receiver_id": self.receiver_id,
            "gift_type": self.gift_type.value,
            "name": self.name,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "purchase_date": self.purchase_date,
            "purchase_location": self.purchase_location,
            "receipt_url": self.receipt_url,
            "delivery_date": self.delivery_date,
            "delivery_method": self.delivery_method,
            "tracking_number": self.tracking_number,
            "status": self.status.value,
            "direction": self.direction.value,
            "memo": self.memo,
            "occasion": self.occasion,
            "photos": self.photos,
            "tags": self.tags,
            "category": self.category,
            "satisfaction_rating": self.satisfaction_rating,
            "reaction_rating": self.reaction_rating,
            "is_reciprocal": self.is_reciprocal,
            "original_gift_id": self.original_gift_id,
            "expects_reciprocation": self.expects_reciprocation,
            "reminder_enabled": self.reminder_enabled,
            "reminder_date": self.reminder_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def is_overdue(self):
        """배송 지연 여부"""
        if self.status == GiftStatus.PURCHASED and self.delivery_date:
            return func.now() > self.delivery_date
        return False
    
    @property
    def days_since_given(self):
        """선물한 지 며칠 경과"""
        if self.delivery_date:
            delta = func.now() - self.delivery_date
            return delta.days
        return None
    
    @property
    def is_expensive(self):
        """고가 선물인지 여부 (10만원 이상)"""
        return self.amount >= 100000
    
    @property
    def is_recent(self):
        """최근 선물인지 여부 (30일 이내)"""
        days_since = self.days_since_given
        return days_since is not None and days_since <= 30
    
    def get_reciprocal_gifts(self, db):
        """관련 답례 선물 조회"""
        return db.query(Gift).filter(
            Gift.original_gift_id == self.id
        ).all()
    
    def needs_reciprocation(self, db):
        """답례가 필요한지 확인"""
        if not self.expects_reciprocation or self.direction != GiftDirection.RECEIVED:
            return False
        
        # 이미 답례를 했는지 확인
        reciprocal_gifts = self.get_reciprocal_gifts(db)
        return len(reciprocal_gifts) == 0
    
    def calculate_recommended_reciprocal_amount(self):
        """추천 답례 금액 계산"""
        if self.direction != GiftDirection.RECEIVED:
            return 0
        
        # 기본적으로 받은 금액과 비슷하게
        base_amount = self.amount
        
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
    
    def get_gift_history_with_contact(self, db):
        """해당 연락처와의 선물 주고받기 기록"""
        if not self.relationship_info:
            return []
        
        return db.query(Gift).filter(
            Gift.relationship_id == self.relationship_id
        ).order_by(Gift.created_at.desc()).all()
    
    def generate_thank_you_message(self):
        """감사 메시지 생성"""
        if self.direction != GiftDirection.RECEIVED:
            return ""
        
        gift_name = self.name or "선물"
        
        if self.gift_type == GiftType.CASH:
            return f"축의금 {self.amount:,}원 감사히 받았습니다. 소중한 마음 정말 고맙습니다."
        else:
            return f"{gift_name} 정말 감사합니다. 소중히 잘 쓰겠습니다."
    
    def update_status_timeline(self, new_status: GiftStatus, db):
        """상태 변경 타임라인 업데이트"""
        self.status = new_status
        
        if new_status == GiftStatus.PURCHASED:
            self.purchase_date = func.now()
        elif new_status == GiftStatus.DELIVERED:
            self.delivery_date = func.now()
        
        self.updated_at = func.now()
        db.commit()
    
    @staticmethod
    def get_gift_statistics(user_id: int, db):
        """사용자의 선물 통계"""
        given_gifts = db.query(Gift).filter(
            Gift.user_id == user_id,
            Gift.direction == GiftDirection.GIVEN
        ).all()
        
        received_gifts = db.query(Gift).filter(
            Gift.user_id == user_id,
            Gift.direction == GiftDirection.RECEIVED
        ).all()
        
        given_total = sum(gift.amount for gift in given_gifts)
        received_total = sum(gift.amount for gift in received_gifts)
        
        return {
            "given_count": len(given_gifts),
            "received_count": len(received_gifts),
            "given_total": given_total,
            "received_total": received_total,
            "balance": received_total - given_total,
            "average_given": given_total / len(given_gifts) if given_gifts else 0,
            "average_received": received_total / len(received_gifts) if received_gifts else 0,
        } 