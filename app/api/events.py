"""
Event API - 경조사 이벤트 관리
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.event import Event
from app.schemas.event import (
    CalendarEventCreate,
    CalendarEventResponse,
    EventCreate,
    EventResponse,
    EventUpdate,
)

router = APIRouter(tags=["경조사 이벤트"])


@router.post(
    "/",
    response_model=EventResponse,
    summary="이벤트 생성",
    description="새로운 경조사 이벤트를 생성합니다.",
)
def create_event(
    event: EventCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """새로운 이벤트 생성"""
    db_event = Event(**event.dict(), user_id=current_user_id)

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get(
    "/",
    response_model=list[EventResponse],
    summary="이벤트 목록 조회",
    description="사용자의 모든 경조사 이벤트를 조회합니다.",
)
def get_events(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    event_type: Optional[str] = Query(None, description="이벤트 타입 필터"),
    is_external: Optional[bool] = Query(None, description="외부 이벤트 여부"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """이벤트 목록 조회"""
    query = db.query(Event).filter(Event.user_id == current_user_id)

    if event_type:
        query = query.filter(Event.event_type == event_type)

    if is_external is not None:
        query = query.filter(Event.is_external == is_external)

    events = query.order_by(Event.event_date.desc()).offset(skip).limit(limit).all()

    return events


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="이벤트 상세 조회",
    description="특정 이벤트의 상세 정보를 조회합니다.",
)
def get_event(
    event_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """이벤트 상세 조회"""
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user_id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다")

    return event


@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="이벤트 수정",
    description="기존 이벤트를 수정합니다.",
)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """이벤트 수정"""
    db_event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user_id)
        .first()
    )

    if not db_event:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다")

    update_data = event_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)

    return db_event


@router.delete("/{event_id}", summary="이벤트 삭제", description="이벤트를 삭제합니다.")
def delete_event(
    event_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """이벤트 삭제"""
    db_event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user_id)
        .first()
    )

    if not db_event:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다")

    db.delete(db_event)
    db.commit()

    return {"message": "이벤트가 삭제되었습니다"}


@router.get(
    "/upcoming",
    response_model=list[EventResponse],
    summary="다가오는 이벤트 조회",
    description="다가오는 이벤트들을 조회합니다.",
)
def get_upcoming_events(
    limit: int = Query(10, ge=1, le=100, description="가져올 이벤트 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """다가오는 이벤트 조회"""
    events = Event.get_upcoming_events(current_user_id, limit)
    return events


@router.get(
    "/type/{event_type}",
    response_model=list[EventResponse],
    summary="타입별 이벤트 조회",
    description="특정 타입의 이벤트들을 조회합니다.",
)
def get_events_by_type(
    event_type: str,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """타입별 이벤트 조회"""
    events = Event.get_events_by_type(current_user_id, event_type)
    return events[skip : skip + limit]


@router.get(
    "/calendar",
    response_model=list[CalendarEventResponse],
    summary="캘린더 이벤트 조회",
    description="캘린더에 표시할 이벤트들을 조회합니다.",
)
def get_calendar_events(
    start_date: datetime = Query(..., description="시작 날짜"),
    end_date: datetime = Query(..., description="종료 날짜"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """캘린더 이벤트 조회"""
    events = (
        db.query(Event)
        .filter(
            Event.user_id == current_user_id,
            Event.event_date >= start_date,
            Event.event_date <= end_date,
        )
        .order_by(Event.event_date)
        .all()
    )

    # CalendarEventResponse 형태로 변환
    calendar_events = []
    for event in events:
        calendar_event = CalendarEventResponse(
            id=event.id,
            title=event.title,
            event_type=event.event_type,
            event_date=event.event_date,
            location=event.location,
            description=event.description,
            memo=event.memo,
            is_external=event.is_external,
            created_at=event.created_at.isoformat() if event.created_at else None,
            updated_at=event.updated_at.isoformat() if event.updated_at else None,
        )
        calendar_events.append(calendar_event)

    return calendar_events


@router.post(
    "/calendar",
    response_model=CalendarEventResponse,
    summary="캘린더 이벤트 생성",
    description="캘린더에 표시할 새로운 이벤트를 생성합니다.",
)
def create_calendar_event(
    event: CalendarEventCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """캘린더 이벤트 생성"""
    db_event = Event(
        title=event.title,
        event_type=event.event_type,
        event_date=event.event_date,
        location=event.location,
        description=event.description,
        memo=event.memo,
        is_external=event.is_external,
        user_id=current_user_id,
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return CalendarEventResponse(
        id=db_event.id,
        title=db_event.title,
        event_type=db_event.event_type,
        event_date=db_event.event_date,
        location=db_event.location,
        description=db_event.description,
        memo=db_event.memo,
        is_external=db_event.is_external,
        created_at=db_event.created_at.isoformat() if db_event.created_at else None,
        updated_at=db_event.updated_at.isoformat() if db_event.updated_at else None,
    )


@router.get(
    "/stats", summary="이벤트 통계", description="사용자의 이벤트 통계를 조회합니다."
)
def get_event_statistics(
    current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """이벤트 통계 조회"""
    # 전체 이벤트 수
    total_events = db.query(Event).filter(Event.user_id == current_user_id).count()

    # 이벤트 타입별 통계
    event_type_stats = {}
    event_types = (
        db.query(Event.event_type)
        .filter(Event.user_id == current_user_id)
        .distinct()
        .all()
    )

    for event_type in event_types:
        if event_type[0]:
            count = (
                db.query(Event)
                .filter(
                    Event.user_id == current_user_id, Event.event_type == event_type[0]
                )
                .count()
            )

            event_type_stats[event_type[0]] = count

    # 다가오는 이벤트 수
    upcoming_events = Event.get_upcoming_events(current_user_id, limit=1000)
    upcoming_count = len(upcoming_events)

    # 외부 이벤트 수
    external_events = (
        db.query(Event)
        .filter(Event.user_id == current_user_id, Event.is_external)
        .count()
    )

    return {
        "total_events": total_events,
        "event_type_stats": event_type_stats,
        "upcoming_events": upcoming_count,
        "external_events": external_events,
    }
