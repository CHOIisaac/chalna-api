"""
🤝 관계 API 라우터

인간관계 관리 엔드포인트
"""

from fastapi import APIRouter
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/")
async def get_relationships():
    """
    🤝 관계 목록 조회
    """
    return {"message": "관계 목록 조회 - 구현 예정"}


@router.post("/")
async def create_relationship():
    """
    ➕ 새 관계 생성
    """
    return {"message": "관계 생성 - 구현 예정"} 