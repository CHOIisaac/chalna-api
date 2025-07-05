"""
🎉 이벤트 API 라우터

경조사 이벤트 관리 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.event import Event, EventType, EventStatus
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_events(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[EventType] = None,
    db: Session = Depends(get_db)
):
    """
    🎉 이벤트 목록 조회
    """
    query = db.query(Event).filter(Event.user_id == user_id)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    events = query.offset(skip).limit(limit).all()
    return [event.to_dict() for event in events]


@router.get("/upcoming")
async def get_upcoming_events(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    📅 다가오는 이벤트 조회
    """
    from datetime import datetime, timedelta
    
    end_date = datetime.now() + timedelta(days=days)
    
    events = db.query(Event).filter(
        Event.user_id == user_id,
        Event.event_date >= datetime.now(),
        Event.event_date <= end_date,
        Event.status != EventStatus.CANCELLED
    ).order_by(Event.event_date).all()
    
    return [event.to_dict() for event in events]


@router.post("/")
async def create_event(
    user_id: int,
    title: str,
    event_type: EventType,
    event_date: datetime,
    relationship_id: Optional[int] = None,
    description: Optional[str] = None,
    venue_name: Optional[str] = None,
    estimated_cost: Optional[float] = 0.0,
    db: Session = Depends(get_db)
):
    """
    ➕ 새 이벤트 생성
    """
    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 새 이벤트 생성
    new_event = Event(
        user_id=user_id,
        relationship_id=relationship_id,
        title=title,
        event_type=event_type,
        event_date=event_date,
        description=description,
        venue_name=venue_name,
        estimated_cost=estimated_cost
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return {
        "message": "이벤트가 생성되었습니다",
        "event": new_event.to_dict()
    }


@router.get("/{event_id}")
async def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    🎯 특정 이벤트 조회
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이벤트를 찾을 수 없습니다"
        )
    
    return event.to_dict()


@router.put("/{event_id}")
async def update_event(
    event_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    venue_name: Optional[str] = None,
    actual_cost: Optional[float] = None,
    status: Optional[EventStatus] = None,
    db: Session = Depends(get_db)
):
    """
    ✏️ 이벤트 정보 수정
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이벤트를 찾을 수 없습니다"
        )
    
    # 정보 업데이트
    if title is not None:
        event.title = title
    if description is not None:
        event.description = description
    if venue_name is not None:
        event.venue_name = venue_name
    if actual_cost is not None:
        event.actual_cost = actual_cost
    if status is not None:
        event.status = status
    
    db.commit()
    db.refresh(event)
    
    return {
        "message": "이벤트가 업데이트되었습니다",
        "event": event.to_dict()
    }


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    🗑️ 이벤트 삭제
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이벤트를 찾을 수 없습니다"
        )
    
    db.delete(event)
    db.commit()
    
    return {"message": "이벤트가 삭제되었습니다"} 