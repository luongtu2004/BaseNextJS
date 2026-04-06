from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(validation_alias="DATABASE_URL")
    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    jwt_access_secret: str = Field(validation_alias="JWT_ACCESS_SECRET")
    jwt_refresh_secret: str = Field(validation_alias="JWT_REFRESH_SECRET")
    jwt_access_expire_minutes: int = Field(default=15, validation_alias="JWT_ACCESS_EXPIRE_MINUTES")
    jwt_refresh_expire_days: int = Field(default=30, validation_alias="JWT_REFRESH_EXPIRE_DAYS")
    otp_length: int = Field(default=6, validation_alias="OTP_LENGTH")
    otp_ttl_seconds: int = Field(default=300, validation_alias="OTP_TTL_SECONDS")
    otp_max_attempts: int = Field(default=5, validation_alias="OTP_MAX_ATTEMPTS")
    
    # Local AI
    local_ai_url: str = Field(default="http://localhost:11434/api/generate", validation_alias="LOCAL_AI_URL")
    local_ai_model: str = Field(default="llama3", validation_alias="LOCAL_AI_MODEL")
    local_ai_api_key: str | None = Field(default=None, validation_alias="LOCAL_AI_API_KEY")

    # Logging (like Log4j configuration)
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_dir: str = Field(default="logs", validation_alias="LOG_DIR")
    log_sql: bool = Field(default="False", validation_alias="LOG_SQL")

    # Identity Verification Thresholds
    ocr_confidence_threshold: float = Field(default=90.0, validation_alias="OCR_CONFIDENCE_THRESHOLD")
    face_match_threshold: float = Field(default=85.0, validation_alias="FACE_MATCH_THRESHOLD")
    liveness_threshold: float = Field(default=85.0, validation_alias="LIVENESS_THRESHOLD")

    # VNPAY Sandbox Configs
    vnpay_tmn_code: str = Field(default="", validation_alias="VNPAY_TMN_CODE")
    vnpay_hash_secret: str = Field(default="", validation_alias="VNPAY_HASH_SECRET")
    vnpay_payment_url: str = Field(default="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html", validation_alias="VNPAY_PAYMENT_URL")
    vnpay_return_url: str = Field(default="http://localhost:8000/api/v1/internal/payments/vnpay/return", validation_alias="VNPAY_RETURN_URL")

    # MoMo Sandbox Configs
    momo_partner_code: str = Field(default="", validation_alias="MOMO_PARTNER_CODE")
    momo_access_key: str = Field(default="", validation_alias="MOMO_ACCESS_KEY")
    momo_secret_key: str = Field(default="", validation_alias="MOMO_SECRET_KEY")
    momo_payment_url: str = Field(default="https://test-payment.momo.vn/v2/gateway/api/create", validation_alias="MOMO_PAYMENT_URL")
    momo_return_url: str = Field(default="http://localhost:8000/api/v1/internal/payments/momo/return", validation_alias="MOMO_RETURN_URL")
    momo_notify_url: str = Field(default="http://localhost:8000/api/v1/internal/payments/momo/callback", validation_alias="MOMO_NOTIFY_URL")

    # ZaloPay Sandbox Configs
    zalopay_app_id: str = Field(default="", validation_alias="ZALOPAY_APP_ID")
    zalopay_key1: str = Field(default="", validation_alias="ZALOPAY_KEY1")
    zalopay_key2: str = Field(default="", validation_alias="ZALOPAY_KEY2")
    zalopay_payment_url: str = Field(default="https://sb-openapi.zalopay.vn/v2/create", validation_alias="ZALOPAY_PAYMENT_URL")
    zalopay_callback_url: str = Field(default="http://localhost:8000/api/v1/internal/payments/zalopay/callback", validation_alias="ZALOPAY_CALLBACK_URL")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
