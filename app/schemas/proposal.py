from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime

from app.models.proposal import ProposalStatus, ProposalCategory
from app.schemas.user import User


# 기본 제안 스키마
class ProposalBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200, description="제안 제목")
    content: str = Field(..., min_length=10, description="제안 내용")
    category: ProposalCategory
    department: str
    expected_effect: Optional[str] = None
    benefit_amount: Optional[float] = 0.0
    before_image: Optional[str] = None
    after_image: Optional[str] = None

    class Config:
        error_msg_templates = {
            "value_error.missing": "필수 필드가 누락되었습니다.",
            "value_error.any_str.min_length": "최소 길이 요구사항을 충족하지 않습니다.",
            "value_error.any_str.max_length": "최대 길이를 초과했습니다."
        }


# 제안 생성 스키마
class ProposalCreate(ProposalBase):
    department: Optional[str] = None


# 제안 업데이트 스키마
class ProposalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    content: Optional[str] = Field(None, min_length=10)
    category: Optional[ProposalCategory] = None
    expected_effect: Optional[str] = None
    benefit_amount: Optional[float] = None
    before_image: Optional[str] = None
    after_image: Optional[str] = None


# 관리자 제안 업데이트 스키마
class AdminProposalUpdate(ProposalUpdate):
    status: Optional[ProposalStatus] = None


# 댓글 생성 스키마
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=2)
    parent_id: Optional[int] = None


# 댓글 업데이트 스키마
class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=2)


# 댓글 스키마
class Comment(BaseModel):
    id: int
    content: str
    user_id: int
    proposal_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


# 투표 생성 스키마
class VoteCreate(BaseModel):
    vote_value: int = Field(..., ge=-1, le=1)
    
    @validator('vote_value')
    def validate_vote_value(cls, v):
        if v not in [-1, 0, 1]:
            raise ValueError('투표 값은 -1, 0, 1만 가능합니다')
        return v


# 투표 스키마
class Vote(BaseModel):
    id: int
    user_id: int
    proposal_id: int
    vote_value: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 첨부파일 스키마
class Attachment(BaseModel):
    id: int
    filename: str
    filepath: str
    filesize: int
    file_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 제안 상태 업데이트 스키마
class ProposalStatusUpdate(BaseModel):
    status: str = Field(..., description="변경할 상태 (approved, rejected, implemented)")
    feedback: Optional[str] = Field(None, description="상태 변경 관련 피드백")


# 제안 목록 조회용 간단한 스키마
class ProposalList(BaseModel):
    id: int
    title: str
    category: ProposalCategory
    status: ProposalStatus
    user_id: int
    department: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 제안 조회용 상세 스키마
class ProposalOut(BaseModel):
    id: int
    title: str
    content: str
    category: ProposalCategory
    status: ProposalStatus
    user_id: int
    department: str
    expected_effect: Optional[str]
    benefit_amount: Optional[float]
    before_image: Optional[str]
    after_image: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[User] = None
    votes: List[Vote] = []
    comments: List[Comment] = []
    attachments: List[Attachment] = []
    
    class Config:
        from_attributes = True


# 제안 응답 스키마
class Proposal(ProposalBase):
    id: int
    status: ProposalStatus
    user_id: int
    department: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 페이징된 제안 목록 스키마
class PaginatedProposals(BaseModel):
    items: List[Proposal]
    total: int
    page: int
    size: int
    pages: int 