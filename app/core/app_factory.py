from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import random
from datetime import datetime, timedelta
import os

from app.core.config import settings
from app.routers import auth, users, proposals, rankings
from app.core.database import Base, engine

# 하드코딩된 관리자 계정 정보
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"

def create_app() -> FastAPI:
    # 데이터베이스 테이블 생성 시도
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"데이터베이스 테이블 생성 오류: {e}")
        print("기본 기능은 유지되지만, 데이터베이스 기능은 제한될 수 있습니다.")
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="한국타이어 제안 시스템 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 정적 파일 마운트
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # 업로드 디렉토리 생성 및 마운트
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    
    # 템플릿 설정
    templates = Jinja2Templates(directory="app/templates")
    app.state.templates = templates
    
    # 관리자 계정 생성 함수 제거하고 시작 시 관리자 계정 정보 출력
    @app.on_event("startup")
    async def print_admin_info():
        print(f"관리자 계정 정보: 아이디: {ADMIN_USERNAME}, 비밀번호: {ADMIN_PASSWORD}")
    
    # 기본 경로 리디렉션
    @app.get("/")
    async def root():
        return RedirectResponse(url="/main")
    
    # 메인 페이지
    @app.get("/main", response_class=HTMLResponse)
    async def main_page(request: Request):
        # 임시 데이터 생성 (실제로는 데이터베이스에서 가져와야 함)
        total_proposals = random.randint(150, 200)
        total_users = random.randint(50, 100)
        implemented_proposals = random.randint(30, 50)
        
        # 최근 제안 샘플 데이터
        recent_proposals = [
            {
                "id": 1,
                "title": "작업장 안전 개선 제안",
                "category": "안전",
                "content": "작업장 안전을 위한 새로운 프로토콜 도입을 제안합니다. 최근 발생한 경미한 사고를 분석한 결과, 특정 작업 공정에서 안전 절차가 미흡한 것으로 확인되었습니다.",
                "created_at": datetime.now() - timedelta(days=2)
            },
            {
                "id": 2,
                "title": "생산 효율성 향상 방안",
                "category": "생산",
                "content": "현재 생산 라인의 효율성을 20% 향상시킬 수 있는 방안을 제안합니다. 설비 배치와 작업 프로세스 개선을 통해 병목 현상을 해소할 수 있습니다.",
                "created_at": datetime.now() - timedelta(days=5)
            },
            {
                "id": 3,
                "title": "원자재 절감 아이디어",
                "category": "비용절감",
                "content": "새로운 원자재 재활용 시스템을 도입하여 연간 약 5% 비용 절감이 가능합니다. 세부 계획과 예상 절감액 분석을 첨부합니다.",
                "created_at": datetime.now() - timedelta(days=7)
            }
        ]
        
        # 상위 사용자 샘플 데이터
        top_users = [
            {"name": "홍길동", "proposal_count": 15, "points": 2300},
            {"name": "김철수", "proposal_count": 12, "points": 1850},
            {"name": "이영희", "proposal_count": 10, "points": 1600}
        ]
        
        return templates.TemplateResponse("pages/index.html", {
            "request": request, 
            "title": "메인 페이지",
            "total_proposals": total_proposals,
            "total_users": total_users,
            "implemented_proposals": implemented_proposals,
            "recent_proposals": recent_proposals,
            "top_users": top_users
        })
    
    # 로그인 페이지
    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return templates.TemplateResponse("pages/login.html", {"request": request, "title": "로그인"})
    
    # 회원가입 페이지
    @app.get("/register", response_class=HTMLResponse)
    async def register_page(request: Request):
        return templates.TemplateResponse("pages/register.html", {"request": request, "title": "회원가입"})
    
    # 제안 목록 페이지
    @app.get("/proposals", response_class=HTMLResponse)
    async def proposals_page(request: Request):
        return templates.TemplateResponse("pages/proposals.html", {"request": request, "title": "제안 목록"})
    
    # 새 제안 작성 페이지
    @app.get("/proposals/new", response_class=HTMLResponse)
    async def new_proposal_page(request: Request):
        return templates.TemplateResponse("pages/proposal_form.html", {"request": request, "title": "새 제안 작성"})
    
    # 제안 상세 페이지
    @app.get("/proposals/{proposal_id}", response_class=HTMLResponse)
    async def proposal_detail_page(request: Request, proposal_id: int):
        return templates.TemplateResponse("pages/proposal_detail.html", {"request": request, "title": "제안 상세", "proposal_id": proposal_id})
    
    # 순위 페이지
    @app.get("/rankings", response_class=HTMLResponse)
    async def rankings_page(request: Request):
        return templates.TemplateResponse("pages/rankings.html", {"request": request, "title": "순위"})
    
    # 사용자 프로필 페이지
    @app.get("/profile", response_class=HTMLResponse)
    async def profile_page(request: Request):
        return templates.TemplateResponse("pages/profile.html", {"request": request, "title": "프로필"})
    
    # 관리자 페이지 - 로그인 없이 접근 가능하도록 설정 (실제로는 권한 체크 필요)
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(request: Request):
        return templates.TemplateResponse("pages/admin/dashboard.html", {"request": request, "title": "관리자 대시보드"})
    
    @app.get("/admin/users", response_class=HTMLResponse)
    async def admin_users(request: Request):
        return templates.TemplateResponse("pages/admin/users.html", {"request": request, "title": "사용자 관리"})
    
    @app.get("/admin/proposals", response_class=HTMLResponse)
    async def admin_proposals(request: Request):
        return templates.TemplateResponse("pages/admin/proposals.html", {"request": request, "title": "제안 관리"})
    
    @app.get("/admin/statistics", response_class=HTMLResponse)
    async def admin_statistics(request: Request):
        return templates.TemplateResponse("pages/admin/statistics.html", {"request": request, "title": "통계 및 분석"})
    
    @app.get("/admin/settings", response_class=HTMLResponse)
    async def admin_settings(request: Request):
        return templates.TemplateResponse("pages/admin/settings.html", {"request": request, "title": "시스템 설정"})
    
    @app.get("/admin/notifications", response_class=HTMLResponse)
    async def admin_notifications(request: Request):
        return templates.TemplateResponse("pages/admin/notifications.html", {"request": request, "title": "알림 관리"})
    
    # 관리자 로그인 검증 API (하드코딩 방식)
    @app.post("/api/v1/auth/admin-login")
    async def admin_login(username: str, password: str):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return {"success": True, "message": "관리자 로그인 성공"}
        return {"success": False, "message": "잘못된 관리자 계정 정보입니다"}
    
    # 라우터 등록
    app.include_router(auth.router, prefix=f"{settings.API_V1_STR}")
    app.include_router(users.router, prefix=f"{settings.API_V1_STR}")
    app.include_router(proposals.router, prefix=f"{settings.API_V1_STR}")
    app.include_router(rankings.router, prefix=f"{settings.API_V1_STR}")
    
    return app 