"""
카카오 로그인 API 엔드포인트
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.kakao_auth_service import KakaoAuthService
from app.schemas.kakao_auth import (
    KakaoLoginRequest, 
    KakaoLoginResponse, 
    KakaoLoginUrlResponse
)

router = APIRouter()


@router.get("/login-url", response_model=KakaoLoginUrlResponse, summary="카카오 로그인 URL 생성", description="카카오 로그인을 위한 URL을 생성합니다")
async def get_kakao_login_url() -> KakaoLoginUrlResponse:
    """
    카카오 로그인 URL 생성
    
    웹에서 카카오 로그인을 사용할 때 필요한 URL을 생성합니다.
    """
    try:
        service = KakaoAuthService(None)  # URL 생성에는 DB가 필요하지 않음
        login_url = service.get_kakao_login_url()
        
        return KakaoLoginUrlResponse(
            success=True,
            login_url=login_url,
            message="카카오 로그인 URL 생성 성공"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카카오 로그인 URL 생성 실패: {str(e)}")


@router.post("/login", response_model=KakaoLoginResponse, summary="카카오 로그인 (모바일)", description="카카오 액세스 토큰으로 로그인합니다")
async def kakao_login_mobile(
    access_token: str,
    db: Session = Depends(get_db)
) -> KakaoLoginResponse:
    """
    카카오 로그인 (모바일 앱용)
    
    - **access_token**: 카카오 SDK에서 받은 액세스 토큰
    
    모바일 앱에서 카카오 SDK로 로그인 후 받은 액세스 토큰을 사용합니다.
    """
    try:
        service = KakaoAuthService(db)
        
        # 모바일 로그인: 액세스 토큰 직접 사용
        result = await service.login_with_kakao_token(access_token)
        
        return KakaoLoginResponse(
            success=True,
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=result["user"],
            kakao_info=result["kakao_info"],
            message="카카오 로그인 성공"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카카오 로그인 실패: {str(e)}")


@router.get("/callback", summary="카카오 로그인 콜백", description="카카오 로그인 후 리다이렉트되는 콜백 엔드포인트")
async def kakao_callback(
    code: str = Query(..., description="카카오 인증 코드"),
    error: str = Query(None, description="에러 코드"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    카카오 로그인 콜백
    
    카카오 로그인 후 리다이렉트되는 콜백 엔드포인트입니다.
    """
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"카카오 로그인 에러: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="인증 코드가 없습니다")
        
        service = KakaoAuthService(db)
        result = await service.login_with_kakao_code(code)
        
        # 실제로는 프론트엔드로 리다이렉트하거나 토큰을 전달해야 합니다
        return {
            "success": True,
            "message": "카카오 로그인 성공",
            "access_token": result["access_token"],
            "user": result["user"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카카오 로그인 콜백 처리 실패: {str(e)}")


@router.post("/test", summary="카카오 로그인 테스트", description="카카오 로그인 기능을 테스트합니다")
async def test_kakao_login(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    카카오 로그인 테스트 (모바일용)
    
    카카오 로그인 설정이 올바른지 확인합니다.
    """
    try:
        from app.core.config import settings
        
        # 설정 확인
        config_status = {
            "KAKAO_CLIENT_ID": bool(settings.KAKAO_CLIENT_ID),
            "KAKAO_CLIENT_SECRET": bool(settings.KAKAO_CLIENT_SECRET),
            "KAKAO_REDIRECT_URI": bool(settings.KAKAO_REDIRECT_URI)
        }
        
        return {
            "success": True,
            "message": "카카오 로그인 설정 확인 완료",
            "config_status": config_status,
            "mobile_test_instructions": {
                "step1": "모바일 앱에서 카카오 SDK 설치 및 설정",
                "step2": "카카오 로그인 버튼 구현",
                "step3": "로그인 성공 시 access_token 받기",
                "step4": "POST /api/v1/kakao/login에 access_token 전송",
                "step5": "JWT 토큰 받아서 API 인증에 사용"
            },
            "api_endpoints": {
                "login": "POST /api/v1/kakao/login",
                "test": "POST /api/v1/kakao/test"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"카카오 로그인 설정 오류: {str(e)}",
            "config_status": {
                "KAKAO_CLIENT_ID": bool(settings.KAKAO_CLIENT_ID),
                "KAKAO_CLIENT_SECRET": bool(settings.KAKAO_CLIENT_SECRET),
                "KAKAO_REDIRECT_URI": bool(settings.KAKAO_REDIRECT_URI)
            }
        }
