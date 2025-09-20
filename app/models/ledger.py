"""
Ledger 모델 - 경조사비 수입지출 장부
"""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.constants import EntryType, EventType
from app.core.database import Base


class Ledger(Base):
    """경조사비 수입지출 장부 모델"""

    __tablename__ = "ledgers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 장부 기록 정보
    amount = Column(Integer, nullable=False, comment="금액")
    entry_type = Column(
        String(20), nullable=False, comment="기록 타입 (income/expense: 수입/지출)"
    )

    # 경조사 정보
    event_type = Column(String(50), comment="경조사 타입 (결혼식, 장례식, 돌잔치 등)")
    event_date = Column(Date, comment="경조사 날짜")
    counterparty_name = Column(String(100), comment="상대방 이름")
    counterparty_phone = Column(String(20), comment="상대방 전화번호")
    relationship_type = Column(String(50), comment="관계 타입")

    # 메타데이터
    memo = Column(Text, comment="메모")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="ledgers")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "entry_type": self.entry_type,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "counterparty_name": self.counterparty_name,
            "counterparty_phone": self.counterparty_phone,
            "relationship_type": self.relationship_type,
            "memo": self.memo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_received(self):
        """받은 금액인지 확인"""
        return self.entry_type == EntryType.RECEIVED

    @property
    def is_given(self):
        """준 금액인지 확인"""
        return self.entry_type == EntryType.GIVEN

    @property
    def formatted_amount(self):
        """포맷된 금액 (천 단위 콤마)"""
        return f"{self.amount:,}원"

    @property
    def entry_type_korean(self):
        """한국어 기록 타입"""
        return "수입" if self.is_income else "지출"

    @property
    def event_type_korean(self):
        """한국어 이벤트 타입"""
        try:
            return EventType(self.event_type).value
        except ValueError:
            return self.event_type

    @property
    def event_type_description(self):
        """이벤트 타입 설명"""
        from app.core.constants import EVENT_TYPE_DESCRIPTIONS

        try:
            event_type = EventType(self.event_type)
            return EVENT_TYPE_DESCRIPTIONS.get(event_type, "설명 없음")
        except ValueError:
            return "설명 없음"

    @property
    def event_type_color(self):
        """이벤트 타입 색상"""
        from app.core.constants import EVENT_TYPE_COLORS

        try:
            event_type = EventType(self.event_type)
            return EVENT_TYPE_COLORS.get(event_type, "#A9A9A9")
        except ValueError:
            return "#A9A9A9"

    @property
    def default_amount(self):
        """기본 축의금/조의금 금액"""
        from app.core.constants import EVENT_TYPE_DEFAULT_AMOUNTS

        try:
            event_type = EventType(self.event_type)
            return EVENT_TYPE_DEFAULT_AMOUNTS.get(event_type, 30000)
        except ValueError:
            return 30000

    @staticmethod
    def get_ledger_statistics(user_id: int):
        """사용자의 장부 통계 반환"""
        from app.core.database import get_db

        db = next(get_db())

        # 전체 통계
        total_received = (
            db.query(Ledger)
            .filter(Ledger.user_id == user_id, Ledger.entry_type == EntryType.RECEIVED)
            .with_entities(func.sum(Ledger.amount))
            .scalar()
            or 0
        )

        total_given = (
            db.query(Ledger)
            .filter(Ledger.user_id == user_id, Ledger.entry_type == EntryType.GIVEN)
            .with_entities(func.sum(Ledger.amount))
            .scalar()
            or 0
        )

        # 경조사 타입별 통계
        event_type_stats = {}
        event_types = (
            db.query(Ledger.event_type)
            .filter(Ledger.user_id == user_id)
            .distinct()
            .all()
        )

        for event_type in event_types:
            if event_type[0]:
                received = (
                    db.query(Ledger)
                    .filter(
                        Ledger.user_id == user_id,
                        Ledger.event_type == event_type[0],
                        Ledger.entry_type == EntryType.RECEIVED,
                    )
                    .with_entities(func.sum(Ledger.amount))
                    .scalar()
                    or 0
                )

                given = (
                    db.query(Ledger)
                    .filter(
                        Ledger.user_id == user_id,
                        Ledger.event_type == event_type[0],
                        Ledger.entry_type == EntryType.GIVEN,
                    )
                    .with_entities(func.sum(Ledger.amount))
                    .scalar()
                    or 0
                )

                event_type_stats[event_type[0]] = {
                    "received": received,
                    "given": given,
                    "balance": received - given,
                }

        return {
            "total_received": total_received,
            "total_given": total_given,
            "balance": total_received - total_given,
            "event_type_stats": event_type_stats,
            "total_records": db.query(Ledger).filter(Ledger.user_id == user_id).count(),
        }
