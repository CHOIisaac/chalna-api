"""
🎁 선물/축의금 API 라우터

선물 관리 및 가계부 기능 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, extract, func
from typing import List, Optional
from datetime import datetime, date, timedelta
import calendar

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.gift import Gift, GiftType, GiftStatus, GiftDirection
from app.models.user import User
from app.models.event import Event
from app.models.relationship import Relationship
from app.schemas.gift import (
    GiftCreate, GiftUpdate, GiftResponse, GiftInDB,
    FinancialTransactionBase, FinancialSummary, 
    MonthlyFinancialReport, YearlyFinancialReport,
    GiftQuickAdd, PendingReciprocals, GiftRecommendation
)

router = APIRouter()


# UI 관련 함수들 삭제 - 프론트엔드에서 처리


@router.get("/", response_model=List[GiftResponse])
async def get_gifts(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    gift_type: Optional[GiftType] = None,
    direction: Optional[GiftDirection] = None,
    status: Optional[GiftStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """🎁 선물/축의금 목록 조회"""
    query = db.query(Gift).options(
        joinedload(Gift.event),
        joinedload(Gift.relationship)
    ).filter(Gift.user_id == current_user.id)
    
    # 필터 적용
    if gift_type:
        query = query.filter(Gift.gift_type == gift_type)
    if direction:
        query = query.filter(Gift.direction == direction)
    if status:
        query = query.filter(Gift.status == status)
    if start_date:
        query = query.filter(Gift.given_date >= start_date)
    if end_date:
        query = query.filter(Gift.given_date <= end_date)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Gift.title.ilike(search_pattern),
                Gift.description.ilike(search_pattern),
                Gift.brand.ilike(search_pattern)
            )
        )
    
    gifts = query.order_by(Gift.given_date.desc()).offset(skip).limit(limit).all()
    
    result = []
    for gift in gifts:
        gift_data = GiftResponse.from_orm(gift)
        
        if gift.event:
            gift_data.event_title = gift.event.title
        if gift.relationship:
            gift_data.relationship_name = gift.relationship.contact_name
            gift_data.relationship_type = gift.relationship.relationship_type.value
        
        gift_data.days_since_given = (date.today() - gift.given_date.date()).days
        
        if (gift.direction == GiftDirection.RECEIVED and 
            gift.status == GiftStatus.COMPLETED and 
            gift.reciprocal_required and 
            not gift.is_reciprocal):
            gift_data.needs_reciprocation = True
            gift_data.recommended_reciprocal_amount = gift.amount
        
        result.append(gift_data)
    
    return result


@router.get("/transactions", response_model=List[FinancialTransactionBase])
async def get_financial_transactions(
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    direction: Optional[GiftDirection] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """💰 가계부 거래 내역 조회"""
    query = db.query(Gift).options(
        joinedload(Gift.event),
        joinedload(Gift.relationship)
    ).filter(Gift.user_id == current_user.id)
    
    if start_date:
        query = query.filter(Gift.given_date >= start_date)
    if end_date:
        query = query.filter(Gift.given_date <= end_date)
    if direction:
        query = query.filter(Gift.direction == direction)
    
    gifts = query.order_by(Gift.given_date.desc()).limit(limit).all()
    
    transactions = []
    for gift in gifts:
        transaction = FinancialTransactionBase(
            id=gift.id,
            title=gift.title,
            amount=gift.amount,
            direction=gift.direction,
            transaction_date=gift.given_date,
            category=gift.category,
            event_title=gift.event.title if gift.event else None,
            relationship_name=gift.relationship.contact_name if gift.relationship else None,
            memo=gift.memo
            # transaction_color, transaction_icon 제거 - 프론트엔드에서 처리
        )
        transactions.append(transaction)
    
    return transactions


@router.get("/summary", response_model=FinancialSummary)
async def get_financial_summary(
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period_type: str = Query("monthly", regex="^(monthly|yearly|custom)$"),
    db: Session = Depends(get_db)
):
    """📊 가계부 요약 정보"""
    if not start_date or not end_date:
        today = date.today()
        if period_type == "monthly":
            start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        elif period_type == "yearly":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
    
    gifts = db.query(Gift).options(
        joinedload(Gift.event)
    ).filter(
        Gift.user_id == current_user.id,
        Gift.given_date >= start_date,
        Gift.given_date <= end_date,
        Gift.status == GiftStatus.COMPLETED
    ).all()
    
    total_income = sum(g.amount for g in gifts if g.direction == GiftDirection.RECEIVED)
    total_expense = sum(g.amount for g in gifts if g.direction == GiftDirection.GIVEN)
    net_amount = total_income - total_expense
    transaction_count = len(gifts)
    
    income_by_category = {}
    expense_by_category = {}
    expense_by_event_type = {}
    income_by_event_type = {}
    
    for gift in gifts:
        category = gift.category or "기타"
        
        if gift.direction == GiftDirection.RECEIVED:
            income_by_category[category] = income_by_category.get(category, 0) + gift.amount
        else:
            expense_by_category[category] = expense_by_category.get(category, 0) + gift.amount
        
        if gift.event:
            event_type = gift.event.event_type.value
            if gift.direction == GiftDirection.RECEIVED:
                income_by_event_type[event_type] = income_by_event_type.get(event_type, 0) + gift.amount
            else:
                expense_by_event_type[event_type] = expense_by_event_type.get(event_type, 0) + gift.amount
    
    months_diff = 1
    if period_type == "yearly":
        months_diff = 12
    elif period_type == "custom":
        months_diff = max(1, ((end_date - start_date).days // 30))
    
    return FinancialSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_amount=net_amount,
        transaction_count=transaction_count,
        period_start=datetime.combine(start_date, datetime.min.time()),
        period_end=datetime.combine(end_date, datetime.max.time()),
        period_type=period_type,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        expense_by_event_type=expense_by_event_type,
        income_by_event_type=income_by_event_type,
        average_monthly_expense=total_expense / months_diff,
        average_monthly_income=total_income / months_diff
    )


@router.post("/", response_model=GiftResponse)
async def create_gift(
    gift_data: GiftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """➕ 새 선물/축의금 생성"""
    if gift_data.event_id:
        event = db.query(Event).filter(
            Event.id == gift_data.event_id,
            Event.user_id == current_user.id
        ).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="이벤트를 찾을 수 없습니다"
            )
    
    if gift_data.relationship_id:
        relationship = db.query(Relationship).filter(
            Relationship.id == gift_data.relationship_id,
            Relationship.user_id == current_user.id
        ).first()
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관계를 찾을 수 없습니다"
            )
    
    gift = Gift(
        user_id=current_user.id,
        **gift_data.dict(exclude_unset=True)
    )
    
    db.add(gift)
    db.commit()
    db.refresh(gift)
    
    return GiftResponse.from_orm(gift)


@router.post("/quick", response_model=GiftResponse)
async def create_quick_gift(
    gift_data: GiftQuickAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """⚡ 빠른 선물/축의금 추가"""
    gift = Gift(
        user_id=current_user.id,
        title=gift_data.title,
        gift_type=gift_data.gift_type,
        direction=gift_data.direction,
        amount=gift_data.amount,
        given_date=gift_data.given_date or datetime.now(),
        memo=gift_data.memo,
        status=GiftStatus.COMPLETED
    )
    
    db.add(gift)
    db.commit()
    db.refresh(gift)
    
    return GiftResponse.from_orm(gift)


@router.get("/pending-reciprocals", response_model=List[PendingReciprocals])
async def get_pending_reciprocals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔄 답례 대기 목록 조회"""
    received_gifts = db.query(Gift).options(
        joinedload(Gift.relationship)
    ).filter(
        Gift.user_id == current_user.id,
        Gift.direction == GiftDirection.RECEIVED,
        Gift.status == GiftStatus.COMPLETED,
        Gift.reciprocal_required == True,
        Gift.is_reciprocal == False
    ).all()
    
    pending_list = []
    today = date.today()
    
    for gift in received_gifts:
        days_overdue = None
        urgency_level = "low"
        
        if gift.reciprocal_deadline:
            days_overdue = (today - gift.reciprocal_deadline.date()).days
            if days_overdue > 0:
                urgency_level = "overdue"
            elif days_overdue > -7:
                urgency_level = "high"
            elif days_overdue > -30:
                urgency_level = "medium"
        
        pending = PendingReciprocals(
            gift_id=gift.id,
            original_gift_title=gift.title,
            giver_name=gift.relationship.contact_name if gift.relationship else "알 수 없음",
            amount_received=gift.amount,
            received_date=gift.given_date,
            reciprocal_deadline=gift.reciprocal_deadline,
            days_overdue=days_overdue if days_overdue and days_overdue > 0 else None,
            recommended_amount=gift.amount,
            urgency_level=urgency_level
        )
        pending_list.append(pending)
    
    urgency_order = {"overdue": 0, "high": 1, "medium": 2, "low": 3}
    pending_list.sort(key=lambda x: urgency_order.get(x.urgency_level, 3))
    
    return pending_list


