"""
카카오 로그인 서비스
"""

import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.models.user import User
from app.models.user_settings import UserSettings
from app.core.security import create_access_token


class KakaoAuthService:
    """카카오 로그인 서비스 클래스"""
    
    KAKAO_API_BASE_URL = "https://kapi.kakao.com"
    KAKAO_OAUTH_BASE_URL = "https://kauth.kakao.com"
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_kakao_user_info(self, access_token: str) -> Dict[str, Any]:
        """카카오 API로 사용자 정보 조회"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.KAKAO_API_BASE_URL}/v2/user/me",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise Exception("유효하지 않은 카카오 액세스 토큰입니다. 다시 로그인해주세요.")
                elif e.response.status_code == 403:
                    raise Exception("카카오 API 접근 권한이 없습니다.")
                else:
                    raise Exception(f"카카오 API 호출 실패 (상태코드: {e.response.status_code})")
            except httpx.HTTPError as e:
                raise Exception(f"카카오 API 호출 실패: {e}")
    
    async def get_kakao_access_token(self, code: str) -> Dict[str, Any]:
        """카카오 인증 코드로 액세스 토큰 발급"""
        if not settings.KAKAO_CLIENT_ID or not settings.KAKAO_CLIENT_SECRET:
            raise Exception("카카오 클라이언트 설정이 필요합니다")
        
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "client_secret": settings.KAKAO_CLIENT_SECRET,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.KAKAO_OAUTH_BASE_URL}/oauth/token",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"카카오 토큰 발급 실패: {e}")
    
    def find_or_create_user(self, kakao_user_info: Dict[str, Any]) -> User:
        """카카오 사용자 정보로 기존 사용자 찾기 또는 새 사용자 생성"""
        kakao_id = str(kakao_user_info.get("id"))
        kakao_account = kakao_user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        
        # 카카오 ID로 기존 사용자 찾기
        existing_user = self.db.query(User).filter(
            or_(
                User.email == kakao_account.get("email"),
                User.username == f"kakao_{kakao_id}"
            )
        ).first()
        
        if existing_user:
            # 기존 사용자 정보 업데이트
            if not existing_user.email and kakao_account.get("email"):
                existing_user.email = kakao_account.get("email")
            if not existing_user.full_name and profile.get("nickname"):
                existing_user.full_name = profile.get("nickname")
            self.db.commit()
            return existing_user
        
        # 새 사용자 생성
        email = kakao_account.get("email")
        nickname = profile.get("nickname", "카카오사용자")
        
        # 이메일이 없으면 임시 이메일 생성
        if not email:
            email = f"kakao_{kakao_id}@kakao.temp"
        
        new_user = User(
            username=f"kakao_{kakao_id}",
            email=email,
            full_name=nickname,
            hashed_password="",  # 소셜 로그인은 비밀번호 없음
            is_verified=True,  # 카카오 인증된 사용자
            is_active=True
        )
        
        self.db.add(new_user)
        self.db.flush()  # ID 생성을 위해 flush
        
        # 🔧 UserSettings 자동 생성 (카카오 로그인 사용자도 기본 설정 필요)
        user_settings = UserSettings(
            user_id=new_user.id,
            notifications_enabled=True,
            event_reminders=True,
            reminder_hours_before=24
        )
        self.db.add(user_settings)
        
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user
    
    async def login_with_kakao_code(self, code: str) -> Dict[str, Any]:
        """카카오 인증 코드로 로그인"""
        try:
            # 1. 카카오 액세스 토큰 발급
            token_response = await self.get_kakao_access_token(code)
            access_token = token_response.get("access_token")
            
            if not access_token:
                raise Exception("카카오 액세스 토큰을 받지 못했습니다")
            
            # 2. 카카오 사용자 정보 조회
            kakao_user_info = await self.get_kakao_user_info(access_token)
            
            # 3. 사용자 찾기 또는 생성
            user = self.find_or_create_user(kakao_user_info)
            
            # 4. JWT 토큰 생성
            jwt_token = create_access_token(data={"sub": str(user.id)})
            
            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active
                },
                "kakao_info": kakao_user_info  # 원본 카카오 API 응답 전달
            }
            
        except Exception as e:
            raise Exception(f"카카오 로그인 실패: {str(e)}")
    
    async def login_with_kakao_token(self, kakao_access_token: str) -> Dict[str, Any]:
        """카카오 액세스 토큰으로 직접 로그인 (모바일 앱용)"""
        try:
            # 1. 카카오 사용자 정보 조회
            print(f"📡 카카오 API 호출 시작...")
            kakao_user_info = await self.get_kakao_user_info(kakao_access_token)
            print(f"✅ 카카오 사용자 정보 조회 성공 - ID: {kakao_user_info.get('id')}")
            
            # 2. 사용자 찾기 또는 생성
            print(f"👤 사용자 찾기 또는 생성 중...")
            user = self.find_or_create_user(kakao_user_info)
            print(f"✅ 사용자 처리 완료 - User ID: {user.id}, Username: {user.username}")
            
            # 3. JWT 토큰 생성
            print(f"🔑 JWT 토큰 생성 중...")
            jwt_token = create_access_token(data={"sub": str(user.id)})
            print(f"✅ JWT 토큰 생성 완료")
            
            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active
                },
                "kakao_info": kakao_user_info  # 원본 카카오 API 응답 전달
            }
            
        except Exception as e:
            print(f"❌ login_with_kakao_token 에러: {type(e).__name__} - {str(e)}")
            raise Exception(f"카카오 로그인 실패: {str(e)}")
    
    def get_kakao_login_url(self) -> str:
        """카카오 로그인 URL 생성"""
        if not settings.KAKAO_CLIENT_ID or not settings.KAKAO_REDIRECT_URI:
            raise Exception("카카오 클라이언트 설정이 필요합니다")
        
        params = {
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code"
        }
        
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"{self.KAKAO_OAUTH_BASE_URL}/oauth/authorize?{query_string}"
