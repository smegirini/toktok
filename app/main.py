from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import logging

from app.routers import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.middleware import setup_middlewares
from app.crud.user import update_admin_status
from app.models.user import UserAuth

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# admin 계정 권한 업데이트
db = SessionLocal()
try:
    update_admin_status(db)
    logger.info("admin 계정 권한 업데이트 완료")
except Exception as e:
    logger.error(f"admin 계정 권한 업데이트 실패: {e}")
finally:
    db.close()

# 정적 파일 저장 디렉토리 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
logger.info(f"main.py: 업로드 디렉토리 {settings.UPLOAD_DIR} 생성 완료")

# 템플릿 설정
templates = Jinja2Templates(directory="app/templates")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="한국타이어 제안 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 미들웨어 설정
setup_middlewares(app)

# 정적 파일 제공 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
logger.info(f"main.py: 업로드 디렉토리 {settings.UPLOAD_DIR}가 /uploads URL로 마운트됨")

# 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_STR)

# 웹 페이지 라우트
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    메인 페이지
    """
    return templates.TemplateResponse(
        "pages/index.html", 
        {"request": request, "title": "한국타이어 제안 시스템"}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지
    """
    return templates.TemplateResponse(
        "pages/login.html", 
        {"request": request, "title": "로그인"}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    회원가입 페이지
    """
    return templates.TemplateResponse(
        "pages/register.html", 
        {"request": request, "title": "회원가입"}
    )

@app.get("/proposals", response_class=HTMLResponse)
async def proposals_page(request: Request):
    """
    제안 목록 페이지
    """
    return templates.TemplateResponse(
        "pages/proposals.html", 
        {"request": request, "title": "제안 목록"}
    )

@app.get("/proposals/new", response_class=HTMLResponse)
async def new_proposal_page(request: Request):
    """
    새 제안 작성 페이지
    """
    return templates.TemplateResponse(
        "pages/proposal_form.html", 
        {"request": request, "title": "새 제안 작성"}
    )

@app.get("/proposals/{proposal_id}", response_class=HTMLResponse)
async def proposal_detail_page(request: Request, proposal_id: int):
    """
    제안 상세 페이지
    """
    return templates.TemplateResponse(
        "pages/proposal_detail.html", 
        {"request": request, "title": "제안 상세", "proposal_id": proposal_id}
    )

@app.get("/rankings", response_class=HTMLResponse)
async def rankings_page(request: Request):
    """
    순위 페이지
    """
    return templates.TemplateResponse(
        "pages/rankings.html", 
        {"request": request, "title": "순위"}
    )

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """
    사용자 프로필 페이지
    """
    return templates.TemplateResponse(
        "pages/profile.html", 
        {"request": request, "title": "프로필"}
    )

# 관리자 페이지 라우트
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    """
    관리자 대시보드 페이지
    """
    # 쿠키에서 토큰 확인
    token = request.cookies.get("auth_token")
    print(f"[관리자 페이지 접근] 쿠키 토큰 존재 여부: {token is not None}")
    logger.info(f"[관리자 페이지 접근] 쿠키 토큰 존재 여부: {token is not None}")
    
    if not token:
        print("[관리자 페이지 접근] 토큰 없음, 로그인 페이지로 리디렉션")
        logger.warning("[관리자 페이지 접근] 토큰 없음, 로그인 페이지로 리디렉션")
        return RedirectResponse(url="/login", status_code=302)
    
    # 토큰 유효성 검증
    from app.core.security import jwt, settings
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        print(f"[관리자 페이지 접근] 토큰 검증 성공: username={username}")
        logger.info(f"[관리자 페이지 접근] 토큰 검증 성공: username={username}")
        
        # 데이터베이스 연결
        db = SessionLocal()
        try:
            # 사용자 정보 확인
            from app.crud.user import get_user_by_username
            user = get_user_by_username(db, username=username)
            
            if not user:
                print(f"[관리자 페이지 접근] 사용자를 찾을 수 없음: {username}")
                logger.warning(f"[관리자 페이지 접근] 사용자를 찾을 수 없음: {username}")
                return RedirectResponse(url="/login", status_code=302)
                
            if user.auth != UserAuth.ADMIN:
                print(f"[관리자 페이지 접근] 관리자 권한 없음: {username}, 권한={user.auth}")
                logger.warning(f"[관리자 페이지 접근] 관리자 권한 없음: {username}, 권한={user.auth}")
                return RedirectResponse(url="/login", status_code=302)
                
            print(f"[관리자 페이지 접근] 관리자 권한 확인 완료: {username}, 권한={user.auth}")
            logger.info(f"[관리자 페이지 접근] 관리자 권한 확인 완료: {username}, 권한={user.auth}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"[관리자 페이지 접근] 토큰 검증 실패: {str(e)}")
        logger.error(f"[관리자 페이지 접근] 토큰 검증 실패: {str(e)}")
        return RedirectResponse(url="/login", status_code=302)
    
    # 템플릿 렌더링
    logger.info(f"[관리자 페이지 접근] 페이지 렌더링: username={username}")
    return templates.TemplateResponse(
        "pages/admin/dashboard.html", 
        {"request": request, "title": "관리자 대시보드"}
    )

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    """
    관리자 사용자 관리 페이지
    """
    # 쿠키에서 토큰 확인
    token = request.cookies.get("auth_token")
    print(f"[관리자 사용자 관리 접근] 쿠키 토큰 존재 여부: {token is not None}")
    
    if not token:
        print("[관리자 사용자 관리 접근] 토큰 없음, 로그인 페이지로 리디렉션")
        return RedirectResponse(url="/login", status_code=302)
    
    # 토큰 유효성 검증
    from app.core.security import jwt, settings
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        # 데이터베이스 연결
        db = SessionLocal()
        try:
            # 사용자 정보 확인
            from app.crud.user import get_user_by_username
            user = get_user_by_username(db, username=username)
            
            if not user or user.auth != UserAuth.ADMIN:
                return RedirectResponse(url="/login", status_code=302)
        finally:
            db.close()
            
    except Exception as e:
        print(f"[관리자 사용자 관리 접근] 토큰 검증 실패: {str(e)}")
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "pages/admin/users.html", 
        {"request": request, "title": "사용자 관리"}
    )

@app.get("/admin/proposals", response_class=HTMLResponse)
async def admin_proposals_page(request: Request):
    """
    관리자 제안 관리 페이지
    """
    # 쿠키에서 토큰 확인
    token = request.cookies.get("auth_token")
    print(f"[관리자 제안 관리 접근] 쿠키 토큰 존재 여부: {token is not None}")
    
    if not token:
        print("[관리자 제안 관리 접근] 토큰 없음, 로그인 페이지로 리디렉션")
        return RedirectResponse(url="/login", status_code=302)
    
    # 토큰 유효성 검증
    from app.core.security import jwt, settings
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        # 데이터베이스 연결
        db = SessionLocal()
        try:
            # 사용자 정보 확인
            from app.crud.user import get_user_by_username
            user = get_user_by_username(db, username=username)
            
            if not user or user.auth != UserAuth.ADMIN:
                return RedirectResponse(url="/login", status_code=302)
        finally:
            db.close()
            
    except Exception as e:
        print(f"[관리자 제안 관리 접근] 토큰 검증 실패: {str(e)}")
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "pages/admin/proposals.html", 
        {"request": request, "title": "제안 관리"}
    )

@app.get("/admin/statistics", response_class=HTMLResponse)
async def admin_statistics_page(request: Request):
    """
    관리자 통계 페이지
    """
    return templates.TemplateResponse(
        "pages/admin/statistics.html", 
        {"request": request, "title": "통계 및 분석"}
    )

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request):
    """
    관리자 시스템 설정 페이지
    """
    return templates.TemplateResponse(
        "pages/admin/settings.html", 
        {"request": request, "title": "시스템 설정"}
    )

@app.get("/admin/notifications", response_class=HTMLResponse)
async def admin_notifications_page(request: Request):
    """
    관리자 알림 관리 페이지
    """
    return templates.TemplateResponse(
        "pages/admin/notifications.html", 
        {"request": request, "title": "알림 관리"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 