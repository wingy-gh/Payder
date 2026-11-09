from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Добавляет защитные заголовки ко всем ответам.

    CSP ограничен только запретом встраивания в чужие страницы (clickjacking):
    строгая политика для скриптов могла бы сломать фронтенд.
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Content-Security-Policy", "frame-ancestors 'none'")
        headers.setdefault("Referrer-Policy", "same-origin")
        headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if get_settings().cookie_secure or request.url.scheme == "https":
            headers.setdefault("Strict-Transport-Security", "max-age=15552000")
        # Статика (JS/CSS) всегда перепроверяется: иначе после обновления браузер
        # может показывать старую версию сайта.
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            headers.setdefault("Cache-Control", "no-cache")
        # Ответы API содержат личные данные и реквизиты: не даём браузеру и прокси их кэшировать.
        if headers.get("content-type", "").startswith("application/json"):
            headers.setdefault("Cache-Control", "no-store")
        return response
