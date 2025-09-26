"""
카카오 로그인 관련 Pydantic 스키마
"""

from typing import Optional
from pydantic import BaseModel, Field


class KakaoLoginRequest(BaseModel):
    """카카오 로그인 요청 스키마"""
    code: Optional[str] = Field(None, description="카카오 인증 코드 (웹용)")
    access_token: Optional[str] = Field(None, description="카카오 액세스 토큰 (모바일용)")


class KakaoUserInfo(BaseModel):
    """카카오 사용자 정보 스키마"""
    kakao_id: str = Field(..., description="카카오 사용자 ID")
    nickname: Optional[str] = Field(None, description="카카오 닉네임")
    profile_image: Optional[str] = Field(None, description="프로필 이미지 URL")


class KakaoLoginResponse(BaseModel):
    """카카오 로그인 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    user: dict = Field(..., description="사용자 정보")
    kakao_info: KakaoUserInfo = Field(..., description="카카오 사용자 정보")
    message: str = Field("카카오 로그인 성공", description="응답 메시지")


class KakaoLoginUrlResponse(BaseModel):
    """카카오 로그인 URL 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    login_url: str = Field(..., description="카카오 로그인 URL")
    message: str = Field("카카오 로그인 URL 생성 성공", description="응답 메시지")
