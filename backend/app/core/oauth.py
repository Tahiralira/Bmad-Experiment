"""
OAuth client configuration using Authlib.
Supports Google and GitHub OAuth2 providers.
"""

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

# OAuth client registry
oauth = OAuth()

# Supported OAuth providers
SUPPORTED_PROVIDERS = {"google", "github"}


def configure_oauth() -> None:
    """
    Configure OAuth clients for all supported providers.
    Called during application startup.
    """
    # Google OAuth2 (OpenID Connect)
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    # GitHub OAuth2
    if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
        oauth.register(
            name="github",
            client_id=settings.GITHUB_CLIENT_ID,
            client_secret=settings.GITHUB_CLIENT_SECRET,
            authorize_url="https://github.com/login/oauth/authorize",
            access_token_url="https://github.com/login/oauth/access_token",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email read:user"},
        )


def is_provider_configured(provider: str) -> bool:
    """Check if a specific OAuth provider is configured with credentials."""
    if provider == "google":
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    elif provider == "github":
        return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
    return False
