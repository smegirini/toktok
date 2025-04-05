from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.proposals import router as proposals_router
from app.routers.rankings import router as rankings_router
from app.routers.admin import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(proposals_router)
api_router.include_router(rankings_router)
api_router.include_router(admin_router)

__all__ = ["api_router"] 