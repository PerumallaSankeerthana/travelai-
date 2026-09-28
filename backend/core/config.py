from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):

    # Application
    app_name: str = "TravelAI"
    environment: str = "development"

    # Database
    database_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # LLM
    llm_provider: str = "gemini"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Ollama - kept for optional local development
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"

    # Travel APIs
    serp_api_key: str = ""
    openweather_api_key: str = ""
    mapbox_access_token: str = ""

    # Other integrations
    sendgrid_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()