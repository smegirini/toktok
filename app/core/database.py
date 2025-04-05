from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency
def get_db():
    """
    FastAPI 엔드포인트에서 데이터베이스 세션을 의존성으로 사용하기 위한 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 