from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.user import User
from app.schemas.proposal import Proposal


# 사용자 랭킹 스키마
class UserRanking(BaseModel):
    id: int
    user_id: int
    rank: int
    points: int
    proposal_count: int
    approved_count: int
    ranking_period: str
    created_at: datetime
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


# 부서 랭킹 스키마
class DepartmentRanking(BaseModel):
    id: int
    department: str
    rank: int
    points: int
    proposal_count: int
    approved_count: int
    ranking_period: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 공장 랭킹 스키마
class FactoryRanking(BaseModel):
    id: int
    factory: str
    rank: int
    points: int
    proposal_count: int
    approved_count: int
    ranking_period: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 제안 랭킹 스키마
class ProposalRanking(BaseModel):
    id: int
    title: str
    category: str
    user_id: int
    department: str
    upvotes: int
    comment_count: int
    created_at: datetime
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


# 제안 통계 스키마
class ProposalStatistic(BaseModel):
    id: int
    total_proposals: int
    approved_proposals: int
    rejected_proposals: int
    pending_proposals: int
    avg_processing_time: float
    total_benefit_amount: float
    reporting_period: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 배지 스키마
class Badge(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 사용자 배지 스키마
class UserBadge(BaseModel):
    id: int
    user_id: int
    badge_id: int
    achieved_at: datetime
    badge: Optional[Badge] = None
    
    class Config:
        from_attributes = True


# 랭킹 응답 스키마
class RankingResponse(BaseModel):
    user_rankings: List[UserRanking]
    department_rankings: List[DepartmentRanking]
    top_contributors: List[User]
    statistics: Optional[ProposalStatistic] = None 