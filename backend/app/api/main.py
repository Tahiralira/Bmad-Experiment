from fastapi import APIRouter

# Import from feature routers (new feature-based architecture)
from app.features.ai.parser_router import router as ai_parser_router
from app.features.auth.router import router as auth_router
from app.features.expenses.router import router as expenses_router
from app.features.groups.router import router as groups_router
from app.features.notifications.router import router as notifications_router

# Utils routes remain in api/routes as they are infrastructure routes.
# (The template's /private user-creation router was deleted in WS8 — an
# env-flag-gated unauthenticated endpoint has no place in the product.)
from app.api.routes import utils

api_router = APIRouter()

# Feature routers - organized by domain
api_router.include_router(auth_router)  # auth + users routes
api_router.include_router(expenses_router)  # expense management routes
api_router.include_router(groups_router)  # expense groups routes
api_router.include_router(ai_parser_router)  # AI parsing routes
api_router.include_router(notifications_router)  # nudge engine routes (WS12)

# Infrastructure routes
api_router.include_router(utils.router)
