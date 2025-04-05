import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "한국타이어 제안 시스템"
    API_V1_STR: str = "/api/v1"
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:8000"]
    
    # 데이터베이스 설정
    # MariaDB 설정
    MARIADB_USER: str = os.getenv("MARIADB_USER", "root")
    MARIADB_PASSWORD: str = os.getenv("MARIADB_PASSWORD", "0633")
    MARIADB_HOST: str = os.getenv("MARIADB_HOST", "127.0.0.1")
    MARIADB_PORT: str = os.getenv("MARIADB_PORT", "3306")
    MARIADB_DATABASE: str = os.getenv("MARIADB_DATABASE", "toktok")
    SQLALCHEMY_DATABASE_URI: str = f"mysql+pymysql://{MARIADB_USER}:{MARIADB_PASSWORD}@{MARIADB_HOST}:{MARIADB_PORT}/{MARIADB_DATABASE}"
    
    # SQLite 설정 (개발 및 테스트용)
    # SQLALCHEMY_DATABASE_URI: str = "sqlite:///./app.db"
    
    # JWT 설정
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()

# 디버깅용: 실제 사용되는 업로드 디렉토리 경로 출력
print(f"업로드 디렉토리 경로: {settings.UPLOAD_DIR}")
# 디렉토리가 없으면 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
print(f"업로드 디렉토리 존재 여부: {os.path.exists(settings.UPLOAD_DIR)}") 