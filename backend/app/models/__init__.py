"""ORM models mirroring `database.sql` (PostgreSQL). Import this module to register metadata."""

from app.db.base import Base
from app.models.identity import (
    UserIdentityFile,
    UserIdentityReviewDecision,
    UserIdentityVerification,
    UserIdentityVerificationLog,
)
from app.models.auth import OtpSession, RefreshToken
from app.models.post import Post, PostCategory, PostMedia
from app.models.provider import (
    Provider,
    ProviderBusinessProfile,
    ProviderDocument,
    ProviderIndividualProfile,
    ProviderStatusLog,
)
from app.models.provider_service import (
    ProviderDocumentService,
    ProviderService,
    ProviderServiceAttribute,
)
from app.models.taxonomy import (
    IndustryCategory,
    ServiceCategory,
    ServiceCategoryAttribute,
    ServiceCategoryRequirement,
    ServiceSkill,
)
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleAvailability,
    ProviderVehicleDocument,
    ServiceRoute,
    ServiceRouteSchedule,
)
from app.models.user import User, UserProfile, UserRole, UserStatusLog
from app.models.booking import (
    Booking,
    BookingStatusLog,
    CommissionConfig,
    DriverAvailabilitySession,
    DriverLocation,
    PriceConfig,
)
from app.models.payment import (
    PaymentTransaction,
    Promotion,
    PromotionUsage,
    Wallet,
    WalletTransaction,
)
from app.models.review import Review
from app.models.notification import Notification, NotificationSetting

__all__ = [
    "Base",
    "Booking",
    "BookingStatusLog",
    "CommissionConfig",
    "DriverAvailabilitySession",
    "DriverLocation",
    "PaymentTransaction",
    "PriceConfig",
    "Promotion",
    "PromotionUsage",
    "OtpSession",
    "RefreshToken",
    "IndustryCategory",
    "Post",
    "PostCategory",
    "PostMedia",
    "Provider",
    "ProviderBusinessProfile",
    "ProviderDocument",
    "ProviderDocumentService",
    "ProviderIndividualProfile",
    "ProviderService",
    "ProviderServiceAttribute",
    "ProviderStatusLog",
    "ProviderVehicle",
    "ProviderVehicleAvailability",
    "ProviderVehicleDocument",
    "ServiceCategory",
    "ServiceCategoryAttribute",
    "ServiceCategoryRequirement",
    "ServiceRoute",
    "ServiceRouteSchedule",
    "ServiceSkill",
    "User",
    "UserIdentityFile",
    "UserIdentityReviewDecision",
    "UserIdentityVerification",
    "UserIdentityVerificationLog",
    "UserProfile",
    "UserRole",
    "UserStatusLog",
    "Wallet",
    "WalletTransaction",
    "Review",
    "Notification",
    "NotificationSetting",
]
