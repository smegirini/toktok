import uvicorn
from app.core.config import settings
from app.core.app_factory import create_app

# app_factory.py에서 애플리케이션 생성
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 