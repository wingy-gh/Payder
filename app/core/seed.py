from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Activity, Card, CardView, Help, User


def _user(
    name: str,
    username: str,
    phone: str,
    bank: str,
    requisites: str,
    initials: str,
) -> User:
    return User(
        name=name,
        username=username,
        phone=phone,
        bank=bank,
        requisites=requisites,
        initials=initials,
    )


def seed_if_empty(db: Session) -> None:
    existing = db.scalar(select(func.count()).select_from(User))
    if existing:
        return

    alex = _user("Алексей Морозов", "alexmoroz", "+7 999 120-34-78", "Т-Банк", "+7 999 120-34-78", "АМ")
    anna = _user("Анна К.", "annak", "+7 999 428-16-03", "Т-Банк", "+7 999 428-16-03", "АК")
    maxim = _user("Максим Л.", "maximl", "2202 2068 4194 0721", "Сбер", "2202 2068 4194 0721", "МЛ")
    sofia = _user("София М.", "sofiam", "+7 921 074-28-11", "Альфа-Банк", "+7 921 074-28-11", "СМ")
    ilya = _user("Илья Р.", "ilyar", "2200 2405 8270 1963", "ВТБ", "2200 2405 8270 1963", "ИР")
    extras = [
        _user(
            f"Помощник {index}",
            f"helper{index}",
            f"+7 900 000-00-{index:02d}",
            "Сбер",
            f"+7 900 000-00-{index:02d}",
            "ПД",
        )
        for index in range(1, 9)
    ]
    db.add_all([alex, anna, maxim, sofia, ilya, *extras])
    db.flush()

    featured = [
        Card(
            public_id="PD-24081",
            amount=12500,
            purpose="Нужны деньги на новый графический планшет для работы и учёбы",
            category="Техника",
            color="#D9F99D",
            author_id=anna.id,
        ),
        Card(
            public_id="PD-24082",
            amount=6800,
            purpose="На курс по веб-разработке, чтобы получить первую работу в IT",
            category="Образование",
            color="#BFDBFE",
            author_id=maxim.id,
        ),
        Card(
            public_id="PD-24083",
            amount=3200,
            purpose="Хочу купить корм и лекарства для кота из приюта",
            category="Доброе дело",
            color="#FBCFE8",
            author_id=sofia.id,
        ),
        Card(
            public_id="PD-24084",
            amount=18000,
            purpose="Собираю на аренду фотостудии для первого коммерческого проекта",
            category="Творчество",
            color="#FED7AA",
            author_id=ilya.id,
        ),
    ]
    alex_cards = [
        Card(
            public_id="PD-11021",
            amount=4500,
            purpose="Сбор на учебники и доступ к онлайн-курсу по продуктовому дизайну",
            category="Образование",
            color="#BFDBFE",
            author_id=alex.id,
        ),
        Card(
            public_id="PD-11022",
            amount=9700,
            purpose="Нужна сумма на ремонт рабочего ноутбука перед сессией",
            category="Техника",
            color="#D9F99D",
            author_id=alex.id,
        ),
    ]
    extra_cards = [
        Card(
            public_id=f"PD-300{index:02d}",
            amount=2000 + index * 250,
            purpose="Нужна небольшая сумма на срочные расходы и поддержку",
            category="Другое",
            color="#E7E5E4",
            author_id=user.id,
            is_active=False,
        )
        for index, user in enumerate(extras, start=1)
    ]
    db.add_all(featured + alex_cards + extra_cards)
    db.flush()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    view_pattern = [28, 45, 34, 72, 55, 88, 64]
    for offset, count in enumerate(view_pattern):
        day = now - timedelta(days=6 - offset)
        for _ in range(count):
            db.add(CardView(card_id=alex_cards[0].id, viewer_id=anna.id, created_at=day))

    incoming = [1500, 500, 2200, 1800, 900, 3100, 700, 2500, 1200, 2650, 2800, 4800]
    donors = extras + [anna, maxim, sofia, ilya]
    for index, (helper, amount, card) in enumerate(
        zip(donors, incoming, [alex_cards[0], alex_cards[1]] * 6, strict=True)
    ):
        created_at = now - timedelta(days=20 if index >= 8 else 1)
        db.add(Help(card_id=card.id, helper_id=helper.id, amount=amount, created_at=created_at))

    outgoing_targets = featured + extra_cards
    for card in outgoing_targets:
        db.add(Help(card_id=card.id, helper_id=alex.id, amount=700))

    db.add_all(
        [
            Activity(
                user_id=alex.id,
                title="Новый перевод",
                amount_label="+1 500 ₽",
                happened_at="Сегодня, 12:42",
                kind="in",
            ),
            Activity(
                user_id=alex.id,
                title="Карточку посмотрели",
                amount_label="24 раза",
                happened_at="Сегодня, 09:18",
                kind="view",
            ),
            Activity(
                user_id=alex.id,
                title="Новый перевод",
                amount_label="+500 ₽",
                happened_at="Вчера, 18:03",
                kind="in",
            ),
            Activity(
                user_id=alex.id,
                title="Вы помогли Анне К.",
                amount_label="−700 ₽",
                happened_at="12 июня, 14:20",
                kind="out",
            ),
        ]
    )
    db.commit()
