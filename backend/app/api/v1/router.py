from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.common import router as common_router
from app.api.v1.customer import router as customer_router
from app.api.v1.customer_transport import router as customer_transport_router
from app.api.v1.health import router as health_router
from app.api.v1.provider import router as provider_router
from app.api.v1.provider_vehicles import router as provider_vehicles_router
from app.api.v1.provider_routes import router as provider_routes_router

api_router = APIRouter()
api_router.include_router(admin_router, prefix="/admin")
api_router.include_router(auth_router)
api_router.include_router(common_router)
api_router.include_router(customer_router)
api_router.include_router(customer_transport_router)
api_router.include_router(health_router)
api_router.include_router(provider_router)
api_router.include_router(provider_vehicles_router)
api_router.include_router(provider_routes_router)
