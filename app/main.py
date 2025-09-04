"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api import (
    auth_router, users_router, events_router, 
    ledgers_router, schedules_router
)
from app.core.security import security

app = FastAPI(
    title="찰나(Chalna) API",
    summary="경조사 관리 애플리케이션",
    description="""
    찰나(Chalna)는 경조사비 수입지출과 일정을 관리하는 애플리케이션입니다.
    
    ## 주요 기능
    * 👤 사용자 관리 및 인증
    * 📅 경조사 일정 관리
    * 💰 경조사비 수입지출 장부
    * 📊 통계 및 분석
    """,
    version="1.0.0",
    terms_of_service="https://chalna.com/terms/",
    contact={
        "name": "Chalna Team",
        "email": "support@chalna.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/swagger",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
    },
    openapi_tags=[
        {
            "name": "인증",
            "description": "사용자 로그인, 회원가입, 토큰 관리"
        },
        {
            "name": "사용자 관리",
            "description": "사용자 정보 관리 및 설정"
        },
        {
            "name": "경조사 이벤트",
            "description": "경조사 이벤트 관리"
        },
        {
            "name": "장부 관리",
            "description": "경조사비 수입지출 장부 관리"
        },
        {
            "name": "일정 관리",
            "description": "경조사 일정 관리"
        }
    ]
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("🚀 찰나(Chalna) API 서버가 시작되었습니다!")
    print("📚 API 문서: http://localhost:8000/swagger")

@app.get("/", summary="루트 엔드포인트", description="API 서버 상태 확인")
async def root():
    return {
        "message": "찰나(Chalna) API 서버에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/swagger",
        "health": "/health"
    }

@app.get("/health", summary="헬스 체크", description="서버 상태 확인")
async def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 작동 중입니다"}

# OpenAPI 스키마에 보안 정의 추가
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 보안 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # 보안이 필요한 엔드포인트에 보안 적용
    for path in openapi_schema["paths"]:
        if path != "/api/v1/auth/login" and path != "/api/v1/auth/token":
            openapi_schema["paths"][path]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# API 라우터 등록 (사용자가 원했던 /api/v1/ prefix 사용)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["인증"])
app.include_router(users_router, prefix="/api/v1/users", tags=["사용자 관리"])
app.include_router(events_router, prefix="/api/v1/events", tags=["경조사 이벤트"])
app.include_router(ledgers_router, prefix="/api/v1/ledgers", tags=["장부 관리"])
app.include_router(schedules_router, prefix="/api/v1/schedules", tags=["일정 관리"])