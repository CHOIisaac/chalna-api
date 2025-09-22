"""
API 라우터 패키지 초기화
"""

from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.home import router as home_router
from app.api.ledgers import router as ledgers_router
from app.api.schedules import router as schedules_router
from app.api.users import router as users_router
from app.api.user_settings import router as user_settings_router

__all__ = [
    "auth_router",
    "users_router",
    "user_settings_router",
    "events_router",
    "home_router",
    "ledgers_router",
    "schedules_router",
]
