from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ledger import Ledger

router = APIRouter(prefix="/stats", tags=["통계"])


@router.get("/total-amounts", summary="나눔/받음 총액 조회", description="특정 연도의 나눔 또는 받음 총액을 이벤트 타입별로 조회")
async def get_total_amounts(
    type: str = Query(..., description="나눔/받음 타입 (given/received)"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    나눔/받음 총액 조회
    
    - **type**: given (나눔) 또는 received (받음)
    - **weddingTotal**: 축의금 총액 (결혼식, 돌잔치, 개업식 등)
    - **condolenceTotal**: 조의금 총액 (장례식)
    - **weddingCount**: 축의금 건수
    - **condolenceCount**: 조의금 건수
    """
    try:
        # 타입 검증
        if type not in ["given", "received"]:
            raise HTTPException(status_code=400, detail="type은 'given' 또는 'received'여야 합니다")
        
        # 최적화: 단일 쿼리로 축의금/조의금 통계 조회
        stats = db.query(
            func.sum(case(
                (Ledger.event_type != "장례식", Ledger.amount),
                else_=0
            )).label('wedding_total'),
            func.sum(case(
                (Ledger.event_type == "장례식", Ledger.amount),
                else_=0
            )).label('condolence_total'),
            func.count(case(
                (Ledger.event_type != "장례식", Ledger.id),
                else_=None
            )).label('wedding_count'),
            func.count(case(
                (Ledger.event_type == "장례식", Ledger.id),
                else_=None
            )).label('condolence_count')
        ).filter(
            and_(
                Ledger.user_id == user_id,
                Ledger.entry_type == type,
            )
        ).first()
        
        return {
            "success": True,
            "data": {
                "weddingTotal": int(stats.wedding_total or 0),
                "condolenceTotal": int(stats.condolence_total or 0),
                "weddingCount": int(stats.wedding_count or 0),
                "condolenceCount": int(stats.condolence_count or 0)
            },
            "message": f"{type} 총액 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"총액 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/monthly-wedding", summary="월별 축의금 추세", description="특정 연도의 월별 축의금 추세 조회")
async def get_monthly_wedding_trend(
    type: str = Query(..., description="나눔/받음 타입 (given/received)"),
    year: int = Query(..., description="조회할 연도"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    월별 축의금 추세 조회
    
    - **type**: given (나눔) 또는 received (받음)
    - **year**: 조회할 연도
    - **data**: 월별 축의금 데이터 (1월~12월)
    """
    try:
        # 타입 검증
        if type not in ["given", "received"]:
            raise HTTPException(status_code=400, detail="type은 'given' 또는 'received'여야 합니다")
        
        # 연도 검증
        current_year = datetime.now().year
        if year < 2020 or year > current_year + 1:
            raise HTTPException(status_code=400, detail=f"연도는 2020년부터 {current_year + 1}년까지 가능합니다")
        
        # 최적화: 단일 쿼리로 월별 축의금 통계 조회
        monthly_stats = db.query(
            extract('month', Ledger.created_at).label('month'),
            func.sum(Ledger.amount).label('amount')
        ).filter(
            and_(
                Ledger.user_id == user_id,
                Ledger.entry_type == type,
                Ledger.event_type != "장례식",  # 축의금 (장례식 제외)
                extract('year', Ledger.created_at) == year
            )
        ).group_by(
            extract('month', Ledger.created_at)
        ).order_by(
            extract('month', Ledger.created_at)
        ).all()
        
        # 월별 데이터 구성 (1월~12월, 없는 월은 0으로)
        monthly_data = []
        stats_dict = {int(stat.month): int(stat.amount) for stat in monthly_stats}
        
        month_names = ["1월", "2월", "3월", "4월", "5월", "6월", 
                      "7월", "8월", "9월", "10월", "11월", "12월"]
        
        for month_num in range(1, 13):
            monthly_data.append({
                "month": month_names[month_num - 1],
                "amount": stats_dict.get(month_num, 0)
            })
        
        return {
            "success": True,
            "data": monthly_data,
            "message": f"{year}년 월별 축의금 추세 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월별 축의금 추세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/monthly-condolence", summary="월별 조의금 추세", description="특정 연도의 월별 조의금 추세 조회")
async def get_monthly_condolence_trend(
    type: str = Query(..., description="나눔/받음 타입 (given/received)"),
    year: int = Query(..., description="조회할 연도"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    월별 조의금 추세 조회
    
    - **type**: given (나눔) 또는 received (받음)
    - **year**: 조회할 연도
    - **data**: 월별 조의금 데이터 (1월~12월)
    """
    try:
        # 타입 검증
        if type not in ["given", "received"]:
            raise HTTPException(status_code=400, detail="type은 'given' 또는 'received'여야 합니다")
        
        # 연도 검증
        current_year = datetime.now().year
        if year < 2020 or year > current_year + 1:
            raise HTTPException(status_code=400, detail=f"연도는 2020년부터 {current_year + 1}년까지 가능합니다")
        
        # 최적화: 단일 쿼리로 월별 조의금 통계 조회
        monthly_stats = db.query(
            extract('month', Ledger.created_at).label('month'),
            func.sum(Ledger.amount).label('amount')
        ).filter(
            and_(
                Ledger.user_id == user_id,
                Ledger.entry_type == type,
                Ledger.event_type == "장례식",  # 조의금 (장례식만)
                extract('year', Ledger.created_at) == year
            )
        ).group_by(
            extract('month', Ledger.created_at)
        ).order_by(
            extract('month', Ledger.created_at)
        ).all()
        
        # 월별 데이터 구성 (1월~12월, 없는 월은 0으로)
        monthly_data = []
        stats_dict = {int(stat.month): int(stat.amount) for stat in monthly_stats}
        
        month_names = ["1월", "2월", "3월", "4월", "5월", "6월", 
                      "7월", "8월", "9월", "10월", "11월", "12월"]
        
        for month_num in range(1, 13):
            monthly_data.append({
                "month": month_names[month_num - 1],
                "amount": stats_dict.get(month_num, 0)
            })
        
        return {
            "success": True,
            "data": monthly_data,
            "message": f"{year}년 월별 조의금 추세 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월별 조의금 추세 조회 중 오류가 발생했습니다: {str(e)}")
