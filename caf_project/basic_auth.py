"""HTTP Basic Auth gate to keep bots and drive-by traffic off the dataroom.

Not a real security boundary — the password lives in env (with a fallback)
and is shared. Goal is just to require an explicit credential before any
content is served.
"""
import base64

from django.conf import settings
from django.http import HttpResponse


def _unauthorized():
    response = HttpResponse("Authentication required.", status=401)
    response["WWW-Authenticate"] = 'Basic realm="CAF Dataroom"'
    return response


class BasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.password = getattr(settings, "BASIC_AUTH_PASSWORD", "") or ""
        self.enabled = bool(self.password)

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Basic "):
            return _unauthorized()

        try:
            decoded = base64.b64decode(header[6:].strip()).decode("utf-8", errors="ignore")
        except (ValueError, UnicodeDecodeError):
            return _unauthorized()

        if ":" not in decoded:
            return _unauthorized()

        _, password = decoded.split(":", 1)
        if password != self.password:
            return _unauthorized()

        return self.get_response(request)
