from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    Uses Pydantic Settings for strict typing and parsing.
    """

    DATABASE_URL: str = ""
    SECRET_KEY: str = "super_secret_pengu_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MOCK_EVENTS_PATH: str = "../data/mock_events.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
