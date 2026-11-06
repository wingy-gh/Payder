from fastapi import APIRouter

from app.api.cards import router as cards_router
from app.api.meta import router as meta_router
from app.api.stats import router as stats_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(meta_router)
api_router.include_router(cards_router)
api_router.include_router(users_router)
api_router.include_router(stats_router)
