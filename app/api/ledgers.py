"""
Ledger API - 경조사비 수입지출 장부 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.constants import EntryType
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.ledger import Ledger
from app.schemas.ledger import (
    LedgerCreate,
    LedgerQuickAdd,
    LedgerResponse,
    LedgerSearch,
    LedgerStatistics,
    LedgerUpdate,
)

router = APIRouter(tags=["장부 관리"])


@router.post(
    "/",
    response_model=LedgerResponse,
    summary="장부 기록 생성",
    description="새로운 경조사비 수입지출 기록을 생성합니다.",
)
def create_ledger(
    ledger: LedgerCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """새로운 장부 기록 생성"""
    db_ledger = Ledger(**ledger.dict(), user_id=current_user_id)

    db.add(db_ledger)
    db.commit()
    db.refresh(db_ledger)

    return db_ledger


@router.get(
    "/",
    response_model=list[LedgerResponse],
    summary="장부 목록 조회",
    description="사용자의 모든 장부 기록을 조회합니다.",
)
def get_ledgers(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """장부 목록 조회"""
    ledgers = (
        db.query(Ledger)
        .filter(Ledger.user_id == current_user_id)
        .order_by(Ledger.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ledgers


@router.get(
    "/{ledger_id}",
    response_model=LedgerResponse,
    summary="장부 상세 조회",
    description="특정 장부 기록의 상세 정보를 조회합니다.",
)
def get_ledger(
    ledger_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """장부 상세 조회"""
    ledger = (
        db.query(Ledger)
        .filter(Ledger.id == ledger_id, Ledger.user_id == current_user_id)
        .first()
    )

    if not ledger:
        raise HTTPException(status_code=404, detail="장부 기록을 찾을 수 없습니다")

    return ledger


@router.put(
    "/{ledger_id}",
    response_model=LedgerResponse,
    summary="장부 기록 수정",
    description="기존 장부 기록을 수정합니다.",
)
def update_ledger(
    ledger_id: int,
    ledger_update: LedgerUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """장부 기록 수정"""
    db_ledger = (
        db.query(Ledger)
        .filter(Ledger.id == ledger_id, Ledger.user_id == current_user_id)
        .first()
    )

    if not db_ledger:
        raise HTTPException(status_code=404, detail="장부 기록을 찾을 수 없습니다")

    update_data = ledger_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_ledger, field, value)

    db.commit()
    db.refresh(db_ledger)

    return db_ledger


@router.delete(
    "/{ledger_id}", summary="장부 기록 삭제", description="장부 기록을 삭제합니다."
)
def delete_ledger(
    ledger_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """장부 기록 삭제"""
    db_ledger = (
        db.query(Ledger)
        .filter(Ledger.id == ledger_id, Ledger.user_id == current_user_id)
        .first()
    )

    if not db_ledger:
        raise HTTPException(status_code=404, detail="장부 기록을 찾을 수 없습니다")

    db.delete(db_ledger)
    db.commit()

    return {"message": "장부 기록이 삭제되었습니다"}


@router.get(
    "/income",
    response_model=list[LedgerResponse],
    summary="수입 내역 조회",
    description="수입 내역만 조회합니다.",
)
def get_income_ledgers(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """수입 내역 조회"""
    ledgers = (
        db.query(Ledger)
        .filter(
            Ledger.user_id == current_user_id, Ledger.entry_type == EntryType.INCOME
        )
        .order_by(Ledger.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ledgers


@router.get(
    "/expense",
    response_model=list[LedgerResponse],
    summary="지출 내역 조회",
    description="지출 내역만 조회합니다.",
)
def get_expense_ledgers(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """지출 내역 조회"""
    ledgers = (
        db.query(Ledger)
        .filter(
            Ledger.user_id == current_user_id, Ledger.entry_type == EntryType.EXPENSE
        )
        .order_by(Ledger.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ledgers


@router.post(
    "/search",
    response_model=list[LedgerResponse],
    summary="장부 검색",
    description="조건에 맞는 장부 기록을 검색합니다.",
)
def search_ledgers(
    search: LedgerSearch,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """장부 검색"""
    query = db.query(Ledger).filter(Ledger.user_id == current_user_id)

    # 검색어 필터
    if search.q:
        search_pattern = f"%{search.q}%"
        query = query.filter(
            or_(
                Ledger.counterparty_name.ilike(search_pattern),
                Ledger.event_name.ilike(search_pattern),
                Ledger.location.ilike(search_pattern),
                Ledger.memo.ilike(search_pattern),
            )
        )

    # 기록 타입 필터
    if search.entry_type:
        query = query.filter(Ledger.entry_type == search.entry_type)

    # 경조사 타입 필터
    if search.event_type:
        query = query.filter(Ledger.event_type == search.event_type)

    # 날짜 범위 필터
    if search.start_date:
        query = query.filter(Ledger.event_date >= search.start_date)

    if search.end_date:
        query = query.filter(Ledger.event_date <= search.end_date)

    # 관계 타입 필터
    if search.relationship_type:
        query = query.filter(Ledger.relationship_type == search.relationship_type)

    ledgers = query.order_by(Ledger.created_at.desc()).offset(skip).limit(limit).all()

    return ledgers


@router.get(
    "/stats",
    response_model=LedgerStatistics,
    summary="장부 통계",
    description="사용자의 장부 통계를 조회합니다.",
)
def get_ledger_statistics(
    current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """장부 통계 조회"""
    return Ledger.get_ledger_statistics(current_user_id)


@router.post(
    "/quick-add",
    response_model=LedgerResponse,
    summary="빠른 장부 추가",
    description="간단한 정보로 장부 기록을 빠르게 추가합니다.",
)
def create_quick_ledger(
    ledger: LedgerQuickAdd,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """빠른 장부 추가"""
    db_ledger = Ledger(
        amount=ledger.amount,
        entry_type=ledger.entry_type,
        event_type=ledger.event_type,
        counterparty_name=ledger.counterparty_name,
        event_date=ledger.event_date,
        memo=ledger.memo,
        user_id=current_user_id,
    )

    db.add(db_ledger)
    db.commit()
    db.refresh(db_ledger)

    return db_ledger


@router.get(
    "/event-type/{event_type}",
    response_model=list[LedgerResponse],
    summary="경조사 타입별 조회",
    description="특정 경조사 타입의 장부 기록을 조회합니다.",
)
def get_ledgers_by_event_type(
    event_type: str,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """경조사 타입별 조회"""
    ledgers = (
        db.query(Ledger)
        .filter(Ledger.user_id == current_user_id, Ledger.event_type == event_type)
        .order_by(Ledger.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ledgers


@router.get(
    "/relationships",
    summary="관계별 통계",
    description="관계별 장부 통계를 조회합니다.",
)
def get_relationship_statistics(
    current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """관계별 통계 조회"""
    # 관계 타입별 통계
    relationship_stats = {}
    relationships = (
        db.query(Ledger.relationship_type)
        .filter(Ledger.user_id == current_user_id)
        .distinct()
        .all()
    )

    for relationship in relationships:
        if relationship[0]:
            income = (
                db.query(Ledger)
                .filter(
                    Ledger.user_id == current_user_id,
                    Ledger.relationship_type == relationship[0],
                    Ledger.entry_type == EntryType.INCOME,
                )
                .with_entities(func.sum(Ledger.amount))
                .scalar()
                or 0
            )

            expense = (
                db.query(Ledger)
                .filter(
                    Ledger.user_id == current_user_id,
                    Ledger.relationship_type == relationship[0],
                    Ledger.entry_type == EntryType.EXPENSE,
                )
                .with_entities(func.sum(Ledger.amount))
                .scalar()
                or 0
            )

            relationship_stats[relationship[0]] = {
                "income": income,
                "expense": expense,
                "balance": income - expense,
            }

    return relationship_stats
