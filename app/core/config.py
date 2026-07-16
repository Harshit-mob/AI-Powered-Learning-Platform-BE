from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "AI-Powered Micro Learning Platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Database Settings
    DATABASE_URL: str
    
    # Read from the .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True, 
        extra="ignore"
    )

settings = Settings()
