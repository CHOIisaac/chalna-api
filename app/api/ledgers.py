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


@router.get("/", summary="장부 목록 조회 (필터링 및 검색 지원)")
def get_ledgers(
        # 기본 파라미터
        skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
        limit: int = Query(20, ge=1, le=100, description="가져올 항목 수"),

        # 필터링 파라미터 (프론트엔드 필터와 매칭)
        entry_type: Optional[str] = Query(None, description="기록 타입: given(나눔), received(받음)"),
        sort_by: str = Query("latest", description="정렬: latest(최신순), oldest(오래된순), highest(높은금액순), lowest(낮은금액순)"),

        # 검색 파라미터
        search: Optional[str] = Query(None, description="이름/행사명/장소/메모 검색"),

        # 추가 필터
        event_type: Optional[str] = Query(None, description="경조사 타입"),
        relationship_type: Optional[str] = Query(None, description="관계 타입"),
        start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),

        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """장부 목록 조회 - 통합 필터링 및 검색"""

    # 기본 쿼리
    query = db.query(Ledger).filter(Ledger.user_id == current_user_id)

    # 💰 기록 타입 필터링
    if entry_type == "given":
        query = query.filter(Ledger.entry_type == EntryType.GIVEN)
    elif entry_type == "received":
        query = query.filter(Ledger.entry_type == EntryType.RECEIVED)

    # 🔍 통합 검색
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Ledger.counterparty_name.ilike(search_pattern),
                Ledger.event_name.ilike(search_pattern),
                Ledger.location.ilike(search_pattern),
                Ledger.memo.ilike(search_pattern),
            )
        )

    # 🎭 경조사 타입 필터
    if event_type:
        query = query.filter(Ledger.event_type == event_type)

    # 👥 관계 타입 필터
    if relationship_type:
        query = query.filter(Ledger.relationship_type == relationship_type)

    # 📅 날짜 범위 필터
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Ledger.event_date >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 시작 날짜 형식")

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Ledger.event_date <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 종료 날짜 형식")

    # 📊 정렬 (금액순 정렬 추가!)
    if sort_by == "latest":
        query = query.order_by(Ledger.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Ledger.created_at.asc())
    elif sort_by == "highest":
        query = query.order_by(Ledger.amount.desc())  # 높은 금액순
    elif sort_by == "lowest":
        query = query.order_by(Ledger.amount.asc())  # 낮은 금액순
    else:
        query = query.order_by(Ledger.created_at.desc())  # 기본값

    # 총 개수 및 페이징
    total_count = query.count()
    ledgers = query.offset(skip).limit(limit).all()

    return {
        "success": True,
        "data": [LedgerResponse.from_orm(ledger).dict() for ledger in ledgers],
        "meta": {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_next": (skip + limit) < total_count,
            "filters_applied": {
                "entry_type": entry_type,
                "sort_by": sort_by,
                "search": search,
                "event_type": event_type,
                "relationship_type": relationship_type,
                "date_range": f"{start_date} ~ {end_date}" if start_date or end_date else None
            }
        }
    }


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
            Ledger.user_id == current_user_id, Ledger.entry_type == EntryType.RECEIVED
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
            Ledger.user_id == current_user_id, Ledger.entry_type == EntryType.GIVEN
        )
        .order_by(Ledger.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

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
                    Ledger.entry_type == EntryType.RECEIVED,
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
                    Ledger.entry_type == EntryType.GIVEN,
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
