from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "internship-readiness-backend"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./internship_backend.db"

    jwt_secret_key: str = "change-this-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_minutes: int = 60 * 24 * 14

    ml_service_url: str = "http://localhost:8001"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
