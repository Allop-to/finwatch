# finwatch/backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FinWatch"
    DATABASE_URL: str = "sqlite:///./finwatch.db"
    DEBUG: bool = True
    DETECTION_SCHEDULE_HOUR: int = 2
    DETECTION_INCREMENTAL_MINUTES: int = 30
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    LLM_ENABLED: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
