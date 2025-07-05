"""
🎯 경조사 관리 앱 "찰나(Chalna)" - FastAPI 백엔드

인간관계 중심의 경조사 생활 도우미 API
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.api import (
    auth_router,
    users_router,
    events_router,
    gifts_router,
    relationships_router,
)

# FastAPI 앱 생성
app = FastAPI(
    title="찰나(Chalna) API",
    description="인간관계 중심의 경조사 관리 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix="/api/v1/auth", tags=["인증"])
app.include_router(users_router, prefix="/api/v1/users", tags=["사용자"])
app.include_router(events_router, prefix="/api/v1/events", tags=["경조사"])
app.include_router(gifts_router, prefix="/api/v1/gifts", tags=["선물관리"])
app.include_router(relationships_router, prefix="/api/v1/relationships", tags=["관계관리"])

# 루트 엔드포인트
@app.get("/")
async def root():
    """
    👋 찰나 API 서버 상태 확인
    """
    return {
        "message": "🎯 찰나(Chalna) API 서버가 정상 작동 중입니다!",
        "version": "0.1.0",
        "description": "인간관계 중심의 경조사 관리 API",
        "docs": "/docs",
        "status": "healthy"
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    🏥 서버 및 데이터베이스 상태 확인
    """
    try:
        # 데이터베이스 연결 확인
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": "2024-01-01T00:00:00Z"
    }

# 앱 시작/종료 이벤트
@app.on_event("startup")
async def startup_event():
    """
    🚀 애플리케이션 시작 시 실행
    """
    print("🎯 찰나(Chalna) API 서버 시작!")
    print("📖 API 문서: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """
    🛑 애플리케이션 종료 시 실행
    """
    print("👋 찰나(Chalna) API 서버 종료!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    ) 