from fastapi import APIRouter

from app.api.v1.admin.taxonomy import router as taxonomy_router
from app.api.v1.admin.users import router as users_router
from app.api.v1.admin.providers import router as providers_router
from app.api.v1.admin.posts import router as posts_router

router = APIRouter()

router.include_router(taxonomy_router, prefix="/taxonomy", tags=["admin-taxonomy"])
router.include_router(users_router, prefix="/users", tags=["admin-users"])
router.include_router(providers_router, prefix="/providers", tags=["admin-providers"])
router.include_router(posts_router, prefix="/posts", tags=["admin-posts"])