from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "AI-Powered Micro Learning Platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False  # Default False for production; override via env var for local dev

    # Database Settings
    DATABASE_URL: str

    @property
    def database_url_fixed(self) -> str:
        """
        SQLAlchemy 2.x requires 'postgresql://' but Render sometimes provides
        'postgres://' in the connection string. This property normalizes it.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Read from the .env file (only applies in local dev)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
