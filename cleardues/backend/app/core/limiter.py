# Per-IP rate limiting (WS8/S5-H2, NFR5).
#
# The only throttle the app had was the per-email DB counter on magic-link
# requests — trivially bypassed by rotating the email field. slowapi gives
# per-IP limits: a strict tier on the brute-forceable/expensive endpoints
# (auth, AI parse) plus a global default on everything else via
# SlowAPIMiddleware in app.main.
#
# Storage is in-memory per worker process (4 uvicorn workers → effective
# limits are up to 4× the configured numbers). Good enough for the private
# beta; a shared Redis backend arrives with the WS12 infra if needed.

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Route-tier limits. Auth endpoints are brute-forceable; AI parse spends
# real money per call.
AUTH_LIMIT = "10/minute"
AI_PARSE_LIMIT = "20/minute"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    enabled=settings.RATE_LIMIT_ENABLED,
)
