"""
🎉 이벤트 API 라우터

경조사 이벤트 관리 엔드포인트 (달력 연동 지원)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, extract, func
from typing import List, Optional
from datetime import datetime, date, timedelta
import calendar

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.event import Event, EventType, EventStatus, ParticipationStatus
from app.models.user import User
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventInDB,
    CalendarEventBase, CalendarEventsResponse, MonthlyCalendarResponse,
    EventQuickCreate
)

router = APIRouter()


# UI 관련 함수들 삭제 - 프론트엔드에서 처리


@router.get("/", response_model=List[EventResponse])
async def get_events(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[EventType] = None,
    status: Optional[EventStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    🎉 이벤트 목록 조회
    
    - 기간별 필터링 지원
    - 검색 기능 지원
    - 관계 정보 포함
    """
    query = db.query(Event).options(
        joinedload(Event.relationship)
    ).filter(Event.user_id == current_user.id)
    
    # 필터 적용
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if status:
        query = query.filter(Event.status == status)
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern),
                Event.venue_name.ilike(search_pattern)
            )
        )
    
    # 최신 순으로 정렬
    events = query.order_by(Event.event_date.desc()).offset(skip).limit(limit).all()
    
    # 응답 데이터 구성
    result = []
    for event in events:
        event_data = EventResponse.from_orm(event)
        
        # 관계 정보 추가
        if event.relationship:
            event_data.relationship_name = event.relationship.contact_name
            event_data.relationship_type = event.relationship.relationship_type.value
        
        # 계산된 필드 추가
        event_data.days_until_event = (event.event_date.date() - date.today()).days
        event_data.is_past_event = event.event_date.date() < date.today()
        
        if event.estimated_cost and event.actual_cost:
            event_data.cost_difference = event.actual_cost - event.estimated_cost
        
        result.append(event_data)
    
    return result


