from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ProposalStatus(str, enum.Enum):
    """제안 상태 정의"""
    DRAFT = "DRAFT"  # 임시저장
    SUBMITTED = "SUBMITTED"  # 제출됨
    REVIEWING = "REVIEWING"  # 검토 중
    APPROVED = "APPROVED"  # 승인됨
    REJECTED = "REJECTED"  # 거부됨
    IMPLEMENTED = "IMPLEMENTED"  # 구현됨


class ProposalCategory(str, enum.Enum):
    """제안 카테고리 정의"""
    QUALITY = "QUALITY"  # 품질 개선
    SAFETY = "SAFETY"  # 안전 개선
    EFFICIENCY = "EFFICIENCY"  # 효율성 개선
    COST = "COST"  # 비용 절감
    ENVIRONMENT = "ENVIRONMENT"  # 환경 개선
    OTHER = "OTHER"  # 기타


class Proposal(Base):
    """제안 모델"""
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(Enum(ProposalCategory), nullable=False)
    status = Column(Enum(ProposalStatus), default=ProposalStatus.DRAFT, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String(100), nullable=False)
    expected_effect = Column(Text, nullable=True)
    benefit_amount = Column(Float, default=0.0)  # 예상 효과 금액
    before_image = Column(String(500), nullable=True)  # 개선 전 이미지 경로
    after_image = Column(String(500), nullable=True)   # 개선 후 이미지 경로
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="proposals")
    votes = relationship("Vote", back_populates="proposal")
    comments = relationship("Comment", back_populates="proposal")
    attachments = relationship("Attachment", back_populates="proposal")
    
    def __repr__(self):
        return f"<Proposal {self.title} ({self.status})>"


class Vote(Base):
    """투표 모델"""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    vote_value = Column(Integer, default=1, nullable=False)  # 1 = 찬성, -1 = 반대
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="votes")
    proposal = relationship("Proposal", back_populates="votes")
    
    def __repr__(self):
        return f"<Vote: User {self.user_id} on Proposal {self.proposal_id}>"


class Comment(Base):
    """댓글 모델"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="comments")
    proposal = relationship("Proposal", back_populates="comments")
    children = relationship("Comment", backref=backref("parent", remote_side=[id]))
    
    def __repr__(self):
        return f"<Comment by User {self.user_id} on Proposal {self.proposal_id}>"


class Attachment(Base):
    """첨부 파일 모델"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    filesize = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    proposal = relationship("Proposal", back_populates="attachments")
    
    def __repr__(self):
        return f"<Attachment {self.filename} for Proposal {self.proposal_id}>" 