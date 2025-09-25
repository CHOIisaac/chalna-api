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


@router.get("/top-items", summary="TOP 5 항목 조회", description="given/received별로 금액이 높은 상위 항목 조회")
async def get_top_items(
    limit: int = Query(5, description="조회할 항목 수 (기본값: 5)"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    TOP 5 항목 조회
    
    - **limit**: 조회할 항목 수
    - **given**: 나눔 TOP 항목들
    - **received**: 받음 TOP 항목들
    - **name**: 상대방 이름 + 이벤트 타입
    - **amount**: 금액
    - **type**: 축의금/조의금 구분
    """
    try:
        # limit 검증
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="limit은 1~50 사이여야 합니다")
        
        result = {
            "given": [],
            "received": []
        }
        
        # given/received별로 TOP 항목 조회
        for entry_type in ["given", "received"]:
            top_items = db.query(
                Ledger.counterparty_name,
                Ledger.event_type,
                Ledger.amount
            ).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type
                )
            ).order_by(
                Ledger.amount.desc()
            ).limit(limit).all()
            
            # 결과 데이터 구성
            for item in top_items:
                # 축의금/조의금 구분
                item_type = "조의금" if item.event_type == "장례식" else "축의금"
                
                result[entry_type].append({
                    "name": f"{item.counterparty_name} {item.event_type}",
                    "amount": int(item.amount),
                    "type": item_type
                })
        
        return {
            "success": True,
            "data": result,
            "message": f"TOP {limit} 항목 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TOP 항목 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/amount-distribution", summary="금액대별 분포 조회", description="given/received별로 금액대별 분포 조회")
async def get_amount_distribution(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    금액대별 분포 조회
    
    - **given**: 나눔 금액대별 분포
    - **received**: 받음 금액대별 분포
    - **range**: 금액대 구간
    - **count**: 해당 구간의 건수
    - **percentage**: 비율 (%)
    """
    try:
        result = {
            "given": [],
            "received": []
        }
        
        # given/received별로 금액대별 분포 조회
        for entry_type in ["given", "received"]:
            # 전체 건수 조회
            total_count = db.query(func.count(Ledger.id)).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type
                )
            ).scalar()
            
            if total_count == 0:
                result[entry_type] = []
                continue
            
            # 금액대별 분포 조회
            distribution = db.query(
                func.sum(case(
                    (Ledger.amount < 50000, 1),
                    else_=0
                )).label('under_50k'),
                func.sum(case(
                    (and_(Ledger.amount >= 50000, Ledger.amount < 100000), 1),
                    else_=0
                )).label('range_50k_to_100k'),
                func.sum(case(
                    (and_(Ledger.amount >= 100000, Ledger.amount < 200000), 1),
                    else_=0
                )).label('range_100k_to_200k'),
                func.sum(case(
                    (Ledger.amount >= 200000, 1),
                    else_=0
                )).label('over_200k')
            ).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type
                )
            ).first()
            
            # 결과 데이터 구성
            ranges = [
                {"range": "5만원 미만", "count": int(distribution.under_50k or 0)},
                {"range": "5-10만원", "count": int(distribution.range_50k_to_100k or 0)},
                {"range": "10-20만원", "count": int(distribution.range_100k_to_200k or 0)},
                {"range": "20만원 이상", "count": int(distribution.over_200k or 0)}
            ]
            
            for range_data in ranges:
                percentage = round((range_data["count"] / total_count) * 100, 1) if total_count > 0 else 0
                result[entry_type].append({
                    "range": range_data["range"],
                    "count": range_data["count"],
                    "percentage": percentage
                })
        
        return {
            "success": True,
            "data": result,
            "message": "금액대별 분포 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"금액대별 분포 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/relationship-breakdown", summary="관계별 분석 조회", description="given/received별로 관계별 통계 조회")
async def get_relationship_breakdown(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    관계별 분석 조회
    
    - **given**: 나눔 관계별 통계
    - **received**: 받음 관계별 통계
    - **relationship**: 관계 유형
    - **count**: 건수
    - **totalAmount**: 총액
    - **avgAmount**: 평균 금액
    """
    try:
        result = {
            "given": [],
            "received": []
        }
        
        # given/received별로 관계별 통계 조회
        for entry_type in ["given", "received"]:
            relationship_stats = db.query(
                Ledger.relationship_type,
                func.count(Ledger.id).label('count'),
                func.sum(Ledger.amount).label('total_amount'),
                func.avg(Ledger.amount).label('avg_amount')
            ).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type
                )
            ).group_by(
                Ledger.relationship_type
            ).order_by(
                func.sum(Ledger.amount).desc()
            ).all()
            
            # 결과 데이터 구성
            for stat in relationship_stats:
                relationship = stat.relationship_type or "기타"
                result[entry_type].append({
                    "relationship": relationship,
                    "count": int(stat.count),
                    "totalAmount": int(stat.total_amount or 0),
                    "avgAmount": int(stat.avg_amount or 0)
                })
        
        return {
            "success": True,
            "data": result,
            "message": "관계별 분석 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관계별 분석 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/personal-details", summary="개인별 상세 조회", description="given/received별로 개인별 통계 조회")
async def get_personal_details(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    개인별 상세 조회
    
    - **given**: 나눔 개인별 통계
    - **received**: 받음 개인별 통계
    - **name**: 상대방 이름
    - **total**: 총액
    - **count**: 건수
    - **avg**: 평균 금액
    - **relationship**: 관계 유형
    """
    try:
        result = {
            "given": [],
            "received": []
        }
        
        # given/received별로 개인별 통계 조회
        for entry_type in ["given", "received"]:
            personal_stats = db.query(
                Ledger.counterparty_name,
                Ledger.relationship_type,
                func.count(Ledger.id).label('count'),
                func.sum(Ledger.amount).label('total'),
                func.avg(Ledger.amount).label('avg')
            ).filter(
                and_(
                    Ledger.user_id == user_id,
                    Ledger.entry_type == entry_type
                )
            ).group_by(
                Ledger.counterparty_name,
                Ledger.relationship_type
            ).order_by(
                func.sum(Ledger.amount).desc()
            ).all()
            
            # 결과 데이터 구성
            for stat in personal_stats:
                result[entry_type].append({
                    "name": stat.counterparty_name,
                    "total": int(stat.total or 0),
                    "count": int(stat.count),
                    "avg": int(stat.avg or 0),
                    "relationship": stat.relationship_type or "기타"
                })
        
        return {
            "success": True,
            "data": result,
            "message": "개인별 상세 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"개인별 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/events", summary="이벤트별 기록 조회", description="이벤트 타입별 통계 조회")
async def get_events_stats(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    이벤트별 기록 조회
    
    - **type**: 이벤트 타입 (결혼식, 출산, 장례식, 돌잔치, 생일, 기타)
    - **count**: 건수
    - **avgAmount**: 평균 금액
    """
    try:
        # 이벤트별 통계 조회
        event_stats = db.query(
            Ledger.event_type,
            func.count(Ledger.id).label('count'),
            func.avg(Ledger.amount).label('avg_amount')
        ).filter(
            Ledger.user_id == user_id
        ).group_by(
            Ledger.event_type
        ).order_by(
            func.count(Ledger.id).desc()
        ).all()
        
        # 결과 데이터 구성
        result = []
        for stat in event_stats:
            event_type = stat.event_type or "기타"
            result.append({
                "type": event_type,
                "count": int(stat.count),
                "avgAmount": int(stat.avg_amount or 0)
            })
        
        return {
            "success": True,
            "data": result,
            "message": "이벤트별 통계 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이벤트별 통계 조회 중 오류가 발생했습니다: {str(e)}")