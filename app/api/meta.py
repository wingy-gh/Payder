from fastapi import APIRouter

from app.menu.items import BANKS, CATEGORIES, CATEGORY_COLORS, NAV_ITEMS

router = APIRouter(tags=["meta"])


@router.get("/menu")
def get_menu() -> dict:
    return {
        "items": NAV_ITEMS,
        "banks": BANKS,
        "categories": CATEGORIES,
        "colors": CATEGORY_COLORS,
    }


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
