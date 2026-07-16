import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.oauth import configure_oauth


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    # send_default_pii=False (S5-M7): request headers/cookies — which carry
    # Bearer tokens — must never ship to Sentry. The 2.x default EventScrubber
    # additionally redacts Authorization and token-shaped values from events.
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        traces_sample_rate=1.0,
        send_default_pii=False,
    )

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Per-IP rate limiting (WS8/S5-H2): the middleware enforces the global
# default; stricter per-route tiers are decorated in the feature routers.
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    # Mediator voice, not a raw slowapi string
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Let's take a short breather — that was a lot of "
            "requests at once. Try again in a minute."
        },
    )


app.add_middleware(SlowAPIMiddleware)


# Security headers on every API response (WS8/S5-M1)
@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Tokens or codes must never leak via Referer (pairs with S5-H1)
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # The API serves JSON; the interactive docs pages are the one exception
    # (Swagger UI loads its assets from a CDN).
    if not request.url.path.startswith(("/docs", "/redoc")):
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
    if settings.ENVIRONMENT != "local":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


# Set all CORS enabled origins.
# allow_credentials stays False (S5-M6): auth is Bearer-in-header, not
# cookies — credentialed CORS would only turn a future origin misconfig
# into a credential leak.
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Session middleware for OAuth state management
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",  # Allow OAuth redirects
    https_only=settings.ENVIRONMENT != "local",  # HTTPS only in staging/production
)

# Configure OAuth providers
configure_oauth()

app.include_router(api_router, prefix=settings.API_V1_STR)
