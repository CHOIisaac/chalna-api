"""
🎯 경조사 관리 앱 "찰나(Chalna)" - 메인 엔트리포인트

FastAPI CLI에서 자동 감지할 수 있도록 app을 export합니다.
"""

from app.main import app

# FastAPI CLI가 자동으로 감지할 수 있도록 app을 export
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
