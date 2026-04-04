from fastapi import APIRouter

from app.api.v1.admin.taxonomy import router as taxonomy_router
from app.api.v1.admin.users import router as users_router
from app.api.v1.admin.providers import router as providers_router
from app.api.v1.admin.posts import router as posts_router
from app.api.v1.admin.verifications import router as verifications_router
from app.api.v1.admin.transport import router as transport_router
from app.api.v1.admin.pricing import router as pricing_router
from app.api.v1.admin.bookings import router as bookings_router

router = APIRouter()

router.include_router(taxonomy_router, prefix="/taxonomy", tags=["admin-taxonomy"])
router.include_router(users_router, prefix="/users", tags=["admin-users"])
router.include_router(providers_router, prefix="/providers", tags=["admin-providers"])
router.include_router(posts_router, prefix="/posts", tags=["admin-posts"])
router.include_router(verifications_router, prefix="/user-verifications", tags=["admin-verifications"])
router.include_router(transport_router)
router.include_router(pricing_router)
router.include_router(bookings_router)