from fastapi import APIRouter, Depends

from app.api.auth import router as auth_router
from app.api.cards import router as cards_router
from app.api.deps import require_same_origin
from app.api.meta import router as meta_router
from app.api.stats import router as stats_router
from app.api.users import router as users_router

# Все POST/PUT/DELETE через этот роутер проверяются на CSRF по заголовку Origin.
api_router = APIRouter(dependencies=[Depends(require_same_origin)])
api_router.include_router(meta_router)
api_router.include_router(auth_router)
api_router.include_router(cards_router)
api_router.include_router(users_router)
api_router.include_router(stats_router)
