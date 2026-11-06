from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.crud.stats import build_stats
from app.database.db_core import get_db
from app.database.models import User
from app.schemas.stats import StatsOut

router = APIRouter(prefix="/stats", tags=["stats"])

Period = Literal["week", "month", "year"]


@router.get("", response_model=StatsOut)
def get_stats(
    period: Period = Query(default="month"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StatsOut:
    return StatsOut.model_validate(build_stats(db, user, period))
