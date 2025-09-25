"""
Firebase 설정 및 초기화
"""

import os
from typing import Optional
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings


class FirebaseService:
    """Firebase 서비스 클래스"""
    
    def __init__(self):
        self.app: Optional[firebase_admin.App] = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Firebase 초기화"""
        try:
            # Firebase 서비스 계정 키 파일 경로
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            
            if service_account_path and os.path.exists(service_account_path):
                # 서비스 계정 키 파일로 초기화
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
            else:
                # 환경변수에서 서비스 계정 정보 읽기
                service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                if service_account_info:
                    import json
                    service_account_dict = json.loads(service_account_info)
                    cred = credentials.Certificate(service_account_dict)
                    self.app = firebase_admin.initialize_app(cred)
                else:
                    print("⚠️ Firebase 서비스 계정 정보가 설정되지 않았습니다.")
                    print("FIREBASE_SERVICE_ACCOUNT_PATH 또는 FIREBASE_SERVICE_ACCOUNT_JSON 환경변수를 설정하세요.")
                    
        except Exception as e:
            print(f"❌ Firebase 초기화 실패: {e}")
            self.app = None
    
    def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """FCM 알림 전송"""
        if not self.app:
            print("❌ Firebase가 초기화되지 않았습니다.")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            
            response = messaging.send(message)
            print(f"✅ 알림 전송 성공: {response}")
            return True
            
        except Exception as e:
            print(f"❌ 알림 전송 실패: {e}")
            return False
    
    def send_multicast_notification(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> dict:
        """다중 FCM 알림 전송"""
        if not self.app:
            print("❌ Firebase가 초기화되지 않았습니다.")
            return {"success_count": 0, "failure_count": len(tokens)}
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            print(f"✅ 다중 알림 전송 완료: 성공 {response.success_count}, 실패 {response.failure_count}")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": response.responses
            }
            
        except Exception as e:
            print(f"❌ 다중 알림 전송 실패: {e}")
            return {"success_count": 0, "failure_count": len(tokens)}


# 전역 Firebase 서비스 인스턴스
firebase_service = FirebaseService()


def get_firebase_service() -> FirebaseService:
    """Firebase 서비스 인스턴스 반환"""
    return firebase_service