@router.get("/{gift_id}", response_model=GiftResponse)
async def get_gift(
    gift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔍 특정 선물 조회"""
    gift = db.query(Gift).options(
        joinedload(Gift.event),
        joinedload(Gift.relationship)
    ).filter(
        Gift.id == gift_id,
        Gift.user_id == current_user.id
    ).first()
    
    if not gift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="선물을 찾을 수 없습니다"
        )
    
    gift_data = GiftResponse.from_orm(gift)
    
    if gift.event:
        gift_data.event_title = gift.event.title
    if gift.relationship:
        gift_data.relationship_name = gift.relationship.contact_name
        gift_data.relationship_type = gift.relationship.relationship_type.value
    
    gift_data.days_since_given = (date.today() - gift.given_date.date()).days
    
    return gift_data


@router.put("/{gift_id}", response_model=GiftResponse)
async def update_gift(
    gift_id: int,
    gift_data: GiftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ 선물 정보 수정"""
    gift = db.query(Gift).filter(
        Gift.id == gift_id,
        Gift.user_id == current_user.id
    ).first()
    
    if not gift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="선물을 찾을 수 없습니다"
        )
    
    update_data = gift_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(gift, field, value)
    
    db.commit()
    db.refresh(gift)
    
    return GiftResponse.from_orm(gift)


@router.delete("/{gift_id}")
async def delete_gift(
    gift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ 선물 삭제"""
    gift = db.query(Gift).filter(
        Gift.id == gift_id,
        Gift.user_id == current_user.id
    ).first()
    
    if not gift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="선물을 찾을 수 없습니다"
        )
    
    db.delete(gift)
    db.commit()
    
    return {"message": "선물이 성공적으로 삭제되었습니다"}
