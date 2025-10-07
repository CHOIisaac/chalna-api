"""
📊 엑셀 내보내기 API

통계 데이터를 엑셀 파일로 내보내는 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.excel_export_service import excel_export_service

router = APIRouter(prefix="/excel", tags=["엑셀 내보내기"])


@router.get("/export/all", summary="전체 통계 엑셀 내보내기", description="모든 통계 데이터를 엑셀 파일로 내보내기")
async def export_all_stats_to_excel(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    전체 통계 엑셀 내보내기
    
    다음 시트들을 포함한 엑셀 파일을 생성합니다:
    - 월별 통계
    - 총액 조회
    - TOP 5 항목
    - 금액대별 분포
    - 관계별 분석
    - 개인별 상세
    - 이벤트별 기록
    """
    try:
        # 엑셀 파일 생성
        excel_buffer = await excel_export_service.export_all_stats(user_id, db)
        
        # 파일명 생성 (현재 날짜/시간 포함)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chalna_stats_{current_time}.xlsx"
        
        # 스트리밍 응답으로 파일 다운로드
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"엑셀 파일 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/export/monthly", summary="월별 통계 엑셀 내보내기", description="월별 통계만 엑셀 파일로 내보내기")
async def export_monthly_stats_to_excel(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    월별 통계 엑셀 내보내기
    
    월별 축의금/조의금 추세 데이터를 엑셀 파일로 내보냅니다.
    """
    try:
        # 엑셀 파일 생성 (월별 통계만)
        excel_buffer = await excel_export_service.export_monthly_stats(user_id, db)
        
        # 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chalna_monthly_stats_{current_time}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"월별 통계 엑셀 파일 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/export/relationship", summary="관계별 분석 엑셀 내보내기", description="관계별 분석 데이터만 엑셀 파일로 내보내기")
async def export_relationship_stats_to_excel(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    관계별 분석 엑셀 내보내기
    
    관계별 통계 데이터를 엑셀 파일로 내보냅니다.
    """
    try:
        # 엑셀 파일 생성 (관계별 분석만)
        excel_buffer = await excel_export_service.export_relationship_stats(user_id, db)
        
        # 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chalna_relationship_stats_{current_time}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"관계별 분석 엑셀 파일 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/export/personal", summary="개인별 상세 엑셀 내보내기", description="개인별 상세 데이터만 엑셀 파일로 내보내기")
async def export_personal_stats_to_excel(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    개인별 상세 엑셀 내보내기
    
    개인별 통계 데이터를 엑셀 파일로 내보냅니다.
    """
    try:
        # 엑셀 파일 생성 (개인별 상세만)
        excel_buffer = await excel_export_service.export_personal_stats(user_id, db)
        
        # 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chalna_personal_stats_{current_time}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"개인별 상세 엑셀 파일 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/export/events", summary="이벤트별 기록 엑셀 내보내기", description="이벤트별 기록 데이터만 엑셀 파일로 내보내기")
async def export_events_stats_to_excel(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    이벤트별 기록 엑셀 내보내기
    
    이벤트별 통계 데이터를 엑셀 파일로 내보냅니다.
    """
    try:
        # 엑셀 파일 생성 (이벤트별 기록만)
        excel_buffer = await excel_export_service.export_events_stats(user_id, db)
        
        # 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chalna_events_stats_{current_time}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"이벤트별 기록 엑셀 파일 생성 중 오류가 발생했습니다: {str(e)}"
        )
