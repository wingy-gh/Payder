import re

_PHONE_RE = re.compile(r"\+?[\d\s\-().]+")
_DIGITS_RE = re.compile(r"[\d\s\-]+")

REQUISITES_HINT = (
    "Укажите номер карты (13–19 цифр), номер телефона для СБП или 20-значный номер счёта"
)


def luhn_ok(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        number = int(char)
        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def normalize_phone(value: str) -> str:
    text = value.strip()
    if not _PHONE_RE.fullmatch(text):
        raise ValueError("Телефон: допустимы только цифры, +, пробелы, скобки и дефисы")
    digits = re.sub(r"\D", "", text)
    if not 7 <= len(digits) <= 15:
        raise ValueError("Телефон: должно быть от 7 до 15 цифр")
    return ("+" if text.startswith("+") else "") + digits


def normalize_requisites(value: str) -> str:
    """Приводит реквизиты к единому виду или бросает ValueError.

    Принимаем только три вида: номер карты (с проверкой контрольной цифры),
    номер телефона (для СБП) и 20-значный номер счёта. Любой другой текст,
    в том числе ссылки и буквы, отклоняется.
    """
    text = value.strip()
    if text.startswith("+"):
        try:
            return normalize_phone(text)
        except ValueError:
            raise ValueError(REQUISITES_HINT) from None
    if not _DIGITS_RE.fullmatch(text):
        raise ValueError(REQUISITES_HINT)
    digits = re.sub(r"\D", "", text)
    if 13 <= len(digits) <= 19 and luhn_ok(digits):
        return " ".join(digits[i:i + 4] for i in range(0, len(digits), 4))
    if len(digits) == 20:
        return digits
    if 10 <= len(digits) <= 15:
        return digits
    if 13 <= len(digits) <= 19:
        raise ValueError("Номер карты введён с ошибкой: не сходится контрольная цифра")
    raise ValueError(REQUISITES_HINT)
