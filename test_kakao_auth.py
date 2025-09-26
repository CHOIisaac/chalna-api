#!/usr/bin/env python3
"""
카카오 로그인 테스트 스크립트
"""

import asyncio
import httpx
from app.core.database import get_db
from app.services.kakao_auth_service import KakaoAuthService

async def test_kakao_auth():
    """카카오 로그인 테스트"""
    print("=== 카카오 로그인 테스트 ===")
    
    # 1. 설정 확인
    from app.core.config import settings
    print(f"KAKAO_CLIENT_ID: {'설정됨' if settings.KAKAO_CLIENT_ID else '설정 안됨'}")
    print(f"KAKAO_CLIENT_SECRET: {'설정됨' if settings.KAKAO_CLIENT_SECRET else '설정 안됨'}")
    print(f"KAKAO_REDIRECT_URI: {'설정됨' if settings.KAKAO_REDIRECT_URI else '설정 안됨'}")
    
    if not all([settings.KAKAO_CLIENT_ID, settings.KAKAO_CLIENT_SECRET, settings.KAKAO_REDIRECT_URI]):
        print("❌ 카카오 설정이 완료되지 않았습니다.")
        print("환경변수를 설정하거나 .env 파일에 다음을 추가하세요:")
        print("KAKAO_CLIENT_ID=your_client_id")
        print("KAKAO_CLIENT_SECRET=your_client_secret")
        print("KAKAO_REDIRECT_URI=http://localhost:8000/api/v1/kakao/callback")
        return
    
    # 2. 로그인 URL 생성 테스트
    try:
        db = next(get_db())
        service = KakaoAuthService(db)
        login_url = service.get_kakao_login_url()
        print(f"✅ 카카오 로그인 URL 생성 성공:")
        print(f"   {login_url}")
    except Exception as e:
        print(f"❌ 카카오 로그인 URL 생성 실패: {e}")
        return
    
    # 3. API 엔드포인트 테스트
    print("\n=== 모바일 API 엔드포인트 ===")
    print("1. POST /api/v1/kakao/test - 설정 확인")
    print("2. POST /api/v1/kakao/login - 카카오 로그인 (모바일용)")
    
    print("\n=== 모바일 테스트 방법 ===")
    print("1. 서버 실행: uv run uvicorn app.main:app --reload")
    print("2. 모바일 앱에서 카카오 SDK 설정")
    print("3. 카카오 로그인 후 access_token 받기")
    print("4. POST /api/v1/kakao/login에 access_token 전송")
    print("5. JWT 토큰 받아서 API 인증에 사용")
    
    print("\n=== 모바일 앱 설정 ===")
    print("1. 카카오 개발자 콘솔에서 앱 등록")
    print("2. 플랫폼 설정 (안드로이드/iOS)")
    print("3. 앱 키 설정 (네이티브 앱 키)")
    print("4. 모바일 앱에서 카카오 SDK 설치")
    print("5. 로그인 구현 및 access_token 받기")

if __name__ == "__main__":
    asyncio.run(test_kakao_auth())
