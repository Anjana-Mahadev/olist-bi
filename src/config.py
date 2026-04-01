import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    API_KEY: str = os.getenv("API_KEY", "")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "30 per minute")
    MAX_QUESTION_LENGTH: int = int(os.getenv("MAX_QUESTION_LENGTH", "1000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "5000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self):
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Set it in .env or as an environment variable.")


_settings = None


def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings