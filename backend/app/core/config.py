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

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
