from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRanking(Base):
    """사용자 랭킹 모델"""
    __tablename__ = "user_rankings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    proposal_count = Column(Integer, nullable=False)
    approved_count = Column(Integer, nullable=False)
    ranking_period = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserRanking {self.user_id}: #{self.rank}>"


class DepartmentRanking(Base):
    """부서 랭킹 모델"""
    __tablename__ = "department_rankings"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(100), nullable=False)
    rank = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    proposal_count = Column(Integer, nullable=False)
    approved_count = Column(Integer, nullable=False)
    ranking_period = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DepartmentRanking {self.department}: #{self.rank}>"


class ProposalStatistic(Base):
    """제안 통계 모델"""
    __tablename__ = "proposal_statistics"

    id = Column(Integer, primary_key=True, index=True)
    total_proposals = Column(Integer, nullable=False)
    approved_proposals = Column(Integer, nullable=False)
    rejected_proposals = Column(Integer, nullable=False)
    pending_proposals = Column(Integer, nullable=False)
    avg_processing_time = Column(Float, nullable=False)  # 평균 처리 시간 (일)
    total_benefit_amount = Column(Float, nullable=False)  # 총 효과 금액
    reporting_period = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ProposalStatistic {self.reporting_period}: {self.total_proposals} proposals>"


class Badge(Base):
    """업적 배지 모델"""
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user_badges = relationship("UserBadge", back_populates="badge")
    
    def __repr__(self):
        return f"<Badge {self.name}>"


class UserBadge(Base):
    """사용자 업적 배지 모델"""
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    badge = relationship("Badge", back_populates="user_badges")
    
    def __repr__(self):
        return f"<UserBadge User {self.user_id}: Badge {self.badge_id}>" 