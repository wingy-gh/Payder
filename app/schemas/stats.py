from pydantic import BaseModel


class ChartPoint(BaseModel):
    day: str
    value: int
    date: str | None = None


class ActivityOut(BaseModel):
    title: str
    amount_label: str
    happened_at: str
    kind: str


class StatsOut(BaseModel):
    collected: int
    collected_delta: str
    helped_people: int
    helped_amount: int
    active_cards: int
    card_limit: int
    views_total: int
    chart: list[ChartPoint]
    activities: list[ActivityOut]
    period: str
