from fastapi import APIRouter

# Import from feature routers (new feature-based architecture)
from app.features.ai.parser_router import router as ai_parser_router
from app.features.auth.router import router as auth_router
from app.features.expenses.router import router as expenses_router
from app.features.groups.router import router as groups_router

# Utils and private routes remain in api/routes as they are infrastructure routes
from app.api.routes import private, utils
from app.core.config import settings

api_router = APIRouter()

# Feature routers - organized by domain
api_router.include_router(auth_router)  # login + users routes
api_router.include_router(expenses_router)  # expense management routes
api_router.include_router(groups_router)  # expense groups routes
api_router.include_router(ai_parser_router.router)  # AI parsing routes

# Infrastructure routes
api_router.include_router(utils.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
