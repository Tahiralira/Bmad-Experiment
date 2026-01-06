from fastapi import APIRouter

# Import from feature routers (new feature-based architecture)
from app.features.auth.router import router as auth_router
from app.features.expenses.router import router as expenses_router

# Utils and private routes remain in api/routes as they are infrastructure routes
from app.api.routes import private, utils
from app.core.config import settings

api_router = APIRouter()

# Feature routers - organized by domain
api_router.include_router(auth_router)  # login + users routes
api_router.include_router(expenses_router)  # items routes (temporary)

# Infrastructure routes
api_router.include_router(utils.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
