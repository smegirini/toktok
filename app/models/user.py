from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserLevel(str, enum.Enum):
    """사용자 등급 정의"""
    ABSOLUTE_GOD = "ABSOLUTE_GOD"  # 절대신
    SUPREME = "SUPREME"  # 지존
    HERO = "HERO"  # 영웅
    MASTER = "MASTER"  # 고수
    INTERMEDIATE = "INTERMEDIATE"  # 중수
    BEGINNER = "BEGINNER"  # 초수
    COMMONER = "COMMONER"  # 평민


class UserAuth(str, enum.Enum):
    """사용자 권한 정의"""
    ADMIN = "ADMIN"  # 관리자
    FACTORY = "FACTORY"  # 공장장
    DEPARTMENT = "DEPARTMENT"  # 부서장
    TEAM = "TEAM"  # 팀장
    USER = "USER"  # 일반 사용자


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    employee_id = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=True)
    level = Column(Enum(UserLevel), default=UserLevel.COMMONER, nullable=False)
    auth = Column(Enum(UserAuth), default=UserAuth.USER, nullable=False)
    points = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    proposals = relationship("Proposal", back_populates="user")
    votes = relationship("Vote", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>" 