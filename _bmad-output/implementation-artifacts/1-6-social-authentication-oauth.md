# Story 1.6: Social Authentication (OAuth)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **new or existing user**,
I want to log in using Google or other social providers,
so that I can access the platform using my existing accounts.

## Acceptance Criteria

1. **Given** OAuth2 providers are configured (Google, GitHub)
   **When** I click "Login with Google"
   **Then** I am redirected to Google's OAuth consent screen

2. **And** after approval, I am redirected back with authorization code

3. **And** the backend exchanges the code for user info

4. **And** a user account is created or linked if it exists

5. **And** I receive a JWT token and am logged in

6. **And** my profile is populated with data from the OAuth provider (email, full_name)

7. **And** the API endpoint follows naming convention: `GET /api/v1/auth/oauth/{provider}`

## Tasks / Subtasks

- [x] Task 1: Install and configure Authlib for OAuth (AC: #1)
  - [x] Add `authlib>=1.3.0` to pyproject.toml dependencies
  - [x] Add `httpx>=0.27.0` for async HTTP client (required by Authlib)
  - [x] Add `itsdangerous>=2.1.0` for secure session signing (required by SessionMiddleware)
  - [x] Add `SessionMiddleware` to FastAPI app for OAuth state management
  - [x] Create `backend/app/core/oauth.py` for OAuth client configuration

- [x] Task 2: Add OAuth configuration settings (AC: #1, #3)
  - [x] Add to `backend/app/core/config.py`:
    - `GOOGLE_CLIENT_ID: str = ""`
    - `GOOGLE_CLIENT_SECRET: str = ""`
    - `GITHUB_CLIENT_ID: str = ""`
    - `GITHUB_CLIENT_SECRET: str = ""`
    - `OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000"` (for dev)
  - [x] Update `.env.example` with placeholder OAuth credentials
  - [x] Document how to obtain OAuth credentials from Google/GitHub

- [x] Task 3: Update User model for OAuth support (AC: #4, #6)
  - [x] Add `auth_method: str = "password"` field to User model (if not exists)
  - [x] Add `oauth_provider: str | None = None` field to User model
  - [x] Add `oauth_provider_id: str | None = None` field for provider's unique user ID
  - [x] Create Alembic migration for new fields
  - [x] Run migration against database

- [x] Task 4: Create OAuth login initiation endpoint (AC: #1, #7)
  - [x] Create `GET /api/v1/auth/oauth/{provider}/login` endpoint
  - [x] Generate OAuth authorization URL with correct scopes
  - [x] For Google: scopes = `['openid', 'email', 'profile']`
  - [x] For GitHub: scopes = `['user:email', 'read:user']`
  - [x] Store OAuth state in session for CSRF protection
  - [x] Return redirect response to provider's consent screen

- [x] Task 5: Create OAuth callback endpoint (AC: #2, #3, #4, #5, #6)
  - [x] Create `GET /api/v1/auth/oauth/{provider}/callback` endpoint
  - [x] Validate OAuth state from session (CSRF protection)
  - [x] Exchange authorization code for access token
  - [x] Fetch user info from provider's userinfo endpoint
  - [x] Extract email, name, and provider user ID from response
  - [x] Check if user exists by email OR by oauth_provider + oauth_provider_id
  - [x] If user exists: update OAuth fields if needed, generate JWT
  - [x] If user doesn't exist: create new user with OAuth data
  - [x] Return JWT token with 30-day expiration (PRD "Walled Garden")

- [x] Task 6: Handle account linking scenarios (AC: #4)
  - [x] If email matches existing password-based account: link OAuth to existing
  - [x] If email matches existing OAuth account (same provider): login normally
  - [x] If email matches existing OAuth account (different provider): link new provider
  - [x] Log account linking actions for audit trail

- [x] Task 7: Create frontend OAuth login buttons (AC: #1)
  - [x] Create `OAuthButtons.tsx` component in `frontend/src/features/auth/components/`
  - [x] Add "Login with Google" button with Google icon
  - [x] Add "Login with GitHub" button with GitHub icon
  - [x] Style buttons according to provider brand guidelines
  - [x] Wire buttons to call backend OAuth initiation endpoints

- [x] Task 8: Create frontend OAuth callback handler (AC: #5)
  - [x] Create route `/auth/callback` in TanStack Router
  - [x] Create `OAuthCallbackPage.tsx` component
  - [x] Read JWT token from URL query params (returned by backend)
  - [x] Store token in localStorage
  - [x] Redirect to dashboard on success
  - [x] Show error message on failure

- [x] Task 9: Write backend tests (All ACs)
  - [x] Test OAuth login initiation redirects correctly
  - [x] Test OAuth callback with valid authorization code
  - [x] Test OAuth callback creates new user
  - [x] Test OAuth callback links existing user by email
  - [x] Test OAuth callback with invalid state (CSRF)
  - [x] Test OAuth callback with invalid provider
  - [x] Mock external OAuth provider responses for testing

- [x] Task 10: Update API documentation
  - [x] Verify OpenAPI docs show new OAuth endpoints at `/docs`
  - [x] Add docstrings to all new functions
  - [x] Document OAuth setup instructions in README

## Dev Notes

### CRITICAL: OAuth Flow Architecture

This story implements **Social Authentication** using the **Authorization Code Flow**. Key architecture decisions:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OAuth2 Authorization Code Flow                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. User clicks "Login with Google"                                  │
│     ↓                                                                │
│  2. Frontend redirects to: GET /api/v1/auth/oauth/google/login       │
│     ↓                                                                │
│  3. Backend generates auth URL with state, redirects to Google       │
│     ↓                                                                │
│  4. User approves on Google consent screen                           │
│     ↓                                                                │
│  5. Google redirects to: GET /api/v1/auth/oauth/google/callback      │
│     with ?code=xxx&state=xxx                                         │
│     ↓                                                                │
│  6. Backend validates state, exchanges code for token                │
│     ↓                                                                │
│  7. Backend fetches user info, creates/links account                 │
│     ↓                                                                │
│  8. Backend redirects to frontend: /auth/callback?token=xxx          │
│     ↓                                                                │
│  9. Frontend stores JWT, redirects to dashboard                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Architecture Compliance

**File Locations:**
- OAuth Config: `backend/app/core/oauth.py` (NEW)
- Router: `backend/app/features/auth/router.py` (add OAuth routes)
- Models: `backend/app/features/auth/models.py` (add OAuth fields)
- Config: `backend/app/core/config.py` (add OAuth settings)
- Frontend: `frontend/src/features/auth/components/` (OAuth buttons)
- Routes: `frontend/src/routes/auth.callback.tsx` (NEW)

**Naming Conventions:**
- Database: `snake_case` (oauth_provider, oauth_provider_id)
- API JSON: `snake_case` fields
- Python: `snake_case` (PEP-8)
- TypeScript: `camelCase` for variables, `PascalCase` for components

**Endpoint Pattern:**
```
GET /api/v1/auth/oauth/{provider}/login     - Initiate OAuth flow
GET /api/v1/auth/oauth/{provider}/callback  - OAuth callback handler
```

### Technical Requirements

**Authlib OAuth Configuration (backend/app/core/oauth.py):**
```python
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config as StarletteConfig

from app.core.config import settings

# OAuth client registry
oauth = OAuth()

# Google OAuth2
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# GitHub OAuth2
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    api_base_url='https://api.github.com/',
    client_kwargs={
        'scope': 'user:email read:user'
    }
)
```

**SessionMiddleware Setup (backend/app/main.py):**
```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",  # Important for OAuth redirects
    https_only=False,  # Set True in production
)
```

**OAuth Login Endpoint Pattern:**
```python
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.core.oauth import oauth

SUPPORTED_PROVIDERS = {'google', 'github'}

@auth_router.get("/oauth/{provider}/login")
async def oauth_login(request: Request, provider: str):
    """
    Initiate OAuth login flow for the specified provider.
    Redirects user to provider's consent screen.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    # Build callback URL
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/{provider}/callback"

    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)
```

**OAuth Callback Endpoint Pattern:**
```python
@auth_router.get("/oauth/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    session: SessionDep
):
    """
    Handle OAuth callback from provider.
    Exchanges code for token, creates/links user, returns JWT.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    client = oauth.create_client(provider)

    try:
        token = await client.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth authentication failed: {str(e)}"
        )

    # Extract user info based on provider
    if provider == 'google':
        user_info = token.get('userinfo')
        if not user_info:
            user_info = await client.get('userinfo').json()
        email = user_info.get('email')
        full_name = user_info.get('name')
        provider_id = user_info.get('sub')  # Google's unique user ID

    elif provider == 'github':
        resp = await client.get('user')
        user_info = resp.json()
        provider_id = str(user_info.get('id'))
        full_name = user_info.get('name') or user_info.get('login')

        # GitHub may not include email in profile - need separate call
        email = user_info.get('email')
        if not email:
            emails_resp = await client.get('user/emails')
            emails = emails_resp.json()
            # Find primary verified email
            for e in emails:
                if e.get('primary') and e.get('verified'):
                    email = e.get('email')
                    break

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve email from OAuth provider"
        )

    # Find or create user
    user = find_or_create_oauth_user(
        session=session,
        email=email,
        full_name=full_name,
        provider=provider,
        provider_id=provider_id
    )

    # Generate JWT with 30-day expiration
    access_token_expires = timedelta(days=settings.LOGIN_TOKEN_EXPIRE_DAYS)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    # Redirect to frontend with token
    frontend_callback_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_callback_url)
```

**User Finding/Creation Service:**
```python
def find_or_create_oauth_user(
    session: Session,
    email: str,
    full_name: str | None,
    provider: str,
    provider_id: str
) -> User:
    """
    Find existing user or create new one for OAuth login.

    Logic:
    1. First try to find by oauth_provider + oauth_provider_id (exact match)
    2. Then try to find by email (account linking)
    3. If not found, create new user
    """
    # Try to find by OAuth provider ID first (existing OAuth user)
    user = session.exec(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_provider_id == provider_id
        )
    ).first()

    if user:
        return user

    # Try to find by email (potential account linking)
    user = session.exec(
        select(User).where(User.email == email)
    ).first()

    if user:
        # Link OAuth to existing account
        user.oauth_provider = provider
        user.oauth_provider_id = provider_id
        if user.auth_method == AUTH_METHOD_PASSWORD:
            user.auth_method = AUTH_METHOD_OAUTH  # Or keep as PASSWORD if you want both
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    # Create new OAuth user
    placeholder_password = secrets.token_urlsafe(32)
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(placeholder_password),
        auth_method=AUTH_METHOD_OAUTH,
        oauth_provider=provider,
        oauth_provider_id=provider_id,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

### Frontend Implementation Details

**OAuth Buttons Component:**
```typescript
// frontend/src/features/auth/components/OAuthButtons.tsx
export function OAuthButtons() {
  const handleOAuthLogin = (provider: 'google' | 'github') => {
    // Redirect to backend OAuth endpoint
    window.location.href = `/api/v1/auth/oauth/${provider}/login`
  }

  return (
    <div className="oauth-buttons">
      <button
        onClick={() => handleOAuthLogin('google')}
        className="oauth-button google"
      >
        <GoogleIcon /> Continue with Google
      </button>
      <button
        onClick={() => handleOAuthLogin('github')}
        className="oauth-button github"
      >
        <GitHubIcon /> Continue with GitHub
      </button>
    </div>
  )
}
```

**OAuth Callback Page:**
```typescript
// frontend/src/routes/auth.callback.tsx
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router'
import { useEffect } from 'react'

export const Route = createFileRoute('/auth/callback')({
  component: OAuthCallbackPage,
  validateSearch: (search: Record<string, unknown>) => ({
    token: search.token as string | undefined,
    error: search.error as string | undefined,
  }),
})

function OAuthCallbackPage() {
  const navigate = useNavigate()
  const { token, error } = Route.useSearch()

  useEffect(() => {
    if (error) {
      // Handle error
      navigate({ to: '/login', search: { error } })
      return
    }

    if (token) {
      // Store token and redirect to dashboard
      localStorage.setItem('access_token', token)
      navigate({ to: '/' })
    }
  }, [token, error, navigate])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
        <p className="mt-4">Completing sign in...</p>
      </div>
    </div>
  )
}
```

### Security Considerations

1. **CSRF Protection via State Parameter:**
   - Authlib automatically generates and validates OAuth state
   - State is stored in session and validated on callback
   - This prevents CSRF attacks on the callback endpoint

2. **Token Storage:**
   - JWT returned via URL query parameter (required for redirect flow)
   - Frontend immediately stores in localStorage
   - Consider adding `state` parameter from frontend for additional verification

3. **Account Enumeration:**
   - OAuth doesn't expose whether email exists
   - Always creates or links account (no enumeration risk)

4. **Provider User ID:**
   - Store `oauth_provider_id` to identify user across sessions
   - More reliable than email (email can change in some providers)

5. **SessionMiddleware Security:**
   - Use `https_only=True` in production
   - Use `same_site="lax"` to allow OAuth redirects
   - Session secret must match `SECRET_KEY`

### OAuth Provider Setup Instructions

**Google OAuth Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client IDs"
5. Configure consent screen (External for public apps)
6. Select "Web application"
7. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/oauth/google/callback`
8. Copy Client ID and Client Secret to `.env`

**GitHub OAuth Setup:**
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in application details
4. Set Authorization callback URL: `http://localhost:8000/api/v1/auth/oauth/github/callback`
5. Copy Client ID
6. Generate and copy Client Secret to `.env`

### Project Structure Notes

**Backend Changes:**
```
backend/app/
├── core/
│   ├── config.py           # Add OAuth client IDs/secrets
│   └── oauth.py            # NEW: Authlib OAuth configuration
├── features/auth/
│   ├── models.py           # Add oauth_provider, oauth_provider_id fields
│   ├── router.py           # Add OAuth login/callback endpoints
│   └── service.py          # Add find_or_create_oauth_user function
├── main.py                 # Add SessionMiddleware
└── alembic/
    └── versions/           # NEW: Migration for OAuth fields
```

**Frontend Changes:**
```
frontend/src/
├── features/auth/
│   └── components/
│       └── OAuthButtons.tsx        # NEW: OAuth login buttons
├── routes/
│   ├── login.tsx                   # Add OAuthButtons component
│   └── auth.callback.tsx           # NEW: OAuth callback handler
└── routeTree.gen.ts                # Auto-generated
```

### Testing Commands

```bash
# Start Docker containers
docker compose up -d

# Run backend tests
docker compose exec backend pytest -v tests/

# Test OAuth login initiation manually
# This should redirect to Google consent screen
open "http://localhost:8000/api/v1/auth/oauth/google/login"

# Frontend build
cd cleardues/frontend && npm run build

# Run frontend type checking
cd cleardues/frontend && npm run typecheck
```

### Previous Story Intelligence

**From Story 1.5 (Login with JWT):**
- JWT token generation with 30-day expiration established
- Token storage in localStorage pattern confirmed
- 401 error handling interceptor already implemented
- TanStack Router file-based routing established
- 18 auth-related backend tests pass

**From Story 1.4 (Registration with Magic Link):**
- `AUTH_METHOD_MAGIC_LINK` constant defined in models.py
- Generic success messages pattern for security
- Rate limiting infrastructure exists (can be extended)

**Patterns to Reuse:**
- `TokenWithUser` response model (for OAuth callback)
- `security.create_access_token()` for JWT generation
- `settings.LOGIN_TOKEN_EXPIRE_DAYS` for 30-day expiration
- localStorage token storage pattern

**Patterns to Add:**
- `AUTH_METHOD_OAUTH = "oauth"` constant
- `oauth_provider` and `oauth_provider_id` User fields

### Git Intelligence

**Recent Commits:**
- `43ed2c5` - Story 1.5: User login with JWT authentication
- `df16775` - Story 1.4: User registration with magic link
- `e4723d3` - Story 1.3: Database models with timestamps
- `2b4721d` - Stories 1.1 & 1.2: Project init and feature-based architecture

**Commit Message Format:**
```
feat: Complete Story 1.6 - Social authentication (OAuth)
```

### Web Research Intelligence (2025/2026 Best Practices)

**OAuth Library Choice: Authlib (Recommended)**
- Native Starlette/FastAPI integration via `authlib.integrations.starlette_client`
- Handles state management, token exchange, and CSRF protection
- Supports automatic OpenID Connect discovery (Google)
- Well-maintained with regular security updates

**Alternative Considered: httpx-oauth (via FastAPI Users)**
- Pure async implementation
- Would require FastAPI Users library (adds complexity)
- Less flexible for custom user model integration

**Google OpenID Connect:**
- Use server_metadata_url for automatic discovery
- URL: `https://accounts.google.com/.well-known/openid-configuration`
- Returns `id_token` with user info (no extra API call needed)

**GitHub OAuth:**
- Requires manual endpoint configuration (not OpenID Connect)
- Requires separate API call to get user email (not always in profile)
- Check primary + verified email from `/user/emails` endpoint

**Security Updates (2025):**
- FastAPI-SSO v1.0.0+ uses server-side state store (more secure)
- Always validate state parameter to prevent CSRF
- Consider adding PKCE for public clients (future enhancement)

Sources:
- [Authlib FastAPI Integration](https://docs.authlib.org/en/latest/client/fastapi.html)
- [FastAPI Users OAuth](https://fastapi-users.github.io/fastapi-users/10.0/configuration/oauth/)
- [FastAPI-SSO](https://github.com/tomasvotava/fastapi-sso)
- [Google OpenID Connect](https://accounts.google.com/.well-known/openid-configuration)

### References

- [Source: epics.md - Story 1.6](../_bmad-output/planning-artifacts/epics.md#story-16-social-authentication-oauth)
- [Source: architecture.md - Authentication & Security](../_bmad-output/planning-artifacts/architecture.md#authentication--security)
- [Source: prd.md - FR1 (Walled Garden)](../_bmad-output/planning-artifacts/prd.md)
- [Source: Story 1.5 - User Login with JWT](./1-5-user-login-with-jwt-authentication.md)
- [Source: Story 1.4 - Magic Link Registration](./1-4-user-registration-with-magic-link.md)
- [Existing Code: features/auth/router.py](../../cleardues/backend/app/features/auth/router.py)
- [Existing Code: features/auth/service.py](../../cleardues/backend/app/features/auth/service.py)
- [Existing Code: features/auth/models.py](../../cleardues/backend/app/features/auth/models.py)
- [Existing Code: core/config.py](../../cleardues/backend/app/core/config.py)
- [Existing Code: core/security.py](../../cleardues/backend/app/core/security.py)

### API Contract

**GET /api/v1/auth/oauth/{provider}/login**
```
// Request
GET /api/v1/auth/oauth/google/login

// Response (302 Redirect)
Location: https://accounts.google.com/o/oauth2/v2/auth?
  client_id=xxx&
  redirect_uri=http://localhost:8000/api/v1/auth/oauth/google/callback&
  scope=openid%20email%20profile&
  state=xxx&
  response_type=code
```

**GET /api/v1/auth/oauth/{provider}/callback**
```
// Request (from OAuth provider)
GET /api/v1/auth/oauth/google/callback?code=xxx&state=xxx

// Response (302 Redirect on success)
Location: http://localhost:5173/auth/callback?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

// Response (400 on error)
{
  "detail": "OAuth authentication failed: invalid state"
}

// Response (400 for unsupported provider)
{
  "detail": "Unsupported OAuth provider: twitter"
}
```

### Environment Variables Required

```bash
# .env additions for OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
OAUTH_REDIRECT_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### Database Migration

```python
# alembic/versions/xxx_add_oauth_fields.py
def upgrade():
    op.add_column('user', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('user', sa.Column('oauth_provider_id', sa.String(255), nullable=True))

    # Create index for OAuth lookups
    op.create_index(
        'ix_user_oauth_provider_id',
        'user',
        ['oauth_provider', 'oauth_provider_id'],
        unique=True,
        postgresql_where=sa.text('oauth_provider IS NOT NULL')
    )

def downgrade():
    op.drop_index('ix_user_oauth_provider_id', 'user')
    op.drop_column('user', 'oauth_provider_id')
    op.drop_column('user', 'oauth_provider')
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. All 10 tasks completed successfully
2. OAuth flow implemented for Google and GitHub providers
3. Authlib library used for OAuth2 client functionality
4. SessionMiddleware added for CSRF state management
5. User model extended with oauth_provider and oauth_provider_id fields
6. Account linking logic handles existing users by email
7. Frontend components added to both login and register pages
8. 15 OAuth-specific tests added covering all scenarios
9. Migration created for new database fields
10. OpenAPI documentation auto-generated by FastAPI

### File List

**Backend Files Created/Modified:**
- `backend/pyproject.toml` - Added authlib and itsdangerous dependencies
- `backend/app/main.py` - Added SessionMiddleware and OAuth configuration
- `backend/app/core/config.py` - Added OAuth settings (client IDs, secrets, redirect URL)
- `backend/app/core/oauth.py` - NEW: OAuth client configuration for Google/GitHub
- `backend/app/features/auth/models.py` - Added oauth_provider and oauth_provider_id fields
- `backend/app/features/auth/router.py` - Added OAuth login/callback endpoints
- `backend/app/features/auth/service.py` - Added find_or_create_oauth_user function
- `backend/app/alembic/versions/b4d8e2f5a6c9_add_oauth_fields_to_user.py` - NEW: Migration
- `backend/tests/api/routes/test_auth.py` - Added 15 OAuth tests
- `.env` - Added OAuth environment variables
- `.env.example` - NEW: OAuth environment variables template (AI-Review fix)
- `README.md` - Added OAuth setup documentation (AI-Review fix)

**Frontend Files Created/Modified:**
- `frontend/src/features/auth/components/OAuthButtons.tsx` - NEW: OAuth login buttons
- `frontend/src/features/auth/components/index.ts` - Export OAuthButtons
- `frontend/src/routes/login.tsx` - Added OAuthButtons component
- `frontend/src/routes/register.tsx` - Added OAuthButtons component
- `frontend/src/routes/auth.callback.tsx` - NEW: OAuth callback handler page
- `frontend/src/routeTree.gen.ts` - Auto-generated route tree (TanStack Router)

## Senior Developer Review (AI)

**Reviewed by:** Claude Opus 4.5 (AI Code Review)
**Review Date:** 2026-01-07

### Review Summary

| Severity | Found | Fixed |
|----------|-------|-------|
| HIGH | 2 | 2 |
| MEDIUM | 4 | 3 |
| LOW | 3 | 1 |

### Issues Fixed During Review

1. **[HIGH] README OAuth Documentation Missing** - Added complete OAuth setup instructions for Google and GitHub to README.md
2. **[HIGH] .env.example Missing** - Created .env.example with OAuth placeholder variables
3. **[MEDIUM] File List Incomplete** - Added routeTree.gen.ts and other missing files to File List
4. **[MEDIUM] Undocumented Dependency** - Added itsdangerous to Task 1 subtasks
5. **[LOW] Import Inside Function** - Moved `import secrets` to top of router.py

### Outstanding Items (Deferred)

1. **[MEDIUM] No Frontend Tests** - OAuthButtons.tsx and auth.callback.tsx have no unit tests. Consider adding in future iteration.
2. **[MEDIUM] JWT Expiration Inconsistency** - Registration magic link uses ACCESS_TOKEN_EXPIRE_MINUTES (8 days) while login uses LOGIN_TOKEN_EXPIRE_DAYS (30 days). May be intentional design decision.
3. **[LOW] .env Contains Actual Secrets** - The .env file has non-placeholder values. Verified .env is in .gitignore - acceptable for local development.
4. **[LOW] Model Index Definition** - oauth_provider_id doesn't have index=True in SQLModel definition, but migration creates the index. Minor inconsistency.

### Acceptance Criteria Validation

| AC | Status | Notes |
|----|--------|-------|
| #1 OAuth providers configured, redirect to consent | PASS | Google and GitHub configured in oauth.py |
| #2 Redirected back with authorization code | PASS | Callback endpoint handles code exchange |
| #3 Backend exchanges code for user info | PASS | authorize_access_token in router.py |
| #4 User account created or linked | PASS | find_or_create_oauth_user in service.py |
| #5 Receive JWT token | PASS | 30-day JWT returned |
| #6 Profile populated from provider | PASS | email, full_name extracted |
| #7 API endpoint naming convention | PASS | /api/v1/auth/oauth/{provider}/login and /callback |

### Recommendation

**Status: APPROVED with notes**

All acceptance criteria are met. Core OAuth functionality is complete and tested. The outstanding items are minor improvements that can be addressed in future iterations.
