import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")

    def __init__(self):
        if not self.GROQ_API_KEY:
            raise ValueError("❌ GROQ_API_KEY not found in .env file")


def get_settings():
    return Settings()