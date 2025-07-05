"""
🎁 선물 API 라우터

선물 관리 엔드포인트
"""

from fastapi import APIRouter
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/")
async def get_gifts():
    """
    🎁 선물 목록 조회
    """
    return {"message": "선물 목록 조회 - 구현 예정"}


@router.post("/")
async def create_gift():
    """
    ➕ 새 선물 생성
    """
    return {"message": "선물 생성 - 구현 예정"} 