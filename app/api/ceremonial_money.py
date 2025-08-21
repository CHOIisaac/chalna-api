"""
💰 경조사비/선물 API 라우터

경조사비, 축의금, 조의금 및 선물 관리 (가계부 기능 포함)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, extract, func
from typing import List, Optional
from datetime import datetime, date, timedelta
import calendar

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ceremonial_money import CeremonialMoney, CeremonialMoneyType, CeremonialMoneyDirection
from app.models.user import User
from app.models.event import Event
from app.models.relationship import Relationship
from app.schemas.ceremonial_money import (
    CeremonialMoneyCreate, CeremonialMoneyUpdate, CeremonialMoneyResponse, CeremonialMoneyInDB,
    FinancialTransactionBase, FinancialSummary, 
    MonthlyFinancialReport, YearlyFinancialReport,
    CeremonialMoneyQuickAdd, PendingReciprocals, CeremonialMoneyRecommendation
)

router = APIRouter()


@router.get("/", response_model=List[CeremonialMoneyResponse])
async def get_ceremonial_money(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ceremonial_money_type: Optional[CeremonialMoneyType] = None,
    direction: Optional[CeremonialMoneyDirection] = None,

    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """💰 경조사비/선물 목록 조회"""
    query = db.query(CeremonialMoney).options(
        joinedload(CeremonialMoney.event),
        joinedload(CeremonialMoney.relationship_info)
    ).filter(CeremonialMoney.user_id == current_user.id)
    
    # 필터 적용
    if ceremonial_money_type:
        query = query.filter(CeremonialMoney.ceremonial_money_type == ceremonial_money_type)
    if direction:
        query = query.filter(CeremonialMoney.direction == direction)

    if start_date:
        query = query.filter(CeremonialMoney.given_date >= start_date)
    if end_date:
        query = query.filter(CeremonialMoney.given_date <= end_date)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                CeremonialMoney.title.ilike(search_pattern),
                CeremonialMoney.description.ilike(search_pattern),
                CeremonialMoney.brand.ilike(search_pattern)
            )
        )
    
    ceremonial_money = query.order_by(CeremonialMoney.given_date.desc()).offset(skip).limit(limit).all()
    
    result = []
    for money in ceremonial_money:
        money_data = CeremonialMoneyResponse.from_orm(money)
        
        if money.event:
            money_data.event_title = money.event.title
        if money.relationship_info:
            money_data.relationship_name = money.relationship_info.contact_name
            money_data.relationship_type = money.relationship_info.relationship_type.value
        
        money_data.days_since_given = (date.today() - money.given_date.date()).days
        
        if (money.direction == CeremonialMoneyDirection.RECEIVED and 
            money.reciprocal_required and 
            not money.is_reciprocal):
            money_data.needs_reciprocation = True
            money_data.recommended_reciprocal_amount = money.amount
        
        result.append(money_data)
    
    return result


@router.get("/transactions", response_model=List[FinancialTransactionBase])
async def get_financial_transactions(
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    direction: Optional[CeremonialMoneyDirection] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """💰 가계부 거래 내역 조회"""
    query = db.query(CeremonialMoney).options(
        joinedload(CeremonialMoney.event),
        joinedload(CeremonialMoney.relationship_info)
    ).filter(CeremonialMoney.user_id == current_user.id)
    
    if start_date:
        query = query.filter(CeremonialMoney.given_date >= start_date)
    if end_date:
        query = query.filter(CeremonialMoney.given_date <= end_date)
    if direction:
        query = query.filter(CeremonialMoney.direction == direction)
    
    ceremonial_money = query.order_by(CeremonialMoney.given_date.desc()).limit(limit).all()
    
    transactions = []
    for money in ceremonial_money:
        transaction = FinancialTransactionBase(
            id=money.id,
            title=money.title,
            amount=money.amount,
            direction=money.direction,
            transaction_date=money.given_date,
            category=money.category,
            event_title=money.event.title if money.event else None,
            relationship_name=money.relationship_info.contact_name if money.relationship_info else None,
            memo=money.memo
            # UI 관련 필드들은 프론트엔드에서 처리
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
    
    ceremonial_money = db.query(CeremonialMoney).options(
        joinedload(CeremonialMoney.event)
    ).filter(
        CeremonialMoney.user_id == current_user.id,
        CeremonialMoney.given_date >= start_date,
        CeremonialMoney.given_date <= end_date
    ).all()
    
    total_income = sum(m.amount for m in ceremonial_money if m.direction == CeremonialMoneyDirection.RECEIVED)
    total_expense = sum(m.amount for m in ceremonial_money if m.direction == CeremonialMoneyDirection.GIVEN)
    net_amount = total_income - total_expense
    transaction_count = len(ceremonial_money)
    
    income_by_category = {}
    expense_by_category = {}
    expense_by_event_type = {}
    income_by_event_type = {}
    
    for money in ceremonial_money:
        category = money.category or "기타"
        
        if money.direction == CeremonialMoneyDirection.RECEIVED:
            income_by_category[category] = income_by_category.get(category, 0) + money.amount
        else:
            expense_by_category[category] = expense_by_category.get(category, 0) + money.amount
        
        if money.event:
            event_type = money.event.event_type.value
            if money.direction == CeremonialMoneyDirection.RECEIVED:
                income_by_event_type[event_type] = income_by_event_type.get(event_type, 0) + money.amount
            else:
                expense_by_event_type[event_type] = expense_by_event_type.get(event_type, 0) + money.amount
    
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


@router.post("/", response_model=CeremonialMoneyResponse)
async def create_ceremonial_money(
    money_data: CeremonialMoneyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """➕ 새 경조사비/선물 생성"""
    if money_data.event_id:
        event = db.query(Event).filter(
            Event.id == money_data.event_id,
            Event.user_id == current_user.id
        ).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="이벤트를 찾을 수 없습니다"
            )
    
    if money_data.relationship_id:
        relationship = db.query(Relationship).filter(
            Relationship.id == money_data.relationship_id,
            Relationship.user_id == current_user.id
        ).first()
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관계를 찾을 수 없습니다"
            )
    
    ceremonial_money = CeremonialMoney(
        user_id=current_user.id,
        **money_data.dict(exclude_unset=True)
    )
    
    db.add(ceremonial_money)
    db.commit()
    db.refresh(ceremonial_money)
    
    return CeremonialMoneyResponse.from_orm(ceremonial_money)


@router.post("/quick", response_model=CeremonialMoneyResponse)
async def create_quick_ceremonial_money(
    money_data: CeremonialMoneyQuickAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """⚡ 빠른 경조사비/선물 추가"""
    ceremonial_money = CeremonialMoney(
        user_id=current_user.id,
        title=money_data.title,
        ceremonial_money_type=money_data.ceremonial_money_type,
        direction=money_data.direction,
        amount=money_data.amount,
        given_date=money_data.given_date or datetime.now(),
        memo=money_data.memo
    )
    
    db.add(ceremonial_money)
    db.commit()
    db.refresh(ceremonial_money)
    
    return CeremonialMoneyResponse.from_orm(ceremonial_money)


@router.get("/pending-reciprocals", response_model=List[PendingReciprocals])
async def get_pending_reciprocals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔄 답례 대기 목록 조회"""
    received_money = db.query(CeremonialMoney).options(
        joinedload(CeremonialMoney.relationship_info)
    ).filter(
        CeremonialMoney.user_id == current_user.id,
        CeremonialMoney.direction == CeremonialMoneyDirection.RECEIVED,
        CeremonialMoney.reciprocal_required == True,
        CeremonialMoney.is_reciprocal == False
    ).all()
    
    pending_list = []
    today = date.today()
    
    for money in received_money:
        days_overdue = None
        urgency_level = "low"
        
        if money.reciprocal_deadline:
            days_overdue = (today - money.reciprocal_deadline.date()).days
            if days_overdue > 0:
                urgency_level = "overdue"
            elif days_overdue > -7:
                urgency_level = "high"
            elif days_overdue > -30:
                urgency_level = "medium"
        
        pending = PendingReciprocals(
            ceremonial_money_id=money.id,
            original_title=money.title,
            giver_name=money.relationship_info.contact_name if money.relationship_info else "알 수 없음",
            amount_received=money.amount,
            received_date=money.given_date,
            reciprocal_deadline=money.reciprocal_deadline,
            days_overdue=days_overdue if days_overdue and days_overdue > 0 else None,
            recommended_amount=money.amount,
            urgency_level=urgency_level
        )
        pending_list.append(pending)
    
    urgency_order = {"overdue": 0, "high": 1, "medium": 2, "low": 3}
    pending_list.sort(key=lambda x: urgency_order.get(x.urgency_level, 3))
    
    return pending_list