@router.get("/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    📅 다가오는 이벤트 조회
    """
    end_date = date.today() + timedelta(days=days)
    
    events = db.query(Event).options(
        joinedload(Event.relationship)
    ).filter(
        Event.user_id == current_user.id,
        Event.event_date >= date.today(),
        Event.event_date <= end_date,
        Event.status != EventStatus.CANCELLED
    ).order_by(Event.event_date.asc()).all()
    
    result = []
    for event in events:
        event_data = EventResponse.from_orm(event)
        event_data.days_until_event = (event.event_date.date() - date.today()).days
        
        if event.relationship:
            event_data.relationship_name = event.relationship.contact_name
            event_data.relationship_type = event.relationship.relationship_type.value
        
        result.append(event_data)
    
    return result


@router.get("/calendar/monthly", response_model=MonthlyCalendarResponse)
async def get_monthly_calendar(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📅 월별 달력 데이터 조회
    
    UI 달력 구성을 위한 최적화된 데이터 제공
    """
    # 월의 첫날과 마지막날 계산
    first_day = datetime(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num, 23, 59, 59)
    
    # 해당 월의 이벤트 조회
    events = db.query(Event).filter(
        Event.user_id == current_user.id,
        Event.event_date >= first_day,
        Event.event_date <= last_day
    ).order_by(Event.event_date.asc()).all()
    
    # 달력용 이벤트 데이터 변환
    calendar_events = []
    days_with_events = set()
    busy_days = []
    day_event_count = {}
    
    total_expenses = 0.0
    total_income = 0.0
    event_count_by_type = {}
    
    for event in events:
        # 달력 이벤트 객체 생성
        calendar_event = CalendarEventBase(
            id=event.id,
            title=event.title,
            event_type=event.event_type,
            event_date=event.event_date,
            start_time=event.start_time,
            end_time=event.end_time,
            status=event.status,
            participation_status=event.participation_status,
            gift_amount=event.gift_amount,
            venue_name=event.venue_name,
            is_all_day=(event.start_time is None)
            # color 제거 - 프론트엔드에서 event_type 기반으로 처리
        )
        calendar_events.append(calendar_event)
        
        # 날짜별 통계
        event_day = event.event_date.day
        days_with_events.add(event_day)
        day_event_count[event_day] = day_event_count.get(event_day, 0) + 1
        
        # 금액 통계
        if event.gift_amount:
            if event.participation_status == ParticipationStatus.ATTENDING:
                total_expenses += event.gift_amount
            # 받은 축의금은 별도 관리 (Gift 모델에서)
        
        # 이벤트 타입별 통계
        event_type_key = event.event_type.value
        event_count_by_type[event_type_key] = event_count_by_type.get(event_type_key, 0) + 1
    
    # 바쁜 날들 (2개 이상 이벤트)
    busy_days = [day for day, count in day_event_count.items() if count >= 2]
    
    return MonthlyCalendarResponse(
        events=calendar_events,
        total_count=len(calendar_events),
        period_start=first_day,
        period_end=last_day,
        total_expenses=total_expenses,
        total_income=total_income,
        net_amount=total_income - total_expenses,
        event_count_by_type=event_count_by_type,
        year=year,
        month=month,
        days_with_events=sorted(list(days_with_events)),
        busy_days=sorted(busy_days)
    )


@router.get("/calendar/week")
async def get_weekly_calendar(
    start_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📅 주별 달력 데이터 조회
    """
    end_date = start_date + timedelta(days=6)
    
    events = db.query(Event).filter(
        Event.user_id == current_user.id,
        Event.event_date >= start_date,
        Event.event_date <= end_date
    ).order_by(Event.event_date.asc()).all()
    
    calendar_events = []
    for event in events:
        calendar_event = CalendarEventBase(
            id=event.id,
            title=event.title,
            event_type=event.event_type,
            event_date=event.event_date,
            start_time=event.start_time,
            end_time=event.end_time,
            status=event.status,
            participation_status=event.participation_status,
            gift_amount=event.gift_amount,
            venue_name=event.venue_name
            # color 제거 - 프론트엔드에서 처리
        )
        calendar_events.append(calendar_event)
    
    return {
        "events": calendar_events,
        "week_start": start_date,
        "week_end": end_date,
        "total_count": len(calendar_events)
    }


@router.post("/", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ➕ 새 이벤트 생성
    """
    # 관계 ID 검증 (선택적)
    if event_data.relationship_id:
        relationship = db.query(Relationship).filter(
            Relationship.id == event_data.relationship_id,
            Relationship.user_id == current_user.id
        ).first()
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관계를 찾을 수 없습니다"
            )
    
    # 이벤트 생성
    event = Event(
        user_id=current_user.id,
        **event_data.dict(exclude_unset=True)
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # 응답 데이터 구성
    event_response = EventResponse.from_orm(event)
    event_response.days_until_event = (event.event_date.date() - date.today()).days
    event_response.is_past_event = event.event_date.date() < date.today()
    
    return event_response


@router.post("/quick", response_model=EventResponse)
async def create_quick_event(
    event_data: EventQuickCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⚡ 빠른 이벤트 생성 (달력에서 사용)
    """
    event = Event(
        user_id=current_user.id,
        title=event_data.title,
        event_type=event_data.event_type,
        event_date=event_data.event_date,
        gift_amount=event_data.gift_amount,
        memo=event_data.memo,
        status=EventStatus.PLANNED
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return EventResponse.from_orm(event)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔍 특정 이벤트 조회
    """
    event = db.query(Event).options(
        joinedload(Event.relationship)
    ).filter(
        Event.id == event_id,
        Event.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이벤트를 찾을 수 없습니다"
        )
    
    event_data = EventResponse.from_orm(event)
    
    # 관계 정보 추가
    if event.relationship:
        event_data.relationship_name = event.relationship.contact_name
        event_data.relationship_type = event.relationship.relationship_type.value
    
    # 계산된 필드 추가
    event_data.days_until_event = (event.event_date.date() - date.today()).days
    event_data.is_past_event = event.event_date.date() < date.today()
    
    if event.estimated_cost and event.actual_cost:
        event_data.cost_difference = event.actual_cost - event.estimated_cost
    
    return event_data


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ✏️ 이벤트 수정
    """
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이벤트를 찾을 수 없습니다"
        )
    
    # 수정 가능한 필드만 업데이트
    update_data = event_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    db.commit()
    db.refresh(event)
    
    return EventResponse.from_orm(event)


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🗑️ 이벤트 삭제
    """
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이벤트를 찾을 수 없습니다"
        )
    
    db.delete(event)
    db.commit()
    
    return {"message": "이벤트가 성공적으로 삭제되었습니다"}


@router.get("/stats/summary")
async def get_event_statistics(
    current_user: User = Depends(get_current_user),
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    📊 이벤트 통계 조회
    """
    query = db.query(Event).filter(Event.user_id == current_user.id)
    
    if year:
        query = query.filter(extract('year', Event.event_date) == year)
    
    events = query.all()
    
    # 통계 계산
    total_events = len(events)
    total_expenses = sum(e.gift_amount or 0 for e in events if e.participation_status == ParticipationStatus.ATTENDING)
    
    event_by_type = {}
    expense_by_type = {}
    
    for event in events:
        event_type = event.event_type.value
        event_by_type[event_type] = event_by_type.get(event_type, 0) + 1
        
        if event.gift_amount and event.participation_status == ParticipationStatus.ATTENDING:
            expense_by_type[event_type] = expense_by_type.get(event_type, 0) + event.gift_amount
    
    return {
        "total_events": total_events,
        "total_expenses": total_expenses,
        "average_expense_per_event": total_expenses / total_events if total_events > 0 else 0,
        "events_by_type": event_by_type,
        "expenses_by_type": expense_by_type,
        "year": year or "전체 기간"
    } 