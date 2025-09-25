from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ledger import Ledger

router = APIRouter(prefix="/stats", tags=["통계"])


@router.get("/monthly", summary="월별 통계 조회", description="월별 축의금/조의금 추세를 given/received별, 연도별로 조회")
async def get_monthly_stats(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    월별 통계 조회
    
    - **wedding**: 축의금 월별 데이터 (given/received)
    - **condolence**: 조의금 월별 데이터 (given/received)
    - **2024, 2025**: 연도별 전체 데이터 (given/received)
    """
    try:
        result = {
            "wedding": {"given": [], "received": []},
            "condolence": {"given": [], "received": []}
        }
        
        # 월별 데이터 구성 함수
        def format_monthly_data(stats):
            month_names = ["1월", "2월", "3월", "4월", "5월", "6월", 
                          "7월", "8월", "9월", "10월", "11월", "12월"]
            return [{"month": month_names[int(stat.month) - 1], "amount": int(stat.amount)} for stat in stats]
        
        # 축의금 월별 통계 조회 (given/received)
        for entry_type in ["given", "received"]:
            wedding_stats = db.query(
                extract('month', Ledger.created_at).label('month'),
                func.sum(Ledger.amount).label('amount')
            ).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type,
                    Ledger.event_type != "장례식"  # 축의금 (장례식 제외)
                )
            ).group_by(
                extract('month', Ledger.created_at)
            ).order_by(
                extract('month', Ledger.created_at)
            ).all()
            
            result["wedding"][entry_type] = format_monthly_data(wedding_stats)
        
        # 조의금 월별 통계 조회 (given/received)
        for entry_type in ["given", "received"]:
            condolence_stats = db.query(
                extract('month', Ledger.created_at).label('month'),
                func.sum(Ledger.amount).label('amount')
            ).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type,
                    Ledger.event_type == "장례식"  # 조의금 (장례식만)
                )
            ).group_by(
                extract('month', Ledger.created_at)
            ).order_by(
                extract('month', Ledger.created_at)
            ).all()
            
            result["condolence"][entry_type] = format_monthly_data(condolence_stats)
        
        # 연도별 전체 통계 조회 (실제 데이터가 있는 연도만)
        year_stats_query = db.query(
            extract('year', Ledger.created_at).label('year'),
            extract('month', Ledger.created_at).label('month'),
            Ledger.entry_type,
            func.sum(Ledger.amount).label('amount')
        ).filter(
            Ledger.user_id == user_id
        ).group_by(
            extract('year', Ledger.created_at),
            extract('month', Ledger.created_at),
            Ledger.entry_type
        ).order_by(
            extract('year', Ledger.created_at),
            extract('month', Ledger.created_at)
        ).all()
        
        # 연도별 데이터 구성
        year_data = {}
        for stat in year_stats_query:
            year = str(int(stat.year))
            entry_type = stat.entry_type
            
            if year not in year_data:
                year_data[year] = {"given": [], "received": []}
            
            month_names = ["1월", "2월", "3월", "4월", "5월", "6월", 
                          "7월", "8월", "9월", "10월", "11월", "12월"]
            
            year_data[year][entry_type].append({
                "month": month_names[int(stat.month) - 1],
                "amount": int(stat.amount)
            })
        
        # 결과에 연도별 데이터 추가
        result.update(year_data)
        
        return {
            "success": True,
            "data": result,
            "message": "월별 통계 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월별 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/total-amounts", summary="총액 조회", description="given/received별 축의금/조의금 총액과 건수 조회")
async def get_total_amounts(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    총액 조회
    
    - **given**: 나눔 데이터 (wedding/condolence)
    - **received**: 받음 데이터 (wedding/condolence)
    - **total**: 총액
    - **count**: 건수
    """
    try:
        # 최적화: 단일 쿼리로 given/received별 축의금/조의금 통계 조회
        stats = db.query(
            Ledger.entry_type,
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
            Ledger.user_id == user_id
        ).group_by(
            Ledger.entry_type
        ).all()
        
        # 결과 데이터 구성
        result = {
            "given": {
                "wedding": {"total": 0, "count": 0},
                "condolence": {"total": 0, "count": 0}
            },
            "received": {
                "wedding": {"total": 0, "count": 0},
                "condolence": {"total": 0, "count": 0}
            }
        }
        
        for stat in stats:
            entry_type = stat.entry_type
            result[entry_type]["wedding"]["total"] = int(stat.wedding_total or 0)
            result[entry_type]["wedding"]["count"] = int(stat.wedding_count or 0)
            result[entry_type]["condolence"]["total"] = int(stat.condolence_total or 0)
            result[entry_type]["condolence"]["count"] = int(stat.condolence_count or 0)
        
        return {
            "success": True,
            "data": result,
            "message": "총액 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"총액 조회 중 오류가 발생했습니다: {str(e)}")