@router.get("/{ceremonial_money_id}", response_model=CeremonialMoneyResponse)
async def get_ceremonial_money_detail(
    ceremonial_money_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔍 특정 경조사비 조회"""
    ceremonial_money = db.query(CeremonialMoney).options(
        joinedload(CeremonialMoney.event),
        joinedload(CeremonialMoney.relationship_info)
    ).filter(
        CeremonialMoney.id == ceremonial_money_id,
        CeremonialMoney.user_id == current_user.id
    ).first()
    
    if not ceremonial_money:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="경조사비를 찾을 수 없습니다"
        )
    
    money_data = CeremonialMoneyResponse.from_orm(ceremonial_money)
    
    if ceremonial_money.event:
        money_data.event_title = ceremonial_money.event.title
    if ceremonial_money.relationship_info:
        money_data.relationship_name = ceremonial_money.relationship_info.contact_name
        money_data.relationship_type = ceremonial_money.relationship_info.relationship_type.value
    
    money_data.days_since_given = (date.today() - ceremonial_money.given_date.date()).days
    
    return money_data


@router.put("/{ceremonial_money_id}", response_model=CeremonialMoneyResponse)
async def update_ceremonial_money(
    ceremonial_money_id: int,
    money_data: CeremonialMoneyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ 경조사비 정보 수정"""
    ceremonial_money = db.query(CeremonialMoney).filter(
        CeremonialMoney.id == ceremonial_money_id,
        CeremonialMoney.user_id == current_user.id
    ).first()
    
    if not ceremonial_money:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="경조사비를 찾을 수 없습니다"
        )
    
    update_data = money_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ceremonial_money, field, value)
    
    db.commit()
    db.refresh(ceremonial_money)
    
    return CeremonialMoneyResponse.from_orm(ceremonial_money)


@router.delete("/{ceremonial_money_id}")
async def delete_ceremonial_money(
    ceremonial_money_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ 경조사비 삭제"""
    ceremonial_money = db.query(CeremonialMoney).filter(
        CeremonialMoney.id == ceremonial_money_id,
        CeremonialMoney.user_id == current_user.id
    ).first()
    
    if not ceremonial_money:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="경조사비를 찾을 수 없습니다"
        )
    
    db.delete(ceremonial_money)
    db.commit()
    
    return {"message": "경조사비가 성공적으로 삭제되었습니다"}
